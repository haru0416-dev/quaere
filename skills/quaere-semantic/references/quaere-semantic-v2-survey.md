# Semantic Review v2 Survey

Survey date: 2026-05-08.

Purpose: document the ADR-0003 external survey and quaere-grounding labels behind the v2 rewrite of `skills/quaere-semantic/SKILL.md`. This artifact is retroactive — the convention of recording survey provenance per skill was established later in quaere-evidence v2 and back-applied here for cross-skill consistency. The commit history (commits up to and including `e610ae4`, plus review fixes through `f4f03f8`) is the primary source for what actually shipped.

## Source-quality note

The survey concerns skill-writing patterns and code-comprehension methodology, not version-sensitive SDK/API behavior. Local executable probes were therefore replaced by artifact checks: Anthropic guidance was read against the current docs URLs, public skills were inspected as full SKILL.md files, and academic citations were checked against abstracts and prior knowledge. Single practitioner sources were imported only as `partially confirmed` unless corroborated.

## Anthropic guidance axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Worked examples should follow Input → Output pattern. | confirmed | anthropics/skills `skill-creator/SKILL.md` (current main). | Inline Worked example with Bad (paraphrase) / Good (semantic understanding) contrast using the TokenCache TypeScript fixture. |
| Anti-patterns expressed as rigid `ALWAYS` / `NEVER` are flagged as a yellow flag; reframe as reasoning. | confirmed | Anthropic engineering blog "Equipping agents for the real world with Agent Skills" (Oct 16 2025). | Anti-patterns reframed from prohibition to "X fails because Y" form for all 5 items. |
| Frontmatter `description` should be "pushy" — explicit "use this skill whenever the user…" framing. | confirmed | anthropics/skills `skill-creator`. | Description begins "This skill should be used whenever..." (validator prefix preserved while keeping the pushy intent). |
| Long skills should split variants into `references/<variant>.md` (progressive disclosure). | confirmed | Anthropic engineering blog (Oct 16 2025). | Not yet needed at v2's 232 lines; v2 retained inline structure. Recorded as a future trigger for a 400+ line revision. |
| Cross-skill handoffs have no official Anthropic guidance. | absence | (none located) | Project convention per ADR-0001 retained as an unsanctioned-but-not-invalid extension. |

Representative URLs:

- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

## Public skill ecosystem axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| High-quality discipline skills lead with a 1-line "Iron Law" refusal. | confirmed | obra/superpowers `systematic-debugging`. | Iron Law: No `Why` without one of three certainty markers. Reasoning paragraph attached to satisfy the Anthropic "no rigid ALWAYS" guidance. |
| Common Drift Modes / Rationalizations 2-column table (rationalization → reality). | confirmed | obra/superpowers (multiple), pytorch/pr-review. | `Common drift modes` table with 7 distinct rows. |
| Load-bearing-line philosophy with concrete domain examples. | confirmed | pytorch/pr-review "treat every line as potentially load-bearing". | "Trivial-looking accessors carry the subtlest invariants" framing in Anti-patterns. |
| Bad / Good inline worked example in the SKILL body (not in `references/`). | confirmed | obra/superpowers, pytorch, awesome-skills. | TokenCache TypeScript fixture, Bad output paraphrase / Good output semantic with operational test verdict. |
| Time-budgeted depth tiers with concrete time signals. | confirmed | awesome-skills/code-review-skill phased budget (2-3 min / 5-10 min / 10-20 min). | Depth tiers with time hints; subsequently re-anchored to scope (commit `5ed8474`) so the tier signal is unit count, not minutes. |

Meta-finding (corpus convergence): high-quality public skills cluster at 130-300 lines and uniformly carry Iron Law + drift-modes table + inline Bad/Good worked example. v1 of this skill (117 lines) was below the floor and missing all three universal patterns; v2 fills the gap.

Representative URLs:

- https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/pytorch/pytorch/blob/main/.claude/skills/pr-review/SKILL.md
- https://github.com/awesome-skills/code-review-skill/blob/main/SKILL.md

