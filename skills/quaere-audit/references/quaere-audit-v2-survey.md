# Security Audit Loop v2 Survey

Survey date: 2026-05-08.

Purpose: document the ADR-0003 external survey and labels behind the v2 rewrite of `skills/quaere-audit/SKILL.md`.

Grounding convention: `confirmed` rows either came from official/current sources for the relevant domain (Anthropic docs, OWASP/NIST/FIRST/MITRE/CISA/HackerOne standards) or from at least two independently inspected public skill artifacts showing the same procedural pattern. `partially confirmed` rows are useful but narrower, safety-caveated, or not directly security-audit-specific. Default-branch public repos are dated 2026-05-08 snapshots and should be rechecked before treating ecosystem patterns as current.

## Anthropic guidance axis

| Finding | Label | Source quality / version fit | Sources | Imported as |
| --- | --- | --- | --- | --- |
| Agent Skills use progressive disclosure; details should move into one-level references when needed. | confirmed | Official Anthropic docs, current live docs as of survey date. | Anthropic Agent Skills overview/best practices; engineering blog. | Main skill coordinates; references hold property and false-positive detail. |
| Skill descriptions drive activation and should include concrete triggers. | confirmed | Official Anthropic/Claude Code docs, current live docs. | Agent Skills best practices; Claude Code skills docs. | Description names audit, bug bounty, threat model, auth/authz, CVE/advisory, exploitability. |
| Worked examples and validation loops improve behavior. | confirmed | Official Anthropic skill-authoring guidance. | Agent Skills best practices. | Inline Bad/Good tenant-isolation worked example. |
| Subagents/fresh review help large or security-sensitive reviews. | confirmed | Official Claude Code docs; Ultrareview is research-preview caveated but corroborated by Code Review docs. | Claude Code subagents, Code Review, Ultrareview docs. | Coordination with quaere-semantic, quaere-grounding, quaere-evidence, quaere-execution. |
| Current advisories/docs are time-sensitive; live/source-grounded checks are needed. | confirmed | Official Anthropic skill guidance plus local project quaere-grounding precedent. | Anthropic claude-api live-sources guidance; Agent Skills avoid time-sensitive info. | Mandatory quaere-grounding for CVEs, advisories, cloud/framework/bounty facts. |
| Production side effects require explicit permission/sandboxing. | confirmed | Official Claude Code security/permissions docs. | Claude Code permissions, sandboxing, secure deployment docs. | Read-only default and safe PoC policy. |

Representative URLs:

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/code-review
- https://code.claude.com/docs/en/permissions
- https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/live-sources.md

## Public skill ecosystem axis

| Finding | Label | Source quality / version fit | Sources | Imported as |
| --- | --- | --- | --- | --- |
| Security review skills require source → boundary → sink/missing guard → impact, not pattern-only reports. | confirmed | Multiple public skill artifacts on default branches, inspected 2026-05-08. | getsentry/warden security-review; remorses/kimaki security-review. | Threat Path model and pattern-only drift rejection. |
| Mature public skills use false-positive gates, confidence thresholds, severity, and report formats. | confirmed | Multiple independent public artifacts with same structure. | johnqtcg/awesome-skills security-review; Warden; Kimaki; Posit critical-code-reviewer. | Gate pass, severity/confidence, finding template updates. |
| Iron Law/rationalization tables are common in discipline skills. | confirmed | obra/superpowers discipline skills; ecosystem pattern, not official Anthropic rule. | obra/superpowers debugging, verification-before-completion, receiving-code-review. | Security Iron Law and Common drift modes table. |
| Safe authorized-scope handling is explicit in pentest/fuzzing skills. | confirmed | Security-specific public skill artifacts; safety policy also corroborated by Anthropic permissions docs. | BrownFineSecurity/iothackbot; Trail of Bits AFL++ skill. | Read-only default, safe PoC policy, artifact/repro handling. |
| Depth tiers and uncovered-risk lists are useful for audit scope control. | confirmed | Security-review artifact plus large-project PR review corroborator. | johnqtcg/awesome-skills security-review; PyTorch pr-review detailed mode. | Triage/Standard/Deep tiering and uncovered/skipped risk output. |
| Bug bounty workflows emphasize real harm, in-scope assets, duplicate/invalid filters, and report quality. | confirmed for workflow / partial for safety | Offensive workflow requires ROE wrapper; safety gates corroborated by HackerOne standards. | shuvonsec/claude-bug-bounty; HackerOne standards corroborate safety gates. | Report quality and no theoretical/no-impact findings. |

