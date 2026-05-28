# Worked example — Triage audit on `POST /api/invoices/export`

A bad-output (pattern-only) vs good-output (Scope / Property Ledger / Attack Surface / Proof / Decision) example, for tenant-isolation triage. See `../SKILL.md` for the procedure this example enacts.


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
