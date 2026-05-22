# Changelog

All notable changes to Quaere are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.2] — 2026-05-22

Security release. Addresses the four findings from the v0.3.1 audit (F-001 — F-004) and adds recurrence prevention for an agent-write incident discovered during the audit cycle.

### Security

- **Release `SHA256SUMS` is now signed with cosign keyless OIDC.** `install.sh` requires `cosign` and verifies the signature against the release workflow's certificate identity (refs/tags/vX.Y.Z) before computing the archive checksum. A `github.com` write compromise can no longer impersonate a signed release without also running the workflow. (F-004, CWE-345.) v0.3.2 is the first signed release; older tags must be installed via `cargo install quaere-cli --version <X.Y.Z>`.
- **Terminal-Bench adapter gates credential forwarding on a dataset allowlist.** Host `~/.codex/auth.json`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY` are forwarded into per-task containers only when `tb run --dataset` names `terminal-bench-core` (currently the sole curated entry) or the operator sets `QUAERE_TB_ALLOW_CRED_FWD=1`. Anything else fails closed and emits a single stderr line so the operator can see why the run aborted. (F-001, CWE-200.)
- **`quaere eval` no longer walks up from CWD.** `--repo` or `$QUAERE_REPO` is now required; running the binary from inside an attacker-controlled directory can no longer execute a planted `evals/run_skill_evals.py`. (F-002, CWE-426/CWE-427.)

### Fixed

- Homebrew tap bump regex pairs `url` lines with their `sha256` lines by target instead of substituting positionally; the four release SHAs no longer risk being bound to the wrong artifact URL if the formula is ever reordered. (F-003, CWE-665.)
- cosign install link in `install.sh`, `README.md`, and `README.ja.md` corrected (`/cosign/system_config/installation/`; the prior path 404'd).
- `evals/terminal_bench/install_scripts/install-with-skill.sh` now bootstraps cosign before invoking the curl|sh installer so the new signature verification works inside the Debian Bookworm task container (apt has no cosign). Pinned to v3.0.6 with SHA256 verification of the downloaded binary on both amd64 and arm64.

### Changed

- Roadmap moved from inline README to `docs/roadmap.md`; CLI behavior contracts moved to `docs/cli-contracts.md`. README gains a short `## Docs` section linking the three reference documents.

### Internal

- `evals/run_skill_evals.py` sets `GIT_CEILING_DIRECTORIES` to the scenario workspace's parent before spawning the agent so a `git commit` inside the workspace cannot walk up and land changes in the parent Quaere repo. (One incident during the v0.3.1 in-tree sweep had to be removed via `git filter-repo` before this push.)
- `eval-manual.yml` artifact upload now drops `eval-results/**/workspace/**` and `**/.git/**`. `eval-terminal-bench.yml` drops `.cast` recordings and `sessions/**` so a task that printed `env` or `cat $HOME/.codex/auth.json` cannot embed credentials in a public artifact.

### Measured

Terminal-Bench (`terminal-bench-core==0.1.1`, 80 tasks, `--global-agent-timeout-sec 1800`):

| mode       | resolved   | accuracy |
| ---------- | ---------: | -------: |
| Baseline   | 41 / 80    | 51.25%   |
| With skill | 42 / 80    | **52.50%** |
| Δ          | —          | **+1.25 pp** |

Narrow positive, well inside run-to-run variance. The honest reading is "Quaere does not regress Terminal-Bench performance"; do not market this as a measurable improvement. The v0.3.1 Δ of −17.5 pp on the same dataset is superseded — that number was dominated by install-pipeline / `agent_timeout` failures (76 timeouts in the worst rerun), not by skill quality. With the v0.3.2 install pipeline (cosign-verified, container bootstrap) and the raised agent timeout, `agent_timeout` count drops from 76 to 7. See [`docs/evaluation.md`](docs/evaluation.md) for the per-task breakdown.

## [0.3.1] — 2026-05-21

