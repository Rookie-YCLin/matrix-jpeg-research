#!/usr/bin/env python3
"""Replay three simple optimizers against the *measured* 150-point Grid CSV.

Usage:
 python experiments/adaptive_d1_simple_replay.py \
   outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/per_d1.csv \
   --output outputs/adaptive-d1-simple-replay/summary.csv

No JPEG evaluations are performed. The grid CSV is the oracle.
"""
import argparse
import csv
import math
from pathlib import Path

class LCG:
    def __init__(self, seed=123):
        self.state = seed
    def random(self):
        self.state = (1664525*self.state + 1013904223) & 0xffffffff
        return self.state / 4294967296

def replay(vals, method, budget, rng):
    seen = set()
    best = float("inf")
    loc = 1
    def take(x):
        nonlocal best, loc
        x = max(1, min(len(vals), math.floor(x + 0.5)))
        if x in seen:
            remaining = [i for i in range(1, len(vals)+1) if i not in seen]
            x = remaining[math.floor(rng.random()*len(remaining))]
        seen.add(x)
        y = vals[x-1]
        if y < best:
            best, loc = y, x
    if method == "random":
        while len(seen) < budget:
            take(1 + math.floor(rng.random()*len(vals)))
    elif method == "stratified":
        for i in range(budget):
            take(1 + math.floor((i + rng.random())*len(vals)/budget))
    elif method == "coarse_refine":
        n = min(10, budget//2)
        for i in range(n):
            take(1 + math.floor((i+0.5)*len(vals)/n + 0.5))
        while len(seen) < budget:
            pool = [i for i in range(1,len(vals)+1) if i not in seen]
            pool.sort(key=lambda x: abs(x-loc))
            top = pool[:min(7,len(pool))]
            take(top[math.floor(rng.random()*len(top))])
    else:
        raise ValueError(method)
    return best, loc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grid_csv", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--trials", type=int, default=200)
    args = ap.parse_args()
    with args.grid_csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    vals = [float(row["model_b_lambda_0_5"]) for row in rows]
    assert len(vals)==150 and [int(row["d1"]) for row in rows]==list(range(1,151))
    oracle = min(vals)
    rng = LCG(123)
    result=[]
    for method in ("random","stratified","coarse_refine"):
        for budget in (12,24,48):
            outcomes=[replay(vals,method,budget,rng) for _ in range(args.trials)]
            result.append(dict(method=method,budget=budget,trials=args.trials,
                mean_final_objective=sum(x[0] for x in outcomes)/len(outcomes),
                oracle_hits=sum(abs(x[0]-oracle)<1e-10 for x in outcomes),
                mean_regret=sum(x[0]-oracle for x in outcomes)/len(outcomes),
                oracle_d1=vals.index(oracle)+1,oracle_objective=oracle))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=result[0].keys())
            writer.writeheader();writer.writerows(result)
    for row in result:
        print(f'{row["method"]:14} budget={row["budget"]:2} meanJ={row["mean_final_objective"]:.8f} hits={row["oracle_hits"]}/{row["trials"]}')

if __name__=="__main__":
    main()
