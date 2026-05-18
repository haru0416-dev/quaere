# Execution Loop v2 Survey

Survey date: 2026-05-08.

Purpose: document the ADR-0003 external survey and labels behind the v2 rewrite of `skills/quaere-execution/SKILL.md`.

## Anthropic guidance axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Claude Code guidance recommends Explore → Plan → Implement → Commit and separates planning/exploration from editing. | confirmed | Claude Code best practices, permission modes, how Claude Code works. | Contract and planning gates before non-trivial edits. |
| Agentic work should gather context, take action, verify results, and repeat. | confirmed | Claude Code "how it works" and common workflows. | Plan → Do → Study → Act loop with targeted checks and fix loop. |
| Verification is one of the highest-leverage practices; give the agent commands/tests to run. | confirmed | Claude Code best practices and common workflows. | Fresh verification evidence required before success claims. |
| Checklists/todos are useful for complex workflows but should not be mandatory for trivial edits. | partially confirmed | Claude Code tools reference; Agent Skills best practices. | Depth control: micro loop vs standard checklist/todo loop. |
| Commit happens when the user asks; side-effect workflows need explicit permission. | partially confirmed | Claude Code workflows and skills side-effect guidance. | Commit/push discipline: implementation authorization is distinct from commit/push authorization. |
| Skill descriptions drive discovery; worked examples and progressive disclosure improve skill behavior. | confirmed | Agent Skills best practices, skill-creator. | Pushy frontmatter description, inline worked example, and this reference file. |

Representative URLs:

- https://docs.anthropic.com/en/docs/claude-code/best-practices
- https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works
- https://docs.anthropic.com/en/docs/claude-code/permission-modes
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

## Public skill ecosystem axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Discipline skills use an Iron Law to prevent the main failure mode. | confirmed | obra/superpowers TDD, verification-before-completion, systematic-debugging. | Iron Law for success claims: fresh verification + reviewed scoped diff. |
| Rationalization tables / red flags are common anti-drift mechanisms. | confirmed | obra/superpowers verification, debugging, TDD, writing-skills. | `Common drift modes` table. |
| Verification-before-completion gates success claims with fresh evidence. | confirmed | obra/superpowers `verification-before-completion`. | No "done/fixed/passes" based on stale or assumed results. |
| Review/fix loops re-run the same review type until issues are resolved. | confirmed | obra/superpowers subagent-driven-development; PyTorch PR review; Posit test author/review skills. | Fix loop requires re-check and diff review after each correction. |
| Commit discipline is repo-dependent; some workflows commit frequently, others explicitly do not auto-commit. | confirmed | obra planning/execution skills; Posit `author-vitest-tests`. | Commit only when user/repo policy authorizes. |
| Public implementation workflows emphasize plan sanity, exact task execution, stopping on blockers, and avoiding improvisation. | confirmed | obra/superpowers executing-plans and receiving-code-review. | Source-of-truth contract and stop/handoff rules. |

Representative URLs:

- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md
- https://github.com/pytorch/pytorch/blob/main/.claude/skills/pr-review/SKILL.md
- https://github.com/posit-dev/positron/blob/main/.claude/skills/author-vitest-tests/SKILL.md

## Domain research axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| PDSA/PDCA is a learning loop: plan with a theory/prediction, do, study observed results, act. | confirmed | Deming Institute PDSA. | Contract → Plan with Prediction → Study checks/diff → Act. |
| Fast automated feedback, CI, and regression testing improve software change reliability. | confirmed | Fowler CI; DORA CI/CD and trunk-based development research. | Targeted checks first, broader final gate second, stop on red. |
| TDD quality benefits are generally positive but context/productivity effects vary. | partially confirmed | Rafique & Misic 2013; Bissi et al. 2016; Nagappan et al. 2008. | Require regression/behavior tests when feasible, but do not require dogmatic TDD for every edit. |
| Modern code review improves maintainability, knowledge transfer, consistency, and defect outcomes. | confirmed | Bacchelli & Bird 2013; Sadowski et al. 2018; McIntosh et al. 2014; Rigby & Bird 2013. | Self-review diff before handoff; use reviewer/subagent for risky changes. |
| Small, self-contained changes are easier to review, merge, and roll back. | confirmed | Google Engineering Practices small CLs; DORA trunk-based development. | Smallest reviewable unit rule and split refactor from behavior change. |
| Checklists help when they create deliberate verification pauses, not rote compliance. | confirmed outside software / partially confirmed in software | WHO surgical checklist; FAA checklist discipline; Agent Skills checklist guidance. | Short observable gates rather than vague reminders. |
| Debugging benefits from reproduce/minimize/hypothesize/test before patching. | partially confirmed | Zeller delta debugging; systematic debugging literature. | Verification failure with unclear cause hands off to quaere-evidence instead of speculative patch stacking. |

Representative URLs / citations:

- https://deming.org/explore/pdsa/
- https://martinfowler.com/articles/continuousIntegration.html
- https://dora.dev/research/
- https://google.github.io/eng-practices/review/developer/small-cls.html
- https://doi.org/10.1109/ICSE.2013.6606617
- https://doi.org/10.1145/3183519.3183525
- https://www.st.cs.uni-saarland.de/dd/

## Rejected or scoped-down imports

- **TDD for every change** — scoped down. Evidence supports tests/regression checks, but strict TDD is context-dependent.
- **Auto-commit as completion** — rejected. Ecosystem practice conflicts; explicit user authorization wins.
- **Persistent logs for every task** — rejected. Micro loop remains lightweight; durable logs are for large/risky work.
- **Subagent review for every edit** — scoped down. Fresh review is recommended for risky/large changes, not trivial local edits.
