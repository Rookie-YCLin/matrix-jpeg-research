"""Paired extreme secondary quantizer study, pinned to upstream and archived payload."""
from __future__ import annotations
import csv, json
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import argparse
import cv2
import numpy as np
from PIL import Image
from experiments import ori_qf_scan as fixed
from experiments.svd_qim_psnr import rgb_psnr

ARMS = {"original_d2_20":(36,20), "extreme_d2_720":(36,720)}
QFS = (5,10,15,20,25,50,95)

def decode(rgb, d1, d2):
    w=fixed.watermark_instance()
    w.bwm_core.d1, w.bwm_core.d2=d1,d2
    assert not w.bwm_core.fast_mode
    bits=np.asarray(w.extract(embed_img=fixed.to_bgr(rgb), wm_shape=32, mode="bit"))
    return "".join(str(int(i)) for i in bits)

def main(output):
    output.mkdir(parents=True, exist_ok=False)
    with urlopen(fixed.SOURCE_URL, timeout=90) as f:
        raw=f.read()
    assert fixed.git_blob_sha(raw)==fixed.SOURCE_BLOB_SHA
    (output/"source.jpeg").write_bytes(raw)
    original=fixed.read_rgb(output/"source.jpeg")
    rows=[]
    for name,(d1,d2) in ARMS.items():
        w=fixed.watermark_instance()
        w.bwm_core.d1,w.bwm_core.d2=d1,d2
        assert w.bwm_core.fast_mode is False
        w.read_img(img=fixed.to_bgr(original))
        w.read_wm([int(x) for x in fixed.PAYLOAD],mode="bit")
        embedded=w.embed()
        embedded_file=output/f"{name}.png"
        assert cv2.imwrite(str(embedded_file),embedded)
        for qf in (None,*QFS):
            if qf is None:
                candidate=fixed.read_rgb(embedded_file)
                label="PNG"
            else:
                fname=output/f"{name}_qf{qf:02d}.jpg"
                with Image.open(embedded_file) as im:
                    im.save(fname,format="JPEG",quality=qf,**fixed.JPEG)
                candidate=fixed.read_rgb(fname)
                label=str(qf)
            bits=decode(candidate,d1,d2)
            errors=sum(x!=y for x,y in zip(fixed.PAYLOAD,bits))
            mse,psnr=rgb_psnr(original,candidate)
            row={"arm":name,"d1":d1,"d2":d2,"qf":label,"errors":errors,
                 "total":32,"ber":errors/32,"psnr_db":psnr,"mse":mse,"decoded_bits":bits}
            rows.append(row)
            print("RESULT",json.dumps(row),flush=True)
    with (output/"results.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    manifest={"upstream_commit":fixed.UPSTREAM_COMMIT,"source_blob_sha":fixed.SOURCE_BLOB_SHA,
              "source_sha256":sha256(raw).hexdigest(),"payload":fixed.PAYLOAD,
              "keys":fixed.KEYS,"mode":"common","fast_mode":False,"arms":ARMS,
              "jpeg":{"encoder":"Pillow",**fixed.JPEG,"qfs":QFS},
              "results":rows}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("SUMMARY: COMPLETE",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    main(p.parse_args().output_dir)
