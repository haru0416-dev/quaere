# Property Types

Use properties that can be proven or falsified against code. Avoid generic bug classes unless they are translated into an explicit assertion.

## Invariant

Must hold for every reachable state or every accepted object.

Examples:

- balances remain conserved across transfer and settlement
- validator set entries are unique and sorted before aggregation
- decoded length equals committed length
- cache key includes every field that affects authorization or output

Audit focus: all writers, constructors, deserializers, cache updates, retries, and state transitions.

## Precondition

Must hold before an operation executes.

Examples:

- caller is authorized for the tenant before reading resource
- nonce has not been used before accepting a signed request
- parser input length is bounded before allocation

Audit focus: caller guards, middleware, schema validation, alternate entrypoints, internal-only assumptions.

## Postcondition

Must hold after an operation completes.

Examples:

- failed transaction leaves no durable partial state
- lock is released on all error paths
- emitted event matches persisted state

Audit focus: error paths, partial writes, transactions, cleanup, event ordering, async tasks.

## Authorization Rule

Defines who can perform an action on which object.

Examples:

- user can only read resources owned by their organization
- admin role in project A does not grant access to project B
- webhook signature binds body, timestamp, and endpoint

Audit focus: object lookup before auth, confused deputy paths, global IDs, cached permissions, background jobs.

## Trust Assumption

Names an input or component trusted by design.

Examples:

- execution layer response is trusted only after JWT-authenticated local channel validation
- oracle signer quorum is assumed honest up to threshold
- migration scripts are operator-only and not remotely triggerable

Audit focus: whether the assumption is documented, enforced at the boundary, and valid under the user-provided threat model.

## Resource Bound

Limits CPU, memory, storage, network, or lock duration.

Examples:

- request fanout is capped by authenticated quota
- recursive parser depth is bounded
- retry loop terminates under permanent failure

Audit focus: attacker-controlled sizes, nested loops, queue amplification, retry storms, cache retention, unbounded logs.

## Good Property Shape

```text
ID:
Type:
Statement:
Source:
Attacker relevance:
Expected enforcing code:
Failure impact:
```

Bad: "Check for authorization bugs."

Good: "A request authenticated as user U must not read invoice I unless I.organization_id is in U.allowed_organization_ids, including export and background-render paths."
