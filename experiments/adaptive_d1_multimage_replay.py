"""Evaluate frozen coarse-to-fine search policies across measured image Grids.

The policy only sees scores of queried d1 points. Full-grid oracle is used
AFTER each search to calculate regret and hit rate. No JPEG is performed here.

Example:
 python -m experiments.adaptive_d1_multimage_replay \
   --grid-root outputs/multimage-qf5-10 \
   --output outputs/multimage-replay.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def select(values: dict[int, float], budget: int = 24, regions: int = 1,
           n_coarse: int = 8, separation: int = 10) -> tuple[int, float, tuple[int, ...]]:
    domain = tuple(sorted(values))
    if domain != tuple(range(1, 151)):
        raise ValueError("A complete d1=1..150 Grid is required")
    if not (1 <= n_coarse <= budget <= 150):
        raise ValueError("Invalid budget or initialization size")
    if regions < 1:
        raise ValueError("regions must be positive")
    seen: dict[int, float] = {}
    for i in range(n_coarse):
        d = min(150, 1 + int((i + .5) * 150 / n_coarse + .5))
        seen[d] = values[d]
    while len(seen) < budget:
        centers = []
        for d in sorted(seen, key=lambda x: (seen[x], x)):
            if all(abs(d - c) > separation for c in centers):
                centers.append(d)
            if len(centers) >= regions:
                break
        center = centers[(len(seen) - n_coarse) % len(centers)]
        candidate = min((d for d in domain if d not in seen),
                        key=lambda d: (abs(d - center), d))
        seen[candidate] = values[candidate]
    best_d = min(seen, key=lambda d: (seen[d], d))
    return best_d, seen[best_d], tuple(seen)


def evaluate_root(root: Path, output: Path, budget: int = 24) -> list[dict]:
    files = sorted(root.glob("*/per_d1.csv"))
    if not files:
        raise ValueError("No per-image Grid CSVs found")
    results = []
    for path in files:
        with path.open(newline="", encoding="utf-8") as stream:
            raw = list(csv.DictReader(stream))
        values = {int(row["d1"]): float(row["model_b_lambda_0_5"]) for row in raw}
        if set(values) != set(range(1, 151)):
            raise ValueError(f"Incomplete Grid: {path}")
        oracle_d = min(values, key=lambda d: (values[d], d))
        for regions in (1, 2):
            chosen_d, chosen_score, trace = select(values, budget=budget, regions=regions)
            regret = max(0.0, chosen_score - values[oracle_d])
            results.append({
                "image_id": path.parent.name, "policy": f"coarse8_nearest_k{regions}",
                "budget": budget, "oracle_d1": oracle_d,
                "oracle_objective": values[oracle_d],
                "selected_d1": chosen_d, "selected_objective": chosen_score,
                "regret": regret, "exact_hit": int(regret <= 1e-10),
                "near_hit_0_005": int(regret <= .005 + 1e-10),
                "near_hit_0_01": int(regret <= .01 + 1e-10),
                "evaluated_d1": ";".join(map(str, trace)),
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    for policy in sorted({r["policy"] for r in results}):
        subset = [r for r in results if r["policy"] == policy]
        print(f"{policy}: exact={sum(r['exact_hit'] for r in subset)}/{len(subset)}, "
              f"near0.01={sum(r['near_hit_0_01'] for r in subset)}/{len(subset)}, "
              f"mean_regret={sum(r['regret'] for r in subset)/len(subset):.8f}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=24)
    args = parser.parse_args()
    evaluate_root(args.grid_root, args.output, args.budget)


if __name__ == "__main__":
    main()
