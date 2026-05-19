# Changelog

All notable changes to Quaere are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

Eval-driven quality pass on the v0.1.0 skill set and harness. The 9 with-skill residual failures from the v0.1.0 evaluation are addressed across two work streams without adding new skills. Tracked under `docs/adr/0006-eval-driven-v0.2-skill-template-fixes.md` (Accepted).

### Changed

#### Skill templates (Stream A)

- `skills/quaere-evidence/SKILL.md` — Hypothesis blocks now require six labeled lines (`H-id` / `Based on` / `Prediction` / `Falsifier` / `Disconfirming probe` / `Alternative`); Review Claim blocks grow from 8 to 10 fields with `Falsifier:` and `Disconfirming probe:` appended after `Suggested probe:`. `Backing:` value must name a source type from `{spec | invariant | test | policy | contract | RFC | ADR}`. Worked example updated to the new shape.
- `skills/quaere-grounding/SKILL.md` — `No-network fallback strategy` is now a fixed `### 10.` heading inside `## Workflow`, replacing the loose `## No-network fallback` H2. Output format carries a labeled `No-network fallback strategy: applied | not needed` block with the three numbered steps (cached/dated → stale-data notice → canonical URLs).
- `skills/quaere-execution/SKILL.md` — `Final gate:` is now a mandatory labeled line at the end of the Study section, including the explicit skip form `Final gate: skipped because <reason>; best next command: <cmd>`.

#### Eval harness (Stream B)

- `evals/run_skill_evals.py` — `requires_pair` assertions accept an optional `skip_when` regex; when the antecedent is present but the consequent is missing, a matching `skip_when` treats the unconditional pair as vacuously satisfied. Used by the targeted-verification and diff-review assertions in `authorized-implementation-loop`.
- `evals/scenarios.json` — Tightened `spec-grounded-security-audit`:
  - `audit tier declared` now requires the canonical `Tier: Triage|Standard|Deep` labeled line, not prose mentions.
  - `findings classified` now requires `Confirmed:` / `Potential:` / `Rejected:` / `Inconclusive:` as labeled lines.
  - Added `confirmed finding references a derived security property or spec clause` so confirmed findings must point to a named Property, spec clause, RFC, or invariant.
- `evals/run_skill_evals.py` — new `--scenarios-extra PATH` flag merges a sibling JSON file at load time. Regex/string fields get `|`-alternation appended; `ordered_sections.patterns` / `not_in_baseline.patterns` get per-position alternation; `contains_any.texts` get array concatenation. Unknown scenario ids or assertion names error out so stale extras cannot silently drop alternates.

### Added

- `eval-fixtures/no-web-local-grounding/` — new workspace fixture: a pinned `slimsync` 0.7.3 POSIX shell stand-in with `--version` / `--help`, a dated vendored manual mirroring an unreachable canonical URL, plus `src/sync.sh` and `.syncignore`. Designed to make baseline and with-skill outputs diverge by colliding with `rsync --exclude-from=FILE` model memory.
- `evals/scenarios.ja.json` — Japanese-locale alternates for the eight assertions whose tokens had previously been embedded directly into `scenarios.json`. The main file is now English-only; locale tokens are merged in only when the user passes `--scenarios-extra evals/scenarios.ja.json`. This keeps the public surface single-language while preserving the language-bias-removal goal from ADR-0006 Stream B-1.
- `tests/test_run_skill_evals.py` — new unit tests covering the `skip_when` clause and the `--scenarios-extra` merge semantics (regex alternation, per-position alternation with empty-slot pass-through, array concatenation, type mismatch and length mismatch errors).

### Distribution

- Homebrew tap [`haru0416-dev/homebrew-quaere`](https://github.com/haru0416-dev/homebrew-quaere) is now live with a working formula for v0.1.0. Install via `brew install haru0416-dev/quaere/quaere`. The in-tree `Formula/quaere.rb` stub is removed; the tap repository is the canonical source going forward.

### Skipped

- ADR-0006 Stream B-5 (language-tagged assertion sets) is intentionally not implemented in this release. Stream B-1's alternation approach already covers the dual-language need without scenario-level duplication; revisit only if a third language or significantly larger token sets are added.

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
