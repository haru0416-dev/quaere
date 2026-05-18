# Evidence-Gated Review v2 Survey

Survey date: 2026-05-08.

Purpose: document the ADR-0003 external survey and quaere-grounding labels that drove the v2 rewrite of `skills/quaere-evidence/SKILL.md`. Findings below are included only when they change procedure, output format, drift modes, or eval coverage.

## Source-quality note

This survey concerns skill-writing patterns and investigation methodology, not a version-sensitive SDK/API surface. Local executable probes are therefore replaced by artifact checks: retrieved source files were compared against the local skill requirements, and imported claims needed either an official/high-authority source plus lateral corroboration or a peer-reviewed/stable domain source plus a procedure-level implication. Single practitioner sources were used only as `partially confirmed` unless corroborated.

## Anthropic guidance axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Skills use `SKILL.md` with frontmatter plus optional `references/`, `scripts/`, and `assets/`; progressive disclosure keeps details in references when needed. | confirmed | Anthropic Agent Skills overview and best practices; agentskills.io specification; Anthropic engineering blog (2025-10-16). | `references/quaere-evidence-v2-survey.md` rather than overloading the main body with survey details. |
| The frontmatter `description` is the discovery mechanism and should state both what the skill does and when to use it. | confirmed | Anthropic Agent Skills best practices; Claude Help Center custom skills article; anthropics/skills `skill-creator`. | Pushier description with concrete triggers: unclear bugs, PR comments, CI failures, flaky tests, risky/security/database/concurrency/external API changes. |
| Worked examples and explicit sequential workflows improve skill behavior. | confirmed | Anthropic Agent Skills best practices; anthropics/skills `skill-creator`. | Inline Bad/Good worked example and numbered workflow. |
| Rigid all-caps `ALWAYS`/`NEVER` is risky when it lacks reasoning, but strict rules are acceptable when attached to why. | confirmed, nuanced | Anthropic Agent Skills best practices and `skill-creator` writing guidance. | Iron Law with explanatory paragraph instead of a bare prohibition. |

Representative URLs:

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

## Public skill ecosystem axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| High-quality debugging/review skills use a first-principle rule before the workflow. | confirmed | obra/superpowers `systematic-debugging`, `verification-before-completion`; PyTorch `.claude/skills/pr-review`. | Iron Law: no patch/comment/root-cause conclusion without falsifiable claim and disconfirming attempt. |
| Common rationalization or red-flag tables reduce predictable agent drift. | confirmed | obra/superpowers `systematic-debugging`, `verification-before-completion`, `receiving-code-review`. | `Common drift modes` table. |
| Inline Bad/Good examples are common in review/debugging skills and make failure modes concrete. | confirmed | obra/superpowers `receiving-code-review`; PyTorch `bc-guidelines`; Anthropic skill-creator examples. | Worked example contrasting confirmation-first vs evidence-gated investigation. |
| Mature PR review workflows fact-check issues before reporting and include file/symbol, risk, evidence, and fix path. | confirmed | PyTorch `.claude/skills/pr-review`; obra code-reviewer template; Posit critical-code-reviewer. | Review Claim fields and output expectations. |
| Depth tiers/budgets help prevent both under-review and unbounded investigation. | partially confirmed | PyTorch review modes/subagent count; obra failed-fix threshold; Anthropic workflow guidance. | Challenge / Standard / Deep depth control, scoped by risk and investigation size. |

Representative URLs:

- https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md
- https://github.com/pytorch/pytorch/blob/main/.claude/skills/pr-review/SKILL.md
- https://github.com/posit-dev/skills/blob/main/posit-dev/critical-code-reviewer/SKILL.md

## Domain research axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Claims should be falsifiable; attempted refutation is more valuable than accumulating confirmations. | confirmed | Popper via Stanford Encyclopedia of Philosophy; scientific hypothesis-testing references. | Iron Law, falsifier fields, disconfirming probes. |
| Practical review arguments need claim, data, warrant, backing, qualifier, and rebuttal/defeater. | confirmed | Toulmin, *The Uses of Argument*; informal logic references. | Toulmin-style Review Claim template. |
| Confirmation bias is a robust cognitive failure mode; investigators seek/interprete evidence in favor of existing beliefs. | confirmed | Nickerson 1998, *Review of General Psychology*. | Mandatory disconfirming probe and drift modes around supporting clues. |
| RCA tools such as 5 Whys and Ishikawa are useful for generating candidate causes but do not prove them. | partially confirmed | iSixSigma practitioner sources; corroborated by fault-tree methodology and debugging literature. | RCA note: hypotheses need validated causal steps; no forced single root cause. |
| Fault Tree Analysis supports modeling multi-factor failures as AND/OR preconditions. | confirmed | NRC Fault Tree Handbook NUREG-0492. | Guardrail against forcing a single root cause; complex failures may need precondition trees. |
| Delta debugging/minimization treats debugging as hypothesis testing over pass/fail deltas and cause-effect chains. | confirmed | Zeller delta debugging work and *Why Programs Fail*. | Probe guidance to minimize reproductions/deltas before asserting cause. |
| Good bug reports record symptoms, environment, recent changes, observed vs expected, and reproduction before guesses. | partially confirmed | Eric Raymond bug-reporting guidance; Spinellis debugging/code-reading guidance. | Step 0 symptom chronology. |
| Bayesian belief updating frames confidence as evidence-sensitive and discriminating between alternatives. | confirmed | Stanford Encyclopedia of Philosophy on Bayes' theorem; scientific method references. | `Prefer discriminating evidence over volume` and confidence/qualifier fields. |

Representative URLs / citations:

- https://plato.stanford.edu/entries/popper/
- https://doi.org/10.1017/CBO9780511840005
- https://doi.org/10.1037/1089-2680.2.2.175
- https://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/sr0492/
- https://www.st.cs.uni-saarland.de/dd/
- https://www.spinellis.gr/debugging/
- http://www.catb.org/esr/faqs/smart-questions.html

## Rejected or scoped-down imports

- **Single-root-cause framing** — rejected. RCA chains are useful, but fault trees and flaky/concurrency failures often require multiple contributing factors.
- **Full academic apparatus in every output** — rejected. The skill imports falsifiability, Toulmin fields, and discriminating probes, but does not require citations in normal user output.
- **Persistent state files for every investigation** — rejected. Ecosystem examples use durable ledgers for larger work, but the v2 skill keeps challenge-pass mode lightweight.
- **Patch automatically after confirmation** — rejected after review. Confirmation proves actionability; editing still requires implementation authorization or handoff to `quaere-execution`.
