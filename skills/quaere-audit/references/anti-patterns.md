# Common drift modes for security audit

Audit-side rationalizations that look like findings but skip required gates (reachability, attacker control, guard absence, impact, false-positive check). See `../SKILL.md` for the procedure each entry below is contrasting against.


| Rationalization | What's actually happening |
| --- | --- |
| "This dangerous function is present, so it's a vulnerability." | Dangerous APIs are leads. Prove attacker source, boundary crossing, failed guard/sink, and impact. |
| "It's OWASP Top 10 / CWE, so it's confirmed." | Taxonomy is classification, not proof. Evidence and gates decide the finding. |
| "The PoC would be convincing, so I'll run it." | Unauthorized or production-like PoCs can cause harm. Use safe substitutes or ask. |
| "This is only Triage, so I can mark it confirmed quickly." | Triage still requires four conditions. High-blast-radius findings promote to Standard. |
| "No guard in this function means no guard exists." | Guards often live in middleware, callers, decoders, DB constraints, protocol layers, or deployment config. Check compensating controls. |
| "A scanner reported it." | Tool output is a candidate. Manual reachability, attacker control, impact, and false-positive gates still apply. |
| "Severity is obvious." | Severity depends on exploitability, privileges, interaction, exposure, blast radius, and environment. State the basis. |
| "I covered the main route." | Alternate entrypoints, background jobs, imports, deserializers, and migrations often bypass primary-path guards. Name uncovered risk if not checked. |

