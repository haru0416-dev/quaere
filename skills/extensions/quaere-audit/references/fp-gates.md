# False-Positive Gates

Run these gates before calling a proof gap a vulnerability.

## Gate 1: Reachability

Reject or downgrade if the vulnerable branch is not reachable from a relevant actor.

Check:

- public route/RPC/job/parser/event path
- required feature flags and deployment config
- caller chain from attacker-controlled input
- test-only, benchmark-only, migration-only, or dead code status

## Gate 2: Attacker Control

Reject or downgrade if the attacker cannot control the critical value.

Check:

- value source and transformations
- schema or type constraints
- authentication and authorization before use
- trusted service boundaries
- signature, MAC, proof, or consensus validation

## Gate 3: Existing Guard

Reject if another layer already enforces the property for all relevant paths.

Check:

- middleware and route guards
- caller validation
- database constraints
- parser normalization
- callee assertions
- transaction rollback
- protocol-layer rejection

Common mistake: checking only the primary function and missing a guard in the dispatcher or typed decoder.

## Gate 4: Scope

Reject or mark out of scope if the issue is excluded by user scope, bounty rules, deployment assumptions, or target commit.

Check:

- explicitly excluded components
- already fixed in the audited commit or version
- non-production tools
- unsupported configurations
- accepted trust assumptions

## Gate 5: Impact

Downgrade or reject if the impact is not security-relevant under the threat model.

Check:

- confidentiality, integrity, availability, funds, consensus, auth, sandbox, privacy
- exploit preconditions and privileges
- blast radius
- whether the result is only code quality or defensive hardening

## Gate 6: Repro Strength

Do not require a destructive PoC, but require enough evidence for a human auditor to validate.

Acceptable evidence:

- minimal test or command
- concrete request/input sequence
- code trace with exact missing guard
- comparison to normative spec
- maintainer-confirmed behavior

If evidence is incomplete, classify as `potential` or `inconclusive`, not confirmed.
