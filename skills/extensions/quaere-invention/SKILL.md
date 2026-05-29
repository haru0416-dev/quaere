---
name: quaere-invention
description: This skill should be used whenever the user asks for a non-obvious approach, an alternative architecture, a research direction, a product or monetization idea, an agent-skill design, or any "not just the obvious solution" / "発想を広げたい" / "普通じゃない解法" request where the agent is likely to converge on the first average answer. It forces the agent to name the default basin it is escaping, break the assumptions that make that default feel inevitable through structured mutation passes, classify each candidate's novelty honestly, and design a kill-probe before promoting any idea — so divergence does not collapse into hype. Trigger when settling on the obvious solution too early would be the failure.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, and git access.
license: MIT
---

# Invention Probe

## Iron Law

**No idea is promoted as novel without naming four things: the default basin it escapes, the assumption it breaks, the mechanism of the break, and the smallest probe that could disconfirm it. An idea that cannot name all four is `recombination` at best — not invention.**

This is not a creativity ritual. Asked for something new, a model regresses toward the mean of its training distribution and dresses the common answer in impressive-sounding language; empirically, LLM assistance even homogenizes ideas across different users *(Anderson, Shah & Kreminski 2024 — arXiv:2402.01536)*. "Novel-sounding" is also not the same as good: creativity evaluations find novelty correlates weakly or negatively with quality and diversity, so it must be scored as its own axis *(CreativityPrism — Hou et al. 2025, arXiv:2510.20091)*. The gate changes the evaluation axis from *does this sound impressive* to *which specific default did this leave, and can it be killed*. Divergence without the kill-probe is just confident averaging; the probe is what separates an invention from a nicer-sounding default. Full research basis: `references/research-basis.md`.

## When to use

- The user wants a non-obvious approach, alternative architecture, or design the obvious path does not reach.
- Research directions, product ideas, monetization paths, or agent-skill designs are being generated before a plan is committed.
- The work is at risk of converging on the first plausible answer ("settling too early").
- The user explicitly asks to widen the option space, escape the obvious, or break out of an approach that feels stuck.

## When NOT to use

- Factual lookup or current SDK/API/CLI behavior; use `quaere-grounding`.
- A small implementation edit, or a plan that is already chosen and just needs building; use `quaere-execution`.
- A bug whose cause is not yet understood; use `quaere-evidence` — do not "invent" around an unknown cause.
- Cases where the obvious answer is correct and the only cost is wanting it to look clever. Inventing here adds risk, not value.

## Handoff triggers (which skill comes after this one)

Invention ends at a small set of candidates with kill-probes, not at a built thing. Hand off when the next step changes discipline:

- A surviving candidate needs current external facts (does this library/API/pattern actually exist or behave this way) → `quaere-grounding`.
- A candidate needs to be tested or disconfirmed as a claim before commitment → `quaere-evidence` (run the kill-probe there).
- A candidate is chosen and authorized to build → `quaere-execution`.
- No candidate is testable yet → stop and report the option space and what evidence would unlock a decision; do not build.

