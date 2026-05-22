# Evaluation

Quaere's public numbers come from the in-tree eval harness under [`evals/`](../evals/). The harness is meant to catch the failure modes Quaere targets: shallow code reading, ungrounded external facts, unsupported bug claims, unscoped implementation, and unsafe audit reporting.

It is not a third-party benchmark. Treat it as a regression harness and a falsifiable claim about Quaere's own scenarios.

## Headline sweep — v0.3.1 (in-tree)

18 scenarios / 106 deterministic assertions, single-run via Codex CLI (OAuth Codex on host, `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox`):

| mode                | assertion pass rate | scenario-level    |
| ------------------- | ------------------: | ----------------: |
| Baseline (no skill) | 53% (56 / 106)      | 0 / 18 pass       |
| **With skill**      | **91% (96 / 106)**  | **10 / 18 pass**  |
| Δ                   | **+37.7 pp**        | **+10 scenarios** |

v0.2.1 measured `+27 pp` on 97 assertions; the v0.3.1 sweep adds adversarial assertions and lifts both the assertion-rate gap and the first-time non-zero scenario count.

Scenarios still failing under with-skill are concentrated in the harder evidence / audit families: `ci-failure-evidence-before-patch`, `dangerous-external-operation`, `pressure-to-skip-evidence-gate`, `semantic-understanding-before-change`, `spec-grounded-security-audit`, `triage-tier-confirmation-rule`, plus 2 more — these are the scenarios where pressure or partial information is supposed to defeat the gate.

## Terminal-Bench sweep — v0.3.2 (`terminal-bench-core==0.1.1`)

80 tasks, both modes via the Codex-OAuth adapter under [`evals/terminal_bench/`](../evals/terminal_bench/), `--global-agent-timeout-sec 1800`, install pipeline cosign-verified:

| mode                | resolved   | accuracy |
| ------------------- | ---------: | -------: |
| Baseline (no skill) | 41 / 80    | 51.25%   |
| With skill          | 42 / 80    | 52.50%   |
| Δ                   | —          | **+1.25 pp** |

Recovered (baseline ✗ → with-skill ✓): 7 — `build-tcc-qemu`, `crack-7z-hash.easy`, `crack-7z-hash.hard`, `csv-to-parquet`, `extract-moves-from-video`, `reshard-c4-data`, `swe-bench-astropy-1`. Regressed (baseline ✓ → with-skill ✗): 6 — `extract-safely`, `fix-permissions`, `heterogeneous-dates`, `openssl-selfsigned-cert`, `simple-sheets-put`, `train-fasttext`. Net +1 task, +1.25 pp.

The margin is narrow and well within typical LLM-driven benchmark run-to-run variance. Read this as **"Quaere does not hurt Terminal-Bench performance"** rather than as a measurable improvement. The in-tree sweep above is the load-bearing measurement; Terminal-Bench is reported alongside as an external check that the skills do not regress general agent capability.

### Prior runs and what changed

v0.3.1 reported Δ −17.5 pp on the same dataset. That number was structurally contaminated: `agent_timeout` failure_modes were 9 (baseline) → 33 (with-skill), and a separate cosign-migration push during one of the reruns introduced 0/80 install-pipeline failures in a v0.3.1.5-era rerun. The v0.3.2 measurement above runs with the fixed install pipeline (cosign bootstrapped in the container, `SHA256SUMS.sig` present), agent_timeout raised from default to 1800s, and `agent_timeout` count down from 76 (contaminated rerun) to 7. The −17.5 pp result should be treated as superseded.

## Variance and runner notes

v0.2.0 used two sweeps. The with-skill range was **91.1 – 94.4%**, with a **+27 to +29 pp** delta. Run-to-run variance is real for stochastic LLM output; numbers should be read as a range, not a point estimate. Per-version detail lives in [`CHANGELOG.md`](../CHANGELOG.md).

Cross-runner stability was confirmed during the v0.1.0 measurement: the same `sdk-version-grounding` scenario hit identical 6P/0F with-skill scores on Claude Code 2.1.141 and Codex CLI 0.128.0.

## Running the harness

Run a single scenario:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

See [`evals/README.md`](../evals/README.md) for the full assertion-type table, the three `llm_judge` backends (Anthropic SDK / openai-compat / Codex CLI), the locale-alternate mechanism, and the Terminal-Bench adapter.

## Limits

The in-tree eval does not show that Quaere improves every agent workflow. It shows that, on scenarios designed around Quaere's target failure modes, the skills reduce specific, deterministic mistakes. The Terminal-Bench result above is the honest counterexample: on time-boxed black-box benchmarks, the skills' deliberation cost can land negative until the time budget is widened. External benchmarks are tracked in [`roadmap.md`](roadmap.md).