Patch release: rebuild the Linux release binaries against musl libc so they no longer require a specific GLIBC version. v0.3.0's `x86_64-unknown-linux-gnu` artifact was built against GLIBC 2.39 (Ubuntu 24.04 builder) and refused to run on Debian Bookworm (2.36), Ubuntu 22.04 (2.35), and older. The musl static binaries are GLIBC-independent and run unchanged on Alpine through RHEL 7 class systems.

### Changed

- Linux release artifacts are now `x86_64-unknown-linux-musl` and `aarch64-unknown-linux-musl`. The host-facing tarball name pattern changes accordingly (`quaere-vX.Y.Z-<target>.tar.gz`). The curl one-liner picks the right artifact via `uname -m` and continues to work transparently.
- `release.yml` switches the linux x86_64 builder to native ubuntu-latest with `musl-tools` and the linux aarch64 builder to `cross` (via `taiki-e/install-action`) so that ring's C bits cross-compile with a musl-aware toolchain.

### Fixed

- `evals/terminal_bench/README.md`'s `tb run` smoke examples used flags that no longer exist in the current terminal-bench CLI (`--task`, `--output-dir`, `TB_AGENT_REGISTRY`). Replaced with the canonical form (`--agent-import-path`, `--task-id`, `--output-path`, `--dataset 'terminal-bench-core==0.1.1'`) that the v0.3.0-era smoke run actually used.

### Measured

In-tree sweep (18 scenarios / 106 assertions, OAuth Codex single-run):

| mode       | assertion pass rate | scenarios |
| ---------- | ------------------: | --------: |
| Baseline   | 53% (56 / 106)      | 0 / 18    |
| With skill | **91% (96 / 106)**  | **10 / 18** |
| Δ          | **+37.7 pp**        | +10       |

This is the first sweep where the v0.3 line was measured directly; v0.2.1 reported `+27 pp` on 97 assertions.

Terminal-Bench (`terminal-bench-core==0.1.1`, 80 tasks, both modes via `evals/terminal_bench/`):

| mode       | resolved   | accuracy |
| ---------- | ---------: | -------: |
| Baseline   | 45 / 80    | 56.25%   |
| With skill | 31 / 80    | 38.75%   |
| Δ          | —          | **−17.5 pp** |

Of 20 regressions, 17 hit `agent_timeout`; the `agent_timeout` count jumped from 9 (baseline) to 33 (with-skill). Quaere's deliberation pass widens wall time on time-boxed tasks past the grader's budget. The in-tree number is the load-bearing measurement; the Terminal-Bench number is reported for honesty, not as a quality verdict. See [`docs/evaluation.md`](docs/evaluation.md).

## [0.3.0] — 2026-05-20

Minor release: introduces an agent-aware install pipeline (`quaere install claude / codex / all`) so the same CLI deploys to both Claude Code (`~/.claude/skills/`) and Codex CLI (`~/.agents/skills/`). The curl one-liner now ends with an explicit `quaere install all` step and a `Commands:` block, and `quaere install --force` swaps skills atomically so a mid-extract failure no longer leaves dest half-written.

### Added

#### Agent-aware install pipeline

- `quaere install` accepts an `agent` positional (`claude` / `codex` / `all`). `claude` targets `~/.claude/skills/`, `codex` targets `~/.agents/skills/`, and `all` writes both, deduplicating by canonical real path so symlinked targets do not produce double-writes. `--target` is preserved as a hidden escape hatch for advanced relocation.
- The curl installer (`scripts/install.sh`) runs `quaere install all` as an explicit post-download step instead of leaving deployment implicit. The `QUAERE_SKILLS=0` env var skips this step for binary-only installs.
- Install output ends with a `Commands:` block listing every deployed skill, so users see the slash commands immediately after `curl ... | sh`.

### Changed

