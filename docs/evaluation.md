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

## Terminal-Bench sweep — v0.3.1 (`terminal-bench-core==0.1.1`)

A separate sweep against the public Terminal-Bench dataset (80 tasks, both modes via the Codex-OAuth adapter under [`evals/terminal_bench/`](../evals/terminal_bench/)):

| mode                | resolved      | accuracy   |
| ------------------- | ------------: | ---------: |
| Baseline (no skill) | 45 / 80       | 56.25%     |
| With skill          | 31 / 80       | 38.75%     |
| Δ                   | —             | **−17.5 pp** |

Recovered (baseline-fail → with-skill-pass): 6. Regressed (baseline-pass → with-skill-fail): 20. Of the 20 regressions, **17 hit `agent_timeout`**, and the `agent_timeout` count overall jumped from 9 (baseline) to 33 (with-skill).

The dominant failure mode is structural, not quality: Quaere's deliberation pass (claim → defense → probe → patch) consumes time the Terminal-Bench grader counts against the agent budget. Mean non-timeout agent duration was 226s; the regressions live in tasks where with-skill takes longer than the time budget allows. A follow-up sweep with `--global-agent-timeout-sec 1800` and `max_timeout_sec=1800` in the adapter is in flight; results will be added here.

The in-tree sweep is the load-bearing measurement. Terminal-Bench is reported to be honest about where the skills hurt; do not read these numbers as a quality verdict on the skills themselves.

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
