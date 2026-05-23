# Security Audit Ledger

## Scope

- Target:
- Commit/version:
- Tier: Triage | Standard | Deep
- Tier rationale:
- Assets:
- Actors:
- Trust boundaries:
- Specs and source-of-truth:
- Non-goals:
- Unsafe actions requiring approval:

## Property Ledger

| ID | Type | Statement | Source / version | Expected enforcement | Failure impact | Priority | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Attack Surface / Threat Paths

| Surface | Attacker source | Trust boundary | Sink / state transition | Expected guard | Impact | Notes |
| --- | --- | --- | --- | --- | --- | --- |

## Proof Traces

| Property | Code map | Semantic-review needed? | Proof result | Gap | Evidence | Disconfirming check |
| --- | --- | --- | --- | --- | --- | --- |

## Gates

| Finding | Reachability | Attacker control | Existing guard | Scope | Impact | Repro strength | Decision impact |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Severity / Priority

| Finding | Severity | Confidence | CWE | CVSS / SSVC / KEV / EPSS | Blast radius | Baseline status |
| --- | --- | --- | --- | --- | --- | --- |

## Companion Skill Checks

Tier-conditional. Triage requires only conditions 1–4 of the Confirmation Rule (no companion skill round trip is mandatory beyond a disconfirming probe) unless the finding relies on a current external fact. Any current CVE, advisory, SDK/API behavior, cloud/framework default, versioned spec, or bounty-rule fact needs `quaere-grounding` at any tier or the item remains `potential` / `inconclusive`. Standard requires `quaere-evidence` and an external-fact status: either `quaere-grounding` result or `no external fact required`. Deep additionally requires `quaere-semantic`. Mark `n/a` for companions not required at the audit's tier.

| Finding | Tier | External fact used? | Semantic review | External grounding | Evidence-gated review | Execution loop / PoC | Promotion required? | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Decisions

| ID | Decision | Reason | Next probe |
| --- | --- | --- | --- |

## Handoff

- Confirmed findings:
- Potential findings:
- Rejected claims:
- Inconclusive areas:
- Uncovered risks / skipped tools:
- Recommended next checks:
