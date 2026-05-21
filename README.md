# Quaere

> Stop coding agents from confidently doing the wrong thing.

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Coding agents rarely fail by saying "I do not know." They fail by sounding finished too early: they skim code, accept plausible claims, patch a wide diff, and report success before the cause is proven.

Quaere is five skills for Claude Code, Codex, and other skill-aware coding agents. Each skill adds a gate at one of those failure points: read the code semantically, ground external facts, prove claims, execute changes in small verified steps, and audit security properties before publishing findings.

```text
Without Quaere: plausible claim -> broad patch -> partial test -> confident summary
With Quaere:    claim -> evidence -> disconfirming probe -> scoped patch -> verified diff
```

In the current in-tree eval sweep, the same scenarios scored **53%** assertion pass rate without the skills and **91%** with them. The eval is not a substitute for external benchmarks; it is a concrete regression harness for the failure modes Quaere is designed to catch.

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

[Why Quaere](#why-quaere) · [Measured effect](#measured-effect) · [Skills](#skills) · [Picking a skill](#picking-a-skill) · [Installation](#installation) · [Docs](#docs) · [quaere.dev](https://quaere.dev/) · [日本語](README.ja.md)

## Why Quaere

Coding agents drift at four predictable points:

- they read code shallowly,
- they accept plausible claims without proof,
- they edit in unreviewed blobs,
- they commit without authorization.

Quaere slows the agent down at those points. It does not try to make agents more verbose or more cautious everywhere; it forces one move where drift is expensive: **state a claim, defend it with evidence, only then act.**

The name comes from Latin *quaere* — "ask", "seek", "interrogate". Every skill in this collection enforces the same gate.

### Measured effect

The current headline comes from the v0.3.1 in-tree eval sweep. v0.3.0 / v0.3.1 changed the CLI and install pipeline, not the skill bodies, so the result describes the shipped skills:

| mode                | assertion pass rate | scenario-level     |
| ------------------- | ------------------: | -----------------: |
| Baseline (no skill) | 53% (56 / 106)      | 0 / 18 pass        |
| **With skill**      | **91% (96 / 106)**  | **10 / 18 pass**   |
| Δ                   | **+37.7 pp**        | **+10 scenarios**  |

The eval is a regression harness for Quaere's own failure modes, not a third-party benchmark. A separate Terminal-Bench sweep (80 tasks, `terminal-bench-core==0.1.1`) went the other way (baseline 56.25% → with-skill 38.75%); root-cause analysis is in [`docs/evaluation.md`](docs/evaluation.md). Variance notes and roadmap benchmarks live there too.

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

Downloads the `quaere` binary, verifies that `SHA256SUMS` was signed by the release workflow itself (cosign keyless OIDC, identity-bound), verifies the archive checksum against the signed `SHA256SUMS`, places the binary in `$HOME/.local/bin/quaere`, runs `quaere install all` to deploy skills to both Claude Code and Codex, and prints the available slash commands.

**Prerequisite: `cosign`** — install via `brew install cosign`, `apt install cosign` (Debian 13+ / Ubuntu 24.04+), or follow <https://docs.sigstore.dev/cosign/system_config/installation/>. Releases starting with v0.3.2 require it; for older tags, use `cargo install quaere-cli --version <X.Y.Z>` instead.

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

The CLI behavior contracts are documented in [`docs/cli-contracts.md`](docs/cli-contracts.md).

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

The in-tree harness lives at `evals/`. It is fast, mostly deterministic, and a good fit for per-PR checks. The headline numbers in [Measured effect](#measured-effect) come from running it through Codex CLI.

Run a single scenario:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

See [`docs/evaluation.md`](docs/evaluation.md) for measurement notes and [`evals/README.md`](evals/README.md) for the full assertion-type table, judge backends, locale alternates, and Terminal-Bench adapter.

## Docs

- [`docs/evaluation.md`](docs/evaluation.md) — measured effect, variance notes, current benchmark limits.
- [`docs/cli-contracts.md`](docs/cli-contracts.md) — install, force, doctor, and update behavior contracts.
- [`docs/roadmap.md`](docs/roadmap.md) — external benchmark roadmap.

## Contributing

Run the local validator before publishing changes:

```bash
python scripts/validate_skills.py
```

The validator checks frontmatter, directory / name consistency, README coverage, line-count budget, and accidental `.agent-state/` inclusion. GitHub Actions runs the same validation on push and pull request, alongside the Rust-side `quaere doctor` parity check.

For Rust changes under `cli/`, run `cargo fmt --manifest-path cli/Cargo.toml`, `cargo build`, and `cargo test` before committing. The CI `fmt` gate is strict.

## License

MIT. See [`LICENSE`](LICENSE).
