# Quaere

> Process-correction skills that make coding agents ask before they act.

Quaere is a set of skills for Claude Code, Codex, and other coding agents that slows them down at the points where they most often drift: shallow code reading, plausible but unverified claims, unreviewed implementation blobs, and unauthorized commits.

The name comes from Latin *quaere* — "ask", "seek", "interrogate". Every skill in this collection forces the same move: state a claim, defend it with evidence, and only then act.

## Skills

| Skill | Use when | Main safeguard |
| --- | --- | --- |
| [`skills/quaere-semantic`](skills/quaere-semantic/SKILL.md) | You need to understand unfamiliar code, module intent, invariants, or why code is shaped a certain way before changing it. | Forces `What / Why / Invariants / Failure modes / Connections` per meaningful unit and marks unknown intent instead of inventing it. |
| [`skills/quaere-grounding`](skills/quaere-grounding/SKILL.md) | The task depends on external, version-sensitive facts: SDKs, APIs, libraries, CLIs, cloud services, security advisories, changelogs, release notes, or docs. | Anchors local versions, ranks source quality, checks version fit and conflicts, and turns confirmed external facts into implementation constraints. |
| [`skills/quaere-evidence`](skills/quaere-evidence/SKILL.md) | You are handling unclear bugs, risky PR review, CI failures, flaky tests, security-sensitive changes, database/concurrency changes, external APIs, or claims that need evidence before patching. | Requires findings, hypotheses/claims, defense, disconfirming probes, decisions, verification, and handoff before accepting a fix. |
| [`skills/quaere-execution`](skills/quaere-execution/SKILL.md) | You are authorized to implement a multi-step coding change, apply a plan, finish review feedback, or turn a specification into working code. | Enforces read → plan → execute → review → fix → verify → commit, with commits only when explicitly authorized. |
| [`skills/quaere-audit`](skills/quaere-audit/SKILL.md) | You are doing deep security auditing, bug bounty preparation, protocol conformance checking, exploitability analysis, or SPECA-style specification-grounded vulnerability discovery. | Derives explicit security properties, maps attack surfaces and code, attempts proofs, gates false positives, and reports confirmed/potential/rejected findings with evidence or PoCs. |

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

### Recommended: curl one-liner (after v0.1.0 release)

```bash
curl -fsSL https://raw.githubusercontent.com/haru0416-dev/quaere/main/scripts/install.sh | sh
```

This downloads the `quaere` CLI binary for your platform, verifies its checksum against the release `SHA256SUMS`, places it in `$HOME/.local/bin/quaere`, and runs `quaere install` to extract the skill set to `~/.claude/skills/`.

Environment overrides: `QUAERE_VERSION` to pin a tag, `QUAERE_REPO` to install from a fork, `QUAERE_INSTALL_DIR` to relocate the binary, `QUAERE_SKILLS=0` to skip the skill extraction step.

### cargo install (Rust toolchain users)

```bash
cargo install quaere-cli
quaere install
```

`cargo install` builds the CLI from source and the second command extracts the bundled skills.

### Homebrew (planned v0.2)

A `Formula/quaere.rb` stub exists in this repo; the tap repository `haru0416-dev/homebrew-quaere` will be set up alongside the v0.2 release, after which:

```bash
brew install haru0416-dev/quaere/quaere
```

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

The validator checks frontmatter, directory/name consistency, README coverage, line-count budget, and accidental `.agent-state/` inclusion. GitHub Actions runs the same validation on push and pull request (see ADR-0003).

## Skill evaluation

`evals/scenarios.json` contains portable scenario prompts for qualitative evaluation. Run them through any local agent CLI by providing a command template:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both
```

The runner writes isolated prompts, stdout/stderr, metadata, and grades under `eval-results/<timestamp>/`. `--mode both` runs a baseline prompt without the skill and a with-skill prompt that injects the relevant `SKILL.md`.

Runner command templates are shell commands. They can print the agent response to stdout or redirect it to `$output_file`. They can use:

- `$prompt_file` — generated prompt file
- `$output_file` — stdout capture path
- `$workspace` — isolated working directory
- `$run_dir` — result directory
- `$scenario_id`, `$skill`, `$mode` — run metadata

Scenarios may include deterministic `assertions` (`contains`, `contains_any`, `not_contains`, `regex`, `exit_code`) for CI-friendly checks, in addition to the manual rubric in `expected`. Real-LLM eval runs are gated behind a manual workflow trigger and are not required to pass on every PR (see ADR-0003).

## Project decisions

Design and process decisions live in [`docs/adr/`](docs/adr/):

- [ADR-0001](docs/adr/0001-rebrand-to-quaere.md) — Rebrand to Quaere
- [ADR-0002](docs/adr/0002-distribution-stack.md) — Distribution stack (Rust CLI, releases, Homebrew, marketplace)
- [ADR-0003](docs/adr/0003-test-strategy.md) — Test strategy (validator unit, golden, scenario assertions, manual LLM eval)
- [ADR-0004](docs/adr/0004-new-repo-and-v0.1.md) — New repo and v0.1 release line

## License

MIT. See [`LICENSE`](LICENSE).
