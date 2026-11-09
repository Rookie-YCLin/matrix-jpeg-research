"""32-bit, pilot-free G6 decoder candidates + singular-gap QIM control.

All decisions use only received image/known keys; payload only for scoring.
Original G6 marked PNG hash is checked against archived evidence. No prior
payload bits or correct BER are used to choose a decoding orientation.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from urllib.request import urlopen
from importlib.metadata import distribution
from types import MethodType

import cv2
import numpy as np
from PIL import Image
from blind_watermark.bwm_core import random_strategy1, one_dim_kmeans

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance
from experiments.svd_qim_validation import PAYLOADS

D1, D2 = 90, 20
QFS = (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30,40,50,70,95)
PAYLOAD_NAMES = ("primary", "holdout", "complement")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def bitstr(vec):
    return "".join(str(int(v)) for v in vec)


def error_count(a,b):
    assert len(a)==len(b)
    return sum(x!=y for x,y in zip(a,b))


def invert(bits):
    return "".join("1" if v=="0" else "0" for v in bits)


def kmeans(scores):
    return bitstr(one_dim_kmeans(np.asarray(scores,dtype=np.float64)))


def align(scores, n):
    indices=np.arange(n)
    np.random.RandomState(fixed.KEYS["password_wm"]).shuffle(indices)
    y=np.array(scores,dtype=float)
    z=y.copy()
    z[indices]=y
    return z


def aggregate(raw, n):
    # Return n payload positions after averaging all 3 channels and repetitions.
    per_channel=np.asarray([align([raw[c,i::n].mean() for i in range(n)],n)
                            for c in range(3)])
    return per_channel.mean(axis=0), per_channel


def signals(rgb, n=32):
    core=configured_instance(D1,D2).bwm_core
    core.wm_size=n
    core.read_img_arr(img=fixed.to_bgr(rgb))
    core.init_block_index()
    permutation=random_strategy1(seed=core.password_img,size=core.block_num,block_shape=16)
    hard1=np.empty((3,core.block_num))
    hard2=np.empty((3,core.block_num))
    soft1=np.empty((3,core.block_num))
    soft2=np.empty((3,core.block_num))
    for c in range(3):
        for k, b_index in enumerate(core.block_index):
            block=core.ca_block[c][b_index]
            shuffled=cv2.dct(block).flatten()[permutation[k]].reshape(4,4)
            singular=np.linalg.svd(shuffled,compute_uv=False)
            r1=float(singular[0] % D1)
            r2=float(singular[1] % D2)
            hard1[c,k]=float(r1>D1/2)
            hard2[c,k]=float(r2>D2/2)
            soft1[c,k]=0.5*(1-np.sin(2*np.pi*r1/D1))
            soft2[c,k]=0.5*(1-np.sin(2*np.pi*r2/D2))
    h1,ch1=aggregate(hard1,n)
    h2,ch2=aggregate(hard2,n)
    t1,_=aggregate(soft1,n)
    t2,_=aggregate(soft2,n)
    return h1,h2,t1,t2,ch1,ch2


def correlation(a,b):
    x=np.asarray(a,dtype=float);y=np.asarray(b,dtype=float)
    if x.std()<1e-12 or y.std()<1e-12:return 0.0
    return float(np.corrcoef(x,y)[0,1])


def decode_candidates(h1,h2,t1,t2):
    base=kmeans(.75*h1+.25*h2)
    b1=kmeans(h1)
    b2=kmeans(h2)
    rho=correlation(h1,h2)
    agreement=sum(a==b for a,b in zip(b1,b2))
    # Reference is *the independent second singular value*, not known payload.
    flip=agreement<16
    center_s1=(1-h1) if flip else h1
    corr_soft=correlation(t1,t2)
    soft_flip=corr_soft<0
    # Use only received QIM votes; never compare with ground truth.
    return {
      "G6_baseline":base,
      "s1_hard_only":b1,
      "s2_hard_only":b2,
      "fixed_equal_weights":kmeans(.5*h1+.5*h2),
      "fixed_s2_weight_75":kmeans(.25*h1+.75*h2),
      "self_polarity_S1_only":invert(b1) if flip else b1,
      "self_polarity_G6":invert(base) if flip else base,
      "self_select_S2_on_conflict":b2 if flip else base,
      "self_fuse_oriented_S1_S2":kmeans(.75*center_s1+.25*h2),
      "soft_QIM_combined":kmeans(.75*t1+.25*t2),
      "soft_QIM_s2_only":kmeans(t2),
      "soft_QIM_orient_from_soft_rho":kmeans(.75*((1-t1) if soft_flip else t1)+.25*t2),
      "soft_QIM_orient_from_hard_agreement":kmeans(.75*((1-t1) if flip else t1)+.25*t2),
    }, {
      "hard_corr":rho,
      "soft_corr":corr_soft,
      "b1_b2_agree":agreement,
      "flip_from_agreement":flip,
      "soft_flip_from_corr":soft_flip,
    }


def gap_embed(self,arg):
    block, shuffler, i=arg
    bit=int(self.wm_bit[i%self.wm_size])
    mat=cv2.dct(block).flatten()[shuffler].reshape(self.block_shape)
    u,s,v=np.linalg.svd(mat)
    delta=float(s[0]-s[1])
    new_delta=(np.floor(delta/D1)+.25+.5*bit)*D1
    s[0]=s[1]+new_delta
    mat_flat=np.dot(u,np.dot(np.diag(s),v)).flatten()
    mat_flat[shuffler]=mat_flat.copy()
    return cv2.idct(mat_flat.reshape(self.block_shape))


def gap_get(self,arg):
    block,shuffler=arg
    mat=cv2.dct(block).flatten()[shuffler].reshape(self.block_shape)
    s=np.linalg.svd(mat,compute_uv=False)
    return float((s[0]-s[1])%D1>D1/2)


def gap_instance():
    wm=configured_instance(D1,D2)
    wm.bwm_core.block_add_wm_slow=MethodType(gap_embed,wm.bwm_core)
    wm.bwm_core.block_get_wm_slow=MethodType(gap_get,wm.bwm_core)
    return wm


def gap_decode(rgb):
    wm=gap_instance()
    vals=np.asarray(wm.extract(embed_img=fixed.to_bgr(rgb),
                               wm_shape=32,mode="bit"))
    return bitstr(vals)


def attack(path,out,prefix,qf):
    jpg=out/f"{prefix}_q{qf:02d}.jpg"
    with Image.open(path) as im:
        im.save(jpg,format="JPEG",quality=qf,**fixed.JPEG)
    return fixed.read_rgb(jpg)


def baseline_decoder(rgb):
    wm=configured_instance(D1,D2)
    return bitstr(np.asarray(wm.extract(embed_img=fixed.to_bgr(rgb),wm_shape=32,mode="bit")))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=False)
    info=json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if info.get("vcs_info",{}).get("commit_id")!=fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Pinned upstream revision changed")
    with urlopen(fixed.SOURCE_URL,timeout=60) as u:
        payload=u.read()
    if fixed.git_blob_sha(payload)!=fixed.SOURCE_BLOB_SHA:
        raise RuntimeError("Pinned image changed")
    source=out/"original.jpeg"
    source.write_bytes(payload)
    rgb=fixed.read_rgb(source)
    attempts=[]
    benchmarks=[]
    for case in PAYLOAD_NAMES:
        truth=PAYLOADS[case]
        png=out/f"{case}_G6.png"
        wm=configured_instance(D1,D2)
        wm.read_img(img=fixed.to_bgr(rgb))
        wm.read_wm([int(v) for v in truth],mode="bit")
        wm.embed(filename=str(png))
        if baseline_decoder(fixed.read_rgb(png))!=truth:
            raise RuntimeError("G6 clean PNG invalid")
        if case=="primary":
            archived="d289b94ff41a4509fa363577b34e4a51026d834afa9dd4a3bcc6c1728d987541"
            if fixed.sha256_file(png)!=archived:
                raise RuntimeError("G6 mark not identical to archived control")
        for qf in QFS:
            rx=attack(png,out,f"{case}_G6",qf)
            h1,h2,t1,t2,_,_=signals(rx)
            result,diag=decode_candidates(h1,h2,t1,t2)
            stock=baseline_decoder(rx)
            if result["G6_baseline"]!=stock:
                raise RuntimeError(f"Extractor not equivalent to G6 at {case}, QF{qf}")
            for method,bits in result.items():
                row={"case":case,"qf":qf,"method":method,
                     "errors":error_count(truth,bits),
                     "ber":error_count(truth,bits)/32,
                     "bits":bits}
                attempts.append(row)
            benchmarks.append({"case":case,"qf":qf,**diag})
            print("DECODE_COMPARE="+json.dumps(
                {"case":case,"qf":qf,"rho":round(diag["hard_corr"],4),
                 "agreement":diag["b1_b2_agree"],"flip":diag["flip_from_agreement"],
                 "errors":{k:error_count(truth,v) for k,v in result.items()}}
            ),flush=True)
    write_csv(out/"decoder_results.csv",attempts)
    write_csv(out/"decoder_diagnostics.csv",benchmarks)

    gap_rows=[]
    for case in PAYLOAD_NAMES:
        truth=PAYLOADS[case]
        marked=out/f"{case}_gap_QIM.png"
        encoder=gap_instance()
        encoder.read_img(img=fixed.to_bgr(rgb))
        encoder.read_wm([int(v) for v in truth],mode="bit")
        encoder.embed(filename=str(marked))
        clean=gap_decode(fixed.read_rgb(marked))
        nerr=error_count(truth,clean)
        if nerr:
            raise RuntimeError(f"Gap QIM has {nerr}/32 errors on clean PNG; method invalid")
        # Relative original-image quality before JPEG (one of several trade-off metrics).
        original=rgb.astype(float)
        embedded=fixed.read_rgb(marked).astype(float)
        mse=float(np.mean(np.square(embedded-original)))
        psnr=float(10*np.log10(255.0**2/mse)) if mse else float("inf")
        for qf in QFS:
            rx=attack(marked,out,f"{case}_gap",qf)
            got=gap_decode(rx)
            row={"case":case,"qf":qf,"method":"singular_gap_QIM_90",
                 "errors":error_count(truth,got),"ber":error_count(truth,got)/32,
                 "pre_jpeg_psnr_db":psnr,"bits":got}
            gap_rows.append(row)
            print("GAP_COMPARE="+json.dumps(
                {"case":case,"qf":qf,"errors":row["errors"],"psnr":round(psnr,3)}),flush=True)
    write_csv(out/"gap_results.csv",gap_rows)
    (out/"manifest.json").write_text(json.dumps({
        "status":"complete","d1":D1,"d2":D2,"qfs":QFS,
        "cases":PAYLOAD_NAMES,"jpeg":fixed.JPEG,
        "upstream_commit":fixed.UPSTREAM_COMMIT,
        "source_sha256":fixed.sha256_file(source),
        "notes":[
          "G6 decoder variants reuse exact archived 32bit marked PNG for primary",
          "No pilot; decoder orientation relies only on agreement of s1/s2 estimates",
          "SVD-gap candidate re-embeds exactly 32 data bits with a new rule",
          "Payload is used only for evaluation, not for decoding or parameter selection"
        ]
    },indent=2)+"\n",encoding="utf-8")
    print("TEST_COMPLETE="+json.dumps({
      "original_decoder":next(r for r in attempts if r["case"]=="primary" and r["qf"]==5 and r["method"]=="G6_baseline"),
      "primary_5_8": [
         {"qf":q,"method":name,"errors":next(r["errors"] for r in attempts
                 if r["case"]=="primary" and r["qf"]==q and r["method"]==name)}
         for q in (5,6,7,8)
         for name in ("G6_baseline","self_polarity_S1_only","self_select_S2_on_conflict",
                      "self_fuse_oriented_S1_S2","soft_QIM_orient_from_hard_agreement")
      ]
    }),flush=True)

if __name__=="__main__":
    main()