The standard handoff payload (Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is documented at the end of this file under "Handoff to other skills".

## Core procedure

Run the steps in order. Each step's output is named so the next step (and any reviewer) can audit it. Keep it tight — output length should match the number of live candidates, not an imagined brainstorming quota.

### 1. Default basin

State the boring answer the model would produce by default. Naming it is what makes "escaping it" auditable later.

- Default answer:
- Why it is attractive (why the model lands here):
- Why it may be insufficient:

### 2. Constraint frame

Separate what cannot move from what only feels fixed.

- Hard constraints (real, externally imposed):
- Soft preferences (movable, often mistaken for hard):
- Non-goals:
- Forbidden shortcuts (cheats that would game the goal):

### 3. Assumption inventory

List the assumptions that make the default feel inevitable. Each is a candidate to break in step 4. Tag each with its kind, because different kinds break differently.

- A1 — <assumption> — kind: structural | economic | UX | technical | social | evaluation
- A2 — ...
- A3 — ...

### 4. Mutation passes

Generate candidates by forcing a named mechanism against a named assumption. Use **at least four** different operators. The full operator catalog with worked mini-examples is in `references/mutation-passes.md`; the operators are:

- **Inversion** — make the opposite of the default useful.
- **Subtraction** — remove a part assumed necessary.
- **Transfer** — import a structure from another domain.
- **Recomposition** — split the system and reconnect it differently.
- **Constraint shift** — optimize a different bottleneck.
- **Adversarial design** — assume the obvious solution will be gamed.
- **Temporal shift** — move work earlier, later, or into a background loop.

Each candidate must name:

- broken assumption (by ID from step 3)
- mechanism (which operator, and how)
- expected gain
- likely failure mode

### 5. Novelty filter

Classify every candidate. The label is a finding, not a compliment. Do not oversell `recombination` as invention.

- `known pattern` — already a named, common solution.
- `recombination` — a new mix of known parts.
- `locally novel` — likely new for this context, not in general.
- `genuinely uncertain` — cannot tell if it exists; needs grounding.
- `incoherent` — does not actually hold together; drop it.

**Forbidden:** asserting an idea is "truly novel", "groundbreaking", "revolutionary", or otherwise self-rating its originality. Use the five labels only. If you want to claim general novelty, that is a `quaere-grounding` task (prior-art search), not a self-assessment.

### 6. Probe design

For the best 1–3 candidates, define the smallest test that could kill the idea — not confirm it.

- Probe:
- Success signal:
- Kill signal:
- Cost:
- What evidence would change the decision:

A candidate with no kill-probe is not ready to promote; mark it `genuinely uncertain` and hand off to grounding/evidence.

## Output format

```text
Invention probe
- Default basin: <default answer + why attractive + why insufficient>
- Constraints: hard / soft / non-goals / forbidden shortcuts
- Assumptions: A1..An with kinds

Candidates
- C-001: <one line>
  Broken assumption: <A-id>
  Mechanism: <operator + how>
  Expected gain: <...>
  Failure mode: <...>
  Novelty: known pattern | recombination | locally novel | genuinely uncertain | incoherent
- C-002: ...

Probes (top 1-3)
- P-001 for C-00x: Probe / Success / Kill / Cost / Decision-changing evidence

Handoff
- Surviving candidates: <ids>
- Required next skill: <quaere-grounding | quaere-evidence | quaere-execution | none yet>
- Stop condition: <what the next skill must return>
```

## Common drift modes and anti-patterns

The recurring ways a divergence skill collapses back into hype — overselling recombination, generating volume instead of mechanism, skipping the kill-probe, self-rating novelty — are in `references/anti-patterns.md`. Read it when output starts to feel impressive rather than auditable.

## Worked example

A full invention pass on a concrete prompt (default basin → assumptions → four mutation passes → novelty labels → kill-probe → handoff) is in `references/worked-example.md`. Read it when the step outputs feel abstract.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-invention
- Blocking question: <what cannot be decided by generating options alone>
- Confirmed inputs: <surviving candidates with kill-probes — safe to evaluate next>
- Inconclusive inputs: <candidates marked genuinely uncertain or unprobed — not safe to commit>
- Required next skill: <quaere-grounding | quaere-evidence | quaere-execution>
- Stop condition: <what the next skill must return before a candidate is committed>
```

- A surviving candidate depends on whether an external pattern/library/API actually exists or behaves as assumed → `quaere-grounding` with the candidate and the unconfirmed external claim.
- A candidate is a testable hypothesis that should be disconfirmed before commitment → `quaere-evidence` with the candidate as a claim and its kill-probe as the disconfirming probe.
- A candidate is chosen and building is authorized → `quaere-execution` with the candidate, the constraints from step 2, and the kill-probe as a verification.

Invention ends at options with kill-probes. It does not pick the winner for the user, and it does not build. Naming the option space and the probes is the deliverable.

## Stop condition

The skill is complete when:

- The default basin is named (step 1).
- At least four mutation passes produced candidates, each naming broken assumption / mechanism / gain / failure mode.
- Every candidate carries a novelty label from the fixed five, with no self-rated "truly novel" language.
- The top 1–3 candidates each have a kill-probe.
- A handoff or an explicit "not testable yet" stop is stated.

Do not keep generating once the option space is covered and the survivors have probes. More candidates past that point is volume, not invention.