- `quaere install --force` now swaps a skill atomically. The new content is staged at `<target>/.<name>.staging`, the previous dest is renamed to `<target>/.<name>.backup`, staging is renamed into place, and only then is the backup removed. A mid-extract I/O failure leaves dest at the previous complete content; previously a `remove_dir_all -> extract` sequence could half-write the dest while the manifest still claimed it as installed. Crash residue (`.staging`, `.backup`) is silently skipped by `quaere doctor`'s orphan policy (dot-prefixed) and reclaimed on the next install.
- `Agent::targets` and `paths::resolve_target` share a single source for the default install paths via `paths::claude_default` / `paths::codex_default`, eliminating the previous duplicate hardcodes.

### Fixed

- `quaere doctor` flags frontmatter values that contain `: ` when not quoted, matching `scripts/validate_skills.py`. `tests/test_validator_parity.py` pins the cross-validator agreement so future drift fails CI.
- `validate_skills.py` `MAX_SKILL_LINES` aligned with the Rust doctor at 500 (was 600).
- `evals/run_skill_evals.py` builds the runner prompt with `printf` instead of heredoc, preventing shell-injection when scenario prompts contain `EOF`-like delimiters.
- `scripts/install.sh` passes `--strip-components=1` to `tar` so the extracted binary lands at the expected path on all release tarball layouts.
- `release.yml` `workflow_dispatch` checks out the requested tag ref instead of HEAD, so manual re-runs build the tag the user asked for, not the current `main`.

### Internal

- `.gitignore` excludes `evals/results/` so per-run eval output does not accidentally land in commits.

## [0.2.1] — 2026-05-20

Infrastructure release: lands the eval-harness graders and Terminal-Bench adapter that v0.3 will use to publish external-benchmark numbers, plus a Skill content pass addressing post-v0.2.0 review feedback. Treated as a PATCH bump because the Skill changes are additive structural improvements — no Iron Laws changed, no existing gates weakened.

### Added

#### Eval harness graders (ADR-0008)

- `behavior` assertion type — per-run resource thresholds against runtime metadata (`max_tool_calls` / `min_tool_calls` / `max_duration_seconds` / `max_tokens_output` / `max_tokens_input`). Records `status: "manual"` when the runner has not emitted the relevant metric, so adoption can land before runner-side metadata extraction does.
- `llm_judge` assertion type — LLM grades output against a free-form `rubric`. Default-off via `--enable-llm-judge` (per-PR CI cost stays at zero). Three transport backends share the same grading contract:
  - `anthropic` (default): Anthropic SDK + `ANTHROPIC_API_KEY`.
  - `openai-compat`: openai SDK + `--llm-judge-base-url` (or `$QUAERE_LLM_JUDGE_BASE_URL`) for Ollama, vLLM, LM Studio, LocalAI, LiteLLM, etc. Enables fully local eval flows.
  - `codex`: shells out to `codex exec --output-last-message`, reusing Codex CLI's existing auth and endpoint. No extra Python SDK required.
- Responses cached at `evals/.llm_judge_cache/<sha>.json` keyed by `sha256(backend:model + rubric + output)`. The backend prefix in the key prevents cross-backend cache hits.
- Sample assertions added to `evals/scenarios.json` for both new types (two `behavior`, one `llm_judge`) so the schema is exercised end-to-end.

#### Terminal-Bench adapter (ADR-0007)

- `evals/terminal_bench/` package with two `AbstractInstalledAgent` subclasses:
  - `quaere-tb-codex-baseline` — Codex CLI only.
  - `quaere-tb-codex-with-skill` — Codex CLI + `quaere install`.

  Both share env, model selection, and command shape; the only difference is whether `~/.claude/skills/quaere-*` is present inside the per-task container. Lazy-imports the optional `terminal-bench` dependency so the package can be inspected without it installed.
- `evals/terminal_bench/install_scripts/install-baseline.sh` and `install-with-skill.sh` — pin Codex CLI to `0.128.0` by default; the baseline script refuses to run when `~/.claude/skills/quaere-*` exists (treats a leaked treatment as a void run); the with-skill script verifies the five expected skills landed before exiting.
- `.github/workflows/eval-terminal-bench.yml` — manual-trigger (`workflow_dispatch`) workflow that runs `tb run` against the registered agents. Inputs choose `agent` (baseline / with-skill / both), `scope` (smoke / full / task_id), and `codex_version`. 4h timeout cap. Never PR-triggered.

