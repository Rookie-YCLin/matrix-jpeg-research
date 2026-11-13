"""Compare budget-matched discrete optimizers using the measured d1 Grid oracle.

No BER value is synthesized here: every score is looked up from the completed
QF5--10 Grid.  One proposed, previously unseen integer d1 counts as one
effective expensive evaluation.
"""
from __future__ import annotations

import argparse
import csv
import json
from math import erf, exp, pi, sqrt
from pathlib import Path
from time import perf_counter

import numpy as np


DOMAIN = np.arange(1, 151)
DEFAULT_BUDGET = 24
DEFAULT_SEEDS = tuple(range(10))


def read_oracle(path: Path) -> dict[int, dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as stream:
        raw = list(csv.DictReader(stream))
    oracle = {int(r["d1"]): {k: float(r[k]) for k in ("mean_ber", "worst_ber", "png_psnr_db", "model_b_lambda_0_5")} for r in raw}
    if set(oracle) != set(DOMAIN):
        raise ValueError("Oracle must contain exactly integer d1=1..150")
    return oracle


def unused_pick(candidates: np.ndarray, seen: set[int], rng: np.random.Generator) -> int:
    available = [int(x) for x in candidates if int(x) not in seen]
    if not available:
        available = [int(x) for x in DOMAIN if int(x) not in seen]
    return int(rng.choice(available))


def random_method(rng: np.random.Generator, budget: int):
    return list(map(int, rng.choice(DOMAIN, size=budget, replace=False)))


def pso_method(rng: np.random.Generator, budget: int, oracle: dict[int, dict[str, float]]):
    positions = rng.uniform(1, 150, size=8); velocity = np.zeros(8); seen: set[int] = set(); proposed: list[int] = []
    personal = positions.copy(); personal_score = np.full(8, np.inf); global_pos = 75.5
    while len(proposed) < budget:
        for i in range(8):
            d = unused_pick(np.array([round(positions[i])]), seen, rng)
            seen.add(d); proposed.append(d); score = oracle[d]["model_b_lambda_0_5"]
            if score < personal_score[i]: personal[i], personal_score[i] = d, score
            if score <= min(personal_score): global_pos = d
            if len(proposed) == budget: break
        velocity = 0.55 * velocity + 1.35 * rng.random(8) * (personal - positions) + 1.35 * rng.random(8) * (global_pos - positions)
        positions = np.clip(positions + velocity, 1, 150)
    return proposed


def de_method(rng: np.random.Generator, budget: int, oracle: dict[int, dict[str, float]]):
    population = rng.uniform(1, 150, size=8); seen: set[int] = set(); proposed: list[int] = []
    scores = np.full(8, np.inf)
    while len(proposed) < budget:
        for i in range(8):
            d = unused_pick(np.array([round(population[i])]), seen, rng); seen.add(d); proposed.append(d); scores[i] = oracle[d]["model_b_lambda_0_5"]
            if len(proposed) == budget: return proposed
        trial = population.copy()
        for i in range(8):
            choices = [j for j in range(8) if j != i]; a, b, c = rng.choice(choices, size=3, replace=False)
            mutant = np.clip(population[a] + 0.8 * (population[b] - population[c]), 1, 150)
            candidate = unused_pick(np.array([round(mutant if rng.random() < 0.9 else population[i])]), seen, rng)
            if oracle[candidate]["model_b_lambda_0_5"] <= scores[i]: trial[i] = candidate
        population = trial
    return proposed


def bo_method(rng: np.random.Generator, budget: int, oracle: dict[int, dict[str, float]]):
    seen: set[int] = set(); proposed: list[int] = []
    for d in rng.choice(DOMAIN, size=6, replace=False): seen.add(int(d)); proposed.append(int(d))
    while len(proposed) < budget:
        x = np.array(sorted(seen), dtype=float); y = np.array([oracle[int(d)]["model_b_lambda_0_5"] for d in x])
        length = 18.0; kernel = np.exp(-((x[:, None] - x[None, :]) ** 2) / (2 * length**2)) + np.eye(len(x)) * 1e-6
        inv = np.linalg.inv(kernel); candidates = np.array([d for d in DOMAIN if int(d) not in seen], dtype=float)
        k = np.exp(-((candidates[:, None] - x[None, :]) ** 2) / (2 * length**2)); mean = k @ inv @ y
        variance = np.maximum(1e-12, 1 - np.einsum("ij,jk,ik->i", k, inv, k)); sigma = np.sqrt(variance)
        improve = y.min() - mean; z = improve / sigma
        cdf = 0.5 * (1 + np.vectorize(erf)(z / sqrt(2))); pdf = np.exp(-0.5 * z**2) / sqrt(2 * pi)
        ei = improve * cdf + sigma * pdf
        top = candidates[ei == ei.max()]; d = int(rng.choice(top)); seen.add(d); proposed.append(d)
    return proposed


def evaluate(method: str, seed: int, budget: int, oracle: dict[int, dict[str, float]]) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed); started = perf_counter()
    if method == "random": picks = random_method(rng, budget)
    elif method == "pso": picks = pso_method(rng, budget, oracle)
    elif method == "de": picks = de_method(rng, budget, oracle)
    elif method == "bo": picks = bo_method(rng, budget, oracle)
    else: raise ValueError(method)
    elapsed = perf_counter() - started; best = float("inf"); rows = []
    for index, d in enumerate(picks, start=1):
        score = oracle[d]["model_b_lambda_0_5"]; best = min(best, score)
        rows.append({"method": method, "seed": seed, "evaluation": index, "d1": d, "objective": score, "best_objective": best, "algorithm_seconds_total": elapsed})
    return rows


