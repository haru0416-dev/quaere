---
name: quaere-evidence
description: This skill should be used whenever the user asks to investigate unclear bugs, defend or reject PR review comments, triage CI failures or flaky tests, review risky/security/database/concurrency/external-API changes, or make any claim that needs evidence before patching. It enforces a falsifiable Finding → Hypothesis / Review Claim → Defense → Probe → Decision → Patch → Verification → Handoff workflow so the agent does not jump to fixes, accept plausible but unverified explanations, or publish noisy review comments.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, shell, test, and git access.
license: MIT
---

# Evidence-Gated Review

## Iron Law

**No patch, review comment, or root-cause conclusion without a falsifiable claim and at least one serious attempt to disconfirm it.**

This is not ceremony. Review and debugging drift toward confirmation: once an agent sees a plausible cause, it collects facts that fit and edits before testing whether another explanation fits better. The gate is simple: before acting, state what would make the hypothesis or review claim wrong, run or name the smallest probe that could reveal that, then decide. If a claim cannot be falsified at the current scope, label it `inconclusive` or hand it off; do not promote it by sounding confident.

## Output contract

Emit these labeled sections exactly, in this order, even in lightweight mode:

1. **Scope / safety constraints**
2. **Findings**
3. **Claims / Hypotheses**
4. **Defense and probes**
5. **Decision**
6. **Patch** *(omit if no fix is needed)*
7. **Verification**
8. **Handoff**

If a section is not applicable, write: `skipped because: <reason>`

### Lightweight evidence pass

When scope is small (one claim, low blast radius), collapse to this minimum — but never omit the falsifier or disconfirming probe:

```
Findings:
- F1: <observed fact + source>

Claim:
- C1: <falsifiable claim>
- Backing: F1
- Falsifier: <what would prove it wrong>
- Disconfirming probe: <probe / result, or "not yet run">

Decision: accept | reject | inconclusive

Verification:
- <fresh command / result, or "unavailable because ...">
```

The full 10-field Review Claim format (in the Workflow section) applies to Standard and Deep investigations. The lightweight pass is the same gate run with fewer words — not a bypass.

## When to use

- CI failures, flaky tests, regressions, or bugs where the cause is not already proven.
- Risky PR reviews, reviewer comments, security claims, API contract concerns, database/concurrency changes, or multi-file refactors.
- Any situation where a weak claim would create noisy review feedback, unnecessary code churn, data loss, auth bypass, production side effects, or a misleading handoff.
- Any implementation blocked by deciding whether a claim is true.

## When NOT to use

- Typos, formatting-only edits, obvious one-line type errors, or a tiny user-requested edit where cause and fix are already known.
- Pure code comprehension with no claim to decide; use `quaere-semantic` instead.
- Version-sensitive external facts whose truth depends on current docs, SDKs, CLIs, APIs, or advisories; hand that sub-claim to `quaere-grounding`, then resume here.

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

Prefer discriminating evidence over volume. Ten observations that fit one story do less work than one probe that separates two competing hypotheses. Treat confidence as an update from evidence, not as a writing style: a claim is high-confidence only when source context, runtime behavior, tests, and counter-evidence survive the defense pass.

## Depth control

Choose the lightest process that still preserves falsifiability. The time hints below are illustrative human-equivalent signals from prior-art skills (PyTorch review modes, obra failed-fix threshold) — they are not empirically calibrated for LLM agents. For an agent, the binding signal is *scope and risk*: how many independent claims, how reachable the impact, how unsafe the probe. Pad output to fill an imagined hour budget and you have already drifted.

- **Challenge pass (one claim, ~10–20 min)** — one review comment, one suspicious stack trace, or a small non-obvious bug. Inline ledger is fine, but include a falsifier and a decision.
- **Standard investigation (one failure/risky diff, ~30–90 min)** — CI failures, flaky behavior, auth/API contract concerns, or a multi-file review claim. Use IDs (`F-001`, `H-001`, `C-001`, `P-001`) and keep a concise ledger.
- **Deep / handoff investigation (multi-system or high-blast-radius, 2h+)** — production-like effects, security-sensitive changes, concurrency/database behavior, several competing hypotheses, or work that may span sessions. Persist useful state files and stop after the budget with a clear handoff rather than looping.

