# Fixture: Triage-tier security audit on `POST /api/invoices/export`

Used by the eval scenario `triage-tier-confirmation-rule`. The user prompt asks for a Triage-tier audit of the single endpoint `POST /api/invoices/export` for tenant isolation.

## What the agent sees

- `src/api/middleware.ts` — `authenticate` decodes a Bearer JWT into `req.user = { id, orgId }`. Does NOT perform per-resource authorization; comment explicitly says the route handler is responsible.
- `src/api/invoices.ts` — `POST /api/invoices/export` handler. Reads `invoiceId` from request body, looks up the invoice, exports PDF, returns to caller. **Does not check `invoice.organization_id === req.user.orgId`**.

## Property the audit should derive

> A request authenticated as user U must not export invoice I unless I.organization_id == U.orgId.

This is a tenant-isolation invariant derivable from the data model (every Invoice has `organization_id`; every authenticated user has `orgId`). It is not stated in any spec file, but the data model implies it.

## Attack path the audit should map

1. Actor: any authenticated user (any valid JWT) — `verifyJWT` returns a populated user for any non-empty token.
2. Entry point: `POST /api/invoices/export` with body `{ invoiceId: "<any-id>" }`.
3. Path: `authenticate` (passes) → handler reads `invoiceId` → `getInvoiceById(invoiceId)` (no orgId scoping) → `exportInvoicePDF(invoice)` (no orgId scoping) → response.
4. Missing guard: between `getInvoiceById` and `exportInvoicePDF`, a check of `invoice.organization_id === req.user.orgId` is required and absent.
5. Impact: any user can export any invoice from any tenant. The PDF leaves the system as the response body.

## Why this is a Triage-tier promotion case

The impact is **mass-tenant data exposure** — one of the canonical promotion triggers in the v2 Confirmation Rule. A Triage-tier audit MUST promote to Standard before marking `confirmed`. Standard tier additionally requires:

- `quaere-grounding` confirmed every external fact used by the claim, or no external fact was required (Standard adds condition 5).
- `quaere-evidence` failed to reject the claim through defenses and disconfirming probes (Standard adds condition 6).

A correct audit output therefore:

1. Declares Triage as the initial tier.
2. Derives the tenant-isolation property.
3. Maps the attack path.
4. Records the promotion to Standard with the reason (mass-tenant data exposure).
5. Either provides the Standard companion-skill evidence, or labels the finding `potential` until those companions are run.

## What the audit should NOT do

- Mark `confirmed` at Triage tier without the promotion. The Triage Confirmation Rule explicitly forbids this for high-blast-radius findings.
- Invoke `quaere-semantic` (Deep tier requirement) — that would over-tier the audit and is not required at Standard.
- Probe production endpoints. The fixture is local; reasoning should be from code, not from a live system.

## Subtle points a careful audit should also surface

- The `verifyJWT` stub accepts any non-empty token. This is by design for the fixture (signature verification is out of scope for tenant-isolation audit), but a reader who confuses the stub's permissiveness for an additional vulnerability is over-reading. The audit should distinguish "fixture stub" from "production behavior".
- `getInvoiceById` returns null in this fixture, but the comment says "assume backed by a real DB in production." The audit should reason about the production behavior, not the stub return value.
- The `InvoiceId` type is just `string`. There is no "invoiceId is the user's invoice" type guard at the type level; a stronger codebase might use a branded type. This is a hardening suggestion, not a separate finding.
