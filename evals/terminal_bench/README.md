# Terminal-Bench adapter

External benchmark adapter that runs Quaere through
[Terminal-Bench v2](https://www.tbench.ai/). Two agents wrap Codex CLI:

- **`quaere-tb-codex-baseline`** — Codex CLI only. The control.
- **`quaere-tb-codex-with-skill`** — Codex CLI + `quaere install`. The treatment.

The only difference between the two is whether `~/.claude/skills/quaere-*`
is present in the per-task container. Δ in pass rate between the two
attributes the difference to the Quaere skill set.

## Layout

```
evals/terminal_bench/
├── README.md                        ← this file
├── __init__.py                      ← lazy-import shim
├── agents/
│   ├── __init__.py
│   └── quaere_tb_codex.py           ← AbstractInstalledAgent subclasses
└── install_scripts/
    ├── install-baseline.sh          ← Codex only
    └── install-with-skill.sh        ← Codex + quaere-cli + quaere install
```

## Prerequisites

- Docker (Terminal-Bench provisions per-task Debian containers).
- Python 3.11+ and `pip install terminal-bench` on the host.
- `OPENAI_API_KEY` in the environment (the Codex CLI reads it from there).
  Optional: `CODEX_MODEL` to pin a model.

The adapter package itself imports without `terminal-bench` installed —
helpful for CI and IDEs — but actually running a sweep requires the
dependency.

## Running locally

```bash
# 1. Install the host harness.
uv tool install terminal-bench
# or:
pip install terminal-bench

# 2. Point Terminal-Bench at the adapter package.
export TB_AGENT_REGISTRY=$(pwd)/evals/terminal_bench

# 3. Smoke phase: run one task per mode to verify wire-up.
tb run \
  --agent quaere-tb-codex-baseline \
  --task hello-world \
  --output-dir "$(pwd)/eval-results/tb-smoke-$(date -u +%Y%m%dT%H%M%SZ)"

tb run \
  --agent quaere-tb-codex-with-skill \
  --task hello-world \
  --output-dir "$(pwd)/eval-results/tb-smoke-$(date -u +%Y%m%dT%H%M%SZ)"
```

If the baseline run reports any `~/.claude/skills/quaere-*` after install,
the script exits non-zero (we treat a leaked treatment as a void run).

## Sweep phases

The benchmark plan ships in three phases:

1. **Smoke** (5–10 hand-picked tasks across SWE / sysadmin / security).
   - Confirms both install scripts succeed inside the task container.
   - Confirms `quaere doctor` inside the with-skill container reports
     the expected Quaere CLI version (matches the in-tree pin) and lists
     the five `quaere-*` skills.
   - Calibrates API cost per task before committing to the full suite.

2. **Full suite** (terminal-bench-core v0.1.1 — 80 tasks, both modes, ≥2 runs).
   - Per-task pass/fail recorded under `eval-results/tb-<timestamp>/`.
   - Aggregate Δ reported as a range across runs (matches the v0.2
     measurement narrative — point estimates hide LLM stochasticity).
   - Per-task breakdown identifies tb task types where Quaere moves
     the needle and those where it does not.

3. **Leaderboard** (optional, after stability).
   - Submit the with-skill registration so the claim is externally
     auditable. Submit only after at least 2 full-suite runs agree
     within run-to-run variance.

## Cost note

Each tb task is a multi-turn agent session (not a single prompt). Per-task
token cost depends on the Codex model selected and the task surface. The
smoke phase exists specifically to measure this before committing to a
full sweep budget. Expect the full sweep to run for **at least an hour of
wall-clock** and use a non-trivial API budget; do not run it casually.

## Updating the pinned Codex version

Both install scripts read `CODEX_VERSION` from the environment with a
default of `0.128.0`. Bump the default in both scripts together so the
treatment and control stay aligned. The Quaere in-tree eval is also
pinned to Codex CLI 0.128.0; bumping the tb adapter version without
bumping the in-tree pin would make cross-eval comparisons unsound.

## Why this is gitignored-ADR-driven and not in-README

The full design rationale (Stream split, scope decisions, alternatives
considered) lives in an internal design note (`docs/adr/` tree, gitignored
in this repo). This README is the public face — what the directory does,
how to use it, what to expect. Read the public surface here; if you are a
maintainer, the design note is local-only.
