---
name: quaere-evidence
description: This skill should be used whenever the user asks to investigate unclear bugs, defend or reject PR review comments, triage CI failures or flaky tests, review risky/security/database/concurrency/external-API changes or multi-file refactors, or make any claim that needs evidence before patching. It enforces a falsifiable claim → defense → probe → decision workflow so the agent does not jump to fixes, accept plausible but unverified explanations, or publish noisy review comments.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, shell, test, and git access.
license: MIT
---

# Evidence-Gated Review

<!-- quaere:layer gate -->
## Iron Law

**No patch, review comment, or root-cause conclusion without a falsifiable claim and one executed attempt to defeat it.**

## Output contract

Every claim or hypothesis acted on carries the four lines below. Everything else about format is the investigator's choice.

### Lightweight evidence pass

```text
Claim: <what you assert>
Evidence: <file:line / log / repro / trace>
Falsifier: <the observation that would defeat this>
Probe: <the check you ran trying to defeat it → its result>
```

## Decisions

- `confirmed` — the probe ran and did not defeat the claim.
- `confirmed (rebuttal-substituted)` — the probe is unsafe or unavailable in scope (production replay, payments, destructive ops); the strongest counter-explanation was argued from source, tests, or spec, and failed. Label it exactly so the substitution is auditable.
- `rejected` / `inconclusive` / `deferred` — when the Probe line says "not run", these are the only legal labels.
<!-- /quaere:layer -->

<!-- quaere:layer method -->
## When to use

- CI failures, flaky tests, regressions, or bugs whose cause is not already proven.
- Risky PR reviews, security claims, API contract concerns, database/concurrency changes, multi-file refactors.
- Any claim that would create noisy review feedback or a misleading handoff if published unverified.

## When NOT to use

- Typos, formatting-only edits, or a tiny user-requested edit where cause and fix are already known.
- Pure code comprehension with no claim to decide — use `quaere-semantic`.
- Version-sensitive external facts whose truth depends on current docs or SDKs — hand that sub-claim to `quaere-grounding`, then resume.

## Probe budget

One discriminating probe per decision — the check whose outcome differs between the claim and its best alternative. Two at most; if both are inconclusive, stop and hand off. Supporting evidence never substitutes for the disconfirming attempt. Running a flaky test N times for a pass rate is one probe with a sample size, not N retries.

## Workflow

1. **Scope** — what is being decided, observed vs expected, what is out of bounds.
2. **Facts before explanations** — read the diff, log, test, and source; note each fact with its source and its limit. "Validation is broken" is not a fact.
3. **Claims with falsifiers** — the four-line shape. Name the best competing explanation, or state `alternative: none`.
4. **Defense before probes** — try to defeat the claim from source context, tests, contracts, callers, history. A claim defeated here is not probed and not patched.
5. **Probe and decide** — within the budget, then patch only the smallest change tied to the confirmed cause. Record what must not break.
6. **Verify targeted-first** — the check that proves this fix, fail-before/pass-after when practical. A green broad suite does not substitute.
7. **Handoff** — confirmed, rejected, and inconclusive items; the next 1–3 probes if any remain.

## Autonomy policy

Local reads, searches, tests, and typechecks proceed without asking. Destructive actions, production-like endpoints, credentials, payments, external side effects, and broad rewrites stop for approval. Patch only what is confirmed AND explicitly authorized; a review-only request stops at the decision with an actionable comment.

## Budgets

5 investigation iterations, 5 planned probes, 1 retry of an unchanged command after a fix. When a budget is spent, hand off instead of looping.

## Depth

One small claim: the four-line shape inline, a decision, done. Multi-claim or high blast radius: use IDs (F-001 / C-001) and a short ledger. Persist state files only for multi-session investigations (see the deep-investigation forms below when installed with the full profile).

## Handoff triggers

A version-sensitive external fact → `quaere-grounding`. Unclear code intent → `quaere-semantic`. Confirmed and authorized implementation → `quaere-execution`. A property-driven security audit rather than a single claim → `quaere-audit` when installed. Name the handoff and carry: the blocking question, confirmed inputs, inconclusive inputs, and the stop condition.

**Stop now —** when a budget is spent, when two probes for the same claim come back inconclusive, before any destructive or production-like action, and once a confirmed fix is verified: stop and hand back rather than pushing past a gate.
<!-- /quaere:layer -->

<!-- quaere:layer pedagogy -->
## Deep investigations

The forms below extend the gate for Standard and Deep investigations — multi-claim reviews, high-blast-radius changes, or work that spans sessions. They are the same gate with more bookkeeping, not a different rule.

## Core model