Do not let bookkeeping become the work. Collapse repeated facts, group related probes, and keep moving — but do not collapse away the falsifier, defense, decision, or safety stop.

## State files

For durable investigations, create or update only the useful subset of:

```text
.agent-state/
  targets/
    <task-or-issue-slug>/
      findings.md
      hypotheses.md
      review-claims.md
      defenses.md
      probes.md
      session-log.md
      handoff.md
```

Use the templates in `templates/`. Do not create all seven files by default; `findings.md`, `probes.md`, and `handoff.md` are often enough. If the user does not want files written, keep the same structure in the response.

### Git handling for state files

Treat `.agent-state/` as local investigation state by default:

- Do not commit `.agent-state/` unless the user explicitly wants the investigation ledger preserved as a project artifact.
- Prefer adding `.agent-state/` to `.gitignore` when state files are useful but local-only.
- Before committing, inspect status and ensure no private logs, credentials, production data, or noisy scratch files from `.agent-state/` are staged.
- If handoff notes are part of the deliverable, ask whether they should live under `.agent-state/`, project docs, an issue/PR comment, or the final response.

## Guardrails

- Do not patch before the defense/probe pass when root cause or risk is unclear.
- Stop and ask before destructive actions, production-like endpoints, credentials, payment flows, external side effects, or broad rewrites. Prefer a safe substitute probe.
- Default investigation budget unless the user says otherwise. Raise it only when risk justifies the cost.
  - max investigation iterations: 5
  - max planned probes at once: 5
  - max retries of the same command after a *configuration or fix change*: 1 (re-running the same command after a change should produce a different result; if not, the change was not load-bearing). This budget is **not** the cap on flakiness characterization: running the same test 10× to gather pass-rate data is a single *probe* with a sample size, not 10 retries.
  - max new state/template files per target: 8
- If two probes for the same hypothesis are inconclusive, stop and hand off unless the user explicitly approves a meaningfully different third probe.
- Always run at least one disconfirming probe for plausible hypotheses or risky review claims; "naming" a probe without running it does not satisfy the gate. **Carve-out for unprobeable claims**: when a hypothesis cannot be probed within the safety budget (production replay, payment flow, destructive operation), substitute a *defended rebuttal* — an explicit attempt to argue the strongest counter-explanation from source-context, tests, advisories, or specification — and label the Decision `confirmed (rebuttal-substituted)` with the rebuttal recorded under Defense. This substitution does not lower the bar; it trades execution evidence for documented-counter-argument evidence.
- Do not force a single root cause. Some failures require necessary contributing factors or sufficient AND/OR combinations.

## Workflow

### 0. Scope and symptom chronology

Before forming explanations, record the boundary:

- task or review claim being evaluated
- files, commits, CI job, endpoint, or runtime path in scope
- observed vs expected behavior
- environment and recent changes when relevant
- safety constraints and actions that need approval

Symptoms before guesses matters: bug-reporting practice and debugging research both reward precise observed behavior, environment, chronology, and reproduction notes before diagnosis.

### 1. Findings — facts only

Read the request, relevant diffs, failing logs, tests, source context, and runtime paths. Record observations as Findings. Include evidence and limits; an observation is provisional and can be superseded.

Good Finding:

```text
F-003: `POST /reservations` accepts `deposit` from the client payload in `src/api/reservations.ts`.
Evidence: line X reads `deposit` from `body` and passes it to `createReservation`.
Limit: this does not yet prove the value is trusted downstream.
```

Bad Finding:

```text
Validation is broken.
```

### 2. Hypotheses — explanations with falsifiers

Use Hypotheses for possible root causes: why a test fails, why a regression appears, why a race occurs, or why a system behaves differently than expected.

**Every Hypothesis MUST contain these 6 fields, each on its own labeled line, in this exact order:**

```text
H-001: <short title>
Based on: <Finding IDs>
Prediction: <result if the hypothesis is true>
Falsifier: <observation that would defeat the hypothesis>
Disconfirming probe: <command or check whose unexpected result would falsify>
Alternative: <competing hypothesis, or "none" when no plausible alternative exists>
```

