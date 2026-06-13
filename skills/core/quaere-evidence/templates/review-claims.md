# Review Claims

Use for PR review, risky diffs, security concerns, or specification mismatch candidates. Each claim should be actionable, falsifiable, and argued with evidence plus limits.

## Claim template

```md
## C-001: <short title>

Severity: critical | warning | suggestion
Status: proposed | defended | confirmed | confirmed (rebuttal-substituted) | rejected | inconclusive | fixed | deferred

# Analytical phase — the claim and its evidential support
Claim: <the actionable concern>
Data/Evidence: <file:line, diff, log, repro, spec, or trace>
Warrant: <why the evidence implies the risk>
Backing: <spec | invariant | test | policy | contract | RFC | ADR> — <reference>

# Falsifiability phase — how the claim could be defeated
Qualifier: high | medium | low confidence, with why
Rebuttal / false-positive reason: <what could defeat the claim>
Suggested probe: <supporting check whose expected result would corroborate the claim>
Falsifier: <observation that would defeat the claim>
Disconfirming probe: <check whose unexpected result would defeat the claim>

Affected files/symbols:

Why this matters:
```

The ten labeled lines above (C-001 through Disconfirming probe) are the mandatory contract from `../SKILL.md` — keep their labels and order exactly; `Affected files/symbols` and `Why this matters` are optional extras.

## Claims

<!-- Add claims below. -->
