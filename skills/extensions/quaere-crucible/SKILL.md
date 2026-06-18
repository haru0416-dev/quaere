---
name: quaere-crucible
description: This skill should be used whenever the user wants a plan, claim, design, decision, PR, or their own understanding adversarially pressure-tested before committing — grill me, poke holes in this, challenge my thinking, play devil's advocate, red-team my plan, stress-test this, 詰めて, 反論して, この設計の穴を突いて — or when an agent should grill its OWN proposed plan before shipping it. It runs an evidence-gated interrogation that decomposes the target into load-bearing claims, attacks the most decisive one with falsifier-seeking and alternative-hypothesis questions, and refuses to bless it until each load-bearing claim has survived a named challenge backed by new evidence or a defended rebuttal, or been logged as an explicit unresolved gap, never flipping a claim to survived on confident-but-unverified pushback. Intensity is calibrated to stakes. Do not use to cooperatively flesh out a vague under-specified idea (use deep-interview) or to self-investigate an unexplained bug (use quaere-evidence).
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, web, and shell access.
license: MIT
---

# Crucible Probe

## Iron Law

**No target is blessed until every load-bearing claim has either survived a named, falsifier-seeking challenge — backed by NEW evidence or a defended rebuttal, in full or within a stated scope — or been recorded as an explicit unresolved gap. Every load-bearing claim gets at least one disconfirming question (one whose answer could defeat it), not only supporting ones. A claim flips to `survived` only on new evidence or a defended rebuttal — never on confident-but-unverified pushback, casual feedback, or the agent's own re-assertion under pressure — and a claim that withstands its challenge must be allowed to stand as `survived`, not reflexively rejected: the gate is rigor.**

This is not an interrogation ritual. Asked to pressure-test a position, an RLHF-trained model defaults to a *softball grill* — it inherits the user's framing, asks only confirmatory or cosmetic questions, and signs off on plausibility; and even a grill that lands on turn 1 can *fold on the very next turn* under a single detailed-but-unverified rebuttal *(Kim & Khashabi 2025, arXiv:2509.16533)*. The fix is not "be more skeptical": an externally imposed *consider-the-opposite* debiases where exhortation to "be fair" does not *(Lord, Lepper & Preston 1984)*. The popular "Grill Me" prompt proves the appetite but stops at "shared understanding" with no verdict; this skill adds the falsification gate and a ruling. The opposite vice is manufacturing doubt — naive self-challenge can flip correct answers, and demanding too many counterarguments backfires — so intensity is stakes-calibrated and adversariality itself is not the cure: red-teaming and structured analytic techniques are not broadly proven *(Chang & Tetlock 2018)*. The value is the gate, not the hostility. Full method: `references/question-taxonomy.md` and `references/research-basis.md`.

**Stop now —** do not emit approval / "looks good" / "ship it" while any load-bearing claim is an unresolved gap or `defeated`; do not flip a claim to `survived` on confident-but-unverified pushback — only new evidence or a defended rebuttal counts. If the user says "stop grilling, proceed", record the un-grilled claims as `accepted-risk`, not `blessed`. Full conditions: `## Stop condition`.

## When to use

- The user wants a held plan, claim, design, decision, PR, or understanding attacked before they commit ("grill me", "poke holes", "red-team this", "詰めて").
- An agent is about to ship its OWN proposed plan and should grill it first (self-target mode — crank the intensity, agents under-attack themselves).
- A surviving candidate from `quaere-prospect` (an opportunity) or `quaere-invention` (an approach) needs pressure-testing before it is promoted to a build.

## When NOT to use

- A vague, under-specified idea that needs cooperative gap-filling, not attack → `deep-interview`. crucible attacks a *stated* position; it does not complete a fog.
- An unexplained bug where the agent must self-investigate a claim it owns and reach a private decision → `quaere-evidence`.
- Generating alternatives or a novel approach (not evaluating a held one) → `quaere-invention`; deciding what to build → `quaere-prospect`.
- A trivial, low-stakes, or already-verified target. Grilling here manufactures doubt — naive self-challenge can flip a correct answer. Skip or grill only the one load-bearing part.

## Handoff triggers (which skill comes after this one)

Crucible ends at a graded verdict ledger, not at a fix or a built thing. Hand off when the next step changes discipline:

- A challenge needs an *executed* disconfirming probe (a test, repro, query, benchmark) the conversation cannot run → `quaere-evidence`; resume after its Decision label returns.
- A challenge rests on a version-sensitive external fact (SDK / API / advisory / current docs) → `quaere-grounding`.
- A challenge needs the reviewed code's intent or invariants understood first → `quaere-semantic`.
- The target is blessed (or blessed-narrowed) and building is authorized → `quaere-execution` / `plan`, carrying the blessed claims and the unresolved-gap list as success criteria.
- An independent second-*model* counter-argument is wanted → `cross-check` (a different model, not this agent).
- No load-bearing claim survives → report the gap list; do not bless.

