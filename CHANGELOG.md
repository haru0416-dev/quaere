# Changelog

All notable changes to Quaere are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] — 2026-05-20

Eval-driven quality pass on the v0.1.0 skill set and harness. The 9 with-skill residual failures from the v0.1.0 evaluation are addressed across two work streams without adding new skills.

### Measured effect

Two independent baseline + with-skill sweeps via Codex CLI 0.128.0 against the 14 scenarios with 90 deterministic assertions, `--scenarios-extra evals/scenarios.ja.json` enabled:

| mode                | range (2 runs)     |
| ------------------- | -----------------: |
| Baseline (no skill) | 63.9 – 65.1%       |
| **With skill**      | **91.1 – 94.4%**   |
| Δ                   | **+27 to +29 pp**  |

Compared to v0.1.0 (with-skill 89.8% / Δ +28 pp), v0.2.0 lifts the upper bound of with-skill by ~+4.6 pp and leaves Δ in the same band. Run-to-run variance is real for stochastic LLM output; numbers are a range, not a point estimate.

All four Stream A targeted assertion flips confirmed across the runs (`regex disconfirm/falsify` in `ci-failure-evidence-before-patch`; `requires_pair Backing→source-type` in `weak-review-claim-rejection`; `ordered_sections` in `authorized-implementation-loop`; `ordered_sections` in `no-web-local-grounding`). Both post-measurement residuals also closed at the assertion level: markdown-tolerant tier regex now matches `**Tier:** Standard` / `**Tier:**\nStandard`, and `攻撃者` / `主体` / `攻撃元` alternates landed in the spec-grounded-security-audit ordered_sections position 4.

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

- Homebrew tap [`haru0416-dev/homebrew-quaere`](https://github.com/haru0416-dev/homebrew-quaere) is live with a working formula. Install via `brew install haru0416-dev/quaere/quaere`. The in-tree `Formula/quaere.rb` stub is removed; the tap repository is the canonical source going forward.
- First publish to crates.io as [`quaere-cli`](https://crates.io/crates/quaere-cli). Install via `cargo install quaere-cli && quaere install`. The v0.1.0 CHANGELOG previously claimed a crates.io publish in error; v0.2.0 is the first version actually on the registry.
- `cli/Cargo.toml` bumped to `0.2.0` so the release binary self-identifies correctly. The v0.1.0 binary embedded version was correctly `0.1.0`, but a missed bump at tag time would have caused v0.2.0 binaries to report `quaere 0.1.0` — caught and fixed before the release artifacts were finalized.

### Web

- `web/index.html` — added explicit `:focus-visible` outline, wrapped main content in `<main>`, and grouped the bottom resources into `<nav aria-label="Project resources">` to address WCAG 2.4.7 (Focus Visible) and 1.3.1 (Info and Relationships) findings.
- `web/CNAME` — removed. The Pages publishing source is a custom Actions workflow, and the current GitHub docs state that any existing CNAME file in workflow-source Pages is ignored and is not required. The custom domain is held in Pages settings only.
- GitHub Pages `https_enforced` toggled to `true` via REST API. `http://quaere.dev/` now 301-redirects to `https://quaere.dev/`.

### Known limitations (deferred to v0.3)

The v0.2 Codex sweep left these residual failure modes that this release does not address. All belong to the same axis — `skills/quaere-*.md` Output format does not push the model strongly enough toward canonical section headers and tier-companion sub-decisions:

- `ci-failure-evidence-before-patch` `ledger sections appear in canonical order` — `Defense` section header position drift.
- `weak-review-claim-rejection` `claim, defense, decision in order` — content is right, but the model paraphrases rather than emitting labeled sections.
- `triage-tier-confirmation-rule` `Triage tier vocabulary absent in baseline` — with-skill output is missing the canonical phrase `promote to Standard` / `tier promotion`.
- `spec-grounded-security-audit` `Standard tier requires grounding and evidence-gated review` — newly exposed by the v0.2 markdown-tolerant tier regex; when the audit declares Standard tier, the model does not consistently emit the External grounding + Evidence-gated review sub-decision pair.

v0.3 targets template-strengthening across these axes.

### Skipped

- Stream B-5 of the internal v0.2 plan (language-tagged assertion sets) is intentionally not implemented. The alternation approach (English-only `scenarios.json` + opt-in `scenarios.ja.json` via `--scenarios-extra`) already covers the dual-language need without scenario-level duplication; revisit only if a third language or significantly larger token sets are added.

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

[Unreleased]: https://github.com/haru0416-dev/quaere/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/haru0416-dev/quaere/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/haru0416-dev/quaere/releases/tag/v0.1.0
