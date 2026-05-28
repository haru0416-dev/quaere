---
name: quaere-semantic
description: This skill should be used whenever the user asks to "read", "review", "explore", "understand", "explain", "全文レビュー", "意味を分析", or "コード探索" in depth, or whenever implementation requires understanding existing code's intent before changing it. The skill forces per-symbol meaning analysis — splitting mechanical behavior from domain intent, naming invariants and failure modes, mapping backward and forward slice — so the agent does not paraphrase code as understanding. Trigger when surface-level scanning would produce a wrong edit.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, and git access.
license: MIT
---

# Semantic Review

## Iron Law

**No `Why` without one of: direct evidence, calibrated reasoning marked `plausible`, or `UNKNOWN — probe: <next step>`.**

This is not a stylistic rule. Paraphrasing implementation is not understanding, and a fabricated `Why` becomes ground truth for the next agent (or the same agent in a later session) that reads the analysis. The three states of grounding — `confident` (evidence supports the claim), `plausible` (reasoned but unverified, and explicitly marked as such), `UNKNOWN — probe: <step>` (the next action that would resolve it) — are the only acceptable forms. Fabricated certainty is the failure mode this rule prevents; `plausible` and `UNKNOWN` are explicit acknowledgments of weaker grounding, not loopholes.

The operational test: a piece of analysis is *understanding* only if it survives a semantic-preserving rewrite of the underlying code (rename a local, swap an equivalent loop form, replace an `if/else` with a ternary). If the rewrite would change your answer, you produced *paraphrase*. *(Operational definition adapted from arXiv 2504.04372 2025; preprint, applied as a working test rather than as authority.)*


## Industry baseline

Empirical software-engineering research (Maalej, Tiarks, Roehm & Koschke 2014, *ACM TOSEM*) shows professional developers practice *partial, pragmatic* comprehension and avoid full comprehension when possible — they rely heavily on running the system, inspecting GUIs, and skipping aggressively. **This skill is the deliberate exception to that norm.** It is invoked when the cost of misunderstanding outweighs the cost of full coverage. Do not optimize for token cost or response length; the user accepted the cost when invoking this skill.

## When to use

- Full-file or full-module review where the user wants comprehension, not a checklist.
- Exploring an unfamiliar codebase before implementing a feature that touches it.
- Reading code where the author's intent is non-obvious — clever optimizations, workarounds, hidden invariants, unusual abstractions.
- Any task where "I don't understand what this does" would block the next step.

## When NOT to use

- Single-line edits, typo fixes, formatting.
- Code where naming alone makes the intent self-evident *and* the operational test (mutation invariance) would not change the answer.
- Quick lookups: locate a symbol, list files.
- Bulk mechanical refactors with no semantic risk.

## Handoff triggers (which skill comes after this one)

Semantic review ends at understanding. If the next step needs a different discipline, invoke the relevant skill rather than continuing to read:

- Implementation is authorized after the review → `quaere-execution`.
- An external library / SDK / API / CLI behavior the analysis depended on may have changed → `quaere-grounding`.
- A specific bug hypothesis or review claim needs evidence before patching → `quaere-evidence`.
- Security properties of the module are now in question → flag it as needing a security audit. If the `quaere-audit` extension is installed, hand off to it; otherwise stop and escalate the security risk to the user rather than guessing.

The full handoff payload format (Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) and per-skill payload details are documented at the end of this file under "Handoff to other skills".

## Depth control

Three tiers. Choose by *scope*: how many units, the cost of misreading them, and how the agent will be evaluated. Wall-clock time is a hint for human reviewers; for an LLM agent, the primary signal is the unit count and the breadth of slicing required, not minutes.

- **Lightweight semantic pass (≤5 units; human equivalent ~5–15 min)** — small file, a few symbols, or pre-implementation orientation. Apply the procedure to only the relevant units; the module hypothesis (see Step 0) can be one sentence. Suitable when scope is one function or one small module and edits are bounded.
- **Standard semantic review (one module, all meaningful units; ~30–90 min)** — full-file or focused module review. Module hypothesis pre-pass first; then the per-unit procedure for every meaningful unit; group results by module, layer, or concern.
- **Deep module review (≥30 units or multi-module, batched; ~2+ hours)** — broad architectural uncertainty. First produce a module map and risk hotspots; then audit highest-risk units in detail. Continue in batches instead of dumping an unbounded review.

If the target is too large for one response, say which units were covered, which were deferred, and what order to continue in. Do not pad output to fill an imagined time budget — output length should match the unit count and slicing depth, not a clock.

## Meaningful unit selection

Analyze a unit if it:

- is exported or called across module boundaries
- mutates state, cache, storage, network, process, auth, or filesystem
- crosses a trust, API, or protocol boundary
- encodes a domain branch or invariant
- is touched by the planned change

Collapse pure local helpers into their caller unless they carry a separate invariant or failure mode. The goal is not exhaustive coverage — it is to avoid missing a meaningful boundary. A unit that passes none of the above conditions can be noted as `skipped: local helper, no independent invariant`.