`Falsifier:` and `Disconfirming probe:` are mandatory — naming what would defeat the hypothesis is what makes it falsifiable. A hypothesis missing either line is a guess.

Use RCA tools as hypothesis generators, not proof. 5 Whys can expose a chain, Ishikawa/fishbone can enumerate cause categories, and fault-tree analysis can model AND/OR preconditions for complex failures. None of them confirms a cause until probes validate the leaves.

### 3. Review Claims — actionable concerns with argument structure

Use Review Claims for PR comments, security risks, API contract mismatches, data-loss risks, concurrency hazards, or design review issues. **Every Review Claim MUST contain these 10 fields, each on its own labeled line, in this exact order:**

The 10 fields form two phases. The *analytical* phase (Claim → Backing) builds the positive argument; the *falsifiability* phase (Qualifier → Disconfirming probe) records every channel through which the argument could fail. Both phases are required — the analytical phase without the falsifiability phase is advocacy, not review.

```text
C-001: <short title>

# Analytical phase — the claim and its evidential support
Claim: <the actionable concern>
Data/Evidence: <file:line, diff, log, repro, spec, or trace>
Warrant: <why the evidence implies the risk>
Backing: <source-type> — <reference>

# Falsifiability phase — how the claim could be defeated
Qualifier: high | medium | low confidence, with why
Rebuttal / false-positive reason: <what could defeat the claim>
Suggested probe: <supporting check whose expected result would corroborate the claim>
Falsifier: <observation that would defeat the claim>
Disconfirming probe: <check whose unexpected result would defeat the claim>
```

The two `# Analytical phase` / `# Falsifiability phase` markers are visual cues; the contract is the 10 labeled lines, not the comment headers. `Suggested probe:` and `Disconfirming probe:` are NOT the same line. The first names a *supporting* check (success corroborates the claim); the second names a *defeating* check (success refutes the claim). Collapsing them removes the falsifiability gate.

`<source-type>` MUST be one of `spec | invariant | test | policy | contract | RFC | ADR`. Writing `Backing: docs say so` or `Backing: it seems likely` does not satisfy the contract — name the source type, then the concrete reference (e.g., `Backing: contract — src/reservations/contract.md:17 requires HTTP 400 for startTime >= endTime`).

The format is not a "shape" or a "style" — it is the contract. Drop or reorder a field and the claim is incomplete. Most missed in practice: **Backing** (the spec/invariant/test/contract that justifies the warrant — without it the warrant is a naked assertion that the data means what the claim says), **Falsifier + Disconfirming probe** (without naming what would defeat the claim, the writer has not engaged the falsifiability gate from the Iron Law).

The warrant remains load-bearing: it explains why the data means the claim, not just that both appear nearby. The backing remains the answer to "why should I believe the warrant" — typically a referenced spec line, contract test, or invariant the codebase already enforces elsewhere.

### 4. Defense — try to reject before accepting

For each plausible hypothesis or review claim, attempt to defeat it before acting. Check source context, tests, runtime paths, contracts, caller/callee invariants, history, and counter-evidence.

Defense results (separate vocabulary from Decision labels — Decision uses `confirmed/rejected/inconclusive/deferred`; Defense uses the four below to track what the rejection attempt produced before the Decision step):

- **survives** — no counter-evidence found; still needs probe or already has one
- **narrowed** — true only for a subset of paths, inputs, versions, or environments
- **defeated** — counter-evidence or context contradicts the claim at this stage (formerly `rejected`; renamed to disambiguate from Decision-level `rejected`)
- **inconclusive** — evidence is missing or unsafe to gather within scope

Weak, style-only, or unsupported claims should be `defeated` here rather than patched around. Defense=`defeated` typically leads to Decision=`rejected`, but the two columns remain separate so a defended-but-deferred claim does not lose its Defense audit trail.

### 5. Probes — supporting, disconfirming, and discriminating

Create small verification actions. Prefer targeted tests, minimal reproductions, pass/fail delta comparisons, grep/code search, typecheck/lint, logs, or browser/manual checks over broad rewrites.

Each important hypothesis or risky review claim should have:

