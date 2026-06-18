# Quaere

> Stop coding agents from confidently doing the wrong thing.

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Coding agents rarely fail by saying "I do not know." They fail by sounding finished too early: they skim code, accept plausible claims, patch a wide diff, and report success before the cause is proven.

Quaere is four core [skills](https://docs.claude.com/en/docs/claude-code/skills) plus four opt-in extensions for Claude Code, Codex CLI, and other skill-aware coding agents. A skill is a markdown file the agent loads on demand based on task context — each core skill gates a different drift point: read the code semantically, ground external facts, prove claims, and execute changes in small verified steps. The extensions add security auditing, structured ideation, naming, and 0→1 origination on top.

> Quaere is an independent project, not affiliated with or endorsed by Anthropic. The skills run through Claude Code's and Codex CLI's built-in skill systems.

The name is Latin *quaere* — *to ask, to seek, to inquire*. The point is not more process; it is to wedge one move — *make a claim, defend it with evidence, then act* — in at the spots where agents drift.

```text
Without Quaere: plausible claim -> broad patch -> partial test -> confident summary
With Quaere:    claim -> evidence -> disconfirming probe -> scoped patch -> verified diff
```

In the in-tree eval sweep measured at v0.3.1, the same scenarios scored **53%** assertion pass rate without the skills and **91%** with them. The eval is not a substitute for external benchmarks; it is a concrete regression harness for the failure modes Quaere is designed to catch.

[Measured effect](#measured-effect) · [Skills](#skills) · [Picking a skill](#picking-a-skill) · [Installation](#installation) · [Docs](#docs) · [quaere.dev](https://quaere.dev/) · [日本語](README.ja.md)

## Measured effect

The headline comes from the in-tree eval sweep against the v0.3.1 skill set. Skill bodies have changed since the measurement: v0.5.0 reorganized every skill for the Codex read cap, and unreleased commits since then added the `quaere-naming` and `quaere-prospect` extensions, distilled `quaere-semantic` to its measured active core, and gated the `confident` / `locally novel` certainty labels on an executed probe. The published sweep numbers predate those changes:

| mode                | assertion pass rate | scenario-level     |
| ------------------- | ------------------: | -----------------: |
| Baseline (no skill) | 53% (56 / 106)      | 0 / 18 pass        |
| **With skill**      | **91% (96 / 106)**  | **10 / 18 pass**   |
| Δ                   | **+37.7 pp**        | **+10 scenarios**  |

Measured at v0.3.1 on the 18-scenario / 106-assertion suite; the suite has since grown to 22 scenarios / 125 assertions. See [`docs/evaluation.md`](docs/evaluation.md) for measurement notes.

The eval is a regression harness for Quaere's own failure modes, not a third-party benchmark. A separate Terminal-Bench sweep (`terminal-bench-core==0.1.1`, v0.3.2 install pipeline) reports two cuts:

- **+1.25 pp on the full 80-task set** (41/80 → 42/80, 51.25% → 52.50%). Within typical run-to-run variance — read it as "does not regress".
- **+8.7 pp on the 69 tasks where the install pipeline wasn't broken** (52.2% → 60.9%). The other 11 tasks failed before the skill could load.

The per-category cut, taken on the clean 69-task subset, sits underneath those averages — with small per-category samples (n = 3 to 10), treat the splits as suggestive rather than confirmed effects: data-processing +60 pp, SWE-bench style +25 pp, security +22 pp, build/compile +17 pp, ML/AI −10 pp, the remaining five categories ~0. Variance notes and the per-task breakdown live in [`docs/evaluation.md`](docs/evaluation.md).

### What that looks like on one task

The Terminal-Bench task `csv-to-parquet` — *"Convert `/app/data.csv` into a Parquet file named `/app/data.parquet`"* — recovered (baseline ✗ → with-skill ✓). Same model, same task, two runs.

**Baseline (test_data_matches: failed)**

> The CSV is small and straightforward. I found Node/npm, so I'll use a temporary Node package… *[npm installs `parquetjs-lite`, hand-rolls a CSV parser and type inferrer, writes the file]*
>
> Converted `/app/data.csv` to `/app/data.parquet`. Verified read-back: 5 rows, columns: name, age, city, first row: John, 25, New York…

The agent read its own output back through its own writer, found it consistent with itself, and declared success. The Terminal-Bench test that decoded the file with a canonical Parquet reader did not agree.

**With skill (test_data_matches: passed)**

> I'll convert the CSV with a structured CSV reader and Parquet writer, then verify the output file exists and is readable. *[bootstraps a `python3-venv`, installs `pyarrow`, reads through `pyarrow.csv`, writes through `pyarrow.parquet.write_table`, reads back through `pq.read_table`]*
>
> Converted `/app/data.csv` to `/app/data.parquet`. Verified the Parquet file reads back successfully: 5 rows, 3 columns: name, age, city.

Two behaviors changed. The opening sentence names a verification step before writing anything (*"then verify the output file exists and is readable"*), and the verification uses a canonical library (`pyarrow`) the Terminal-Bench test agrees with — not a homemade encoder verified against itself. This is the skill working as designed: state a checkable claim, run the check the world will judge you by, stop if it fails.

## Skills

Quaere is **four core skills** plus opt-in **extensions**. `quaere install`
installs the core set; extensions are installed on request
(`quaere install --extensions`, or `quaere install --skill <name>`).

### Core (installed by default)

| Skill | Use when | Main safeguard |
| --- | --- | --- |
| [`skills/core/quaere-semantic`](skills/core/quaere-semantic/SKILL.md) | You need to understand unfamiliar code, module intent, invariants, or why code is shaped a certain way before changing it. | Forces `What (mechanical) / What (domain intent) / Why / Invariants / Failure / Connections (← / →)` per meaningful unit and marks unknown intent instead of inventing it. |
| [`skills/core/quaere-grounding`](skills/core/quaere-grounding/SKILL.md) | The task depends on external, version-sensitive facts: SDKs, APIs, libraries, CLIs, cloud services, security advisories, changelogs, release notes, or docs. | Anchors local versions, ranks source quality, checks version fit and conflicts, and turns confirmed external facts into implementation constraints. |
| [`skills/core/quaere-evidence`](skills/core/quaere-evidence/SKILL.md) | You are handling unclear bugs, risky PR review, CI failures, flaky tests, security-sensitive changes, database/concurrency changes, external APIs, or claims that need evidence before patching. | Requires findings, hypotheses/claims, defense, disconfirming probes, decisions, verification, and handoff before accepting a fix. |
| [`skills/core/quaere-execution`](skills/core/quaere-execution/SKILL.md) | You are authorized to implement a multi-step coding change, apply a plan, finish review feedback, or turn a specification into working code. | Enforces read → plan → execute → review → fix → verify → commit, with commits only when explicitly authorized. |

### Extensions (opt-in)

| Skill | Use when | Main safeguard |
| --- | --- | --- |
| [`skills/extensions/quaere-audit`](skills/extensions/quaere-audit/SKILL.md) | You are doing deep security auditing, bug bounty preparation, protocol conformance checking, exploitability analysis, or specification-grounded vulnerability discovery. | Derives explicit security properties, maps attack surfaces and code, attempts proofs, gates false positives, and reports confirmed/potential/rejected findings with evidence or PoCs. Install with `quaere install --skill audit`. |
| [`skills/extensions/quaere-invention`](skills/extensions/quaere-invention/SKILL.md) | You need a non-obvious approach, alternative architecture, research direction, product or monetization idea, or agent-skill design before committing to a plan. | Forces the agent to name the default basin it is escaping, break assumptions through structured mutation passes, classify novelty honestly with fixed labels (no self-rated "truly novel"), and design a kill-probe before promoting an idea. Install with `quaere install --skill invention`. |
| [`skills/extensions/quaere-naming`](skills/extensions/quaere-naming/SKILL.md) | You need to name a product, SaaS, brand, library, open source project, CLI, bot, or app, or escape generic AI-slop names. | Forces a metaphor-driven process — naming brief before any name, conceptual territories instead of thesaurus synonyms, anti-pattern filtering, and a mandatory tool-verified availability gate (never from memory) — so only vetted finalists with origin stories reach the user. Install with `quaere install --skill naming`. |
| [`skills/extensions/quaere-prospect`](skills/extensions/quaere-prospect/SKILL.md) | You are deciding what to build next — a missing feature, tool, product, or improvement in a codebase or domain — before any problem is chosen, and want grounded opportunities instead of a generic wishlist. | Forces every opportunity to name a gap verified to exist in the actual system, a beneficiary and the job they are blocked on, demand evidence (not assumed), and a validation probe — classifying each as verified gap, assumed gap, already covered, or wishlist (no self-rated "game-changing"). Install with `quaere install --skill prospect`. |

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

A small implementation can use only `quaere-execution` in lightweight mode; a pure code-reading task can stop after `quaere-semantic`; SDK, cloud API, or dependency work can start with `quaere-grounding`.

For deep security work — discovering or validating vulnerabilities from properties, attack surfaces, and exploitability gates — install the `quaere-audit` extension (`quaere install --skill audit`). It coordinates the four core skills as needed.

When the risk is settling on the obvious answer too early — choosing an approach, architecture, or research/product direction before widening the option space — install the `quaere-invention` extension (`quaere install --skill invention`). Chained, it sits between grounding and evidence (`semantic → grounding → invention → evidence → execution`); standalone ideation can run `invention → evidence`.

When the risk is upstream of that — not which approach, but *what to build at all* (a missing feature, tool, or product before any problem is chosen) — install the `quaere-prospect` extension (`quaere install --skill prospect`). It runs before invention (`prospect → invention → grounding/evidence → execution`): prospect finds the gap worth solving, invention finds the non-obvious way to solve it. Every opportunity it presents names a verified gap, a beneficiary, demand evidence, and a validation probe — not a generic wishlist.

### Standalone: match the main risk

Use the first matching row that describes the main risk in the task:

| Main risk | Start with | Then use |
| --- | --- | --- |
| The existing code's intent or invariants are unclear. | `quaere-semantic` | `quaere-execution` only after the important invariants are known. |
| The answer depends on current SDK, API, CLI, cloud, advisory, or docs behavior. | `quaere-grounding` | `quaere-execution` with only confirmed constraints, or `quaere-evidence` if facts conflict. |
| A bug cause, CI failure, flaky test, or review claim might be wrong. | `quaere-evidence` | `quaere-execution` after a claim or hypothesis is confirmed. |
| The plan is already approved and implementation is the main work. | `quaere-execution` | `quaere-evidence` if the work turns risky or the cause becomes unclear. |
| The task is to discover or validate vulnerabilities from specs and attack surfaces. | `quaere-audit` (extension) | It coordinates `quaere-semantic`, `quaere-grounding`, `quaere-evidence`, and `quaere-execution` as needed. |
| You are about to commit to the obvious approach and want to widen the option space first. | `quaere-invention` (extension) | Hands surviving candidates with kill-probes to `quaere-grounding`, `quaere-evidence`, or `quaere-execution`. |
| You need to decide what to build next, before any problem is chosen, and want grounded gaps instead of a wishlist. | `quaere-prospect` (extension) | Hands verified gaps with validation probes to `quaere-invention` (for the approach), `quaere-grounding`, `quaere-evidence`, or `quaere-execution`. |

### Tie-breaker

If two skills seem plausible, choose the one that answers the blocking question first:

- "What does this code mean?" → `quaere-semantic`
- "Is this external fact true for this version?" → `quaere-grounding`
- "Is this claim actually proven?" → `quaere-evidence`
- "Are we ready to change files?" → `quaere-execution`
- "What security properties can fail?" → `quaere-audit`
- "Are we trapped in the obvious solution space?" → `quaere-invention`
- "What is even worth building here?" → `quaere-prospect`

## Installation

Quaere ships as the `quaere-cli` npm package. The CLI's only job is to copy skill files into `~/.claude/skills/` and `~/.agents/skills/`, so a zero-install run is fine — no global package needed.

```bash
npx quaere-cli install
```

This auto-detects which agents are present and deploys to all of them. Pass an explicit target to scope the deployment:

```bash
npx quaere-cli install claude     # only Claude Code
npx quaere-cli install codex      # only Codex CLI
npx quaere-cli install all        # both
```

### Bun

```bash
bunx quaere-cli install
```

### Global install

If you would rather have the CLI permanently in PATH:

```bash
npm install -g quaere-cli
quaere install                    # the package also exposes the `quaere` alias
```

### Verifying the install

```bash
npx quaere-cli list               # show installed skills and the recorded version
npx quaere-cli doctor             # validate frontmatter, names, and line budgets
npx quaere-cli update             # check GitHub Releases for a newer version
```

Substitute `quaere` for `npx quaere-cli` once you have installed globally.

Releases ship with npm provenance attestations (Sigstore OIDC) binding the tarball back to the release workflow at the exact tag. `npm audit signatures` verifies the chain end to end.

See [`CHANGELOG.md`](CHANGELOG.md) for the per-version change history; the `Unreleased` section is the next-up shipping list. The CLI behavior contracts are documented in [`docs/cli-contracts.md`](docs/cli-contracts.md).

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
- For security-sensitive paths, database schema, or concurrency changes, use `quaere-evidence` before patching — not after.

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

Run the skills validator before publishing changes:

```bash
python scripts/validate_skills.py
```

It checks frontmatter, directory/name consistency, README and README.ja coverage, reachability-anchor positions within the Codex read cap, the line-count budget, that reference links resolve, and accidental `.agent-state/` inclusion. GitHub Actions runs the same validation on push and pull request.

For changes under `cli/` (the npm package), run the local check pipeline before committing:

```bash
cd cli
pnpm install --frozen-lockfile
pnpm check                        # oxlint + tsc --noEmit + vitest
```

The same pipeline runs in CI before publish, so a failing check there will hold the release.

## License

MIT. See [`LICENSE`](LICENSE).
