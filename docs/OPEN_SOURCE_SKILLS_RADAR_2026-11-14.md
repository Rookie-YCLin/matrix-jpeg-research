# Open-source trend → reusable research practices (2026-11-14)

Scope: practical engineering lessons from **recent-week**, **rolling-month**, and **prior-year** popular GitHub projects, independently checked against primary repository READMEs/source. Trending counts are snapshots, not scientific evidence or license/security approval. Projects relevant to this particular d1 optimizer are separated from general engineering examples.

## Time windows and evidence

- **Recent week** (GitHub Trending snapshot around 2026-11-13, not a permanent rank): [GitHub trending weekly](https://github.com/trending?since=weekly), [weekly snapshot](https://githubtrending.today/weekly/). [anthropics/skills](https://github.com/anthropics/skills) and [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) were prominent. [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) also appears in week/month trackers. `max-sixty/worktrunk` and NVIDIA's `auto-ontology` appeared in monitored recent-week snapshots; exact ranks vary with time.
- **Recent month** (rolling 30 days): [GitHub Trending monthly](https://github.com/trending?since=monthly), [Nov 13 snapshot](https://githubtrending.today/monthly/). Many high-attention projects are agent workflow, code review, memory and agent security tools, e.g. [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) and [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem). Popularity is **not** the same as reliability.
- **Previous years / multi-year ecosystem**: [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/) highlights contributor activity in vLLM, VS Code, Codex, transformers and llama.cpp; [Octoverse 2026](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/) highlights growing agent workflows and active open source inference projects. These reports rank by **contributors/engagement**, not necessarily trending stars. [uv](https://github.com/astral-sh/uv) is called out among 2025's fastest-growing developer tools in GitHub's follow-up analysis: [2025 fastest-growing tools](https://github.blog/news-insights/octoverse/what-the-fastest-growing-tools-reveal-about-how-software-is-being-built/).

## Lessons worth reusing

| Project | Source-read insight | Action applicable to this research |
| --- | --- | --- |
| [anthropics/skills](https://github.com/anthropics/skills) | Agent skills are explicit folders with task instructions and tools; skill-creator discusses evaluation and iteration | Keep a repo-local `.agents/skills/expensive-black-box-experiments/SKILL.md` with reproducibility rules rather than unreliable implicit memory |
| [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) | Distinguishes candidate findings from independently verified findings and retains machine-checkable audit records | Distinguish *new code*, *CI passed*, *real JPEG data*, and *scientific improvement*; make PR findings verifiable |
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | Uses compact, element-referenced snapshots for testable browser actions | Prefer auditable source-based actions to fragile screenshot/location guesses |
| [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk) | Git worktree isolation for parallel coding workflows | Keep V2, DIRECT and early-rejection research changes isolated and individually reviewable |
| [astral-sh/uv](https://github.com/astral-sh/uv) | Fast deterministic Python environment / lockfile workflows | Freeze image/compression dependencies for trustworthy cross-run comparisons |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | Fast lint/formatter on Python code | Catch errors cheaply before expensive JPEG benchmarks |
| [vllm-project/vllm](https://github.com/vllm-project/vllm), [sgl-project/sglang](https://github.com/sgl-project/sglang) | Optimize measured inference throughput and resource constraints | Distinguish bottleneck cost, wall time and numerical quality; batch only if it preserves semantics |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | Explicit quantization/performance tradeoffs with different hardware backends | Measure both performance and numerical consequences; compression is not free |
| [kornia/kornia](https://github.com/kornia/kornia) | Differentiable, GPU-ready classical image processing in PyTorch with a research/benchmark focus | Potential future differentiable watermarks, but JPEG BER for this project is currently discrete; do **not** substitute differentiability claims for real JPEG tests |

## Specialized optimization repositories (relevance outweighs popularity)

- [DIRECTGO](https://github.com/blockchain-group/DIRECTGO): deterministic global/local partitioning. Our **negative coffee** case shows aggressive local refinement can miss a second feasible island.
- [pySOT](https://github.com/dme65/pySOT): supports asynchronous surrogate optimization, integer variables, SRBF/DYCORS; candidate for a budget-matched, proposal-only future selector.
- [RBFOpt](https://github.com/coin-or/rbfopt): mixed-integer black-box optimization via radial basis models; useful model design but heavyweight implementation/dependencies.
- [SMAC3](https://github.com/automl/SMAC3): Bayesian optimization and racing. Borrow *staged evaluation*, not its ML-specific assumptions; all nine QFs must still be verified for accepted d1.
- [BayBE](https://github.com/emdgroup/baybe) and [BoTorch](https://github.com/meta-pytorch/botorch): constrained experimental design and modular probabilistic surrogate/acquisition functions; may be overkill for a single integer variable.
- [Nevergrad](https://github.com/facebookresearch/nevergrad): derivative-free, integer-compatible baseline for comparisons.

## Skill adoption criteria

When evaluating a fashionable repository:
1. Verify the repository **actually exists**, inspect its README and relevant source, check license, recent changes, issues, reproducibility and security risks.
2. Record what *specific mechanism* is transferable to our problem, and which assumptions break (e.g. smoothness, expensive constraints, discrete variables).
3. Prefer a minimal isolated reproduction/test to a major dependency. Never execute unreviewed third-party install scripts or copy hidden permissions.
4. Record a measurable prediction such as “fewer actual JPEG attacks with no loss of verified d1/PNG PSNR”, then test fairly.
5. Separate an **engineering practice** (reusable skill) from a benchmarked **scientific claim** (requires real data).

## Immediate results tied to this note

- Verified negative DIRECT experiment: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/44 (coffee missed lower feasible island).
- Implemented early-rejection V2 pilot: this research branch; no new performance claims until workflow artifacts are checked.
- Reusable research process is written in `.agents/skills/expensive-black-box-experiments/SKILL.md`; it is **repository-local guidance**, not an automatically installed ChatGPT skill.

The current goal is still narrow: preserve all-nine-QF zero BER and maximize PNG PSNR with fewer real embedding+JPEG+extraction operations. Do not launch unrelated hot projects into the scientific pipeline.
