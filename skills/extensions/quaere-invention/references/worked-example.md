# Worked example — invention probe end to end

A full pass on a concrete prompt, showing what each step's output actually looks like.
See `../SKILL.md` for the procedure.

**Input prompt:** "We need onboarding for our dev tool. Most users drop off before
they finish setup. Suggest a non-obvious approach."

## 1. Default basin

- Default answer: a guided multi-step wizard with a progress bar and tooltips.
- Why it is attractive: it is the standard onboarding pattern; every PM has seen it;
  it looks like progress.
- Why it may be insufficient: it assumes the drop-off is confusion, and adds *more*
  steps to a flow people already abandon. It optimizes the thing that may be the
  problem.

## 2. Constraint frame

- Hard constraints: the tool genuinely needs an API key and one config file to work.
- Soft preferences: "onboarding should feel guided" (movable — it could feel like
  nothing at all).
- Non-goals: not trying to increase signups, only completion.
- Forbidden shortcuts: fake "you're almost done!" progress; dark-pattern nags.

## 3. Assumption inventory

- A1 — drop-off is caused by confusion (UX) — kind: UX
- A2 — onboarding is a phase the user must complete before value (structural)
- A3 — setup must happen on the user's machine, by the user (technical)
- A4 — success = user finishes setup (evaluation)

## 4. Mutation passes (four operators, different assumptions)

- K-001 — **Subtraction** on A2: remove the onboarding phase; ship a zero-config
  hosted sandbox that already works, and let setup happen *after* the user has felt
  value. Broken assumption: A2. Mechanism: delete the "complete before value" gate.
  Expected gain: value precedes effort, so effort feels worth it. Failure mode:
  sandbox diverges from real local behavior.
- K-002 — **Transfer** on A3 (from CI/CD): treat setup as a generated artifact —
  detect the user's stack and emit a ready-made config + key-injection script, like a
  scaffolding tool. Broken assumption: A3. Mechanism: import codegen from
  project-bootstrap tooling. Expected gain: the user runs one command instead of
  following ten steps. Failure mode: stack detection is wrong on unusual setups.
- K-003 — **Inversion** on A1: assume drop-off is *boredom*, not confusion; make
  setup produce something immediately shareable (a live status badge / first trace)
  so finishing is rewarded, not just completed. Broken assumption: A1. Mechanism:
  invert "reduce friction" into "add payoff." Expected gain: finishing carries an
  immediate, visible payoff, so completion becomes self-rewarding. Failure mode:
  payoff feels gimmicky.
- K-004 — **Temporal shift** on A4: redefine success as time-to-first-real-use, not
  setup completion; let users do real work with a temporary key and reconcile full
  setup in the background. Broken assumption: A4. Mechanism: move setup after first
  use. Expected gain: users reach real value without blocking on full setup, so
  completion pressure disappears. Failure mode: temporary-key sprawl / security
  review needed.

## 5. Novelty filter

- K-001 zero-config sandbox: `recombination` (common in SaaS, less so for local dev
  tools).
- K-002 generated config: `recombination` (scaffolding is known; applying it to
  onboarding is the twist).
- K-003 shareable-payoff setup: `locally novel (unprobed)` for this category — its
  kill-probe (P-002) is designed below but has not run yet.
- K-004 success = time-to-first-use: `genuinely uncertain` — depends on whether a
  temporary-key flow is even allowed by the security model.

No candidate is self-rated as broadly original; a general-novelty claim would need a
prior-art search via `quaere-grounding`.

## 6. Probe design (top candidates)

- P-001 for K-001: ship the hosted sandbox to 5% of new users; **success signal** =
  real local-setup completion rises vs control; **kill signal** = completion of
  *real* local setup does not rise vs control (sandbox just delays the same
  drop-off). Cost: one sandbox env. Decision-changing evidence: local-setup
  completion rate at 7 days.
- P-002 for K-003: add a shareable first-trace to the existing wizard for a cohort;
  **success signal** = setup completion rises in the badge cohort; **kill signal** =
  no change in completion, or shares but still no setup finish. Cost: one feature
  flag. Decision-changing evidence: completion delta between badge cohort and
  control.

## 7. Handoff

```
Handoff
- From skill: quaere-invention
- Blocking question: which candidate actually moves local-setup completion, and is K-004's temporary-key flow allowed?
- Confirmed inputs: K-001 and K-003 have kill-probes and fit the hard constraints — ready to test.
- Inconclusive inputs: K-004 (genuinely uncertain — security model unknown); K-002 (recombination, untested).
- Required next skill: quaere-evidence (run P-001 / P-002 as disconfirming probes); quaere-grounding for K-004's temporary-key security question.
- Stop condition: a candidate whose kill-probe ran and did not kill it, before any build.
```
