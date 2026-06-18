# Gap taxonomy

The six gap kinds prospect inventories (Step 2), how to find each, how the
reality gate (Step 4) checks each, and how each silently degrades into a
`wishlist` item. Tag every candidate gap with exactly one kind — different kinds
are verified and validated differently.

## Contents

- [How to read this](#how-to-read-this)
- [capability](#capability)
- [UX-friction](#ux-friction)
- [reliability](#reliability)
- [reach (new users)](#reach-new-users)
- [integration](#integration)
- [business / monetization](#business--monetization)
- [Cross-kind rule](#cross-kind-rule)

## How to read this

Each kind lists: **Signal** (where the gap shows up), **Reality check** (what the
Step 4 gate must confirm before the opportunity is presented), and **Wishlist
trap** (the generic version that fails the Iron Law). One term per concept: a
"gap" is a missing or weak capability tied to a beneficiary; without a beneficiary
it is a `wishlist` item, not a gap.

## capability

A job the user wants done that the system cannot do at all.

- **Signal:** feature requests, "can it…" questions, TODO/FIXME naming the missing
  function, competitors that do it.
- **Reality check:** grep/read the codebase for a partial or hidden implementation
  before calling it absent; check non-goals for a deliberate exclusion.
- **Wishlist trap:** "add export / add an API / add a plugin system" with no named
  user who is blocked and no evidence anyone asked.

## UX-friction

The job is doable but costs the user too much — steps, confusion, manual work.

- **Signal:** support questions, repeated manual workarounds, multi-step flows in
  the code, "why is this so hard" feedback.
- **Reality check:** trace the actual current flow in the code; confirm the
  friction exists rather than assuming it from the feature's name.
- **Wishlist trap:** "improve the UX / make it more intuitive" with no specific
  step measured as costly.

## reliability

The capability exists but fails, flakes, or is too slow to trust.

- **Signal:** bug reports, flaky tests, error logs, latency complaints, retries in
  the code.
- **Reality check:** find the actual failure (issue, log, reproducing test) — do
  not propose hardening something with no evidence of breakage. (If the cause is
  unknown, this is a `quaere-evidence` task, not a prospect one.)
- **Wishlist trap:** "add more tests / make it more robust / add monitoring" with
  no failure pointed to.

## reach (new users)

The system serves its current users but a named adjacent segment cannot adopt it.

- **Signal:** drop-off at onboarding, missing platform/runtime/locale, a segment
  that asks but bounces.
- **Reality check:** name the specific segment and the concrete blocker (no Windows
  build, no SSO, English-only); confirm the blocker is real, not assumed.
- **Wishlist trap:** "support more platforms / add i18n / grow the audience" with
  no segment named and no blocker located.

## integration

The system would be more valuable connected to a tool the beneficiary already uses.

- **Signal:** "does it work with X", manual import/export between tools, a common
  partner in the ecosystem.
- **Reality check:** confirm the partner tool and its interface exist and behave as
  assumed — this often needs `quaere-grounding` for the external API.
- **Wishlist trap:** "integrate with everything / add webhooks / add a marketplace"
  with no specific partner and no user who needs that link.

## business / monetization

A path to capture or sustain value the current shape leaves on the table.

- **Signal:** usage that exceeds free-tier intent, enterprise asks, manual billing,
  a feature users would pay to keep.
- **Reality check:** confirm the willingness-to-pay signal is real (an ask, a
  contract, churn data) — assumed willingness is the easiest thing to fabricate.
- **Wishlist trap:** "add a paid tier / monetize / add enterprise features" with no
  evidence anyone will pay.

## Cross-kind rule

A candidate that fits no kind, or that needs the kind label invented to justify
it, is almost always a `wishlist` item. The kind is a finding about *where the
demand lives*, not a slot to fill. If two kinds seem to apply, the gap is probably
two opportunities — split them so each carries its own beneficiary and probe.
