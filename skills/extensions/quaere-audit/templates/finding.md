# Security Finding

## Decision

Confirmed / Potential / Rejected / Inconclusive

## Audit tier

Triage | Standard | Deep

If `Confirmed` with `Triage` and the finding has high blast radius (consensus break, funds movement, auth bypass, parser RCE, sandbox escape, key compromise, mass/bulk tenant data exposure, cross-tenant write, tenant impersonation, or multi-tenant secret leak), the audit must be promoted to Standard before this verdict stands. The list is canonical; if the finding does not fit one of these categories, it does not require promotion. Record the promotion in the audit ledger.

## Severity / confidence

- Severity: critical | high | medium | low | informational
- Confidence: high | medium | low
- CWE:
- CVSS / SSVC / KEV / EPSS context:
- Baseline status: new | existing | unknown | fixed-before-target

## Summary

One sentence describing the violated property and impact.

## Property

- ID:
- Type:
- Source:
- Statement:

## Affected Code

- File:
- Symbol:
- Lines:
- Related callers/callees:

## Proof Gap

What exact check, state transition, guard, or invariant is missing or wrong?

## Attack Path

1. Actor:
2. Entry point:
3. Attacker-controlled input/state:
4. Trust boundary crossed:
5. Sink / missing or failed guard:
6. Trigger sequence:
7. Impact:

## False-Positive Gates

- Reachability:
- Attacker control:
- Existing guard:
- Scope:
- Impact:
- Repro strength:
- Disconfirming check performed:

## Companion Skill Checks

Mark `n/a` for companions not required at this finding's tier.

- External fact used? yes | no. If yes, `quaere-grounding` is required at any tier before `Confirmed`.

- Semantic review (Deep tier required):
- External grounding / external-fact status (Standard records grounding result or `no external fact required`; grounding is required for external facts at any tier):
- Evidence-gated review (Standard tier required):
- Execution loop / PoC:

## Reproduction Or Evidence

Test, command, input, trace, or reason a PoC was not safely run.

## Regression / prevention

Test, property check, guard, monitoring, or process change that would prevent recurrence.

## Recommended Fix Direction

Smallest behavioral change that would enforce the property.