## Core procedure

### Step 0 — Module hypothesis (pre-pass)

Before reading any unit, state a 2–3 sentence hypothesis about the module's purpose: what problem it solves, what its central abstraction is, what kind of caller it expects. The unit-level fields below confirm or refute this hypothesis. Without a hypothesis, you have nothing to falsify; the analysis becomes bottom-up paraphrase rather than top-down comprehension. *(Brooks 1983, "Towards a theory of the comprehension of computer programs", IJMMS — comprehension is hypothesis-driven.)*

**Verdict and update rule.** Once unit-level analysis is complete, the hypothesis lands in one of three states:

- *Confirmed* — units are consistent with the original framing. Record the verdict and proceed to summary.
- *Refined* — a sub-claim was incomplete or imprecise. Record the refined hypothesis alongside the original, naming which units forced the refinement.
- *Refuted* — the units reveal a different module purpose than the hypothesis claimed. Restate the corrected hypothesis as the units actually showed it ("originally framed as X; refuted by units Y, Z, which show A"), and *re-check any earlier per-unit fields filled while assuming the refuted frame*. Fields filled under the wrong hypothesis often carry distorted `Why` claims and biased slice descriptions; flag them for re-reading even if you cannot re-pass them all in this session.

Refutation is a signal, not a failure. Holding the hypothesis lightly and updating it is the comprehension move; sticking to the original framing despite contrary evidence is paraphrase wearing a different hat.

### Step 1 — Per-unit fields

For each meaningful unit (function, type, branch, module boundary, non-trivial constant), produce these seven fields. The split between *mechanical* and *domain intent* is load-bearing: high-comprehension readers cross-reference the two; conflating them is the failure mode novice readers exhibit. *(Pennington 1987, "Stimulus structures and mental representations in expert comprehension of computer programs", Cognitive Psychology.)*

1. **What (mechanical)** — runtime behavior in one sentence. Code-level: input → transformation → output.
2. **What (domain intent)** — what problem this solves in the application's domain. Different from mechanical: the domain answer is "checkout total with sales tax", not "sums an array and multiplies by 1.0825".
3. **Why** — the constraint, historical reason, or invariant that justifies the code's shape. Mark certainty per claim: `confident` / `plausible` / `UNKNOWN — probe: <git blame / callers / tests / ADR>`. A unit may carry multiple `Why` claims at different certainties; list each as a separate line with its own marker. *(Letovsky 1986 — comprehension proceeds via inquiry episodes with certainty levels.)*
4. **Invariants** — what must hold for this code to be correct. Beyond types: caller discipline, ordering, lock state, transaction state, freshness windows.
5. **Failure modes** — what happens when invariants fail: silent corruption, panic, wrong result, deadlock, data leak, resource exhaustion.
6. **Connections (←) backward slice** — what affects this unit. Inputs, mutable state read, environment, feature flags, side-channel reads. *(Weiser 1984, "Program Slicing" — backward direction.)*
7. **Connections (→) forward slice** — what this unit affects. Call sites, mutated state, observable side effects, cache entries, downstream consumers, tests that pin behavior. *(Bergeretti & Carré 1985 for forward slicing; Robillard & Murphy concern graphs for non-co-located concerns.)*

**Bound rules for slices and units.**

- *Cardinality bound.* If a (←) or (→) slice would enumerate more than ~10 sites, name distinct call categories ("all auth-middleware paths; the GraphQL resolver for `getInvoice` is the outlier") rather than every site. The slice's purpose is comprehension, not exhaustive bibliography; always name the unusual cases that deviate from the dominant pattern.
- *Boundary bound.* When a slice crosses a scope or trust boundary — third-party library, exported public API, RPC, OS interface, plugin host — stop at the boundary and name the contract that crossing imposes ("consumed via the public `TokenCache.get` interface; external callers are unbounded"). Do not chase into territory the analysis cannot reach.
- *Generated / vendored.* If a unit is generated (`*.gen.*`, schema-derived clients, compiler output), vendored (under `vendor/`, `node_modules/`, `third_party/`), or carries a "DO NOT EDIT" header, mark it `skipped: generated/vendored — refer to <upstream source>` and do not attempt the seven-field analysis. Intent for these lives upstream.

When meaning is genuinely obvious from naming and shape, you may collapse `What (mechanical)` and `What (domain intent)` into a single line — but only after confirming the operational test does not break under semantic-preserving rewrite. `Why`, `Invariants`, `Failure`, and both slice fields must always be considered. If they are vacuous, say so explicitly ("Why: trivial accessor, no constraint to record") rather than omitting.

### Step 2 — Apply the operational test

For each unit, run the mental rewrite: would a semantic-preserving change (rename a local, swap loop form, restructure an `if/else`, change variable order in a commutative op) alter any of your seven answers? If yes, the answer that changed is paraphrase, not understanding — rewrite it to the underlying semantics.

## Output format

Per unit:

