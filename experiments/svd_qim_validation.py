"""Independent follow-up verification of selected SVD-only QIM d1=90, d2=20.

The experimental candidate was selected from a prior explicit grid with
QF=15 as the predetermined primary condition. This script compares with the
original (36,20) using the same user-selected source, fixed baseline payload,
plus two distinct payloads NOT used in candidate selection. No true bits
are supplied to blind extraction; original payload is used only for scoring.

Run: python -m experiments.svd_qim_validation --output-dir outputs/svd90-validate
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from importlib.metadata import distribution
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance

SOURCE_NAME = "ori_img.jpeg"
PRIMARY = fixed.PAYLOAD
# Pre-declared after selecting (90,20), NOT used to select the candidate.
HOLDOUT = "01101011000100111010010101100110"  # 16 ones, 16 zeros.
COMPLEMENT = "".join(str(1-int(c)) for c in PRIMARY)
PAYLOADS = {"primary": PRIMARY, "holdout": HOLDOUT, "complement": COMPLEMENT}
VARIANTS = {"upstream": (36,20), "svd_step_90": (90,20)}
QA_PRIMARY = tuple(range(5,100,5))
QA_HOLDOUT = (10,15,20,25)


def decode(rgb: np.ndarray, d1: int, d2: int) -> str:
    wm = configured_instance(d1,d2)
    bits = np.asarray(wm.extract(embed_img=fixed.to_bgr(rgb), wm_shape=32, mode="bit"))
    if bits.shape != (32,) or not np.isin(bits,[0,1]).all():
        raise AssertionError("Blind upstream API did not return 32 valid bits")
    return "".join(str(int(x)) for x in bits)


def count_errors(expected: str, observed: str) -> tuple[int, list[int]]:
    wrong = [i+1 for i,(b,c) in enumerate(zip(expected,observed)) if b != c]
    return len(wrong), wrong


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    output=parser.parse_args().output_dir
    output.mkdir(parents=True,exist_ok=False)

    provenance=json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info",{}).get("commit_id") != fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Wrong pinned upstream version")
    with urlopen(fixed.SOURCE_URL,timeout=60) as response:
        source_bytes=response.read()
    if fixed.git_blob_sha(source_bytes) != fixed.SOURCE_BLOB_SHA:
        raise ValueError("Source image bytes changed")
    source=output / SOURCE_NAME
    source.write_bytes(source_bytes)
    rgb=fixed.read_rgb(source)

    rows=[]
    for payload_name, payload in PAYLOADS.items():
        if len(payload)!=32:
            raise ValueError("Invalid payload")
        qualities=QA_PRIMARY if payload_name=="primary" else QA_HOLDOUT
        for variant,(d1,d2) in VARIANTS.items():
            prefix=f"{payload_name}_{variant}"
            marked=output / f"{prefix}_marked.png"
            encoder=configured_instance(d1,d2)
            encoder.read_img(img=fixed.to_bgr(rgb))
            encoder.read_wm([int(bit) for bit in payload],mode="bit")
            encoder.embed(filename=str(marked))
            clean=decode(fixed.read_rgb(marked),d1,d2)
            clean_err,_=count_errors(payload,clean)
            if clean_err:
                raise RuntimeError(f"PNG check failed {prefix}: {clean_err}/32")
            for qf in qualities:
                attacked=output / f"{prefix}_qf{qf:02d}.jpg"
                with Image.open(marked) as image:
                    image.save(attacked,format="JPEG",quality=qf,**fixed.JPEG)
                bits=decode(fixed.read_rgb(attacked),d1,d2)
                errors,positions=count_errors(payload,bits)
                row={
                    "payload":payload_name,"variant":variant,"d1":d1,"d2":d2,"qf":qf,
                    "errors":errors,"total_bits":32,"ber":errors/32,
                    "expected_bits":payload,"extracted_bits":bits,
                    "positions_1based":json.dumps(positions),
                    "marked_sha256":fixed.sha256_file(marked),
                    "attack_sha256":fixed.sha256_file(attacked),
                }
                rows.append(row)
                print(f"VERIFY payload={payload_name} variant={variant} QF={qf} errors={errors}/32",flush=True)

    with (output/"results.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    def error(payload, variant, qf):
        matches=[row["errors"] for row in rows if row["payload"]==payload and row["variant"]==variant and row["qf"]==qf]
        assert len(matches)==1
        return matches[0]
    # Strictly reproduce original archived W1 result at its pre-selected x=15.
    if error("primary","upstream",15)!=32:
        raise RuntimeError("Control does not reproduce original baseline 32/32")
    if error("primary","upstream",10)!=1 or error("primary","upstream",20)!=32:
        raise RuntimeError("Control does not reproduce original adjacent-QF baseline")
    new_errors=error("primary","svd_step_90",15)
    rr=fixed.relative_reduction(32,new_errors)
    summary={
        "status":"complete","selected":"svd_step_90",
        "source_sha256":sha256(source_bytes).hexdigest(),
        "source_blob_sha":fixed.SOURCE_BLOB_SHA,
        "upstream_commit":fixed.UPSTREAM_COMMIT,
        "payloads":PAYLOADS,"variants":VARIANTS,
        "jpeg":{"quality_primary":15,"primary_qfs":QA_PRIMARY,"holdout_qfs":QA_HOLDOUT,**fixed.JPEG},
        "baseline_qf15_errors":32,"new_qf15_errors":new_errors,
        "relative_reduction_percent":rr,
        "meets_5_percent":rr >= 5.0,
        "meets_10_percent":rr >= 10.0,
        "qf15_other_payloads":{key:{
            variant:error(key,variant,15) for variant in VARIANTS
        } for key in ("holdout","complement")},
        "all_png_checks_zero":True,
        "files_sha256":{p.name:fixed.sha256_file(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    (output/"manifest.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("VERIFY_SUMMARY="+json.dumps({k:v for k,v in summary.items() if k not in ("files_sha256","payloads")}),flush=True)


if __name__=="__main__":
    main()
