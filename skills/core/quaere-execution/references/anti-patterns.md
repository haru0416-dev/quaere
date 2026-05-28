# Common drift modes for the execution loop

Rationalizations that look like progress but actually fragment the loop. See `../SKILL.md` for the Contract → Plan → Do → Study → Act sequence each entry below is contrasting against.


| Rationalization | What's actually happening |
| --- | --- |
| "I'll just make all the edits, then test once." | The work became one unreviewable blob. Split into units so failures identify the responsible change. |
| "I have two units open at once — I'll close them both at the end." | Two units in flight means a failed check cannot localize to one Reason; the unit boundary disappears. Keep exactly one unit in progress: finish, verify, and review its diff before opening the next. |
| "The broad suite passed, so the bug is fixed." | The targeted behavior may never have been exercised. A broad suite is a regression net, not proof of the changed behavior. |
| "This cleanup is nearby and cheap." | Drive-by changes enlarge review and rollback cost. If it is not required by the current unit, leave it out or make a separate authorized unit. |
| "The reviewer asked for it, so I implemented it." | Review feedback can be ambiguous or wrong. If the claim is unclear, hand it to `quaere-evidence` before coding. |
| "I know the API shape." | Version-sensitive facts must be grounded. Use `quaere-grounding` before coding against SDK/CLI/API behavior. |
| "Tests failed, so I'll try another patch." | That is speculative patch stacking. Reproduce, form a hypothesis, and hand off if cause is unclear. |
| "Commit is part of finishing." | Commit is a side effect that requires explicit authorization; implementation authorization alone is not enough. |
| "No need to inspect the diff; I wrote it." | Self-generated diffs still drift. The final diff review is the check against accidental scope expansion. |

