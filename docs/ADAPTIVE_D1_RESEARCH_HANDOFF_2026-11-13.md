# Adaptive d1 zero-BER research — current handoff (2026-11-13)

> **Read this document first if you are Codex, ChatGPT Work, or another agent.** This is the current research direction for the **adaptive-d1 project on the research branch**. The older G6/QF15-only closure instructions in `AGENTS.md`, `README.md`, `docs/RESEARCH_NEXT_PHASE.md`, and historical reports remain valid **for the completed G6 project**, but **do not forbid new experiments in the separately scoped adaptive-d1 research track**. Do not erase or rewrite historical records.

## 0. Executive abstract (研究摘要)

We study automatic **image-dependent selection of the first SVD-QIM quantization step `d1`** in the existing DWT–DCT–SVD blind image watermarking pipeline. The problem is that a fixed or manually chosen `d1` can yield bit errors under JPEG recompression, while overly large values destroy visual quality. For the explicitly screened set of input images for which `d1=720` already achieves **zero BER at *every* target JPEG quality factor** (and zero clean-extraction errors), we optimize image quality (PSNR) **subject to zero BER as a hard constraint**. We want an adaptive black-box optimizer to identify a high-quality feasible `d1` with **substantially fewer actual embedding/JPEG/extraction evaluations** than exhaustive enumeration. We are **not** claiming all images qualify, and we are **not** attempting to re-engineer DWT/DCT/SVD or to prove that any untested QF has zero BER.

中文：研究既有 DWT–DCT–SVD 浮水印演算法的 **量化步長 `d1` 自動選擇問題**。先以 `d1=720` 在指定 JPEG QF 全數零 BER 且無攻擊擷取正確的條件篩選研究影像，確保每張納入的影像**至少有一個已測可行解**；再尋找具有更高 PSNR 的 `d1`。核心新意應落在 **如何減少真實 JPEG 評估次數**，而不只是自動窮舉。

## 1. Mathematical formulation and precise scope

For each image `x`, payload, keys and fixed JPEG pipeline, predeclare a finite set `Q` of JPEG quality factors and a discrete allowed domain `D` **containing 720**.

- Screening/eligibility: `clean_errors(x,720)=0` and `BER(x,720,q)=0` for **every** `q in Q`. Otherwise report `image_not_eligible_for_current_study` rather than treating an unsatisfiable case as an optimizer failure.
- Once admitted: `max_{d1 in D} PSNR(x,d1)` subject to `clean_errors(x,d1)=0` and `BER(x,d1,q)=0 for every q in Q`.
- `d1=720` is a **verified feasible fallback/incumbent**, not an assertion that `720` is optimal, the smallest feasible step, or suitable for all images.
- Keep the best feasible incumbent and do not replace it with a worse candidate. Thus the incumbent's *measured* PSNR never decreases.
- Fixed `d2=20` in currently archived experiments. Match payload, keys, bit length, JPEG save parameters, image processing, and upstream version when comparing algorithms.
- **Hard constraints take priority.** Never silently substitute a weighted BER/PSNR loss for the zero-BER feasibility criterion. A prior *historical* `model_a_feasible` field additionally enforces a **40 dB floor** and is **not the same** as current zero-BER feasibility. For this research, determine feasibility from `clean_errors==0 && worst_ber==0` across the predeclared Q.
- PSNR is currently measured between original RGB and watermarked **PNG** before JPEG attack; state this precisely. Don't conflate it with PSNR of JPEG-compressed output.
- The study is conditioned on the screening rule. Generalization claims must acknowledge that the selected population is conditional on `d1=720` being feasible; evaluate eligibility rate separately when expanding to a wider image corpus.

## 2. Verified experiments as of 2026-11-13 (GitHub artifacts; not guessed)

### A. Broad-QF real-JPEG sparse-grid feasibility pilot

Workflow run: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43358837574 — **completed/success**, commit `985e34e6782a4cda257b686bf1416487e545063f`, all **three parallel image jobs successful**; each has `per_d1.csv`, `per_qf.csv`, `zero_ber_result.json`.

- Fixed Q: **{5,10,15,20,30,50,70,90,95}** (9 values), 68 candidate d1 per image; this is a **sparse** grid, not exhaustive over all positive integers.
- `astronaut`: 24/68 measured zero-BER feasible candidates; best measured `d1=161`, PNG PSNR **25.6145 dB**. `d1=720` zero-BER feasible, PSNR **13.1697 dB**. Artifact `14007327919`.
- `chelsea`: 30/68; best measured `d1=145`, PSNR **27.0836 dB**; `d1=720` zero-BER feasible, PSNR **13.9578 dB**. Artifact `14006803545`.
- `coffee`: 25/68; best measured `d1=97`, PSNR **30.9425 dB**; `d1=720` zero-BER feasible, PSNR **15.2217 dB**. Artifact `14006989482`.
- All the above candidates also had zero clean-extraction errors under the frozen experiment. This is evidence of **feasibility on these exact images and QFs**, not robustness to unseen compression settings, different watermark payloads, or other images.

