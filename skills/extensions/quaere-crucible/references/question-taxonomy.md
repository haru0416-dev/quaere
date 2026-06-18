# Grilling question taxonomy

The question types crucible uses to attack a load-bearing claim. Each names the
weakness it exposes and a usable phrasing. Two types are **mandatory** on every
load-bearing claim (Falsifier, Alternative hypothesis); the rest are drawn on by
target type. Cap the set to a few high-quality challenges per claim — demanding
an exhaustive list backfires (low fluency is misread as "there are no problems").

## Contents

- [How to use](#how-to-use)
- [Mandatory: Falsifier / kill-criterion](#mandatory-falsifier--kill-criterion)
- [Mandatory: Alternative hypothesis](#mandatory-alternative-hypothesis)
- [Claim extraction](#claim-extraction)
- [Disconfirming probe](#disconfirming-probe)
- [Assumption / consider-the-opposite](#assumption--consider-the-opposite)
- [Warrant / inferential bridge](#warrant--inferential-bridge)
- [Steelmanned rebuttal](#steelmanned-rebuttal)
- [Outside-view / base-rate](#outside-view--base-rate)
- [Premortem / consequence](#premortem--consequence)
- [Meta / standard-of-proof](#meta--standard-of-proof)
- [Target-type weighting](#target-type-weighting)

## How to use

Grill the most-decisive claim first, one sharp question at a time, after stating
the agent's own recommended counter-position (the anti-stall move). Grade each
answer with the flip rule: `survived` only on new evidence or a defended
rebuttal, never on confident-but-unverified pushback.

## Mandatory: Falsifier / kill-criterion

- **Exposes:** a belief held as fact with no possible disconfirming observation — the deepest weakness, since nothing can update it.
- **Ask:** "Name the concrete observation that would make you abandon this. If the honest answer is 'nothing', this is faith, not reasoning, and I log it as an unresolved gap rather than bless it."

## Mandatory: Alternative hypothesis

- **Exposes:** premature convergence on one cause or design when several fit the same facts (the five-whys single-path trap).
- **Ask:** "Name two other explanations consistent with the same evidence, and the one probe that distinguishes your story from theirs — without it, your root cause is just the first one you liked."

## Claim extraction

- **Exposes:** a target too vague to be true or false — unfalsifiable mush. You cannot grill a fog.
- **Ask:** "State the single load-bearing claim in one disputable sentence — what exactly am I being asked to bless, such that I could in principle show it false?"

## Disconfirming probe

- **Exposes:** confirmation bias — only supporting checks were run; the claim was never attacked. (Prefer this whenever an executed test exists; if it cannot run in conversation, hand off to `quaere-evidence`.)
- **Ask:** "What is the smallest, cheapest test whose FAILURE would kill this claim — and have you run it, or only the checks you expected to pass?"

## Assumption / consider-the-opposite

- **Exposes:** load-bearing premises taken for granted that, if false, collapse the structure; inherited "of course X" never verified. The single best-supported debiasing primitive.
- **Ask:** "List the two or three assumptions this rests on; for the most load-bearing one, construct the strongest case it is FALSE with concrete evidence — and say whether you verified it or just inherited it."

## Warrant / inferential bridge

- **Exposes:** the hidden leap from evidence to conclusion — where most arguments silently break; grounds can be true yet not license the claim.
- **Ask:** "Spell out the unstated rule that lets THIS evidence imply THAT conclusion; now give me one case where the evidence holds but the rule fails."

## Steelmanned rebuttal

- **Exposes:** a position that never survived its strongest opponent — only strawman objections, if any, were considered.
- **Ask:** "State the STRONGEST argument a competent engineer who disagrees would make, in its best form, not a strawman — then show precisely why it loses, or concede it does not."

## Outside-view / base-rate

- **Exposes:** inside-view optimism — accepting the plan's internal self-narrative instead of the distribution of similar past outcomes.
- **Ask:** "Set this diff's logic aside: how often do refactors / migrations / claims of THIS shape actually hold or regress in this codebase? Cite prior similar PRs or incidents, not just this plan's reasoning."

## Premortem / consequence

- **Exposes:** unexamined downstream and second-order failure modes — local correctness with no system-level reckoning.
- **Ask:** "Assume we shipped this and six months later it failed badly — write the post-mortem's first sentence. What did this decision cause that we are not pricing in now?"

## Meta / standard-of-proof

- **Exposes:** effort misallocation — over-rigor on the trivial, under-rigor on the load-bearing, or grilling the easy claim to avoid the decisive one.
- **Ask:** "Is this even the claim that decides the outcome, and is the evidence bar I am applying the right one — or am I grilling the peripheral part to feel rigorous while the load-bearing claim goes unchallenged?"

## Target-type weighting

The two mandatory types fire on every load-bearing claim; weight the rest by target:

- **Plan / decision** → premortem + assumption + outside-view.
- **Claim / root cause** → claim-extraction + warrant + disconfirming probe.
- **PR / diff** → scope + consistency + steelmanned rebuttal + disconfirming probe.
- **The agent's own plan (self-target)** → steelman + alternative, with intensity cranked up — an agent under-attacks itself, so the standard of proof must be raised, not lowered.
