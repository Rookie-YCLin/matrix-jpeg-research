"""Budgeted coarse-to-fine d1 search; deterministic-nearest variant.

Replay uses measured Grid objectives only, never synthesizes JPEG/BER.
NOTE: the n=8 nearest-neighbor configuration was selected *after* observing
one image's Grid; its in-sample hit rate is not generalization evidence.
"""
import argparse
import csv
from pathlib import Path

def replay(values, budget=24, n_coarse=8, n_regions=1, min_separation=10, width=1, seed=0):
    state=(seed+12345)&0xffffffff
    def rand():
        nonlocal state
        state=(1664525*state+1013904223)&0xffffffff
        return state/4294967296
    seen=set()
    scores=[]
    def evaluate(d):
        d=max(1,min(len(values),int(d+0.5)))
        if d in seen:
            raise AssertionError("duplicate objective query")
        seen.add(d)
        scores.append((d,values[d-1]))
    n=min(n_coarse,budget//2)
    for i in range(n):
        evaluate(1+int((i+0.5)*len(values)/n+0.5))
    while len(seen)<budget:
        centers=[]
        for d,_ in sorted(scores,key=lambda x:x[1]):
            if all(abs(d-c)>min_separation for c in centers):
                centers.append(d)
            if len(centers)>=n_regions:
                break
        center=centers[(len(seen)-n)%len(centers)]
        available=[d for d in range(1,len(values)+1) if d not in seen]
        available.sort(key=lambda d:abs(d-center))
        evaluate(available[int(rand()*min(width,len(available)))])
    return min(y for _,y in scores), seen

def main():
    p=argparse.ArgumentParser()
    p.add_argument("grid_csv",type=Path)
    p.add_argument("--budget",type=int,default=24)
    p.add_argument("--trials",type=int,default=200)
    args=p.parse_args()
    with args.grid_csv.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    assert [int(x["d1"]) for x in rows]==list(range(1,151))
    values=[float(x["model_b_lambda_0_5"]) for x in rows]
    oracle=min(values)
    outcomes=[replay(values,budget=args.budget,seed=s)[0] for s in range(args.trials)]
    print({"budget":args.budget,"trials":args.trials,
        "oracle_d1":values.index(oracle)+1,
        "hits":sum(abs(y-oracle)<1e-10 for y in outcomes),
        "mean_final_objective":sum(outcomes)/len(outcomes)})
if __name__=="__main__":
    main()
