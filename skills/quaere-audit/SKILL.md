---
name: quaere-audit
description: "This skill should be used whenever the user asks for a serious security audit, vulnerability review, bug bounty triage, threat-model-driven code review, protocol/spec conformance audit, auth/authz or tenant-isolation review, exploitability analysis, CVE/advisory impact assessment, or security-sensitive PR review. It coordinates a property-driven audit: scope and rules of engagement → security properties → attack surface → source/boundary/sink or guard mapping → proof attempt → false-positive gates → severity/confidence → safe repro/report, with companion handoffs for external facts, semantic invariants, evidence-gated claims, and authorized PoC/fix work."
compatibility: Designed for Codex, Claude Code, Opencode, and Agent Skills-compatible coding agents with file, search, shell, test, git, and optional web access.
license: MIT
---

# Security Audit Loop

## Iron Law

**No security finding is `confirmed` without a falsifiable property, a reachable attacker-controlled path, a missing or failed guard, concrete impact, and a disconfirming false-positive pass.**

This is the security version of evidence-gating. Dangerous APIs, scary strings, stale advisories, and pattern matches are leads, not findings. A finding becomes actionable only when the audit can show why the property should hold, where an attacker crosses a boundary, which sink/state/guard fails, what impact follows under the threat model, and what counter-evidence was checked. If any link is missing, classify it as `potential`, `rejected`, or `inconclusive`.


## When to use

- Vulnerability discovery, security code review, bug bounty preparation, exploitability triage, or protocol/spec-grounded auditing.
- Auth/authz, tenant isolation, injection, parser, sandbox, cryptography, consensus, payments, secrets, SSRF, deserialization, supply-chain, cloud/config, or CI/CD security work.
- Security-sensitive PRs or incidents where false positives, unsafe probes, or stale external facts would be costly.

## When NOT to use

- Pure dependency lookup or CVE freshness checks with no local exploitability analysis; use `quaere-grounding` first.
- Normal implementation after a vulnerability is already confirmed and a fix is authorized; use `quaere-execution`.
- General maintainability review, one-line known fixes, or shallow checklist-only reviews.
- Any task whose rules of engagement are missing and probing could affect third-party or production systems; stop and ask.

## Core model

```text
Scope / ROE        target, assets, actors, trust boundaries, source-of-truth specs, unsafe actions
Tier               Triage / Standard / Deep, selected by scope and blast radius
Security Property  falsifiable invariant/rule mapped to spec, ASVS/WSTG/NIST/CWE when relevant
Threat Path        attacker source -> trust boundary -> sink/state transition/missing guard -> impact
Attack Surface     entrypoints, actors, external input, privilege/state boundaries, alternate paths
Code Map           files, symbols, callers/callees, storage/state, validation layers, configs
Proof Attempt      evidence that each property sub-claim holds or breaks on reachable paths
Gate Pass          reachability, attacker control, existing guard, scope, impact, repro strength
Severity           priority calibrated by impact, exploitability, blast radius, CVSS/SSVC/KEV/EPSS when relevant
Decision           confirmed / potential / rejected / inconclusive
Repro / Evidence   safe test, command, trace, minimal PoC, or why PoC is unsafe/unavailable
Handoff            findings, rejected claims, uncovered risks, skipped tools, next probes
```

Security auditing is property-driven, not bug-class-driven. OWASP Top 10/CWE labels help classify a finding after evidence exists; they do not prove the finding. For web/appsec properties, prefer versioned ASVS/WSTG references when applicable. For current CVEs, advisories, cloud defaults, framework guidance, or bounty rules, use `quaere-grounding` before relying on the fact.

## Depth control

- **Triage audit (one endpoint/component or short bug-bounty pass)** — compact property ledger, highest-risk surfaces first, four-condition Confirmation Rule. Do not invoke companion skills unless promotion is triggered or a blocking fact requires them.
- **Standard audit (feature, API boundary, protocol subsystem, or security-sensitive module)** — full property ledger, attack-surface map, proof traces, false-positive gates, severity/confidence, external facts grounded, candidate findings defended with `quaere-evidence`.
- **Deep audit (multi-system, protocol, crypto, consensus, payments, parser, sandbox, concurrency, or high-blast-radius target)** — batched ledger, semantic review for critical paths, stronger repro/independent verification, artifacted findings, and explicit uncovered-risk list.

Do not expand scope just because the codebase is large. Start from assets, trust boundaries, and rules of engagement. Promote the tier when blast radius demands it; never lower the tier to make a finding easier to confirm.

## Safety boundaries

Default to read-only analysis. Ask first before:

- production-like requests, replaying webhooks/events, destructive PoCs, brute force, scanning third-party hosts, credential use, payment/funds movement, exploit payloads against live services, or rate-limit/DoS tests
- changing code, adding PoCs/tests, deploying, rotating secrets, or modifying configs

