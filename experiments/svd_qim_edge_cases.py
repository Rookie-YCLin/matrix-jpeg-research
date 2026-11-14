"""Three edge-case settings of the upstream SVD-QIM embedding, no formula modifications."""
from __future__ import annotations
import argparse,csv,json,warnings
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import cv2
import numpy as np
from PIL import Image
from experiments import ori_qf_scan as fixed
from experiments.svd_qim_psnr import rgb_psnr

ARMS={"d1_36_d2_0":(36,0),"d1_0_d2_20":(0,20),"d1_720_d2_720":(720,720),"d1_0_d2_720":(0,720),"d1_720_d2_0":(720,0)}
QFS=(5,10,15,20,25,50,95)

def watermark(d1,d2):
    w=fixed.watermark_instance()
    w.bwm_core.d1,w.bwm_core.d2=d1,d2
    assert w.bwm_core.fast_mode is False
    return w

def decode(rgb,d1,d2):
    w=watermark(d1,d2)
    bits=np.asarray(w.extract(embed_img=fixed.to_bgr(rgb),wm_shape=32,mode="bit"))
    return "".join(str(int(bit)) for bit in bits)

def main(output):
    output.mkdir(parents=True,exist_ok=False)
    with urlopen(fixed.SOURCE_URL,timeout=90) as stream:
        source_bytes=stream.read()
    assert fixed.git_blob_sha(source_bytes)==fixed.SOURCE_BLOB_SHA
    (output/"source.jpeg").write_bytes(source_bytes)
    original=fixed.read_rgb(output/"source.jpeg")
    rows=[]
    invalid=[]
    for name,(d1,d2) in ARMS.items():
        if d1==0:
            invalid.append({"arm":name,"d1":d1,"d2":d2,
                "status":"invalid","reason":"Upstream always evaluates s[0] // d1; d1=0 yields undefined division/modulo and cannot be evaluated as an unchanged baseline."})
            print("INVALID",json.dumps(invalid[-1]),flush=True)
            continue
        w=watermark(d1,d2)
        w.read_img(img=fixed.to_bgr(original))
        w.read_wm([int(b) for b in fixed.PAYLOAD],mode="bit")
        marked_file=output/f"{name}.png"
        assert cv2.imwrite(str(marked_file),w.embed())
        for qf in (None,*QFS):
            if qf is None:
                candidate=fixed.read_rgb(marked_file)
                stage="PNG"
            else:
                attack_file=output/f"{name}_qf{qf:02d}.jpg"
                with Image.open(marked_file) as im:
                    im.save(attack_file,format="JPEG",quality=qf,**fixed.JPEG)
                candidate=fixed.read_rgb(attack_file)
                stage=str(qf)
            bits=decode(candidate,d1,d2)
            errors=sum(x!=y for x,y in zip(fixed.PAYLOAD,bits))
            mse,psnr=rgb_psnr(original,candidate)
            row={"arm":name,"d1":d1,"d2":d2,"qf":stage,"errors":errors,
                "total":32,"ber":errors/32,"psnr_db":psnr,"mse":mse,"decoded_bits":bits}
            rows.append(row)
            print("RESULT",json.dumps(row),flush=True)
    with (output/"results.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    manifest={"source_sha256":sha256(source_bytes).hexdigest(),
      "upstream_commit":fixed.UPSTREAM_COMMIT,"source_blob":fixed.SOURCE_BLOB_SHA,
      "payload":fixed.PAYLOAD,"mode":"common","fast_mode":False,
      "jpeg":{"encoder":"Pillow",**fixed.JPEG,"qualities":QFS},
      "arms":ARMS,"invalid":invalid,"results":rows}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("SUMMARY: COMPLETE",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True,type=Path)
    main(parser.parse_args().output_dir)