def run(output: Path, oracle_path: Path, budget: int, seeds: tuple[int, ...]):
    if output.exists(): raise FileExistsError(output)
    oracle = read_oracle(oracle_path); output.mkdir(parents=True); rows = [r for method in ("random", "pso", "de", "bo") for seed in seeds for r in evaluate(method, seed, budget, oracle)]
    with (output / "traces.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    oracle_best = min(oracle, key=lambda d: (oracle[d]["model_b_lambda_0_5"], d))
    summary = []
    for method in ("random", "pso", "de", "bo"):
        finals = [r for r in rows if r["method"] == method and r["evaluation"] == budget]
        summary.append({"method": method, "seeds": len(seeds), "effective_evaluations_per_seed": budget, "oracle_d1": oracle_best, "oracle_objective": oracle[oracle_best]["model_b_lambda_0_5"], "mean_final_objective": float(np.mean([r["best_objective"] for r in finals])), "best_final_objective": min(r["best_objective"] for r in finals), "oracle_hits": sum(r["best_objective"] == oracle[oracle_best]["model_b_lambda_0_5"] for r in finals), "mean_algorithm_seconds": float(np.mean([r["algorithm_seconds_total"] for r in finals]))})
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axis = plt.subplots(figsize=(7, 4.5))
    for method in ("random", "pso", "de", "bo"):
        values = [[r["best_objective"] for r in rows if r["method"] == method and r["seed"] == seed] for seed in seeds]
        axis.plot(range(1, budget + 1), np.mean(values, axis=0), label=method)
    axis.axhline(oracle[oracle_best]["model_b_lambda_0_5"], color="black", linestyle="--", label="Grid oracle")
    axis.set(xlabel="effective evaluations", ylabel="best-so-far Model B objective", title="Budget-matched optimizer convergence")
    axis.legend(); figure.tight_layout(); figure.savefig(output / "convergence.svg", format="svg"); plt.close(figure)
    (output / "config.json").write_text(json.dumps({"oracle_csv": str(oracle_path), "domain": [1, 150], "objective": "model_b_lambda_0_5", "budget": budget, "seeds": list(seeds), "methods": ["random", "pso", "de", "bo"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir", type=Path, required=True); parser.add_argument("--oracle-csv", type=Path, required=True); parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET); parser.add_argument("--seeds", type=str, default=",".join(map(str, DEFAULT_SEEDS))); args = parser.parse_args()
    run(args.output_dir, args.oracle_csv, args.budget, tuple(int(x) for x in args.seeds.split(",")))


if __name__ == "__main__": main()
