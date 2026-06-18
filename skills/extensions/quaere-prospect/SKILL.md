---
name: quaere-prospect
description: This skill should be used whenever the user asks what to build next, what feature, tool, or product is missing, where the opportunities are in a codebase or domain, or makes any 0→1 origination request — 次に何を作るべきか, what should we build, this repo is missing something, find the gaps, surface opportunities — where the agent would otherwise answer with a generic, ungrounded wishlist (add tests, add CI, add dark mode) instead of a real gap. It forces every proposed opportunity to name a gap verified to exist in the actual system, the beneficiary and the job they are blocked on, evidence the demand is real rather than assumed, and the smallest probe that would validate or kill it before any build, classifying each as verified gap, assumed gap, already covered, or wishlist. Trigger before a problem is chosen; for non-obvious solutions to an already-chosen problem, use quaere-invention instead.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, web, and shell access.
license: MIT
---

# Prospect Probe

## Iron Law

**No opportunity is proposed as worth building without four things named: the gap it fills (verified to actually exist in the system, not already built and not deliberately out of scope), the beneficiary and the job they are blocked on, the evidence the demand is real rather than assumed, and the smallest probe that would validate or kill it before any build. An opportunity that cannot name all four is a `wishlist` item, not a proposal — do not present it.**

This is not a brainstorming ritual. Asked "what should I build" or "what's missing here", a model regresses toward the mean of its training distribution and emits a plausible-sounding, codebase-agnostic wishlist — add tests, add CI, add dark mode, add a dashboard, add caching — that sounds productive but is tied to no verified gap, names no beneficiary, may already exist or be out of scope, and gives no signal for what is worth building first. LLM assistance even *homogenizes* the directions it suggests across different users *(Anderson, Shah & Kreminski 2024 — arXiv:2402.01536)*. The gate changes the question from *does this sound like useful work* to *which concrete gap does this fill, who is blocked by it, and how do we know before we build*. Proposing from assumption is the failure this skill exists to stop. Full method: `references/gap-taxonomy.md` and `references/research-basis.md`.

**Stop now —** do not present any opportunity you have not checked against the actual system (the capability may already exist, or be a deliberate non-goal); assumption is not evidence. If fewer than the gaps you surface survive the reality gate, loop back and survey more terrain — do not pad with wishlist. Full conditions: `## Stop condition`.

## When to use

- The user asks what to build next, what feature / tool / product is missing, or where the opportunities are — before any problem is chosen.
- A codebase, domain, or user context needs to be scanned for unmet jobs, friction, or underserved users.
- The work is at risk of answering with a generic feature wishlist instead of a grounded gap.
- The user wants to originate the work item (0→1), not solve a problem already on the table.

## When NOT to use

- The problem is already chosen and only the *approach* is hard (how to solve it non-obviously) → `quaere-invention`. prospect finds WHAT; invention finds HOW.
- A factual question about whether a market / library / API exists or behaves a certain way → `quaere-grounding`.
- A bug whose cause is unknown → `quaere-evidence`; do not "prospect" around an unexplained failure.
- A chosen opportunity that just needs building → `quaere-execution` / `plan`.

## Handoff triggers (which skill comes after this one)

Prospect ends at a small set of grounded opportunities with validation probes, not at a built thing or a chosen winner. Hand off when the next step changes discipline:

- A surviving opportunity's hard part is the *approach itself* (the obvious solution will not reach it) → `quaere-invention`.
- An opportunity depends on an external fact — does this market / library / API actually exist or behave this way → `quaere-grounding`.
- A demand or "gap" claim is disputed and must be disconfirmed before commitment → `quaere-evidence` (run the validation probe there).
- An opportunity is chosen and authorized to design or build → `quaere-execution` / `plan`.
- No opportunity survives the reality gate → stop and report the terrain surveyed and why each gap failed; do not present wishlist.

