"""Reproducible toy-landscape benchmark for discrete d1 search.

These are SYNTHETIC functions, not measured JPEG BER. Run:
  python -m experiments.adaptive_d1_toy_benchmark
"""
import math
import random
import statistics

from experiments.adaptive_d1_adaptive_regions import optimize


def fixed(f, budget=24, coarse=8, regions=1):
    seen = {}
    for i in range(coarse):
        d = 1 + int((i + .5) * 150 / coarse)
        seen[d] = f(d)
    while len(seen) < budget:
        centers = []
        for d in sorted(seen, key=lambda x: (seen[x], x)):
            if all(abs(d-c) > 10 for c in centers):
                centers.append(d)
            if len(centers) == regions:
                break
        center = centers[(len(seen)-coarse) % len(centers)]
        d = min((x for x in range(1,151) if x not in seen),
                key=lambda x: (abs(x-center), x))
        seen[d] = f(d)
    return min(seen.values())


def landscapes():
    rng = random.Random(901)
    for _ in range(100):
        centers = rng.sample(range(5,146), 3)
        floors = [rng.uniform(0,.15) for _ in range(3)]
        widths = [rng.uniform(4,20) for _ in range(3)]
        ripple = rng.uniform(0,.05)
        yield lambda d, cs=centers, fs=floors, ws=widths, r=ripple: (
            min(f+(d-c)**2/(w*w)*.12 for c,f,w in zip(cs,fs,ws))
            +r*(1+math.sin(d*1.7))
        )


def main():
    functions = list(landscapes())
    for budget in (12,24,48):
        for method in ("single","dual","adaptive"):
            regrets = []
            for f in functions:
                oracle = min(f(d) for d in range(1,151))
                if method == "adaptive":
                    best = optimize(f, budget=budget, regions=3).best_objective
                else:
                    best = fixed(f, budget=budget, regions=1 if method=="single" else 2)
                regrets.append(best-oracle)
            print(method, budget, "mean_regret", statistics.mean(regrets),
                  "near_0.01", sum(x<=.01 for x in regrets), "/100")


if __name__ == "__main__":
    main()