```text
Finding       observed fact: code, diff, log, test, runtime behavior, user report
Hypothesis    falsifiable explanation of an observed failure or behavior
Review Claim  actionable risk or defect candidate, argued with evidence and limits
Defense       attempt to reject, narrow, or qualify the hypothesis/claim
Probe         small verification action; includes supporting and disconfirming checks
Decision      confirmed / rejected / inconclusive / deferred
Patch         smallest change tied to a confirmed claim or hypothesis
Verification  targeted check that the patch addresses the confirmed cause/risk
Handoff       remaining open items, confidence, limits, and next probes
```

Prefer discriminating evidence over volume: one probe that separates two competing hypotheses outworks ten observations that fit one story. Confidence is an update from evidence, not a writing style.

### Findings — facts with limits

```text
F-003: `POST /reservations` accepts `deposit` from the client payload (src/api/reservations.ts:42).
Evidence: line 42 reads `deposit` from `body`. Limit: does not yet prove the value is trusted downstream.
```

### Hypotheses — the 6-field form

RCA tools (5 Whys, fishbone, fault trees) only *generate* hypotheses; nothing is confirmed until probes validate the leaves.

```text
H-001: <short title>
Based on: <Finding IDs>
Prediction: <result if the hypothesis is true>
Falsifier: <observation that would defeat the hypothesis>
Disconfirming probe: <command or check whose unexpected result would falsify>
Alternative: <competing hypothesis, or "none" when no plausible alternative exists>
```

### Review Claims — the 10-field form

The analytical phase (Claim → Backing) builds the positive argument; the falsifiability phase (Qualifier → Disconfirming probe) records how it could fail — the first without the second is advocacy, not review.

```text
C-001: <short title>

# Analytical phase
Claim: <the actionable concern>
Data/Evidence: <file:line, diff, log, repro, spec, or trace>
Warrant: <why the evidence implies the risk>
Backing: <source-type> — <reference>

# Falsifiability phase
Qualifier: high | medium | low confidence, with why
Rebuttal / false-positive reason: <what could defeat the claim>
Suggested probe: <supporting check whose expected result would corroborate>
Falsifier: <observation that would defeat the claim>
Disconfirming probe: <check whose unexpected result would defeat the claim>
```

`<source-type>` is one of `spec | invariant | test | policy | contract | RFC | ADR`, followed by the concrete reference; `Backing: docs say so` does not satisfy the contract. `Suggested probe` (supporting) and `Disconfirming probe` (defeating) are different lines — collapsing them removes the falsifiability gate.

### Defense vocabulary

- **survives** — no counter-evidence found; still needs its probe
- **narrowed** — true only for a subset of paths, inputs, versions, or environments
- **defeated** — counter-evidence or context contradicts the claim at this stage
- **inconclusive** — evidence is missing or unsafe to gather within scope

### State files

For durable / multi-session investigations, persist a per-target ledger under `.agent-state/targets/<slug>/` (`findings.md`, `probes.md`, `handoff.md` are often enough). Templates are in `templates/`; layout and git-handling rules are in [`references/state-files.md`](references/state-files.md). If the user does not want files written, keep the same structure in the response.

## Handoff to other skills

When switching skills, emit this payload so the receiver knows exactly what it is given:

```text
Handoff
- From skill: quaere-evidence
- Blocking question: <what cannot be decided within this skill's scope>
- Confirmed inputs: <findings, claims, and decisions safe to carry forward>
- Inconclusive inputs: <claims or facts not safe to treat as true>
- Required next skill: <quaere-grounding | quaere-semantic | quaere-execution | quaere-audit>
- Stop condition: <what the next skill must return before this investigation can resume>
```

## Stop condition

This skill is complete when every active claim or hypothesis has a Decision; when every non-trivial `confirmed` names the evidence that supported it and the disconfirming probe that ran and did not defeat it (or, for `confirmed (rebuttal-substituted)`, the unsafe-probe reason and the defended rebuttal that closed the gap); when confirmed and authorized items are patched and verified or explicitly handed off; when inconclusive items carry the next probe needed and the budget already consumed; and when the user has enough material to decide whether to expand probes, accept the result, or hand off. Do not loop on the same claim past the budget — if two probes come back inconclusive, hand off instead of running a third.

## Worked example

A bad-output (confirmation-first patch) vs good-output walkthrough is in [`references/worked-example.md`](references/worked-example.md). Read it when the deep-investigation forms feel abstract.

## Common drift modes and anti-patterns

Confirmation-bias rationalizations ("plausible — I can act", "three supporting clues", "test passed after my patch") and how each one skips the falsifier or defense are in [`references/anti-patterns.md`](references/anti-patterns.md). Read them before promoting a claim to `confirmed` in a high-stakes review.
<!-- /quaere:layer -->