Prefer safe substitutes: local fixtures, sandboxed test environments, dry runs, synthetic inputs, symbolic traces, or code proofs. If a safe repro cannot be produced, record why and classify accordingly; do not run unsafe probes just to strengthen a report.

## Workflow

### 1. Scope and rules of engagement

Define before searching for bugs:

- target repository/module/commit/version/deployment assumptions
- assets: funds, consensus, data integrity, privacy, auth, availability, sandbox, secrets
- actors and capabilities: unauthenticated user, tenant user, admin, compromised service, external node, malicious file, CI actor
- trust boundaries and data flows
- source-of-truth specs: ASVS/WSTG IDs, protocol docs, RFC/EIP, API schemas, tests, types, bounty rules, historical incidents
- non-goals, explicit exclusions, disclosure constraints, unsafe actions, and PoC permission
- selected tier and rationale

If the scope is missing or unsafe, ask before probing.

### 2. Derive falsifiable security properties

Create a property ledger. Translate broad bug classes into explicit assertions:

```text
Property: A request authenticated as user U must not read invoice I unless I.organization_id is in U.allowed_organization_ids, including export and background-render paths.
Source: tenant-isolation requirement / ASVS 5.0.0 access-control control / product spec
Expected enforcement: route guard before object fetch; render job re-checks tenant context
Failure impact: cross-tenant invoice disclosure
```

Property sources include normative spec language, auth/tenancy rules, parser/decoder contracts, state-machine transitions, crypto/consensus/accounting invariants, resource bounds, tests, types/schema constraints, persistence assumptions, and historical fixes. See `references/property-types.md` for property shapes.

### 3. Map attack surface and threat paths

For each high-value property, map:

- attacker source: actor, controlled request/input/file/message/state/config
- trust boundary: route/RPC/parser/job/webhook/service boundary, tenant boundary, privilege transition, wallet/signer boundary
- sink or missing guard: data read/write, command execution, deserialization, allocation, funds movement, signature check, state transition, secret access
- mitigation check: caller/callee guard, middleware, schema, database constraint, feature flag, protocol layer, sandbox, rate limit
- impact: confidentiality, integrity, availability, funds, consensus, auth bypass, privacy, sandbox escape, key compromise

Do not audit only the obvious primary function. Include alternate constructors, deserializers, imports, sync/admin/migration paths, background processors, persistence boundaries, cache invalidation, retries, and error paths when they can affect the property.

### 4. Attempt proofs and record gaps

For each property:

1. Decompose it into sub-claims.
2. Map each sub-claim to code, config, tests, or spec.
3. Try to prove it holds for all reachable attacker-controlled paths.
4. Record exact evidence: file, symbol, branch, guard, test, config, source URL, or missing check.
5. If proof fails, record the proof gap and the smallest safe trigger path.

If code intent/invariants are unclear, invoke `quaere-semantic`. If the proof depends on current docs, CVEs, advisories, API behavior, cloud defaults, or bounty scope, invoke `quaere-grounding`. If the candidate finding is subtle or disputed, invoke `quaere-evidence` before reporting.

### 5. Run false-positive gates

Before `confirmed`, run all gates from `references/fp-gates.md`:

- reachability from relevant actor
- attacker control over the critical value/state
- existing guard or compensating control
- scope/exclusion/accepted trust assumption
- meaningful security impact
- repro or evidence strength

Also perform a second-pass falsification: actively ask what benign explanation, compensating control, deployment assumption, or alternate path would invalidate the finding. Drop pattern-only findings, best-practice-only issues, and theoretical impacts unless the user explicitly asked for hardening suggestions.

### 6. Decide severity and confidence

Decisions:

- `confirmed` — property + reachable attacker path + failed guard + impact + gates + repro/trace meet the tier's Confirmation Rule
- `potential` — plausible proof gap but incomplete reachability, impact, grounding, or safe repro
- `rejected` — gate or defense defeats the claim
- `inconclusive` — evidence unavailable or unsafe within scope; include next probe

Severity should be calibrated, not guessed. Use project severity rules when supplied. Otherwise consider impact, exploitability, privileges, user interaction, blast radius, exposure, and whether KEV/EPSS/SSVC/CVSS applies. CVSS is a vector and input to prioritization, not the whole risk decision. CWE describes root cause after the weakness is established.

### 7. Reproduce or constrain safely

For confirmed or high-value potential findings, provide the smallest safe verification:

- unit/integration/security test
- command-line repro or request sequence against local/sandbox target
- crafted input, parser corpus, or state-machine trace
- differential oracle/spec comparison when a reference implementation exists
- symbolic proof/trace when runtime repro is unsafe

If PoC/test/harness/fix implementation requires editing, hand off to `quaere-execution` only after explicit authorization.

### 8. Report and handoff

Use `templates/audit-ledger.md` for persistent audits and `templates/finding.md` for report-ready findings. For final output, include:

