"""Investigate G6 QF5-8 inversion and test a *blind* pilot-based correction.

Existing G6 d1/d2 values, image, JPEG settings, 32 data bits and upstream
algorithm are unchanged for the local-vote diagnostic. Pilot control embeds
extra, public reference bits and is clearly marked a *new* candidate.
All decision functions use only received data and published pilots.
Ground truth is used exclusively for post-hoc reporting.
"""
from __future__ import annotations
import csv
import json
from argparse import ArgumentParser
from pathlib import Path
from urllib.request import urlopen
from importlib.metadata import distribution

import cv2
import numpy as np
from PIL import Image
from blind_watermark.bwm_core import one_dim_kmeans, random_strategy1

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance
from experiments.svd_qim_validation import PAYLOADS

D1,D2=90,20
QFS_DIAG=(4,5,6,7,8,9,10)
QFS_PILOT=(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30,40,50,70,95)
PILOTS={"p8":"01011010","p16":"0101101010010110"}

def dump(path, rows):
    if not rows: return
    with path.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

def bits_str(a):
    a=np.asarray(a)
    return "".join(str(int(x)) for x in a)

def errs(reference, received):
    if len(reference)!=len(received): raise AssertionError("Different lengths")
    return sum(a!=b for a,b in zip(reference,received))

def undo_shuffle(scores, length):
    indices=np.arange(length)
    np.random.RandomState(fixed.KEYS["password_wm"]).shuffle(indices)
    score=np.array(scores,copy=True,dtype=float)
    out=score.copy()
    out[indices]=score.copy()
    return out

def km_bits(scores):
    return bits_str(one_dim_kmeans(np.asarray(scores,dtype=float)))

def qf_attack(path, directory, qf, prefix):
    file=directory/f"{prefix}_qf{qf:02}.jpg"
    with Image.open(path) as img:
        img.save(file,format="JPEG",quality=qf,**fixed.JPEG)
    return fixed.read_rgb(file)

def generic_extract(rgb,n):
    wm=configured_instance(D1,D2)
    result=np.asarray(wm.extract(embed_img=fixed.to_bgr(rgb),wm_shape=n,mode="bit"))
    if result.shape!=(n,) or not np.isin(result,[0,1]).all():
        raise AssertionError("Public blind decoder returned wrong shape")
    return bits_str(result)

def localized_votes(rgb):
    core=configured_instance(D1,D2).bwm_core
    core.wm_size=fixed.WM_SIZE
    core.read_img_arr(img=fixed.to_bgr(rgb))
    core.init_block_index()
    shuffle=random_strategy1(seed=core.password_img,size=core.block_num,
                             block_shape=16)
    first=np.empty((3,core.block_num),dtype=np.float64)
    second=np.empty_like(first)
    for channel in range(3):
        blocks=core.ca_block[channel]
        for i,where in enumerate(core.block_index):
            b=blocks[where]
            shuffled=cv2.dct(b).flatten()[shuffle[i]].reshape(4,4)
            sigma=np.linalg.svd(shuffled,compute_uv=False)
            first[channel,i]=float(sigma[0]%D1 > D1/2)
            second[channel,i]=float(sigma[1]%D2 > D2/2)

    def aggregate(raw):
        perchannel=np.array([
            undo_shuffle(np.array([raw[c,j::fixed.WM_SIZE].mean()
                                   for j in range(fixed.WM_SIZE)]),fixed.WM_SIZE)
            for c in range(3)])
        return perchannel,perchannel.mean(axis=0)

    ch1,s1=aggregate(first)
    ch2,s2=aggregate(second)
    comb=(3*s1+s2)/4
    first_y=ch1[0]; second_y=ch2[0]
    candidates={
        "original_KMeans":km_bits(comb),
        "global_fixed_half":bits_str(comb>0.5),
        "first_only_KMeans":km_bits(s1),
        "second_only_KMeans":km_bits(s2),
        "Y_combined_KMeans":km_bits((3*first_y+second_y)/4),
        "Y_first_only_KMeans":km_bits(first_y),
        "YUV_channel_KMeans_majority":bits_str(np.sum(
            [np.array([int(x) for x in km_bits((3*ch1[c]+ch2[c])/4)])
             for c in range(3)],axis=0)>=2),
    }
    decoded=generic_extract(rgb,fixed.WM_SIZE)
    if candidates["original_KMeans"]!=decoded:
        raise AssertionError("Instrumented QIM votes disagree with official decoder")
    return candidates,{"s1":s1,"s2":s2,"combined":comb,"Y_s1":first_y,
                      "Y_combined":(3*first_y+second_y)/4},ch1,ch2

def measure_gap(scores,truth):
    a=np.array([int(x) for x in truth])
    return float(np.mean(scores[a==1])-np.mean(scores[a==0]))

