---
name: quaere-semantic
description: This skill should be used whenever the user asks to "read", "review", "explore", "understand", "explain", "全文レビュー", "意味を分析", or "コード探索" in depth, or whenever implementation requires understanding existing code's intent before changing it. The skill forces per-symbol meaning analysis — splitting mechanical behavior from domain intent, naming invariants and failure modes, mapping backward and forward slice — so the agent does not paraphrase code as understanding. Trigger when surface-level scanning would produce a wrong edit.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, and git access.
license: MIT
---

# Semantic Review

## Iron Law

**No `Why` without one of: a consulted corroborator marked `confident`, calibrated reasoning marked `plausible`, or `UNKNOWN — probe: <next step>`.**

Paraphrasing implementation is not understanding, and a fabricated `Why` becomes ground truth for the next agent that reads the analysis. Three grounding states, and only these, are acceptable:

- `confident` — a NAMED external corroborator (a test, caller, `git blame`, spec, or ADR) was **actually consulted** and supports the claim.
- `plausible` — reasoned from the code's own shape but unverified, and explicitly marked as such.
- `UNKNOWN — probe: <step>` — the next action that would resolve it.

`confident` is earned by a consulted corroborator, never by felt certainty. **For any unit that mutates state or crosses a trust boundary, if no co-located test, caller, blame, or spec was actually read, the highest marker permitted is `plausible`.** When corroboration is impossible (no tests, no comments, no history, no spec), non-obvious constants and ordering get `plausible` or `UNKNOWN` — never an invented intent stated as fact. `plausible` and `UNKNOWN` are honest acknowledgments of weaker grounding, not loopholes.

This gate is the load-bearing rule; everything below exists to make the gated `Why` get produced per unit.

## Operational anti-paraphrase test

Analysis is *understanding* only if it survives a semantic-preserving rewrite of the code (rename a local, swap an equivalent loop form, replace `if/else` with a ternary, reorder a commutative op). If the rewrite would change any of your answers, that answer is paraphrase — rewrite it to the underlying semantics.

## When to use

- Full-file or full-module review where the user wants comprehension, not a checklist.
- Reading an unfamiliar codebase before implementing a feature that touches it.
- Code where intent is non-obvious: clever optimizations, workarounds, hidden invariants.

## When NOT to use

- Single-line edits, typos, formatting, quick symbol lookups.
- Code where naming makes intent self-evident *and* the operational test would not change the answer.
- Bulk mechanical refactors with no semantic risk.

## Meaningful unit selection

Analyze a unit if it:

- is exported or called across module boundaries
- mutates state, cache, storage, network, auth, or filesystem
- crosses a trust, API, or protocol boundary
- encodes a domain branch or invariant
- is touched by the planned change

Collapse pure local helpers into their caller unless they carry a separate invariant or failure mode. A unit passing none of the above may be noted `skipped: local helper, no independent invariant`. Generated/vendored/`DO NOT EDIT` units get `skipped: generated/vendored — refer to <upstream>`; intent for those lives upstream.

## Core procedure

### Step 0 — Module hypothesis (pre-pass)

Before reading any unit, state a 2–3 sentence hypothesis: what problem the module solves, its central abstraction, what caller it expects. The unit fields confirm or refute it. At the end, record the verdict — **confirmed** / **refined** (a sub-claim was imprecise; name which units) / **refuted** (units reveal a different purpose; restate it as the units actually showed, and flag earlier fields filled under the wrong frame for re-reading). Refutation is a signal, not a failure.

### Step 1 — Per-unit fields

For each meaningful unit, produce these fields. The split between *mechanical* and *domain intent* is load-bearing — conflating them is the novice failure mode.

1. **What (mechanical)** — runtime behavior in one sentence: input → transformation → output.
2. **What (domain intent)** — the problem this solves in the application's domain (e.g. "checkout total with sales tax", not "sums an array and multiplies by 1.0825").
3. **Why** — the constraint, historical reason, or invariant justifying the code's shape. Mark certainty per claim: `confident` / `plausible` / `UNKNOWN — probe: <git blame / callers / tests / ADR>`. `confident` requires the named corroborator was actually consulted, not inferred from shape; absent that, use `plausible`. A unit may carry multiple `Why` lines at different certainties.
4. **Invariants** — what must hold for correctness beyond types: caller discipline, ordering, lock/transaction state, freshness windows.
5. **Failure modes** — what happens when invariants fail: silent corruption, panic, wrong result, deadlock, data leak, resource exhaustion.
6. **Connections (←) backward slice** — what affects this unit: inputs, mutable state read, environment, feature flags.
7. **Connections (→) forward slice** — what this unit affects: call sites, mutated state, side effects, cache entries, downstream consumers, tests that pin behavior.