```text
Supporting probe: result expected if the hypothesis/claim is true
Disconfirming probe: result expected if it is false or scoped differently
Scope probe: optional check for whether this is local or systemic
```

For unclear failures, minimize the reproduction or delta before asserting cause: reduce input, configuration, commit range, environment, or code path until the cause-effect chain is visible. For complex failures, name which probe distinguishes between competing hypotheses; a probe that fits every hypothesis is weak evidence.

### 6. Decision — label before editing or commenting

After defense and probes, name the decision:

```text
confirmed: evidence supports action now; a disconfirming probe was run and did not defeat it
confirmed (rebuttal-substituted): the probe was unsafe or unavailable within scope; the strongest counter-explanation was named, defended against source context, and rejected. Mark this label exactly so reviewers can audit the substitution.
rejected: counter-evidence or source context defeats the claim
inconclusive: evidence is insufficient, or the probe is unsafe to run and no defended rebuttal closes the gap
deferred: real concern, but outside current request or budget
```

If no claim or hypothesis survives defense, say so and do not invent a patch. If the concern is real but external/version-sensitive, hand off to `quaere-grounding`. If code intent is the blocker, hand off to `quaere-semantic`.

### 7. Patch — only confirmed and authorized items

Patch only when the claim/hypothesis is confirmed **and** implementation is explicitly authorized. If the user asked for review, investigation, or validation only, stop at Decision and provide the actionable review comment or handoff payload; do not edit. When editing is authorized, make the smallest change tied to the confirmed cause or risk. Do not refactor adjacent code unless the confirmed fix requires it.

Before editing or handing off to `quaere-execution`, record the implementation constraint:

```text
Patch target: <file/symbol>
Confirmed cause/risk: H-001 / C-001
Must preserve: <invariant, API, behavior, or safety guard>
Verification: <targeted check that should fail before and pass after, when practical>
```

### 8. Verification

Run targeted verification first: the check that proves the confirmed item was addressed. Then run broader checks only when justified by risk and project convention. Record command, result, and conclusion.

A passing broad suite does not erase the need for the targeted check. If a check cannot be run, say why and name the best substitute or next command.

### 9. Handoff

Summarize:

- confirmed and fixed items
- rejected claims/hypotheses and why
- inconclusive probes and what blocked them
- remaining open hypotheses or necessary contributing factors
- confidence shifts and limits
- next 1–3 recommended probes

## Output expectations

Prefer this structure:

```text
Scope / safety constraints
- ...

Findings
- F-001 ... Evidence: ... Limit: ...

Claims / Hypotheses
- H-001 ... Based on: ... Prediction: ... Falsifier: ... Disconfirming probe: ... Alternative: ... status: confirmed|rejected|inconclusive|deferred
- C-001 ... Claim/Data/Warrant/Backing (<source-type>)/Qualifier/Rebuttal/Suggested probe/Falsifier/Disconfirming probe: ... status: ...

Defense and probes
- D/P IDs, what was checked, what would have disproved it, and result

Decision
- confirmed/rejected/inconclusive/deferred, with confidence and limits

Patch
- Minimal files changed and why, or "no patch because ..."

Verification
- Commands/checks run and results

Handoff
- Remaining risks and next probes
```

## Worked example

**Input:**

```text
CI is failing in tests/reservation.spec.ts after my branch. A reviewer thinks validation is broken, but the failure only happens sometimes. Investigate and only patch if the claim survives evidence.
```

### Bad output (confirmation-first)

```text
The reviewer is right. I found the reservation validation code and patched the schema to require startTime before endTime. Tests should pass now.
```

Why this fails: it starts with the reviewer's conclusion, not Findings; it never states what would falsify the validation hypothesis; "sometimes" is a flakiness clue, but no timing/order/environment probe was run. The patch may hide the symptom while leaving the actual race or fixture leak intact.

### Good output (evidence-gated)