The standard handoff payload (Blocking question / Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is at the end of this file under "Handoff to other skills".

## Core procedure

Run in order. Steps 1–5 are internal — the user sees opportunities only after the reality gate (Step 4). Keep output proportional to surviving opportunities, not to an imagined idea quota.

### 1. Survey the terrain

Establish where to look and what the system already is, so a gap is measured against reality, not imagined. Name the survey scope.

- Subject: codebase | domain | user context (which one, and its boundary).
- What it is for (one sentence): the job the system already serves.
- Current boundaries: what it deliberately does — and the explicit non-goals (from docs, README, ADRs, comments). Naming non-goals up front is what makes "this is out of scope" auditable later.

### 2. Gap inventory

Find candidate gaps: unmet jobs, friction points, missing capabilities, underserved users, adjacent opportunities. Tag each by kind, because different kinds are verified and validated differently (full catalog in `references/gap-taxonomy.md`).

- G1 — <gap> — kind: capability | UX-friction | reliability | reach (new users) | integration | business/monetization
- G2 — ...
- For each: is it **absent**, **present-but-weak**, or **out-of-scope on purpose**? (The third is not a gap.)

### 3. Beneficiary and demand

An opportunity with no nameable beneficiary is wishlist. For each candidate gap:

- Beneficiary + job-to-be-done: who is blocked, and on what.
- Demand evidence: issue reports, usage signals, the code's own TODO / FIXME, a named user segment, support load — vs. *assumed*. Mark each as `evidenced` or `assumed`.
- Kill any gap that names no beneficiary, or whose demand is purely assumed with no path to evidence.

### 4. Reality gate

MANDATORY, blocking, internal. Do NOT present any opportunity that has not passed this. Assumption and memory are not evidence — check the actual system.

1. **Already built?** Search the codebase (grep / read) for the capability. If it exists, drop it or downgrade to "improve existing", not "build new".
2. **Deliberately out of scope?** Check docs / README / ADRs / non-goals for an explicit decision against it. A stated non-goal = dead unless the user is reopening it.
3. **Demand evidence real?** For gaps marked `evidenced` in Step 3, confirm the evidence actually exists (open the issue, find the TODO, cite the usage signal). Downgrade unconfirmed evidence to `assumed`.
4. **Blocked check:** if the system cannot be inspected (no repo access, no network for a market check), never guess "this is missing" — mark the gap `unverified (check blocked)` and hand it to `quaere-grounding` rather than presenting it as real.

### 5. Validation probe

For the best 1–3 opportunities, define the smallest test that would validate demand or feasibility — or kill the idea — *before* any build.

- Probe:
- Validate signal (demand/feasibility confirmed):
- Kill signal:
- Cost:
- What evidence would change the decision:

An opportunity with no validation probe is not ready to promote; mark it `assumed gap` and hand off to grounding / evidence.

### 6. Opportunity filter

Classify every survivor. The label is a finding, not a pitch. Do not oversell.

- `verified gap` — real, evidenced, not already built, not a non-goal. Permitted as a proposal only with a beneficiary and a validation probe (Step 5).
- `assumed gap` — plausible gap whose demand is unproven; carries a probe but the probe has not run. Present as `assumed gap (unprobed)`, never as confirmed.
- `already covered` — exists in the system or is a deliberate non-goal. Drop (or reframe as "improve existing").
- `wishlist` — generic, no verified gap or no beneficiary. Drop. This is the slop label.

**Forbidden:** self-rating an opportunity as "game-changing", "must-have", "huge", "massive opportunity", or otherwise asserting its value. Use the four labels only. A general market-size or demand claim is a `quaere-grounding` task, not a self-assessment.

## Output format

```text
Prospect probe
- Survey: <subject + what it is for + boundaries / non-goals>
- Gaps: G1..Gn with kinds and absent / present-but-weak / out-of-scope

Opportunities
- O-001: <one line>
  Gap: <G-id — what is missing, verified how>
  Beneficiary: <who is blocked + job-to-be-done>
  Demand: evidenced (<source>) | assumed
  Label: verified gap | assumed gap (unprobed) | already covered | wishlist
- O-002: ...

Probes (top 1-3)
- P-001 for O-00x: Probe / Validate signal / Kill signal / Cost / Decision-changing evidence

Handoff
- <emit the standard 6-field block from "## Handoff to other skills">
```

## Common drift modes and anti-patterns

The recurring ways an origination pass collapses into a wishlist — proposing capabilities that already exist, naming no beneficiary, calling assumed demand evidenced, self-rating opportunities as game-changing, generating volume instead of verified gaps — are in `references/anti-patterns.md`. Read it when output starts to feel like a feature list rather than grounded, checked opportunities.

## Worked example

A full prospect pass on a concrete codebase (survey → gap inventory → beneficiary/demand → reality gate → validation probe → labels → handoff) is in `references/worked-example.md`. Read it when the step outputs feel abstract.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-prospect
- Blocking question: <what surveying for opportunities alone cannot decide>
- Confirmed inputs: <verified gaps with beneficiary and validation probe — safe to evaluate next>
- Inconclusive inputs: <assumed gaps or unverified (check blocked) — not safe to commit>
- Required next skill: <quaere-invention | quaere-grounding | quaere-evidence | quaere-execution>
- Stop condition: <what the next skill must return before an opportunity is committed>
```

- A surviving opportunity's hard part is the approach itself → `quaere-invention` with the opportunity as the problem to escape the default on.
- An opportunity depends on whether an external market / library / API exists or behaves as assumed → `quaere-grounding` with the unconfirmed external claim.
- A demand or gap claim must be disconfirmed before commitment → `quaere-evidence` with the claim and the validation probe as the disconfirming probe.
- An opportunity is chosen and building is authorized → `quaere-execution` / `plan` with the opportunity and its validation probe as a success criterion.

Prospect ends at grounded opportunities with probes. It does not pick the winner for the user, and it does not build.

## Stop condition

The skill is complete when:

- The terrain was surveyed and the system's boundaries / non-goals were named before any gap was proposed (Step 1).
- Candidate gaps were inventoried with kinds and beneficiaries (Steps 2–3); gaps with no nameable beneficiary were killed.
- Every presented opportunity passed the reality gate (Step 4) — checked against the actual system, never asserted from assumption or memory.
- The top 1–3 opportunities each carry a validation probe (Step 5).
- Every opportunity carries a label from the fixed four (`verified gap | assumed gap | already covered | wishlist`), with no self-rated "game-changing" language.
- A handoff or an explicit "no opportunity survived the reality gate" stop is stated.

Do not present an opportunity you have not checked against the system. Do not pad to a count with wishlist — looping back to survey more terrain beats shipping slop. A capability proposed as missing when it already exists, or asserted as wanted with no evidence, is the worst outcome; the reality gate exists to prevent exactly that.