The standard handoff payload (Blocking question / Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is at the end of this file under "Handoff to other skills".

## Core procedure

Run in order. Grill load-bearing claims hard; leave trivia alone. Keep output proportional to the claims that actually decide the outcome.

### 1. Scope the target and triage by stakes

- Name the target (plan / claim / design / decision / PR / understanding / the agent's own plan) and the commitment at stake — what would `blessed` actually authorize.
- Decompose into claims and mark each: **load-bearing** (the target fails if it is false), **high-stakes / irreversible**, or **minor**. Only load-bearing and high-stakes claims are grilled hard. Grilling minor claims to look rigorous is the failure mode of the opposite vice.

### 2. Grill the most-decisive claim first (adaptive drill-down)

Take the single most-decisive claim and attack it with ONE sharp question at a time. State the agent's own recommended counter-position first (the anti-stall move — do not loop neutrally). Two question types are **mandatory** per load-bearing claim:

- **Falsifier** — "name the concrete observation that would make you abandon this; if the honest answer is 'nothing', it is a gap, not a blessing."
- **Alternative hypothesis** — "name two other explanations the same facts fit, and the one probe that distinguishes your story from theirs."

Prefer a **disconfirming-probe** question where an executed test exists ("what is the cheapest test whose FAILURE would kill this — have you run it, or only the checks you expected to pass?"). Cap to a few high-quality challenges per claim — demanding an exhaustive list backfires. The full question taxonomy (warrant, steelmanned rebuttal, outside-view/base-rate, premortem, meta) is in `references/question-taxonomy.md`.

### 3. Grade the answer — the flip rule

Grade each answer against the Iron Law's flip rule:

- `survived` — only on **new evidence or a defended rebuttal**. NOT on confident-but-unverified reasoning, casual pushback, or re-assertion. A claim that genuinely withstands its challenge survives — say so and move on; do not re-litigate.
- `narrowed` — true only for a subset of inputs, versions, or paths (record the scope).
- `defeated` — counter-evidence or context sinks it.
- `inconclusive` — cannot be resolved in conversation; needs an executed probe → hand off (Step 4).

### 4. Hand off what conversation cannot settle

A challenge that needs an executed test, a current external fact, or code-intent analysis is not resolvable by talking. Emit the handoff (see "Handoff triggers") and mark the claim `inconclusive` until the other skill returns — do not bless around it.

### 5. Blessing — the terminal verdict

Rule on the whole target. The blessing is a fixed closed set; there is no "looks fine":

- `blessed` — every load-bearing claim `survived`.
- `blessed-narrowed` — blessed within stated scope limits (some claims `narrowed`).
- `blocked` — a load-bearing claim was `defeated`; the target as stated cannot be blessed.
- `unresolved gap` — one or more load-bearing claims are `inconclusive`. The explicit gap list IS the deliverable.

A user override ("stop grilling, proceed") does not silently drop the gate: record the un-grilled claims as `accepted-risk`, not `blessed`.

## Output format

```text
Crucible
- Target: <what + the commitment at stake>
- Load-bearing claims: L1..Ln (each marked load-bearing / high-stakes / minor)

Grilling (load-bearing claims only)
- L-001: <claim in one disputable sentence>
  Falsifier asked: <question> -> <answer>
  Alternative asked: <question> -> <answer>
  Verdict: survived (new evidence: <what>) | narrowed (scope: <...>) | defeated (<counter-evidence>) | inconclusive (needs: <probe>)
- L-002: ...

Verdict: blessed | blessed-narrowed (scope: <...>) | blocked (defeated: L-00x) | unresolved gap (open: L-00y)
Unresolved gaps / accepted-risk: <explicit list — this IS the deliverable when blessing is withheld>

Handoff
- <emit the standard handoff block from "## Handoff to other skills">
```

## Common drift modes and anti-patterns

The recurring ways a grill collapses — the softball grill (only confirmatory questions), caving under a confident-but-unverified rebuttal, nitpicking trivia instead of the load-bearing claim, blessing on plausibility, and stopping at "shared understanding" with no verdict — are in `references/anti-patterns.md`. Read it when the output starts to feel like agreeable Q&A rather than a graded verdict.

## Worked example

A full grilling pass on a concrete target (a "switch the session store to fix slow login" plan), showing claim triage → falsifier + alternative → grade → blocked verdict with a gap list, is in `references/worked-example.md`. Read it when the steps feel abstract.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-crucible
- Blocking question: <what grilling alone cannot settle>
- Confirmed inputs: <blessed / blessed-narrowed claims — safe to carry forward>
- Inconclusive inputs: <unresolved-gap and accepted-risk claims — not safe to treat as blessed>
- Required next skill: <quaere-evidence | quaere-grounding | quaere-semantic | quaere-execution | cross-check (external companion, if installed)>
- Stop condition: <what the next skill must return before the target can be blessed>
```

- A challenge needs an executed disconfirming probe → `quaere-evidence` with the claim and the probe as its disconfirming probe.
- A challenge rests on an external, version-sensitive fact → `quaere-grounding` with the unconfirmed claim and the local version anchor.
- A challenge needs code intent / invariants understood → `quaere-semantic`.
- The target is blessed and building is authorized → `quaere-execution` / `plan` with the blessed claims and the gap list as success criteria.
- An independent second-model counter-argument is wanted → `cross-check`.

`deep-interview` and `cross-check` are external companion skills (not part of quaere); route to them only when they are installed.

Crucible ends at a verdict ledger. It does not build, and it does not bless a target whose load-bearing claims it could not actually defend.

## Stop condition

The skill is complete when:

- Every load-bearing claim carries a Verdict (`survived` / `narrowed` / `defeated` / `inconclusive`) and the target carries a terminal Blessing (`blessed` / `blessed-narrowed` / `blocked` / `unresolved gap`) — not "shared understanding", not user disengagement, not exhaustion.
- Every load-bearing claim received at least one disconfirming (not merely confirmatory) question, and the two mandatory types (falsifier, alternative) were asked.
- No `survived` was granted on confident-but-unverified pushback, casual feedback, or re-assertion — only on new evidence or a defended rebuttal.
- No approval / "looks good" was emitted while any load-bearing claim is `defeated` or an unresolved gap; when blessing is withheld, the explicit gap list is the deliverable.
- A user override is recorded as `accepted-risk`, never silently dropped.

Do not keep grilling once every load-bearing claim has a verdict and the target has a ruling. More questions past that point is the manufacturing-doubt vice, not rigor. A claim that withstood its challenge must be allowed to stand.
