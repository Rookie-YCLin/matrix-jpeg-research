"""Controlled SVD-QIM ablation: second singular value, shuffle, and decoder.

Six embeddings keep the fixed image/payload/upstream unchanged. For each received
image compute average soft scores once; compare K-means and 0.5 threshold.
Oracle polarity correction is diagnostic only and NOT a blind decoder.
"""
from __future__ import annotations
import argparse, csv, json
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen
import cv2
import numpy as np
from PIL import Image
from blind_watermark.bwm_core import one_dim_kmeans
from experiments import ori_qf_scan as fixed
from experiments.svd_qim_psnr import rgb_psnr

ARMS = (
    ("common_36_20", False, 36, 20),
    ("common_36_0",  False, 36, 0),
    ("fast_36",      True, 36, 0),
    ("common_90_20", False, 90, 20),
    ("common_90_0",  False, 90, 0),
    ("fast_90",      True, 90, 0),
)
QFS = (5, 10, 15, 20, 25, 50, 95)
PAYLOAD = fixed.PAYLOAD

def wm_instance(fast,d1,d2):
    wm=fixed.watermark_instance()
    wm.bwm_core.fast_mode=fast
    wm.bwm_core.d1=d1
    wm.bwm_core.d2=d2
    assert (wm.bwm_core.fast_mode,wm.bwm_core.d1,wm.bwm_core.d2)==(fast,d1,d2)
    return wm

def bitstring(values):
    return "".join(str(int(x)) for x in values)

def count_errors(bits):
    return sum(a!=b for a,b in zip(PAYLOAD,bits))

def decode(rgb,fast,d1,d2):
    wm=wm_instance(fast,d1,d2)
    # The upstream bit decoder first averages scores, clusters with K-means,
    # then reverses password_wm's bit permutation.
    raw=wm.bwm_core.extract(img=fixed.to_bgr(rgb),wm_shape=32)
    wm.wm_size=32
    scores=wm.extract_decrypt(np.asarray(raw).copy())
    clustered=wm.extract_decrypt(one_dim_kmeans(np.asarray(raw).copy()).astype(np.float64))
    threshold=(scores>=0.5).astype(np.int32)
    kmeans=clustered.astype(np.int32)
    return scores,bitstring(kmeans),bitstring(threshold)

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    with urlopen(fixed.SOURCE_URL,timeout=90) as response:
        original_bytes=response.read()
    assert fixed.git_blob_sha(original_bytes)==fixed.SOURCE_BLOB_SHA
    (out/"source.jpeg").write_bytes(original_bytes)
    original=fixed.read_rgb(out/"source.jpeg")
    rows=[]
    for name,fast,d1,d2 in ARMS:
        wm=wm_instance(fast,d1,d2)
        wm.read_img(img=fixed.to_bgr(original))
        wm.read_wm([int(b) for b in PAYLOAD],mode="bit")
        marked=out/f"{name}_marked.png"
        assert cv2.imwrite(str(marked),wm.embed())
        for qf in (None,*QFS):
            if qf is None:
                attacked_rgb=fixed.read_rgb(marked)
                label="PNG"
            else:
                attacked=out/f"{name}_qf{qf:02d}.jpg"
                with Image.open(marked) as image:
                    image.save(attacked,format="JPEG",quality=qf,**fixed.JPEG)
                attacked_rgb=fixed.read_rgb(attacked)
                label=str(qf)
            scores,km,th=decode(attacked_rgb,fast,d1,d2)
            ke=count_errors(km)
            te=count_errors(th)
            mse,psnr=rgb_psnr(original,attacked_rgb)
            row={
              "arm":name,"fast_mode":fast,"d1":d1,"d2":d2,"qf":label,
              "kmeans_errors":ke,"threshold_errors":te,
              "kmeans_ber":ke/32,"threshold_ber":te/32,
              "oracle_polarity_errors":min(ke,32-ke),
              "is_full_complement":ke==32,
              "km_bits":km,"threshold_bits":th,
              "mean_score_true_0":float(scores[np.array(list(PAYLOAD))=="0"].mean()),
              "mean_score_true_1":float(scores[np.array(list(PAYLOAD))=="1"].mean()),
              "min_score":float(scores.min()),"max_score":float(scores.max()),
              "psnr_db":psnr,"mse":mse
            }
            rows.append(row)
            print("ABLATION "+json.dumps(row),flush=True)
    with (out/"results.csv").open("w",newline="",encoding="utf-8") as file:
        w=csv.DictWriter(file,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    with (out/"manifest.json").open("w",encoding="utf-8") as file:
        json.dump({"status":"complete","upstream_commit":fixed.UPSTREAM_COMMIT,
          "source_sha256":sha256(original_bytes).hexdigest(),
          "source_blob":fixed.SOURCE_BLOB_SHA,"payload":PAYLOAD,"keys":fixed.KEYS,
          "jpeg":{"encoder":"Pillow","subsampling":0,"optimize":False,
                  "progressive":False,"qualities":QFS},
          "arms":ARMS,
          "diagnostic_note":"oracle_polarity_errors uses true payload and is not a deployable blind decoder",
          "results":rows},file,indent=2)
    print("ABLATION_COMPLETE",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    main(p.parse_args().output_dir)
