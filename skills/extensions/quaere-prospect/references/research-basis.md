# Research basis

Why prospect gates origination the way it does. The skill makes a falsifiable
claim — that asked "what to build", an LLM defaults to an ungrounded wishlist —
and structures the workflow to counter it.

## The grounded failure mode

Direction-space ideation ("what should exist") has the same regression-to-the-mean
problem as solution-space ideation ("how to solve it"). The model fills the
request with the highest-prior, most generic answers available in its training
distribution: the suggestions that are true of *most* software (more tests, more
CI, more docs, a dashboard, dark mode) rather than the gap specific to *this*
system and *this* user.

- **Homogenization.** LLM assistance converges the ideas different users produce,
  reducing collective diversity — measured for ideation broadly
  *(Anderson, Shah & Kreminski 2024 — arXiv:2402.01536)*. Applied to "what to
  build", this is exactly the ungrounded-wishlist pattern: the same handful of
  generic directions surface regardless of the actual codebase.

This citation is reused from ADR-0011, where its arXiv ID was fetched and
verified directly. prospect does not add unverified citations; the rest of the
case rests on the observable wishlist behavior above, which any user can
reproduce by asking a fresh agent "what should I add to this repo" and noting how
little of the answer depends on the repo.

## Why the four-part Iron Law

Each clause removes one degree of freedom the wishlist exploits:

- **Verified gap** defeats "propose what already exists" and "ignore non-goals" —
  the proposal must survive a check against the real system.
- **Beneficiary + job** defeats the capability-with-no-one-blocked wishlist.
- **Demand evidence (evidenced vs. assumed)** defeats assumption dressed as
  knowledge, and routes unproven demand to a probe instead of a claim.
- **Validation probe** defeats commitment-before-evidence: the cheapest test that
  could kill the idea runs before any build.

## Why a fixed label set

Self-rated importance ("game-changing") is unfalsifiable and is what a wishlist
reaches for to sound like strategy. Replacing it with four findings
(`verified gap | assumed gap | already covered | wishlist`) makes the evaluation
axis *evidence state*, not *enthusiasm* — the same move `quaere-invention` makes
with its novelty labels and `quaere-naming` makes with `slop`. A general
market-size or demand claim is punted to `quaere-grounding`, not asserted here.

## Boundary with invention

prospect and invention attack adjacent failures. invention assumes the problem is
chosen and gates against *settling on the average solution*. prospect runs one
step earlier and gates against *manufacturing the average problem*. Keeping them
separate keeps each gate sharp; the handoff (`prospect → invention`) chains them
when both the WHAT and the HOW are hard.
