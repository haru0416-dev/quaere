# Worked example — evidence-gated review of an intermittent CI failure

A bad-output (confirmation-first patch) vs good-output (Findings → Claims/Hypotheses → Defense and probes → Decision → Patch → Verification) example, applied to a flaky reservation-spec failure. See `../SKILL.md` for the procedure this example enacts.


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