Slice bounds: if a slice exceeds ~10 sites, name distinct categories and outliers, not every site. When a slice crosses a trust/API/library boundary, stop there and name the contract it imposes.

You may collapse the two `What` lines into one only after confirming the operational test does not break. `Why`, `Invariants`, `Failure`, and both slices must always be considered; if vacuous, say so ("Why: trivial accessor, no constraint") rather than omitting. After filling a unit, run the operational test on each answer and rewrite any that would change.

## Output format

Per unit:

```text
<symbol> @ <file>:<line>
  What (mechanical):    <one sentence>
  What (domain intent): <one sentence>
  Why:                  <one or more claims; each with its own marker (confident / plausible / UNKNOWN — probe: ...)>
  Invariants:           <bullets, or "none beyond types">
  Failure:              <bullets, or "n/a">
  Connections (←):      <backward slice>
  Connections (→):      <forward slice>
```

Group units by module / layer / concern. End the review with:

- **Module hypothesis verdict** — confirmed / refined / refuted, with which units forced the change.
- **Open questions** — every `UNKNOWN — probe: …` still needing the user or further probing.
- **Risk hotspots** — units whose invariants are subtle, fragile, undocumented, or rely on caller discipline.
- **Implementation implications** — only if the user asked for next steps; otherwise stop at understanding.

## Worked example

A side-by-side paraphrase-vs-understanding example (applied to `TokenCache.get`) is in [`references/worked-example.md`](references/worked-example.md). Read it when the seven-field contract feels abstract.

## Probes for `Why` (order for earning `confident`)

When the reason for code's shape is unclear, in this order:

1. **Read nearby tests** — they encode intended behavior and edge cases.
2. **Read callers (forward slice probe)** — calling context reveals the contract.
3. **Run `git blame` + read the commit message** — original author rationale.
4. **Ask the user.** Better one question than a fabricated explanation.

If none of these is available, the unit stays `plausible` or `UNKNOWN — probe: <step>`. Do not upgrade to `confident` without a consulted corroborator. Deeper question templates (protocol/state, lifetime, ownership, reachability) are in [`references/anti-patterns.md`](references/anti-patterns.md); a side-by-side paraphrase-vs-understanding example is in [`references/worked-example.md`](references/worked-example.md).

## Common drift modes and anti-patterns

The recurring shapes that look like analysis but are paraphrase — and why each fails — are in [`references/anti-patterns.md`](references/anti-patterns.md). Read it before promoting a `Why` to `confident`.

## Handoff triggers

Semantic review ends at understanding. If the next step needs a different discipline, hand off rather than continuing to read. Emit a short block naming: confirmed inputs (fields safe as facts), inconclusive inputs (every `plausible`/`UNKNOWN`), the next skill, and its stop condition.

- Implementation is authorized → `quaere-execution` (carry units, invariants to preserve, risk hotspots).
- An external library/SDK/API/CLI behavior the analysis depended on may have changed → `quaere-grounding`.
- A specific bug hypothesis or review claim needs evidence before patching → `quaere-evidence`.
- Security properties are in question → hand off to `quaere-audit` if installed; otherwise stop and escalate to the user.

Do not edit during the semantic review itself when the user asked to understand first.

## Handoff to other skills

When switching, emit the standard block so the receiving skill knows what it is given:

```
Handoff
- From skill: quaere-semantic
- Confirmed inputs: <What/Why/Invariants/Failure/Connections fields safe as facts>
- Inconclusive inputs: <every Why marked plausible or UNKNOWN>
- Required next skill: <quaere-grounding | quaere-evidence | quaere-execution | quaere-audit (if installed)>
- Stop condition: <what the next skill must return before implementation or audit>
```

## Stop condition

The skill is complete when:

- A module hypothesis was stated before unit analysis, and its verdict (confirmed / refined / refuted) is at the end.
- Every meaningful unit has all fields filled, the two `What` lines collapsed *only* after the operational test, or is explicitly `skipped: <reason>`.
- Every `Why` carries a certainty marker, and every `confident` on a state-mutating or trust-boundary unit names the corroborator that was actually consulted (test / caller / blame / spec / ADR).
- Open questions and risk hotspots are listed.

Do not append a fix or refactor on top. Hand off to the user or to `quaere-execution`.