### B. Full integer d1=1..150 reference grid (different QF set)

Workflow run: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43358837832 — **completed/success**; artifact `14008146232`, with per-image `per_d1.csv` and `manifest.jsonl`.

- Fixed Q: **{5,6,7,8,9,10}**, not the nine broad QFs above! 150 d1 evaluations per image, 6 attacks per d1.
- `astronaut`: **0** zero-BER feasible d1 in 1..150 on these six QFs.
- `chelsea`: **9** zero-BER feasible d1; among them `d1=139`, PSNR **27.3665 dB** is best measured. **Do not claim it passes the nine-QF broad set until those QFs are actually tested.**
- `coffee`: **0** zero-BER feasible d1 in 1..150 on these six QFs.
- The historical `model_a_feasible=False` in this artifact is due to an additional 40 dB quality floor; don't confuse it with zero BER.

### C. Research CI

https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43358837587 — **completed/success**. Research, original-image-QF scan, SVD-QIM exploration, and selected SVD validation passed. This establishes those jobs ran; it is **not** validation of a new adaptive optimizer.

## 3. What Codex should implement next (proposed work, **not yet measured**)

1. Preserve and hash/archive the existing experiment artifacts; do not overwrite original CSV/JSON or make up missing values.
2. Build a **reproducible black-box adaptive-d1 optimization runner** with a shared evaluation budget, cost accounting, deterministic seed, per-image logs, exact Q set, incumbent history, and a `d1=720` feasibility precheck.
3. Baselines: `d1=36`, `90`, `720`; exhaustive optimum on the **same predefined finite D and Q**; and at least a simple adaptive multi-region/multi-start search before testing discrete PSO (or other justified optimizer). Compare algorithms using **the same evaluations budget** and prohibit hindsight leakage from exhaustive outputs into the adaptive search.
4. Handle strongly non-monotonic/discontinuous BER-vs-d1. Do not use binary search assuming monotonicity. Cache evaluated d1 values. If zero-BER verification is expensive, use safe early termination when any required QF fails, while logging cost consistently.
5. Metric priority: (a) correct zero-BER feasibility across every target QF + clean extraction, (b) highest PSNR of feasible solutions, (c) actual number of costly evaluations / JPEG attacks, (d) repeatability. Record budget vs solution-quality curves. If none found, retain verified 720 and report.
6. Pilot a small benchmark before expanding to 50+ public photos; keep a held-out image split. Explicitly log images failing the d1=720 eligibility condition; don't erase them.
7. Provide unit tests for selector, budget exhaustion, eligibility, incumbent never degrading, caching, image/QF isolation, and reproducibility. Run tests plus a genuinely executable small end-to-end experiment. Commit results/PR links. Don't claim an optimizer success from a conceptual design alone.

## 4. What ChatGPT Work should do next

- Audit GitHub PRs, commits, CI, artifact provenance and document inconsistencies; reconcile historical G6 scope vs new adaptive-d1 research without rewriting historical success criteria.
- Read results CSV/JSON *before* writing literature claims. Produce a short evidence-based status report distinguishing **measured**, **hypothesis**, and **planned**.
- Research discrete constrained black-box optimization, PSO, region-adaptive search and alternatives in relevant watermarking literature. Propose evaluation protocols and fair comparator selection; cite real sources and limitations.
- Maintain an up-to-date experimental ledger and change log, preferably linked from `AGENTS.md` and Issue #42: https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/42.
- Aim for a professor-ready **matrix theory + numerical optimization** discussion, but only after verifying performance. A useful rank-one identity for interpreting an isolated singular-value change is `Delta A = Delta sigma_1 u_1 v_1^T` and `||Delta A||_F^2=(Delta sigma_1)^2`; this is a *local matrix-level explanation* and does not by itself prove final-image PSNR or JPEG BER properties.

## 5. Agent operational protocol

- This repository is the **experimental laboratory**. Use GitHub Actions for actual experiments; use artifacts as data and commits/PRs as provenance.
- **Do not rely on ChatGPT conversation context** as a source of truth; read `AGENTS.md`, this file, relevant experiment code and run artifacts. Update this handoff if the strategy changes.
- Never equate `commit succeeded`, `workflow started`, `workflow passed`, and `scientific hypothesis supported`.
- Parallel workflows and image jobs are encouraged, subject to cost/concurrency limits. Track each run until a terminal conclusion; inspect job logs, data artifacts, and failed/skipped jobs.
- Keep changes on an isolated research branch / PR. Don't merge or delete important research history merely to simplify management.
- Don't claim universal zero BER, exact global optimum, or effectiveness of PSO until measured. Prefer explicit, falsifiable claims and exact tested conditions.

## 6. Links and entry points

- Main research PR: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/40
- Research management issue: https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/42
- Broad-QF pilot code: `experiments/adaptive_d1_zero_ber_pilot.py`
- Zero-BER selector: `experiments/adaptive_d1_zero_ber_selection.py`
- Shared real JPEG evaluator: `experiments/adaptive_d1_grid.py`
- Parallel workflow: `.github/workflows/zero-ber-broad-qf-pilot.yml`