def main():
    pa=ArgumentParser()
    pa.add_argument("--output-dir",type=Path,required=True)
    out=pa.parse_args().output_dir
    out.mkdir(parents=True,exist_ok=False)
    provenance=json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info",{}).get("commit_id")!=fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Pinned upstream revision mismatch")
    with urlopen(fixed.SOURCE_URL,timeout=60) as r: img_bytes=r.read()
    if fixed.git_blob_sha(img_bytes)!=fixed.SOURCE_BLOB_SHA:
        raise RuntimeError("Original source image hash mismatch")
    original=out/"original.jpeg"
    original.write_bytes(img_bytes)
    rgb=fixed.read_rgb(original)

    truth=fixed.PAYLOAD
    marked=out/"g6_original32_marked.png"
    wm=configured_instance(D1,D2)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(x) for x in truth],mode="bit")
    wm.embed(filename=str(marked))
    # Exactly verify against archived G6 image for strict reproducibility.
    archived="d289b94ff41a4509fa363577b34e4a51026d834afa9dd4a3bcc6c1728d987541"
    if fixed.sha256_file(marked)!=archived:
        raise RuntimeError("Marked image does not match archived SHA256")
    if generic_extract(fixed.read_rgb(marked),32)!=truth:
        raise RuntimeError("Clean reference extraction != payload")

    local=[]
    variants=[]
    for qf in QFS_DIAG:
        attacked=qf_attack(marked,out,qf,"original32")
        candidates,scores,ch1,ch2=localized_votes(attacked)
        data={"qf":qf,"n_errors":errs(truth,candidates["original_KMeans"])}
        for kind,sc in scores.items():
            data[f"gap_{kind}"]=measure_gap(sc,truth)
            data[f"zero_{kind}"]=float(np.mean(sc[[x=="0" for x in truth]]))
            data[f"one_{kind}"]=float(np.mean(sc[[x=="1" for x in truth]]))
        for c,name in enumerate("YUV"):
            data[f"gap_{name}_first"]=measure_gap(ch1[c],truth)
            data[f"gap_{name}_second"]=measure_gap(ch2[c],truth)
        local.append(data)
        for method,decoded in candidates.items():
            variants.append({"qf":qf,"method":method,"errors":errs(truth,decoded),
                             "decoded":decoded})
        print("LOCAL_DIAG="+json.dumps(
            {"qf":qf,"BER":data["n_errors"],"gap_s1":round(data["gap_s1"],5),
             "gap_s2":round(data["gap_s2"],5),
             "gap_combined":round(data["gap_combined"],5),
             "variants":{r["method"]:r["errors"] for r in variants if r["qf"]==qf}}
        ),flush=True)

    dump(out/"local_vote_gaps.csv",local)
    dump(out/"extraction_variants.csv",variants)

    # Pilot trial. Re-embed payload+public pilot, thus a separate experiment
    # from the unchanged G6. Compare clean and all QFs, not just QF5-8.
    pil_rows=[]
    for case in ("primary","holdout","complement"):
        payload=PAYLOADS[case]
        for pname,pilot in PILOTS.items():
            embedded=payload+pilot
            n=len(embedded)
            watermark=out/f"{case}_{pname}_marked.png"
            m=configured_instance(D1,D2)
            m.read_img(img=fixed.to_bgr(rgb))
            m.read_wm([int(x) for x in embedded],mode="bit")
            m.embed(filename=str(watermark))
            clean=generic_extract(fixed.read_rgb(watermark),n)
            if clean!=embedded:
                raise RuntimeError(f"Pilot candidate has nonzero clean BER: {case}/{pname}")
            for qf in QFS_PILOT:
                attacked=qf_attack(watermark,out,qf,f"{case}_{pname}")
                got=generic_extract(attacked,n)
                data=got[:32]
                observed_pilot=got[32:]
                pilot_err=errs(pilot,observed_pilot)
                invert=pilot_err>len(pilot)/2
                ties=pilot_err==len(pilot)/2
                if invert: fixed_data="".join("1" if x=="0" else "0" for x in data)
                else: fixed_data=data
                row={"case":case,"pilot_length":len(pilot),"qf":qf,
                    "uncorrected_errors":errs(payload,data),
                    "corrected_errors":errs(payload,fixed_data),
                    "pilot_errors":pilot_err,"pilot_invert":invert,
                    "pilot_tie":ties,"corrected_data":fixed_data,
                    "original_data":data}
                pil_rows.append(row)
                print("PILOT_RESULT="+json.dumps(row),flush=True)

    dump(out/"pilot_results.csv",pil_rows)
    report={
      "status":"complete","scope":"exploratory, do not replace G6 findings",
      "local_qfs":list(QFS_DIAG),"pilot_qfs":list(QFS_PILOT),
      "d1":D1,"d2":D2,"image_sha256":fixed.sha256_file(original),
      "pilots":PILOTS,"payloads":{k:PAYLOADS[k] for k in ("primary","holdout","complement")},
      "jpeg":fixed.JPEG,"archived_mark_sha":archived,
      "note":"All pilot decisions use observed pilot only; BER truth used after decision."
    }
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("FINAL_LOCAL_VARIANTS="+json.dumps([
        {"qf":r["qf"],"method":r["method"],"errors":r["errors"]} for r in variants
    ]),flush=True)
    print("FINAL_PILOT_SUMMARY="+json.dumps([
        {"case":c,"pilot":p,
         "results":[{"qf":r["qf"],"old_errors":r["uncorrected_errors"],
                     "new_errors":r["corrected_errors"],
                     "pilot_errors":r["pilot_errors"]}
                    for r in pil_rows if r["case"]==c and r["pilot_length"]==p]}
        for c in ("primary","holdout","complement")
        for p in (8,16)
    ]),flush=True)

if __name__=="__main__":
    main()
