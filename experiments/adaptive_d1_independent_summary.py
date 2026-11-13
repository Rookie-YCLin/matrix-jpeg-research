"""Independent-image benchmark summary with Wilson intervals and strict audit.

Input is the CSV from adaptive_d1_multimage_replay.py.
Images (not seeds) are the independent units.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if not (0 <= k <= n and n > 0):
        raise ValueError("Invalid hit count")
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return max(0, center-half), min(1, center+half)


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Empty replay")
    groups = defaultdict(list)
    for row in rows:
        groups[row["policy"]].append(row)
    report = {}
    for policy, group in sorted(groups.items()):
        ids = [r["image_id"] for r in group]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate image for {policy}")
        budgets = {int(r["budget"]) for r in group}
        if len(budgets) != 1:
            raise ValueError(f"Mixed budgets for {policy}")
        stats = {"n_images": len(group), "budget": budgets.pop()}
        for field in ("exact_hit", "near_hit_0_005", "near_hit_0_01"):
            k = sum(int(r[field]) for r in group)
            lo, hi = wilson(k, len(group))
            stats[field] = {"count": k, "rate": k/len(group),
                            "wilson_95": [lo, hi]}
        regrets = [float(r["regret"]) for r in group]
        stats["mean_regret"] = sum(regrets)/len(regrets)
        stats["worst_regret"] = max(regrets)
        report[policy] = stats
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    with args.replay_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = summarize(rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