#### Skill content improvements (review feedback)

- **quaere-evidence**: Added `## Output contract` section (冒頭契約) with the 8 required output sections in canonical order, plus a `### Lightweight evidence pass` template — same gate run with fewer words for small-scope investigations.
- **quaere-audit**: Added `Tier companion decisions` and `Tier promotion probe` as required output blocks in every Standard/Deep report. These make explicit which companion skills were invoked and whether bulk/cross-tenant exposure was checked before tier promotion.
- **quaere-semantic**: Added `## Meaningful unit selection` section — 6 criteria for which units to analyze in depth; pure local helpers not meeting any criterion can be collapsed into their caller.
- **quaere-grounding**: Added `## Claim result matrix` table and `locally observed` as a new decision label between "confirmed" and "inconclusive". Clarified that sources derived from the same dependency graph (package.json + lockfile + installed types) are not independent corroborators.
- **quaere-execution**: Added `Verification contract` block with labeled `Before check / After check` forms. Clarified that generated files, lockfiles, snapshots, and build output require justification or must be reverted.
- **All 5 skills**: Standardized the `## Handoff to other skills` section with a common 6-field block template (`From skill` / `Blocking question` / `Confirmed inputs` / `Inconclusive inputs` / `Required next skill` / `Stop condition`).
- **evals**: Added 4 adversarial scenarios to `scenarios.json` — urgency pressure (`pressure-to-skip-evidence-gate`), baseless assertion (`baseless-security-assertion`), skip-test pressure (`skip-tests-pressure`), and docs blind-trust (`blind-trust-external-docs`) — each asserting that the relevant skill's Iron Law gate holds under pressure.
- **validator**: `scripts/validate_skills.py` checks for required structural blocks per skill (Output contract, Lightweight evidence pass, Tier companion decisions, Tier promotion probe, Meaningful unit selection, Claim result matrix, Verification contract). Line budget raised from 500 to 600 to accommodate the additions.

#### Validation + docs

- `scripts/validate_skills.py` accepts the two new assertion types in its allowlist.
- `README.md` / `README.ja.md` gain the new grader rows in the assertion-type table, three subsections covering all `llm_judge` backends, and a `Roadmap` upgrade for Terminal-Bench from "v0.3 target" to "v0.3 in progress" with a pointer to the new adapter.
- `tests/test_run_skill_evals.py` covers the new graders end-to-end (6 behavior tests, 11 llm_judge tests including codex backend dispatch and a backend-specific cache-key regression).
- `tests/test_terminal_bench_adapter.py` covers the package's lazy-import discipline and missing-dependency error path.

### Measured effect

Single-run via Codex CLI against 18 scenarios / 97 deterministic assertions (14 original + 4 new adversarial):

| mode                | assertion pass rate | scenario-level |
| ------------------- | ------------------: | -------------: |
| Baseline (no skill) | 60% (58 / 97)       | 0 / 18 pass    |
| **With skill**      | **87% (84 / 97)**   | **8 pass · 4 inconclusive · 6 fail** |
| Δ                   | **+27 pp**          |                |

4 inconclusive runs have zero failed assertions; they contain `not_in_baseline` assertions that require a paired baseline run to resolve. 4 with-skill timeouts account for most failures (complex multi-step skill prompts). The 4 adversarial scenarios score 92% with-skill vs ~46% baseline.

### Known limitations (deferred to v0.3.x)

- `behavior` assertions in the in-tree eval all resolve to `status: "manual"` because the Codex CLI runner does not yet parse out `tool_calls` / `tokens_*` metadata. The grader is ready; the runner-side metric extraction lands separately.
- Terminal-Bench smoke / full sweep / leaderboard runs have not executed; the adapter is wired but the numbers are pending.

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

[Unreleased]: https://github.com/haru0416-dev/quaere/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/haru0416-dev/quaere/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/haru0416-dev/quaere/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/haru0416-dev/quaere/releases/tag/v0.1.0
