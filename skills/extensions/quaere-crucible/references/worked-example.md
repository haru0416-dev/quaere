# Worked example: a crucible pass

A full grilling pass on a concrete plan, showing claim triage, the mandatory
questions, the flip rule in action, and a `blocked` verdict whose gap list is
the deliverable. The scenario is invented but typical; the discipline is the
point.

## Contents

- [Target](#target)
- [Step 1 — Scope and triage](#step-1--scope-and-triage)
- [Step 2-3 — Grill the most-decisive claim](#step-2-3--grill-the-most-decisive-claim)
- [The cave that did not happen](#the-cave-that-did-not-happen)
- [Remaining claims](#remaining-claims)
- [Step 5 — Verdict](#step-5--verdict)
- [What the softball grill would have done](#what-the-softball-grill-would-have-done)

## Target

> "Login is slow. We should switch the session store from Postgres to Redis —
> it'll be much faster, and it's a low-risk change. Grill me before I write it
> up."

## Step 1 — Scope and triage

- Target: a plan. Commitment at stake: a multi-day migration + new infra
  dependency. `blessed` would authorize writing the migration.
- Load-bearing claims:
  - **L-001 (load-bearing):** the slow login is *caused by* Postgres session reads.
  - **L-002 (load-bearing):** moving sessions to Redis will fix the slowness.
  - **L-003 (high-stakes):** the switch is low-risk.
  - L-004 (minor): Redis is the right store vs Memcached. — not grilled; does not decide the outcome.

## Step 2-3 — Grill the most-decisive claim

L-001 is most-decisive: if the cause is not the session store, the whole plan
collapses. Recommended counter-position stated first: *"My prior is that login
slowness is usually a query or N+1 problem, not the session store — convince me
otherwise."*

- **Falsifier asked:** "What observation would make you abandon 'Postgres
  session reads cause the slowness'?" → Answer: "If a profile showed the time is
  spent elsewhere." Good — it is falsifiable.
- **Disconfirming probe asked:** "Have you profiled the login path, or are you
  inferring the store is the cause?" → Answer: "Inferring — Postgres feels slow
  under load."
- **Alternative hypothesis asked:** "Name two other explanations for slow login."
  → Answer: "Maybe the password hash cost, or a missing index on the sessions
  query."

L-001 cannot be graded `survived`: the cause was inferred, not measured, and a
named alternative (missing index) fits the same symptom. **Verdict: inconclusive
— needs an executed profile.** Hand off to `quaere-evidence`: probe = profile the
login path; the claim is blocked until a Decision returns.

## The cave that did not happen

The user pushes back: *"I'm pretty sure it's the store — we saw Postgres CPU
spike during the incident, and everyone knows Postgres is bad at high-write
session churn."* Confident, detailed — and unverified. The flip rule holds:
CPU spiking during an incident does not isolate the session query from every
other query, and "everyone knows" is not evidence. L-001 stays `inconclusive`
until the profile runs. (This is the single-rebuttal cave the gate exists to prevent.)

## Remaining claims

- **L-002 (Redis fixes it):** depends entirely on L-001. With L-001 unproven,
  L-002 is `inconclusive` by inheritance — you cannot know the fix works before
  the cause is known.
- **L-003 (low-risk):** grilled with a premortem — "assume we shipped and it
  failed: first line of the post-mortem?" → surfaces that sessions in Redis
  without persistence config are lost on restart, logging everyone out. Verdict:
  `narrowed` — low-risk only with persistence + a migration/rollback path, which
  the plan does not yet have.

## Step 5 — Verdict

```text
Verdict: unresolved gap
Unresolved gaps / accepted-risk:
- L-001 (cause is the session store): inconclusive — profile the login path first
  [handed to quaere-evidence]
- L-002 (Redis fixes it): inconclusive — depends on L-001
- L-003 (low-risk): narrowed — only with Redis persistence + a rollback path
Blessing withheld: do NOT write the migration until L-001's profile confirms the
store is the cause.
```

The deliverable is the gap list, not approval. The single cheap probe (profile
the login path) gates a multi-day migration — and may show the fix is a one-line
index, not a new datastore.

## What the softball grill would have done

Without the gate: "Great idea — Redis is much faster for sessions, switching is a
common pattern, go for it." It would have inherited the user's framing, blessed
an unmeasured cause, and shipped a needless migration to fix a missing index.
That is the failure crucible exists to stop.