## Domain research axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| High-comprehension readers cross-reference a *program model* (control/operations) with a *domain model* (data flow + problem semantics); single-model readers underperform. | confirmed | Pennington 1987, "Stimulus structures and mental representations in expert comprehension of computer programs", *Cognitive Psychology*. | Split `What` into mechanical (program model) + domain intent. |
| Comprehension is top-down hypothesis-driven; pure bottom-up unit-by-unit sweep is empirically the weaker strategy. | confirmed | Brooks 1983, "Towards a theory of the comprehension of computer programs", *IJMMS*. | Step 0 module hypothesis pre-pass plus the verdict / update rule (refined / refuted handling). |
| Recognizable plan signatures ("beacons") compress historical engineering into recognizable patterns and reveal intent at low cost. | confirmed | Brooks 1983. | Beacon probe added to Probes for `Why`. |
| Comprehension proceeds via inquiry episodes with certainty levels (assertions / conjectures / questions). | confirmed | Letovsky 1986, "Cognitive processes in program comprehension", ESP workshop. | `confident / plausible / UNKNOWN — probe: ...` certainty markers on `Why`. Scoped down from per-field to single-field to control ceremony. |
| The hardest developer questions are about intent and reachability ("why was it done this way", "who calls / affects this"). | confirmed | Sillito, Murphy & De Volder 2008, *IEEE TSE*; LaToza & Myers 2010, *PLATEAU*. | Probe additions: protocol/lifetime/ownership/caller-vs-callee/reachability templates. |
| Backward and forward slicing identify load-bearing code; concerns scatter rather than co-locate. | confirmed | Weiser 1984 (backward); Bergeretti & Carré 1985 (forward); Robillard & Murphy concern graphs. | `Connections` reframed as backward (←) + forward (→) slice with split citations. |
| Industry norm is *partial, pragmatic* comprehension; full per-symbol coverage is the deliberate exception. | confirmed | Maalej, Tiarks, Roehm & Koschke 2014, "On the Comprehension of Program Comprehension", *ACM TOSEM*. | Industry baseline framing positions the skill as the deliberate exception. |
| Understanding survives semantic-preserving rewrites; paraphrase doesn't. | partially confirmed | arXiv 2504.04372 2025 (preprint, not peer-reviewed). | Operational anti-paraphrase test, with explicit caveat that the source is a preprint applied as a working test rather than as authority. |

Representative URLs / citations:

- https://www.sciencedirect.com/science/article/abs/pii/0010028587900076
- https://www.sciencedirect.com/science/article/abs/pii/S0020737383800315
- https://www.sciencedirect.com/science/article/pii/016412128790032X/pdf
- https://link.springer.com/article/10.1007/s11219-006-9216-4
- https://www.semanticscholar.org/paper/Asking-and-Answering-Questions-during-a-Programming-Sillito-Murphy/98cb9e2c4214f0a68bae57e5f5a8d5005fd3f908
- https://dl.acm.org/doi/10.1145/1937117.1937125
- https://www.cse.msu.edu/~cse870/Public/Homework/SS2003/HW5/p439-weiser.pdf
- https://dl.acm.org/doi/10.1145/2622669
- https://arxiv.org/html/2504.04372v2

## Rejected or scoped-down imports

- **Per-field certainty markers everywhere (Letovsky 1986)** — scoped down. Applied to `Why` only to control ceremony.
- **All "when-to-use" info in `description` (Anthropic skill-creator implication)** — rejected. Validator prefix and ecosystem practice both prefer body sections; description has length constraints. Kept the body `When to use` / `When NOT to use` sections.
- **Progressive disclosure to `references/` for depth tiers** — deferred. v2 stays at ~232 lines (within budget); split is the right move only when a future skill exceeds 400 lines.
- **Cross-skill handoffs as Anthropic-blessed convention** — rejected as "Anthropic-blessed". Retained as project convention per ADR-0001.

## Subsequent review fixes

The independent review pass after `e610ae4` produced the following corrections (commits `c907ba5` `76fd172` `5ed8474` `59300fc` `f04daf7` `3c8299f` `f4f03f8`):

- Worked example: off-by-one and non-semantic-preserving rewrite (the example was teaching paraphrase by example).
- Iron Law / Step 1.3 / Output template / Stop condition reconciled to the three-state certainty marker.
- Depth tiers re-anchored from human wall-clock minutes to scope (unit count, slicing breadth).
- Citation precision: forward-slice attribution split off Weiser; Robillard concern graphs added.
- Editing anti-pattern reasoning extended with a comprehension-side mechanism (workflow-only reason was insufficient).
- Handoff payloads symmetrized across all four companion skills.
- Step 1 bound rules (cardinality / boundary / generated-vendored).
- Step 0 verdict and update rule (confirmed / refined / refuted handling for the module hypothesis).

These corrections sharpened the v2 against its own contract; none retracted an imported finding.