```text
Scope / safety constraints
- CI failure in tests/reservation.spec.ts only. No production calls.

Findings
- F-001: Failure is intermittent: 3/10 CI retries fail with "expected 400, got 201". Evidence: CI log job 4821. Limit: no local repro yet.
- F-002: Validation schema rejects startTime >= endTime. Evidence: src/reservations/schema.ts:42 and unit test schema.spec.ts:17.
- F-003: The fixture object is module-scoped and test "creates a valid reservation" mutates `sharedReservation.endTime`. Evidence: tests/reservation.spec.ts:12 and :41. Limit: not yet proven to precede the failing case.

Claims / Hypotheses
- C-001 (review claim): Validation is broken.
  Claim: the reservation endpoint accepts invalid `startTime >= endTime` payloads.
  Data/Evidence: intermittent 201 response in reservation.spec.ts (CI job 4821, 3/10 retries).
  Warrant: if invalid payloads bypass validation, the endpoint returns success instead of 400.
  Backing: contract — src/reservations/contract.md and schema.spec.ts:17 require HTTP 400 for `startTime >= endTime`.
  Qualifier: low — F-002 shows direct validation exists; intermittent behavior suggests ordering or shared state.
  Rebuttal / false-positive reason: validation may be intact, and the failing payload may have been mutated to look invalid only after the request was sent.
  Suggested probe: log the request body in the failing spec and inspect schema dispatch on the path.
  Falsifier: captured request body on failed runs is structurally valid (startTime < endTime).
  Disconfirming probe: P-001 — log the outgoing payload in the failing spec; if it is valid, the validation-broken claim is defeated.
- H-001: Shared fixture mutation changes the payload before the failing assertion.
  Based on: F-001, F-003.
  Prediction: failed runs will show payload.endTime later than startTime in the captured request body.
  Falsifier: captured request body remains invalid (startTime >= endTime) on failed runs.
  Disconfirming probe: P-001 — same log as above; if the payload is invalid on failure, the mutation hypothesis is defeated.
  Alternative: schema dispatcher races on hot-reload of validation rules.

Defense and probes
- D-001 for C-001: Existing schema and schema unit test are counter-evidence; claim narrowed to endpoint path or fixture path.
- P-001 disconfirming C-001 / supporting H-001: log the request body in the failing spec. Result: failed runs send a valid endTime; this rejects "validation schema is broken" but does not yet prove the mutation source.
- P-002 causal probe for H-001: run the failing test alone vs after the mutating test, then deep-clone the fixture per test and repeat 10x. Result: alone = pass; after mutating test = reproduces; cloned fixture = 10/10 pass.

Decision
- C-001 rejected as stated: validation is not generally broken.
- H-001 confirmed (necessary contributing factors): the failing observation requires three factors holding together — (a) the mutating test runs before the failing one, (b) the fixture is module-scoped/shared, (c) the failing test reads the mutated `endTime`. Removing any one of the three (e.g., the deep-clone) suppresses the bug; this is necessary-AND not single-root. P-002 isolated all three by varying order, scope, and clone behavior together.

Patch
- Minimal fix: clone the fixture per test in tests/reservation.spec.ts; do not change validation schema. The fix breaks factor (b) — fixtures are no longer shared at the test boundary — which is the cheapest of the three to invalidate without changing the schema or test ordering contract.

Verification
- Targeted before patch: reservation.spec.ts repeated 10x = 3/10 fail (matches F-001).
- Targeted after patch: reservation.spec.ts repeated 10x = 10/10 pass (the original observation is no longer reproducible).
- Broader: unit suite pass; no other tests reference the previously-shared fixture.
```

## Common drift modes

| Rationalization | What's actually happening |
| --- | --- |
| "This claim looks plausible — I can act." | Plausibility is a prior, not a Defense. Plausible-looking claims still need a source-context contradiction-check (does the existing code already enforce what the claim says is missing?) and an explicit rebuttal before they can survive Decision. |
| "I found three clues that support this cause." | Supporting clues do not discriminate. Ask what would falsify the cause or distinguish it from the next-best hypothesis. |
| "The test passed after my patch, so root cause is confirmed." | A green test may be coincidence or symptom masking. The targeted probe should fail for the original cause and pass for the fix, or the claim remains weaker than it sounds. |
| "This is obviously a single root cause." | Many incidents are combinations. Model contributing factors or AND/OR preconditions when one linear story leaves gaps. |
| "5 Whys found the cause." | RCA tools generate candidate causes; probes confirm them. A tidy chain without evidence is just a story. |
| "The claim is too risky to test, so I'll decide from reasoning." | Unsafe probes should become safe substitutes or approval requests. If neither is possible, mark `inconclusive`, not `confirmed`. |
| "Confidence: high" | Confidence without a qualifier, rebuttal, and disconfirming result is tone, not evidence. State why the evidence should move belief. |
| "No time for the ledger." | Use challenge-pass mode, but keep the falsifier and decision. The ledger can shrink; the gate cannot disappear. |