Representative URLs:

- https://github.com/getsentry/warden/tree/main/src/builtin-skills/security-review
- https://github.com/remorses/kimaki/blob/main/skills/security-review/SKILL.md
- https://github.com/johnqtcg/awesome-skills/blob/main/skills/security-review/SKILL.md
- https://github.com/BrownFineSecurity/iothackbot
- https://github.com/trailofbits/skills/blob/main/plugins/testing-handbook-skills/skills/aflpp/SKILL.md
- https://github.com/pytorch/pytorch/tree/main/.claude/skills/pr-review

## Domain standards / research axis

| Finding | Label | Source quality / version fit | Sources | Imported as |
| --- | --- | --- | --- | --- |
| ASVS is a versioned, testable application-security requirement catalog; WSTG provides testing/probe scenarios and report structure. | confirmed | Official OWASP project docs; versions named (ASVS 5.0.0, WSTG v4.2/stable). | OWASP ASVS 5.0.0; OWASP WSTG v4.2/stable. | Versioned security property and probe guidance. |
| Top 10 is risk awareness, not proof. | confirmed | Official OWASP Top 10 compared with ASVS/WSTG's verification scope. | OWASP Top 10:2025 vs ASVS/WSTG. | Taxonomy cannot confirm a finding. |
| NIST SSDF and SP 800-115 support planning, testing, analysis, mitigation, and recurrence prevention. | confirmed | Official NIST publications with stable DOIs. | NIST SP 800-218; SP 800-115. | Scope/ROE, mitigation direction, regression/security test suggestion. |
| Threat modeling should derive properties from assets, trust boundaries, actors, and attack paths. | confirmed | OWASP/Microsoft guidance plus Schneier attack-tree model; stable but method synthesis. | OWASP threat modeling framing; Microsoft STRIDE; Schneier attack trees. | Scope, actor/capability, trust boundary, threat path steps. |
| CWE describes root cause; CVSS/SSVC/KEV/EPSS inform severity/priority but require context. | confirmed | Official taxonomy/scoring/decision-support sources; current facts still require grounding when applied to a live advisory. | MITRE CWE; FIRST CVSS v4.0; CISA KEV; FIRST EPSS; SSVC. | Severity/confidence section and no bare numeric severity. |
| Bug bounty quality standards reject theoretical/no-impact/hazardous-testing findings. | confirmed | HackerOne platform standards; applies to bug-bounty-style reporting, not all internal hardening. | HackerOne platform standards and core ineligible findings. | False-positive gates and safe PoC policy. |
| Formal/specification-based auditing is useful but not universally required. | partially confirmed | NIST assurance publications support concept; no universal appsec mandate. | NIST SP 800-160 / 800-53A assurance language. | Property/spec/proof language without claiming formal verification is mandatory. |

Representative URLs / citations:

- https://owasp.org/www-project-application-security-verification-standard/
- https://owasp.org/www-project-web-security-testing-guide/
- https://owasp.org/Top10/2025/
- https://doi.org/10.6028/NIST.SP.800-218
- https://doi.org/10.6028/NIST.SP.800-115
- https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- https://www.schneier.com/academic/archives/1999/12/attack_trees.html
- https://cwe.mitre.org/
- https://www.first.org/cvss/v4.0/specification-document
- https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- https://docs.hackerone.com/en/articles/8494488-core-ineligible-findings

## Rejected or scoped-down imports

- **Scanner output as finding** — rejected. Tool output remains a candidate until reachability, attacker control, guard, impact, and gates pass.
- **Top 10/CWE category as confirmation** — rejected. Taxonomy classifies evidence-backed findings; it does not prove them.
- **PoC required at all costs** — rejected. Safe trace or symbolic evidence is preferred when a PoC would violate ROE or cause harm.
- **Formal verification required for all audits** — scoped down. Property/proof framing is required; formal methods are optional strengthening.
- **Deep companion-skill loop for every triage item** — rejected. Triage remains lightweight unless blast radius or uncertainty triggers promotion.
