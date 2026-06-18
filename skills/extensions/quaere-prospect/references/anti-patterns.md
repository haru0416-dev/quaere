# Anti-patterns: how an origination pass collapses into a wishlist

Read this when prospect output starts to feel like a feature list rather than
grounded, checked opportunities. Each anti-pattern is the failure the Iron Law
and the reality gate exist to stop.

## Proposing what already exists

The model suggests a capability the system already has because it never looked.

- **Tell:** no Step 4 search was run; the proposal restates the product's tagline.
- **Fix:** grep/read for the capability before calling it absent. If it exists,
  the opportunity is at most "improve existing", labeled `already covered` for
  the new-build framing.

## No beneficiary

An opportunity stated as a capability with nobody named who is blocked.

- **Tell:** "add X" with no "for whom" and no job-to-be-done.
- **Fix:** kill it in Step 3, or name the specific beneficiary and the job. No
  beneficiary → `wishlist`.

## Assumed demand dressed as evidence

"Users want this" with no issue, signal, or segment behind it.

- **Tell:** the Demand line says `evidenced` but cites nothing checkable.
- **Fix:** downgrade to `assumed` in the reality gate; design a validation probe
  (Step 5) instead of asserting the demand.

## Self-rated importance (hype)

"This is a game-changer / must-have / huge opportunity."

- **Tell:** adjectives rating the opportunity's value instead of labeling its
  evidence state.
- **Fix:** forbidden. Use the four labels only. A market-size or willingness-to-pay
  claim is a `quaere-grounding` task, not a self-assessment.

## Ignoring stated non-goals

Proposing something the project has explicitly decided against.

- **Tell:** the proposal contradicts a README/ADR non-goal nobody re-read.
- **Fix:** survey non-goals in Step 1; a stated non-goal is `already covered`
  unless the user is reopening the decision.

## Volume over verification

Twenty ideas, none checked, presented as a brainstorm.

- **Tell:** the count is high, the reality-gate column is empty.
- **Fix:** output is proportional to *verified* opportunities. Three checked gaps
  beat twenty unchecked ones. Loop back to survey more terrain rather than pad.

## Inventing the problem to justify the build

Reverse-engineering a need so a wanted feature looks necessary.

- **Tell:** the gap only exists if you accept the solution first.
- **Fix:** the gap must stand on its own beneficiary and evidence before any
  solution is named. If it cannot, it is `wishlist`.

## Solving instead of originating

Jumping to *how* to build the chosen thing.

- **Tell:** the output is an implementation plan, not an opportunity set.
- **Fix:** prospect ends at grounded opportunities with probes. The *how* is
  `quaere-invention` (non-obvious approach) or `quaere-execution` / `plan`
  (chosen and authorized). Hand off; do not build.
