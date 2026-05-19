# Changelog

All notable changes to Quaere are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-05-19

Initial release. Quaere is a process-correction skill set for coding agents, relaunched from the archived [`agent-skills`](https://github.com/haru0416-dev/agent-skills) project.

### Added

#### Skills

- `skills/quaere-semantic` — semantic review of unfamiliar code with `What / Why / Invariants / Failure / Connections` per unit, mutation-invariance test.
- `skills/quaere-grounding` — external-fact grounding for SDKs/APIs/CLIs with dual-axis (source + claim-credibility) gate and executable probes.
- `skills/quaere-evidence` — evidence-gated review for unclear bugs, CI failures, and risky PR claims; Toulmin claim/data/warrant structure.
- `skills/quaere-execution` — authorized multi-step implementation with Plan/Do/Study/Act units and explicit commit authorization.
- `skills/quaere-audit` — security-property-driven audit with attack-surface mapping, exploitability gates, and tier-based confirmation rules.

#### CLI (`quaere`)

- `quaere install` — extract the embedded skill set to `~/.claude/skills/` (or any `--target`). Additive across runs; merges with existing manifest. Validates `--skill` names early and rejects unknown ones.
- `quaere list` — show installed skills and the recorded CLI version.
- `quaere doctor` — verify SKILL.md frontmatter, names, line budget, and orphans. `quaere-*` orphans are errors; other directories are informational.
- `quaere update` — check GitHub Releases for a newer version using semver comparison; handles 404/403/429/5xx with specific guidance.
- `quaere eval` — wrapper for `evals/run_skill_evals.py` with auto-detected Quaere checkout.
- `quaere version` — print the CLI version.

#### Distribution

- `scripts/install.sh` — POSIX `curl | sh` installer with SHA256 verification, four-target detection, and PATH hint.
- `.github/workflows/release.yml` — tag-triggered cross-platform build (x86_64 + aarch64 for Linux and macOS), skill tarball, SHA256SUMS, and `gh release create`.
- `Formula/quaere.rb` — Homebrew formula stub (tap repo planned for v0.2).
- Published on crates.io as `quaere-cli` for `cargo install`.

#### Evaluation infrastructure

- `evals/scenarios.json` — 14 portable scenarios across the five skills with 88 deterministic assertions (`contains`, `not_contains`, `regex`, `ordered_sections`, `requires_pair`, `min_section_count`, `not_in_baseline`).
- `evals/run_skill_evals.py` — runner that drives any local agent CLI through baseline/with-skill modes and writes isolated prompts, outputs, and grades.
- `eval-fixtures/` — six workspace fixtures pinned for the relevant scenarios.

#### Tests and CI

- `scripts/validate_skills.py` plus 34 Python unit tests covering frontmatter, naming, line budget, and scenarios.json structure.
- `tests/golden/quaere-*.json` plus a 6-test runner enforcing per-skill required H2 sections, forbidden patterns, and line budgets.
- `tests/test_validator_parity.py` plus a CI parity job that runs both validators against the same eight SKILL.md mutations and asserts they agree.
- Matrix CI: Python 3.11/3.12/3.13 + Rust stable/beta + parity job.
- Manual `eval-manual.yml` workflow for real-LLM evaluation, gated behind `workflow_dispatch`.

### Migration from `agent-skills`

Old skill names are renamed wholesale; there are no compatibility shims.

| Old | New |
| --- | --- |
| `semantic-review` | `quaere-semantic` |
| `external-grounding` | `quaere-grounding` |
| `evidence-gated-review` | `quaere-evidence` |
| `execution-loop` | `quaere-execution` |
| `security-audit-loop` | `quaere-audit` |

To migrate from a prior `agent-skills` install:

```bash
rm -rf ~/.claude/skills/{semantic-review,external-grounding,evidence-gated-review,execution-loop,security-audit-loop}
curl -fsSL https://raw.githubusercontent.com/haru0416-dev/quaere/main/scripts/install.sh | sh
```

[Unreleased]: https://github.com/haru0416-dev/quaere/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/haru0416-dev/quaere/releases/tag/v0.1.0
