# Fixture: spec-grounded security audit on JWT verifier

Used by the eval scenario `spec-grounded-security-audit`. The user prompt asks for a property-driven audit against a spec and tests, classifying findings as confirmed/potential/rejected/inconclusive with reachability/exploitability gates.

## What the agent sees

- `spec.md` — The protocol spec, naming five MUST-reject conditions for a JWT receiver: signature mismatch, `aud` mismatch, expiry beyond 1 hour, missing `aud`, missing `iat`.
- `src/protocol/jwt.ts` — A 30-line `verifyJWT` implementation. Splits on `.`, computes HS256 signature, compares to provided signature, returns the decoded payload on signature match.
- `tests/jwt.spec.ts` — Two tests: valid token passes, wrong-signature rejected.

## Properties the audit should derive

From `spec.md` Validation requirements, five separate falsifiable properties:

- **P1 — Signature gate.** Token with mismatched HS256 signature MUST be rejected.
- **P2 — Audience match.** Token whose `aud` claim does not equal the receiver's identifier MUST be rejected.
- **P3 — Expiry.** Token whose `iat + 3600 < now()` MUST be rejected.
- **P4 — `aud` presence.** Token with missing or non-string `aud` MUST be rejected.
- **P5 — `iat` presence.** Token with missing or non-numeric `iat` MUST be rejected.

## Findings the audit should reach

| Property | Code path | Status the audit should produce |
| --- | --- | --- |
| P1 | The signature check at line 19 (`if (signature !== expectedSignature) return { valid: false }`) | `confirmed` (or `rejected as candidate finding`) — the gate is implemented. |
| P2 | No `aud` check anywhere in `verifyJWT`. | `confirmed` finding (missing guard). |
| P3 | No `iat` / expiry check anywhere in `verifyJWT`. | `confirmed` finding (missing guard). |
| P4 | No `typeof payload.aud === 'string'` check. | `confirmed` finding (subset of P2 in practice; can be reported separately or folded). |
| P5 | No `typeof payload.iat === 'number'` check. | `confirmed` finding (subset of P3 in practice; can be reported separately or folded). |

The audit must surface at least **two distinct missing guards** (P2 and P3 at minimum). Folding P4 into P2 and P5 into P3 is acceptable; reporting all four separately is also acceptable.

## Test coverage observation

`tests/jwt.spec.ts` covers only P1's positive path and one signature-mismatch case. The other three properties (P2, P3, plus the missing-claim variants) are NOT covered by tests. A complete audit should note the test gap and recommend tests for the missing properties.

## Tier and promotion

This audit can plausibly be performed at any tier:

- **Triage** — narrow scope (one file), bounded properties (the spec lists five). The 4-condition Confirmation Rule is satisfiable: explicit property + reachable code + disconfirming probe attempted (e.g., grep for `aud` in the file) + impact reasoning (downstream services receive tokens treated as authenticated when they should be rejected).
- **Standard** — adds `quaere-grounding` (no version-sensitive external fact required if the spec is fully local) + `quaere-evidence` defense pass.
- **Deep** — adds `quaere-semantic` of the verifier and any callers.

The findings are not mass-tenant data exposure per se (the verifier is one component, not a multi-tenant system); promotion is not automatic. However, "auth bypass" is on the canonical promotion list — accepting an aud-mismatched token as authenticated *is* an auth bypass against the receiving service. The audit may reasonably promote on this ground.

## What the audit should NOT do

- Treat the test coverage gap as a separate finding from the missing-guard findings — it is a *contributing factor* (the test suite did not catch the missing checks), not an independent vulnerability.
- Speculate about cryptographic weaknesses in HS256 — the spec mandates HS256; analyzing the choice of algorithm is outside this audit's scope unless the spec itself permits multiple algorithms.
- Assume callers compensate for the missing checks — the audit should flag the missing guards in `verifyJWT` regardless of caller behavior, since the spec places the rejection requirement on "a receiver" and the function is the receiver-facing entry point.
- Run the tests against a live system or attempt token forgery against production. The fixture is local and the audit is property-driven; reasoning, not exploitation, is the deliverable.
