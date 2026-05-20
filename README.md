# Quaere

> Process-correction skills that make coding agents ask before they act.

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

[Why Quaere](#why-quaere) · [Skills](#skills) · [Installation](#installation) · [CLI](#verifying-and-managing-the-install) · [quaere.dev](https://quaere.dev/) · [日本語](README.ja.md)

## Why Quaere

Coding agents drift at four predictable points:

- they read code shallowly,
- they accept plausible claims without proof,
- they edit in unreviewed blobs,
- they commit without authorization.

Quaere is five skills that slow the agent down at each of those points — not by adding ceremony, but by forcing one move: **state a claim, defend it with evidence, only then act.**

The name comes from Latin *quaere* — "ask", "seek", "interrogate". Every skill in this collection enforces the same gate.

### Measured effect

**v0.2.1** — 18 scenarios / 97 deterministic assertions (14 original + 4 new adversarial), single-run via Codex CLI:

| mode                | assertion pass rate | scenario-level            |
| ------------------- | ------------------: | ------------------------: |
| Baseline (no skill) | 60% (58 / 97)       | 0 / 18 pass               |
| **With skill**      | **87% (84 / 97)**   | **8 pass · 4 inconclusive · 6 fail** |
| Δ                   | **+27 pp**          |                           |

4 inconclusive scenarios have zero failed assertions; they contain `not_in_baseline` assertions that require a baseline run to resolve. 4 timeouts in the with-skill sweep (complex skill prompts + multi-step scenarios) account for most remaining failures.

The 4 new adversarial scenarios (urgency pressure, skip-test pressure, docs blind-trust, baseless security assertion) score 92% with-skill vs ~46% baseline — the largest skill-vs-baseline gap in the suite.

**v0.2.0** — 14 scenarios / 90 assertions, two independent sweeps via Codex CLI 0.128.0:

| mode                | range (2 runs)    |
| ------------------- | ----------------: |
| Baseline (no skill) | 63.9 – 65.1%      |
| **With skill**      | **91.1 – 94.4%**  |
| Δ                   | **+27 to +29 pp** |

v0.1.0 baseline: with-skill 89.8% / Δ +28 pp. Run-to-run variance is real for stochastic LLM output; numbers should be read as a range, not a point estimate.

The eval harness lives at `evals/run_skill_evals.py`; the 18 scenarios at `evals/scenarios.json`; Japanese-locale token alternates at `evals/scenarios.ja.json`.

Cross-runner stability was confirmed during the v0.1.0 measurement: the same `sdk-version-grounding` scenario hit identical 6P/0F with-skill scores on Claude Code 2.1.141 and Codex CLI 0.128.0.

## Skills

| Skill | Use when | Main safeguard |
| --- | --- | --- |
| [`skills/quaere-semantic`](skills/quaere-semantic/SKILL.md) | You need to understand unfamiliar code, module intent, invariants, or why code is shaped a certain way before changing it. | Forces `What / Why / Invariants / Failure modes / Connections` per meaningful unit and marks unknown intent instead of inventing it. |
| [`skills/quaere-grounding`](skills/quaere-grounding/SKILL.md) | The task depends on external, version-sensitive facts: SDKs, APIs, libraries, CLIs, cloud services, security advisories, changelogs, release notes, or docs. | Anchors local versions, ranks source quality, checks version fit and conflicts, and turns confirmed external facts into implementation constraints. |
| [`skills/quaere-evidence`](skills/quaere-evidence/SKILL.md) | You are handling unclear bugs, risky PR review, CI failures, flaky tests, security-sensitive changes, database/concurrency changes, external APIs, or claims that need evidence before patching. | Requires findings, hypotheses/claims, defense, disconfirming probes, decisions, verification, and handoff before accepting a fix. |
| [`skills/quaere-execution`](skills/quaere-execution/SKILL.md) | You are authorized to implement a multi-step coding change, apply a plan, finish review feedback, or turn a specification into working code. | Enforces read → plan → execute → review → fix → verify → commit, with commits only when explicitly authorized. |
| [`skills/quaere-audit`](skills/quaere-audit/SKILL.md) | You are doing deep security auditing, bug bounty preparation, protocol conformance checking, exploitability analysis, or specification-grounded vulnerability discovery. | Derives explicit security properties, maps attack surfaces and code, attempts proofs, gates false positives, and reports confirmed/potential/rejected findings with evidence or PoCs. |

## Pipeline

For complex work, the skills compose naturally:

```text
quaere-semantic → quaere-grounding → quaere-evidence → quaere-execution
```

- Use `quaere-semantic` first when misunderstanding existing code would make the implementation risky.
- Use `quaere-grounding` when implementation depends on external facts that may have changed.
- Use `quaere-evidence` when a claim, bug cause, review comment, or proposed fix needs proof.
- Use `quaere-execution` when it is time to implement the confirmed plan and verify the final diff.
- Use `quaere-audit` when the task is not just fixing one claim, but discovering or validating vulnerabilities from properties, attack surfaces, and exploitability gates.

A small implementation can use only `quaere-execution` in lightweight mode; a pure code-reading task can stop after `quaere-semantic`; SDK, cloud API, or dependency work can start with `quaere-grounding`.

## Selection guide

Use the first matching row that describes the main risk in the task:

| Main risk | Start with | Then use |
| --- | --- | --- |
| The existing code's intent or invariants are unclear. | `quaere-semantic` | `quaere-execution` only after the important invariants are known. |
| The answer depends on current SDK, API, CLI, cloud, advisory, or docs behavior. | `quaere-grounding` | `quaere-execution` with only confirmed constraints, or `quaere-evidence` if facts conflict. |
| A bug cause, CI failure, flaky test, or review claim might be wrong. | `quaere-evidence` | `quaere-execution` after a claim or hypothesis is confirmed. |
| The plan is already approved and implementation is the main work. | `quaere-execution` | `quaere-evidence` if the work turns risky or the cause becomes unclear. |
| The task is to discover or validate vulnerabilities from specs and attack surfaces. | `quaere-audit` | It coordinates `quaere-semantic`, `quaere-grounding`, `quaere-evidence`, and `quaere-execution` as needed. |

If two skills seem plausible, choose the one that answers the blocking question first:

- "What does this code mean?" → `quaere-semantic`
- "Is this external fact true for this version?" → `quaere-grounding`
- "Is this claim actually proven?" → `quaere-evidence`
- "Are we ready to change files?" → `quaere-execution`
- "What security properties can fail?" → `quaere-audit`

## Installation

### Recommended: curl one-liner

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

This downloads the `quaere` CLI binary for your platform, verifies its checksum against the release `SHA256SUMS`, places it in `$HOME/.local/bin/quaere`, and runs `quaere install` to extract the skill set to `~/.claude/skills/`.

Environment overrides: `QUAERE_VERSION` to pin a tag, `QUAERE_REPO` to install from a fork, `QUAERE_INSTALL_DIR` to relocate the binary, `QUAERE_SKILLS=0` to skip the skill extraction step.

### cargo install (Rust toolchain users)

```bash
cargo install quaere-cli
quaere install
```

`cargo install` builds the CLI from source and the second command extracts the bundled skills.

### Homebrew

```bash
brew install haru0416-dev/quaere/quaere
quaere install
```

The formula lives in the dedicated tap repository [`haru0416-dev/homebrew-quaere`](https://github.com/haru0416-dev/homebrew-quaere). It pulls the same release tarballs as the curl installer and verifies them against the recorded `SHA256SUMS`. `quaere install` then extracts the skill set to `~/.claude/skills/`.

### Manual (source checkout)

```bash
git clone https://github.com/haru0416-dev/quaere.git
cd quaere
mkdir -p ~/.claude/skills
cp -R skills/quaere-* ~/.claude/skills/
```

Each skill is a directory containing a `SKILL.md`. The `name` frontmatter matches the directory name.

### Verifying and managing the install

```bash
quaere list      # show installed skills and the recorded version
quaere doctor    # verify frontmatter, names, line budget, orphans
quaere update    # check for a newer release on GitHub
quaere version   # print the CLI version
```

See [`CHANGELOG.md`](CHANGELOG.md) for the per-version change history; the `Unreleased` section is the next-up shipping list.

### CLI behavior reference

The v0.1.0 CLI follows these contracts:

- **`quaere install` is additive.** Running `quaere install --skill quaere-semantic` and then `quaere install --skill quaere-audit` against the same `--target` accumulates both skills into the manifest. The manifest stays consistent with the union of (previously installed skills that still exist on disk) + (skills installed this run) + (skills already present and skipped). The manifest entries are sorted for deterministic diffs.
- **Unknown `--skill` names are rejected early.** A typo like `--skill quaere-semantik` aborts with the list of available skills *before* anything is written. There is no partial-install fallback.
- **`quaere doctor` orphan policy.** A directory in the install target that is not recorded in the manifest is surfaced as an orphan. Orphans whose name starts with `quaere-` are treated as errors (a misbehaving Quaere install). Orphans with any other name are informational only — the install target may be shared with other skill management tools.
- **`quaere update` uses semantic version comparison** for the standard `X.Y.Z` form, falling back to string comparison when either side is not parseable as semver. The command never modifies the binary; it only prints upgrade instructions.
- **Default `--repo` is `haru0416-dev/quaere`**. If you are tracking a fork, override it: `quaere update --repo your-fork/quaere`. The same applies to `scripts/install.sh` via the `QUAERE_REPO` environment variable.

These contracts are exercised by the `tests/test_validator_parity.py` cross-check between the Python validator and the Rust doctor (CI job `parity`).

## Examples

See [`examples/`](examples/) for realistic prompts and expected behavior patterns.

Quick examples:

- "Read this module and explain the intent before we change it" → `quaere-semantic`
- "Check the installed SDK version and current docs before suggesting code changes" → `quaere-grounding`
- "This CI failure looks flaky; figure out whether the review comment is real before patching" → `quaere-evidence`
- "Apply this plan, run tests, review the diff, and commit if it passes" → `quaere-execution`
- "Audit this protocol implementation against the spec and produce confirmed or potential vulnerabilities with evidence" → `quaere-audit`

## Safety notes

- Commits happen only when the user explicitly authorizes them.
- `.agent-state/` is local investigation state by default and should not be committed unless the user asks for it as an artifact.
- Risky work should prefer evidence and disconfirming checks over fast-looking patches.

## Validation

Run the local validator before publishing changes:

```bash
python scripts/validate_skills.py
```

The validator checks frontmatter, directory/name consistency, README coverage, line-count budget, and accidental `.agent-state/` inclusion. GitHub Actions runs the same validation on push and pull request.

## Skill evaluation

`evals/scenarios.json` contains 18 portable scenario prompts. Seven of them rely on workspace fixtures under [`eval-fixtures/`](eval-fixtures/) — small, vendored projects that give the agent concrete local evidence (pinned `package.json`, vendored docs, fake CLIs, spec files, etc.). The runner copies the fixture into an isolated directory per run so concurrent evaluations do not interfere.

Run scenarios through any local agent CLI by providing a command template. `--output-dir` should be absolute so the runner can read `$prompt_file` from inside the workspace `cwd`:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

The runner writes isolated prompts, stdout/stderr, metadata, and per-assertion grades under `eval-results/<timestamp>/`. `--mode both` runs a baseline prompt without the skill and a with-skill prompt that injects the relevant `SKILL.md`.

Runner command templates are shell commands. They can print the agent response to stdout or redirect it to `$output_file`. They can use:

- `$prompt_file` — generated prompt file
- `$output_file` — stdout capture path
- `$workspace` — isolated working directory
- `$run_dir` — result directory
- `$scenario_id`, `$skill`, `$mode` — run metadata

Scenarios carry deterministic `assertions` for CI-friendly checks, in addition to a manual rubric in `expected`:

| assertion type | purpose |
| --- | --- |
| `contains` / `contains_any` / `not_contains` | literal substring presence or absence |
| `regex` | one regex match anywhere in output |
| `ordered_sections` | a list of regex patterns must match in that order |
| `min_section_count` | a regex must match at least *N* times |
| `requires_pair` | if `if_contains` matches, then `must_also_contain` (or, optionally, `skip_when`) must also match |
| `not_in_baseline` | a pattern that *only* the with-skill mode should match (signal isolation) |
| `exit_code` | the runner exit code must equal the given integer |
| `behavior` | per-run resource thresholds against runtime metadata (`max_tool_calls` / `min_tool_calls` / `max_duration_seconds` / `max_tokens_output` / `max_tokens_input`); records `status: "manual"` when the runner did not emit the relevant metric |
| `llm_judge` | LLM grades the output against a free-form `rubric`; opt-in via `--enable-llm-judge`. Returns `pass` / `fail` / `manual` based on the judge's response and is skipped (`status: "skipped"`) when the flag is off |

The `skip_when` clause on `requires_pair` lets an assertion treat a labeled skip branch (e.g. `Final gate: skipped because <reason>`) as vacuously satisfied. Anchor `skip_when` tightly — the bare token `(?i)skipped` would silently flip fails to passes whenever the word appears anywhere in output.

`llm_judge` is default-off so per-PR CI cost stays at zero. To run judge-graded assertions:

```bash
export ANTHROPIC_API_KEY=...
pip install anthropic
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

Responses are cached at `evals/.llm_judge_cache/<sha>.json` keyed by `sha256(backend:model + rubric + output)`, so re-running with unchanged outputs is free. Default model is `claude-haiku-4-5-20251001`; per-call cost is approximately ¥0.4 (input $1 / MTok + output $5 / MTok, 2,200 input / 100 output tokens per judgement). A full 14-scenario sweep with ~3 judge assertions per scenario lands around ¥34.

#### Running llm_judge against a local model

Any OpenAI-compatible endpoint works — Ollama, vLLM, LM Studio, LocalAI, LiteLLM proxy, etc. Two extra flags:

```bash
pip install openai
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --llm-judge-backend openai-compat \
  --llm-judge-base-url http://localhost:11434/v1 \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

`--llm-judge-base-url` can also come from `$QUAERE_LLM_JUDGE_BASE_URL`. The `OPENAI_API_KEY` env var is used if set, otherwise a placeholder is sent (most local servers ignore it). The cache key includes the backend, so a switch between backends does not silently reuse responses from the other one. Smaller local models (7–13B) tend to be noisy on PASS / FAIL boundary cases; 30B+ class is recommended for stable grading.

#### Running llm_judge via Codex CLI

A third backend reuses the Codex CLI subprocess for grading. No extra Python SDK; the judge picks up whatever endpoint and auth Codex is already configured for (so the judge sees the same model / OPENAI_BASE_URL / OS auth that the agent under test does):

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --llm-judge-backend codex \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

The codex backend invokes `codex exec --output-last-message <tmpfile> -`, reads the final message, and discards the rest. Per-call cost matches whatever Codex itself bills (Codex's own model selection applies; pass `--llm-judge-model <id>` to pin a specific one). Useful when Codex is already authenticated for the in-tree eval runner and you don't want to manage a second SDK or key.

### Locale alternates

The public surface of the project is English: skill bodies, scenario prompts, and assertion patterns in `evals/scenarios.json` are English-only. Locale-specific token alternates (Japanese, paraphrases, etc.) live in `evals/scenarios.ja.json` and are opt-in via `--scenarios-extra`:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenarios-extra evals/scenarios.ja.json \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

At load time the extras file is merged into the main scenarios by matching `(scenario id, assertion name)`. Regex/string fields get `|`-alternation appended; `ordered_sections.patterns` and `not_in_baseline.patterns` get per-position alternation; `contains_any.texts` get array concatenation. Unknown ids or names error out so stale extras files cannot silently drop alternates.

Real-LLM eval runs are gated behind a manual workflow trigger and are not required to pass on every PR.

## External benchmarks (roadmap)

The in-tree eval is fast and well-suited to per-PR signal, but it does not substitute for third-party validation. Four external benchmarks are tracked for future integration, in this priority order:

1. **[Terminal-Bench v2](https://www.tbench.ai/)** — 80-task `terminal-bench-core` v0.1.1 (the current public leaderboard subset, out of 241 in the broader pool). The closest fit for `quaere-execution` and `quaere-grounding`. Highest expected Δ. **In progress for v0.3**: adapter shipped at [`evals/terminal_bench/`](evals/terminal_bench/) with two Codex-CLI-wrapping agents (`quaere-tb-codex-baseline` / `quaere-tb-codex-with-skill`) and a manual-trigger CI workflow. Smoke / full / leaderboard phases per the adapter README.
2. **[SWE-bench Verified](https://www.swebench.com/)** — 500 human-verified GitHub-issue patches. The standard credibility test for coding agents; non-optional eventually. Heavy infra cost (≥120GB storage, 16GB RAM, 8 CPU) and substantial API budget. Targeted for v1.0.
3. **[SkillsBench](https://www.skillsbench.ai/)** — 84 domain-skill tasks (3D, robotics, security PCAP, energy, etc.). Submission unit is "agent that uses skills". Lower expected Δ because domain skills dominate; Quaere's process-correction angle is less visible. Tracked, not committed.
4. **SWE-Bench Pro** — harder successor to Verified. Considered only after Verified.

Quaere's claim is that process-correction skills lift any agent's quality on the deliberation axis. Terminal-Bench probes that claim directly; SWE-bench Verified probes whether it generalizes to long-form patch generation. Until those numbers exist, the only published evidence is the in-tree eval result above.

## License

MIT. See [`LICENSE`](LICENSE).
