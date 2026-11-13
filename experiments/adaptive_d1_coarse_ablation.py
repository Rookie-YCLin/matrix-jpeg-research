"""Measured-Grid replay for coarse-to-fine d1 search ablations.

Run against PR #39's per_d1.csv. All fitness calls consume one unique
integer d1 evaluation. This is *offline replay*, not new JPEG measurements.
"""
import argparse
import csv
from pathlib import Path

def lcg(seed):
    state = (seed + 12345) & 0xffffffff
    while True:
        state = (1664525 * state + 1013904223) & 0xffffffff
        yield state / 4294967296

def optimize(values, mode, budget, seed):
    rnd = lcg(seed)
    seen = set()
    scores = []
    best = float("inf")
    best_d = 1
    def evaluate(x):
        nonlocal best, best_d
        x = max(1, min(150, int(x + 0.5)))
        if x in seen:
            raise ValueError("duplicate evaluation")
        seen.add(x)
        y = values[x - 1]
        scores.append((x, y))
        if y < best:
            best, best_d = y, x
    n = min(10, budget // 2)
    for i in range(n):
        if mode == "jitter":
            x = 1 + int((i + next(rnd)) * 150 / n)
        elif mode == "randominit":
            while True:
                x = 1 + int(next(rnd) * 150)
                if x not in seen:
                    break
        else:
            x = 1 + int((i + 0.5) * 150 / n + 0.5)
        evaluate(x)
    while len(seen) < budget:
        candidates = [x for x in range(1, 151) if x not in seen]
        center = best_d
        if mode in ("multi2", "multi3"):
            k = 2 if mode == "multi2" else 3
            centers = []
            for x, _ in sorted(scores, key=lambda z: z[1]):
                if all(abs(c-x)>10 for c in centers):
                    centers.append(x)
                if len(centers) == k:
                    break
            center = centers[(len(seen)-n) % len(centers)]
        if mode == "explore" and next(rnd) < 0.2:
            candidates.sort(key=lambda x: -min(abs(z[0]-x) for z in scores))
        else:
            candidates.sort(key=lambda x: abs(x-center))
        x = candidates[int(next(rnd) * min(7, len(candidates)))]
        evaluate(x)
    return best, best_d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seeds", type=int, default=200)
    args = ap.parse_args()
    with args.csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [int(row["d1"]) for row in rows] == list(range(1,151))
    values = [float(row["model_b_lambda_0_5"]) for row in rows]
    oracle = min(values)
    result = []
    for mode in ("coarse", "jitter", "randominit", "multi2", "multi3", "explore"):
        for budget in (12, 24, 48):
            runs = [optimize(values, mode, budget, seed) for seed in range(args.seeds)]
            result.append({
                "mode": mode, "budget": budget, "seeds": args.seeds,
                "mean_final_objective": sum(x[0] for x in runs) / len(runs),
                "oracle_hits": sum(abs(x[0] - oracle) < 1e-10 for x in runs),
                "oracle_d1": values.index(oracle)+1, "oracle_objective": oracle,
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result[0].keys())
        writer.writeheader()
        writer.writerows(result)
    for row in result:
        print(row)

if __name__ == "__main__":
    main()
