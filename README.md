# Quaere

> Process-correction skills that make coding agents ask before they act.

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

[Why Quaere](#why-quaere) · [Skills](#skills) · [Picking a skill](#picking-a-skill) · [Installation](#installation) · [Verifying](#verifying-the-install) · [quaere.dev](https://quaere.dev/) · [日本語](README.ja.md)

## Why Quaere

Coding agents drift at four predictable points:

- they read code shallowly,
- they accept plausible claims without proof,
- they edit in unreviewed blobs,
- they commit without authorization.

Quaere is five skills that slow the agent down at each of those points. They do not add ceremony; they force one move: **state a claim, defend it with evidence, only then act.**

The name comes from Latin *quaere* — "ask", "seek", "interrogate". Every skill in this collection enforces the same gate.

### Measured effect

**v0.2.1** was the last sweep that measured the skills directly. v0.3.0 only changes the CLI and the install pipeline; the skill bodies are untouched, so these numbers still represent the current effect of the skills.

**v0.2.1** — 18 scenarios / 97 deterministic assertions (14 original + 4 new adversarial), single-run via Codex CLI:

| mode                | assertion pass rate | scenario-level                       |
| ------------------- | ------------------: | -----------------------------------: |
| Baseline (no skill) | 60% (58 / 97)       | 0 / 18 pass                          |
| **With skill**      | **87% (84 / 97)**   | **8 pass · 4 inconclusive · 6 fail** |
| Δ                   | **+27 pp**          |                                      |

The 4 inconclusive scenarios have zero failed assertions; they contain `not_in_baseline` assertions that require a baseline run to resolve. 4 timeouts in the with-skill sweep (complex skill prompts × multi-step scenarios) account for most remaining failures.

The 4 new adversarial scenarios (urgency pressure, skip-test pressure, docs blind-trust, baseless security assertion) score 92% with-skill vs ~46% baseline — the largest skill-vs-baseline gap in the suite.

v0.2.0 (two-sweep range): with-skill **91.1 – 94.4%**, Δ **+27 to +29 pp**. Run-to-run variance is real for stochastic LLM output; numbers should be read as a range, not a point estimate. Per-version detail lives in [`CHANGELOG.md`](CHANGELOG.md).

Cross-runner stability was confirmed during the v0.1.0 measurement: the same `sdk-version-grounding` scenario hit identical 6P/0F with-skill scores on Claude Code 2.1.141 and Codex CLI 0.128.0.

The eval harness is documented at [`evals/README.md`](evals/README.md).

## Skills

| Skill | Use when | Main safeguard |
| --- | --- | --- |
| [`skills/quaere-semantic`](skills/quaere-semantic/SKILL.md) | You need to understand unfamiliar code, module intent, invariants, or why code is shaped a certain way before changing it. | Forces `What / Why / Invariants / Failure modes / Connections` per meaningful unit and marks unknown intent instead of inventing it. |
| [`skills/quaere-grounding`](skills/quaere-grounding/SKILL.md) | The task depends on external, version-sensitive facts: SDKs, APIs, libraries, CLIs, cloud services, security advisories, changelogs, release notes, or docs. | Anchors local versions, ranks source quality, checks version fit and conflicts, and turns confirmed external facts into implementation constraints. |
| [`skills/quaere-evidence`](skills/quaere-evidence/SKILL.md) | You are handling unclear bugs, risky PR review, CI failures, flaky tests, security-sensitive changes, database/concurrency changes, external APIs, or claims that need evidence before patching. | Requires findings, hypotheses/claims, defense, disconfirming probes, decisions, verification, and handoff before accepting a fix. |
| [`skills/quaere-execution`](skills/quaere-execution/SKILL.md) | You are authorized to implement a multi-step coding change, apply a plan, finish review feedback, or turn a specification into working code. | Enforces read → plan → execute → review → fix → verify → commit, with commits only when explicitly authorized. |
| [`skills/quaere-audit`](skills/quaere-audit/SKILL.md) | You are doing deep security auditing, bug bounty preparation, protocol conformance checking, exploitability analysis, or specification-grounded vulnerability discovery. | Derives explicit security properties, maps attack surfaces and code, attempts proofs, gates false positives, and reports confirmed/potential/rejected findings with evidence or PoCs. |

## Picking a skill

### Pipeline for complex work

For multi-step work, the skills chain in this order:

```text
quaere-semantic → quaere-grounding → quaere-evidence → quaere-execution
```

- Use `quaere-semantic` first when misunderstanding existing code would make the implementation risky.
- Use `quaere-grounding` when implementation depends on external facts that may have changed.
- Use `quaere-evidence` when a claim, bug cause, review comment, or proposed fix needs proof.
- Use `quaere-execution` when it is time to implement the confirmed plan and verify the final diff.
- Use `quaere-audit` when the task is not just fixing one claim, but discovering or validating vulnerabilities from properties, attack surfaces, and exploitability gates. It coordinates the other four as needed.

A small implementation can use only `quaere-execution` in lightweight mode; a pure code-reading task can stop after `quaere-semantic`; SDK, cloud API, or dependency work can start with `quaere-grounding`.

### Standalone: match the main risk

Use the first matching row that describes the main risk in the task:

| Main risk | Start with | Then use |
| --- | --- | --- |
| The existing code's intent or invariants are unclear. | `quaere-semantic` | `quaere-execution` only after the important invariants are known. |
| The answer depends on current SDK, API, CLI, cloud, advisory, or docs behavior. | `quaere-grounding` | `quaere-execution` with only confirmed constraints, or `quaere-evidence` if facts conflict. |
| A bug cause, CI failure, flaky test, or review claim might be wrong. | `quaere-evidence` | `quaere-execution` after a claim or hypothesis is confirmed. |
| The plan is already approved and implementation is the main work. | `quaere-execution` | `quaere-evidence` if the work turns risky or the cause becomes unclear. |
| The task is to discover or validate vulnerabilities from specs and attack surfaces. | `quaere-audit` | It coordinates `quaere-semantic`, `quaere-grounding`, `quaere-evidence`, and `quaere-execution` as needed. |

### Tie-breaker

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

Downloads the `quaere` binary, verifies its checksum, places it in `$HOME/.local/bin/quaere`, runs `quaere install all` to deploy skills to both Claude Code and Codex, and prints the available slash commands.

Environment overrides: `QUAERE_VERSION` to pin a tag, `QUAERE_REPO` to install from a fork, `QUAERE_INSTALL_DIR` to relocate the binary, `QUAERE_SKILLS=0` to skip skill deployment.

### cargo install (Rust toolchain users)

```bash
cargo install quaere-cli
quaere install all
```

`cargo install` builds the CLI from source; the second command extracts the bundled skills.

### Homebrew

```bash
brew install haru0416-dev/quaere/quaere
quaere install all
```

The formula lives in the dedicated tap [`haru0416-dev/homebrew-quaere`](https://github.com/haru0416-dev/homebrew-quaere). It pulls the same release tarballs as the curl installer and verifies them against the recorded `SHA256SUMS`. `quaere install all` then deploys skills to both Claude Code and Codex.

### Manual (source checkout)

```bash
git clone https://github.com/haru0416-dev/quaere.git
cd quaere
mkdir -p ~/.claude/skills
cp -R skills/quaere-* ~/.claude/skills/
```

Each skill is a directory containing a `SKILL.md`. The `name` frontmatter matches the directory name.

## Verifying the install

```bash
quaere list      # show installed skills and the recorded version
quaere doctor    # verify frontmatter, names, line budget, orphans
quaere update    # check for a newer release on GitHub
quaere version   # print the CLI version
```

See [`CHANGELOG.md`](CHANGELOG.md) for the per-version change history; the `Unreleased` section is the next-up shipping list.

### CLI behavior contracts

The CLI follows these contracts (the Python validator `scripts/validate_skills.py` and the Rust `quaere doctor` are pinned to agree by `tests/test_validator_parity.py`, exercised in the CI `parity` job):

- **`quaere install` is additive.** Running `quaere install --skill quaere-semantic` and then `quaere install --skill quaere-audit` against the same `--target` accumulates both skills into the manifest. The manifest stays consistent with the union of (previously installed skills that still exist on disk) + (skills installed this run) + (skills already present and skipped). The manifest entries are sorted for deterministic diffs.
- **`quaere install --force` is atomic per skill.** The new content is staged at `<target>/.<name>.staging`, the previous dest is renamed to `<target>/.<name>.backup`, staging is renamed into place, and only then is the backup removed. A mid-extract I/O failure leaves dest at the previous complete content; crash residue (`.staging` / `.backup`) is silently skipped by `quaere doctor` and reclaimed on the next install.
- **Unknown `--skill` names are rejected early.** A typo like `--skill quaere-semantik` aborts with the list of available skills *before* anything is written. There is no partial-install fallback.
- **`quaere doctor` orphan policy.** A directory in the install target that is not recorded in the manifest is surfaced as an orphan. Orphans whose name starts with `quaere-` are treated as errors (a misbehaving Quaere install). Orphans with any other name are informational only — the install target may be shared with other skill management tools.
- **`quaere update` uses semantic version comparison** for the standard `X.Y.Z` form, falling back to string comparison when either side is not parseable as semver. The command never modifies the binary; it only prints upgrade instructions.
- **Default `--repo` is `haru0416-dev/quaere`.** If you are tracking a fork, override it: `quaere update --repo your-fork/quaere`. The same applies to `scripts/install.sh` via the `QUAERE_REPO` environment variable.

## Examples

See [`examples/`](examples/) for realistic prompts and expected behavior patterns.

Quick examples:

- "Read this module and explain the intent before we change it" → `quaere-semantic`
- "Check the installed SDK version and current docs before suggesting code changes" → `quaere-grounding`
- "This CI failure looks flaky; figure out whether the review comment is real before patching" → `quaere-evidence`
- "Apply this plan, run tests, review the diff, and commit if it passes" → `quaere-execution`
- "Audit this protocol implementation against the spec and produce confirmed or potential vulnerabilities with evidence" → `quaere-audit`

## Safety

- Commits happen only when the user explicitly authorizes them.
- `.agent-state/` is local investigation state by default and should not be committed unless the user asks for it as an artifact.
- Risky work should prefer evidence and disconfirming checks over patches that just look quick to apply.

## Evaluation

The in-tree harness lives at `evals/`. It is fast, mostly deterministic, and a good fit for per-PR checks. The headline numbers in [Measured effect](#measured-effect) come from running it through Codex CLI; the same scenarios also run on Claude Code with comparable results.

Run a single scenario:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

See [`evals/README.md`](evals/README.md) for the full assertion-type table, the three `llm_judge` backends (Anthropic SDK / openai-compat / Codex CLI), the locale-alternate mechanism, and the Terminal-Bench adapter.

## Roadmap

The in-tree eval does not substitute for third-party validation. Four external benchmarks are tracked for future integration, in this priority order:

1. **[Terminal-Bench v2](https://www.tbench.ai/)** — 80-task `terminal-bench-core` v0.1.1 (the current public leaderboard subset, out of 241 in the broader pool). The closest fit for `quaere-execution` and `quaere-grounding`. Highest expected Δ. **v0.3.0 shipped the adapter** at [`evals/terminal_bench/`](evals/terminal_bench/) with two Codex-CLI-wrapping agents (`quaere-tb-codex-baseline` / `quaere-tb-codex-with-skill`) and a manual-trigger CI workflow. Smoke / full / leaderboard phases per the adapter README.
2. **[SWE-bench Verified](https://www.swebench.com/)** — 500 human-verified GitHub-issue patches. The standard credibility test for coding agents; non-optional eventually. Heavy infra cost (≥ 120 GB storage, 16 GB RAM, 8 CPU) and substantial API budget. Targeted for v1.0.
3. **[SkillsBench](https://www.skillsbench.ai/)** — 84 domain-skill tasks (3D, robotics, security PCAP, energy, etc.). Submission unit is "agent that uses skills". Lower expected Δ because domain skills dominate; Quaere's process-correction angle is less visible. Tracked, not committed.
4. **SWE-Bench Pro** — harder successor to Verified. Considered only after Verified.

Quaere's claim is that process-correction skills raise any agent's deliberation quality. Terminal-Bench tests this claim head-on; SWE-bench Verified tests whether the effect carries over to long-form patch generation. Until those numbers exist, the only published evidence is the in-tree eval result above.

## Contributing

Run the local validator before publishing changes:

```bash
python scripts/validate_skills.py
```

The validator checks frontmatter, directory / name consistency, README coverage, line-count budget, and accidental `.agent-state/` inclusion. GitHub Actions runs the same validation on push and pull request, alongside the Rust-side `quaere doctor` parity check.

For Rust changes under `cli/`, run `cargo fmt --manifest-path cli/Cargo.toml`, `cargo build`, and `cargo test` before committing. The CI `fmt` gate is strict.

## License

MIT. See [`LICENSE`](LICENSE).
