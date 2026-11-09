"""Pre-declared independent 32-bit holdout verification for blind SVD decoders.

Do not tune candidate rules on these payloads; they are deterministically
generated independently of the earlier primary/holdout/complement payloads.
All data are 32 bits. No pilot or known truth enters the decoder.
"""
from __future__ import annotations
import csv
import json
from argparse import ArgumentParser
from pathlib import Path
from urllib.request import urlopen
from importlib.metadata import distribution
import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance
from experiments.svd_qim_validation import PAYLOADS
from experiments.g6_no_pilot_32bit_comparison import signals, decode_candidates, bitstr, error_count

QFS=(1,4,5,6,7,8,9,10,11,15,20,95)
SEEDS=(20261109,20261110,20261111,20261112)
FREEZE=("G6_baseline","self_polarity_S1_only","self_fuse_oriented_S1_S2",
        "soft_QIM_orient_from_hard_agreement")


def bits_for_seed(seed):
    rng=np.random.RandomState(seed)
    bits=bitstr(rng.randint(0,2,size=32))
    if bits in PAYLOADS.values():
        raise AssertionError("Holdout collides with earlier payload")
    return bits


def write_csv(path,rows):
    with path.open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    p=ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    output=p.parse_args().output_dir
    output.mkdir(parents=True,exist_ok=False)
    provenance=json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    assert provenance["vcs_info"]["commit_id"]==fixed.UPSTREAM_COMMIT
    with urlopen(fixed.SOURCE_URL,timeout=60) as stream:
        raw=stream.read()
    assert fixed.git_blob_sha(raw)==fixed.SOURCE_BLOB_SHA
    source=output/"original.jpeg"
    source.write_bytes(raw)
    orig_rgb=fixed.read_rgb(source)

    rows=[]
    meta=[]
    for seed in SEEDS:
        payload=bits_for_seed(seed)
        marked=output/f"seed_{seed}_G6.png"
        encoder=configured_instance(90,20)
        encoder.read_img(img=fixed.to_bgr(orig_rgb))
        encoder.read_wm([int(x) for x in payload],mode="bit")
        encoder.embed(filename=str(marked))
        meta.append({"seed":seed,"payload":payload,"marked_sha256":fixed.sha256_file(marked)})
        with Image.open(marked) as m:
            for qf in QFS:
                attacked=output/f"seed_{seed}_qf{qf:02}.jpg"
                m.save(attacked,format="JPEG",quality=qf,**fixed.JPEG)
                with Image.open(attacked) as image:
                    decoded_rgb=np.asarray(image.convert("RGB")).copy()
                h1,h2,t1,t2,_,_=signals(decoded_rgb,32)
                decoded,diagnostics=decode_candidates(h1,h2,t1,t2)
                entry={"seed":seed,"qf":qf,"rho":diagnostics["hard_corr"],
                       "agreement":diagnostics["b1_b2_agree"],
                       "flip":diagnostics["flip_from_agreement"]}
                for method in FREEZE:
                    entry[method+"_errors"]=error_count(payload,decoded[method])
                rows.append(entry)
                print("HOLDOUT="+json.dumps(entry),flush=True)
    write_csv(output/"holdout_results.csv",rows)
    manifest={
      "status":"complete",
      "scope":"Independent 32-bit payloads, frozen candidate selection; no pilot",
      "source_sha256":fixed.sha256_file(source),
      "qfs":QFS,"seeds":SEEDS,"cases":meta,"methods":FREEZE,
      "jpeg":fixed.JPEG,"upstream_commit":fixed.UPSTREAM_COMMIT,
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print("HOLDOUT_SUMMARY="+json.dumps({
      method: {"total_errors":sum(r[method+"_errors"] for r in rows),
               "errors_qf5_to8":sum(r[method+"_errors"] for r in rows if 5<=r["qf"]<=8),
               "nonzero_qfs":sorted(set(r["qf"] for r in rows if r[method+"_errors"]>0))}
      for method in FREEZE
    }),flush=True)

if __name__=="__main__":
    main()