```text
<symbol> @ <file>:<line>
  What (mechanical):    <one sentence>
  What (domain intent): <one sentence>
  Why:                  <one or more claims; each carries its own certainty marker (confident / plausible / UNKNOWN — probe: ...)>
  Invariants:           <bullets, or "none beyond types">
  Failure:              <bullets, or "n/a">
  Connections (←):      <backward slice: what affects this>
  Connections (→):      <forward slice: what this affects>
```

Group units by module / layer / concern. End the review with:

- **Module hypothesis verdict** — confirmed / refined / refuted, with which units forced the change.
- **Open questions** — every `UNKNOWN — probe: …` that still needs the user or further probing.
- **Risk hotspots** — units where invariants are subtle, fragile, undocumented, or rely on caller discipline.
- **Implementation implications** — only if the user asked for next steps; otherwise stop at understanding.

## Worked example

A side-by-side bad-output (paraphrase) vs good-output (seven-field analysis under the operational test) example, applied to `TokenCache.get`, is at [`references/worked-example.md`](references/worked-example.md). Load it when the contract feels abstract — it shows what the rewrite test actually catches.

## Probes for `Why`

When the reason for code's shape is unclear, in this order:

1. **Read nearby tests** — they often encode intended behavior and edge cases.
2. **Read callers (forward slice probe)** — calling context reveals the contract.
3. **Look for code beacons** — recognizable plan signatures: cache-aside, double-check locking, retry-with-backoff, circuit breaker, builder, visitor. A beacon often reveals intent at lower cost than tests, because beacons compress historical engineering into a recognizable pattern. *(Brooks 1983.)*
4. **Run `git blame` + read the commit message** — original author rationale.
5. **Use intent / protocol / lifetime question templates** *(Sillito, Murphy & De Volder 2008; LaToza & Myers 2010 — empirically the hardest developer questions are about intent and reachability)*:
   - What protocol does this object follow? What states can it be in?
   - What is the lifetime of this state? Who creates it, who destroys it?
   - Who owns this object's mutation? Single writer, multiple writers, none after construction?
   - What invariants does the *caller* assume vs what the *callee* enforces?
   - What is the reachability — who can reach this code and under what conditions?
6. **As a last resort, ask the user.** Better one question than a fabricated explanation.

## Common drift modes and anti-patterns

Drift modes (the rationalization vs the actual failure) and the recurring shapes that look like analysis but are paraphrase — including why each fails — are at [`references/anti-patterns.md`](references/anti-patterns.md). Read it when an analysis "passed the operational test" but still feels thin.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-semantic
- Blocking question: <what cannot be resolved through code reading alone>
- Confirmed inputs: <What/Why/Invariants/Failure/Connections fields that can be carried forward as facts>
- Inconclusive inputs: <Why claims marked "plausible" or "UNKNOWN" — not safe to treat as confirmed>
- Required next skill: <quaere-grounding | quaere-evidence | quaere-execution | (quaere-audit, if the extension is installed)>
- Stop condition: <what the next skill must return before implementation or deeper audit can proceed>
```

Semantic review ends at understanding. When the next step needs a different discipline, name the handoff explicitly rather than continuing to read.

Each handoff carries a payload. The structured `quaere-execution` block below is the canonical example; the other three handoffs follow the same shape — what was confirmed, what is still open, and which artifacts the next skill should consume first.

- Implementation is authorized after the review → invoke `quaere-execution` with the relevant units, invariants to preserve, risk hotspots, and the suggested first implementation unit.
- An external library, SDK, API, or CLI behavior the review depended on may have changed → invoke `quaere-grounding` with the unconfirmed external claim, the local version anchor (if known), and the units whose analysis depends on it.
- A specific bug hypothesis or review claim emerged from the reading and needs evidence → invoke `quaere-evidence` with the Finding, the supporting/disconfirming probes that would resolve it, and the Why claim it would confirm or refute.
- Security properties of the module are now in question → flag it as needing a security audit. If the `quaere-audit` extension is installed, invoke it with the suspected security property, the attack-surface entry point identified during slicing, and the threat-model frame the property assumes; otherwise stop and escalate the security risk to the user.

If the user explicitly asked to understand first and then implement, do not edit during the semantic review itself. End with implementation implications and a handoff block:

```text
Ready for implementation via quaere-execution:
- Relevant units:
- Invariants to preserve:
- Risk hotspots:
- Suggested first implementation unit:
```

Then move into `quaere-execution` only after the semantic review output is complete and implementation remains authorized by the user.

## Stop condition

The skill is complete when:

- A module hypothesis was stated before unit-level analysis began, and its verdict (confirmed / refined / refuted) is at the end of the review.
- Every meaningful unit has all seven fields filled, or `What (mechanical)` and `What (domain intent)` collapsed to one line *only* after the operational test, or the unit is explicitly marked `skipped because: <reason>`.
- Every `Why` carries a certainty marker (`confident` / `plausible` / `UNKNOWN — probe: …`).
- Open questions and risk hotspots are listed at the end.
- The user has enough material to decide *whether* and *how* to proceed with implementation.

Do not append a fix or refactor on top. Hand off to the user or to `quaere-execution`.