## Anti-patterns (each item explains why it fails)

- **Patch-first debugging.** Editing before a falsifiable hypothesis fails because any green result afterward is ambiguous: the patch may fix the root cause, mask the symptom, or merely perturb timing.
- **Review-comment laundering.** Turning a reviewer's concern into your own confirmed finding fails because consensus is not proof. The concern must survive source context, rebuttal, and probe.
- **Evidence as decoration.** Listing logs after deciding what they mean fails because the observations were not allowed to change the decision. Findings precede interpretation so counter-evidence can steer the investigation.
- **Broad suite as proof of cause.** Full tests are valuable regression checks, but they rarely isolate why a bug happened. Use the targeted check to prove the cause/risk, then the broad suite to guard side effects.
- **Forced certainty.** Some investigations end `inconclusive`. That is a useful result when the alternative is inventing a confident but unsupported patch.

## Handoff to other skills

When handing off, emit this standard block so the receiving skill knows exactly what it is being given:

```
Handoff
- From skill: quaere-evidence
- Blocking question: <what cannot be decided within this skill's scope>
- Confirmed inputs: <findings, claims, and decisions safe to carry forward>
- Inconclusive inputs: <claims or facts not safe to treat as true>
- Required next skill: <quaere-grounding | quaere-semantic | quaere-execution | quaere-audit>
- Stop condition: <what the next skill must return before this investigation can resume>
```

Hand control to a companion skill when the blocking question shifts. Name the handoff and the reason in the response — do not silently switch.

- A claim or hypothesis depends on a version-sensitive external fact (SDK, CLI, API, advisory, current docs) → invoke `quaere-grounding` with the unconfirmed external claim, local anchor if known, source/context already read, and the implementation decision blocked by it. Resume only after the fact is labeled `confirmed` / `version-mismatched` / `stale` / `conflicted` / `inconclusive`.
- The reviewed code's intent or invariants are unclear before the claim can be evaluated → invoke `quaere-semantic` for the relevant unit, then return with `What (mechanical) / What (domain intent) / Why / Invariants / Failure / Connections` filled in.
- A claim is confirmed and implementation is authorized → invoke `quaere-execution` with the confirmed claim, patch target, invariants to preserve, and verification commands.
- The work is a property-driven security audit rather than a single claim → defer to `quaere-audit` as coordinator and provide it the active Findings/Claims and probes already run.

When handing off to `quaere-grounding`, spell the next skill name exactly as `quaere-grounding` (lowercase, hyphenated) and include this payload:

```text
Handoff to quaere-grounding
- Unconfirmed external claim: <SDK/API/CLI/advisory claim, e.g. deprecated/renamed method>
- Local anchor: <installed version, lockfile, package manifest, or "missing">
- Blocked decision: <review claim / patch / implementation decision that cannot proceed until the external fact is decided>
```

## Stop condition

This skill is complete when:

- every active hypothesis or claim has a Decision (`confirmed` / `rejected` / `inconclusive` / `deferred`)
- every non-trivial `confirmed` decision names the evidence that supported it and the disconfirming probe that was run and did not defeat it; `confirmed (rebuttal-substituted)` decisions name the unsafe-probe reason and the defended rebuttal that closed the gap instead
- confirmed + authorized items are patched and verified or explicitly handed off to `quaere-execution`; confirmed but unauthorized items stop at an actionable comment/handoff without editing
- inconclusive items are reported with the next probe needed and any budget or safety limit already consumed
- the user has enough material to decide whether to expand probes, accept the result, or hand off

Do not loop on the same hypothesis past the budget. If two probes for the same hypothesis are inconclusive, stop and hand off instead of running a third.