```text
Scope / ROE:
Tier:
Property Ledger:
Attack Surface / Threat Paths:
Audited Proofs:
False-positive Gates:
Findings by decision:
Rejected Claims:
Uncovered Risks / Skipped Tools:
Verification / Safe Repro:
Handoff:
```

Keep these sections separate and in this order. Do not merge `Audited Proofs` and `Findings by decision`: proofs establish evidence and gaps, false-positive gates attempt to defeat the candidate, and only then may a candidate appear under `Findings by decision` as `confirmed`, `potential`, `rejected`, or `inconclusive`.

Each finding should include: property, affected code, attacker path, proof gap, gate results, severity, confidence, CWE/CVSS/ASVS/WSTG tags when relevant, repro/evidence, remediation direction, and regression/security test suggestion.

## Confirmation Rule

A finding cannot be `confirmed` unless the chosen tier's bar is met. Record the tier on the finding.

Tier does not override external-fact freshness. Even in Triage, if a finding relies on a current CVE, advisory, framework/cloud default, versioned spec, SDK/API behavior, or bounty rule, run `quaere-grounding` for that fact or classify the item as `potential` / `inconclusive` until the fact is grounded.

**Triage requires 4 conditions:**

1. Explicit security property and concrete proof gap **naming the missing or failed guard, sink, or invariant** (matching the Iron Law's source → boundary → guard → impact chain).
2. Code evidence that the gap is reachable from attacker-controlled input.
3. False-positive gates run, including at least one disconfirming probe.
4. Safe repro, trace, or strong reasoning showing non-trivial impact; or a safety reason repro is unavailable.

**Standard adds 2 conditions (6 total):**

5. `quaere-grounding` confirmed every external spec, SDK, advisory, CVE, cloud, framework, or bounty-rule fact used by the claim, or no external fact was required.
6. `quaere-evidence` failed to reject the candidate finding through defenses and disconfirming probes.

**Deep adds 1 condition (7 total):**

7. `quaere-semantic` mapped the relevant code intent, invariants, failure modes, and connections for the critical path.

**Tier promotion rule.** If a Triage finding has high blast radius — consensus break, funds movement, auth bypass, parser RCE, sandbox escape, key compromise, mass/bulk tenant data exposure, cross-tenant write, tenant impersonation, or multi-tenant secret leak — promote to Standard before marking `confirmed`. The list is canonical; do not rely on open-ended "similarly broad" phrasing — if a candidate finding does not fit one of these categories, it is single-tenant and does not require promotion regardless of the operational severity.

## Worked example

**Input:**

```text
Triage-audit only POST /api/invoices/export for tenant isolation. Do not broaden into the whole billing module.
```

### Bad output (pattern-only)

```text
Confirmed IDOR: the endpoint accepts invoiceId from the request. Fix by checking ownership.
```

Why this fails: accepting an ID is not a vulnerability by itself. The output has no tenant-isolation property, no reachable attacker path, no caller/middleware guard check, no impact evidence, and no disconfirming pass.

### Good output

```text
Scope / ROE
- Target: POST /api/invoices/export only. Tier: Triage. No live requests.

Property Ledger
- P-001 Authorization Rule: authenticated user U may export invoice I only if I.organization_id is in U.allowed_organization_ids, including background render job.

Attack Surface / Threat Path
- Source: tenant user controls invoiceId in POST body.
- Boundary: API route -> export service -> render job.
- Sink/guard: invoice lookup before tenant guard; render job reads invoice PDF bytes.

Proof / Gates
- Evidence: route loads `Invoice.find(id)` before `authorizeInvoice(user, invoice)`; render job receives invoice object without tenant context.
- Disconfirming probe: checked middleware and `authorizeInvoice` callers; middleware authenticates user but does not constrain invoiceId; no DB row-level policy in this path.
- Gates: reachable yes; attacker controls invoiceId yes; existing guard missing on export path; in-scope yes; impact cross-tenant invoice disclosure; repro via local request fixture only.

Decision
- confirmed at Triage for this single-invoice path if no broader exposure is found.
- Promotion check: if the same missing guard permits bulk export, organization-wide enumeration, or mass-tenant data exposure, promote to Standard before final confirmed report.
```

## Common drift modes

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

## Coordination with other skills

- `quaere-semantic` — when code intent, invariants, failure modes, or downstream connections are unclear.
- `quaere-grounding` — before relying on current specs, CVEs, advisories, docs, cloud behavior, framework guidance, CLI/tool behavior, or bounty rules.
- `quaere-evidence` — for each subtle/disputed/security-sensitive candidate finding before marking it confirmed at Standard/Deep.
- `quaere-execution` — only for safe PoC/test/fix implementation after explicit authorization.

## Stop conditions

Stop when the requested scope is covered, the verification budget is exhausted, unsafe probing would be required, evidence remains insufficient after meaningful disconfirming probes, or the user must decide whether to expand scope, run a PoC, disclose, or fix.

Do not silently continue into broad repository scanning after finishing the requested surface. End with uncovered risks and next probes.
