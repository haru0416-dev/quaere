# Examples

These examples show when each skill should trigger and what behavior to expect. They are intentionally scenario-oriented because these skills improve process quality rather than transforming a fixed file format.

## `quaere-semantic`

Prompt:

> Read `src/scheduler.ts` before we touch it. I need to understand what each function is trying to preserve, especially around retry ordering and cancellation.

Expected behavior:

- Analyze meaningful units with `What (mechanical) / What (domain intent) / Why (with certainty marker) / Invariants / Failure / Connections (←) / Connections (→)`.
- Mark unclear intent as `UNKNOWN` with a probe instead of inventing history.
- End with open questions, risk hotspots, and implementation implications if requested.
- Do not edit code during the semantic review.

## `quaere-evidence`

Prompt:

> CI failed twice on `reservation.spec.ts`. A reviewer says the new deposit validation is broken, but the logs are inconsistent. Please verify the claim before patching.

Expected behavior:

- Record observed logs/code as Findings, not conclusions.
- Create hypotheses or review claims with possible false-positive reasons.
- Attempt Defense and include at least one disconfirming probe.
- Patch only after a Decision confirms the issue.
- Hand off if repeated probes are inconclusive.

## `quaere-grounding`

Prompt:

> We need to update our SDK usage, but I don't trust model memory here. Check the installed package version and current docs before suggesting code changes.

Expected behavior:

- Identifies the stale-knowledge risk.
- Reads local dependency/version anchors first.
- Checks version-matched official docs, changelog, installed types, or source.
- Separates "what current docs say" from "what this local project can use".
- Marks unversioned, conflicting, or stale examples as weak evidence.
- Produces a `Use / Do not use / Verification needed` constraint block before implementation.

## `quaere-execution`

Prompt:

> Apply the approved plan in `PLAN.md`: add the settings toggle, update tests, run the suite, review the diff, and commit if everything passes.

Expected behavior:

- Read the plan and relevant files before editing.
- Split work into ordered implementation units.
- Execute one unit at a time with targeted checks.
- Review the actual diff before finalizing.
- Run a final full gate for multi-unit work.
- Commit only because the prompt explicitly authorized it.

## `quaere-audit`

Prompt:

> Audit this payment webhook and invoice export flow for authorization, replay, and state-consistency bugs. Use the API docs, tests, and code as the source of truth, and only report findings that survive reachability and exploitability checks.

Expected behavior:

- Defines scope, assets, actors, trust boundaries, and unsafe actions before probing.
- Derives explicit security properties from docs, tests, schemas, and implicit behavior.
- Maps properties to attack surfaces, code locations, callers, storage, and validation layers.
- Attempts to prove each selected property and records exact proof gaps.
- Runs false-positive gates for reachability, attacker control, existing guards, scope, impact, and repro strength.
- Classifies results as confirmed, potential, rejected, or inconclusive with evidence or safe PoC notes.

Lightweight prompt:

> Triage-audit only `POST /api/invoices/export` for tenant isolation. Derive the tenant-isolation property, map the request path and authorization checks, and report confirmed/potential/rejected issues. Do not broaden into the whole billing module.

Expected lightweight behavior:

- Keeps scope to one endpoint and one asset boundary.
- Writes a compact property ledger instead of a full repository audit.
- Checks caller/middleware authorization before claiming IDOR or data exposure.
- Stops after the endpoint is classified rather than continuing into broad scanning.

## `quaere-invention`

Prompt:

> Most users drop off before they finish setting up our dev tool. Suggest a non-obvious onboarding approach — not just the standard wizard.

Expected behavior:

- Names the default basin first (the wizard) and why it may be the wrong thing to optimize.
- Separates hard constraints from soft preferences and forbidden shortcuts.
- Lists the assumptions that make the default feel inevitable, tagged by kind.
- Generates candidates with at least four different mutation operators, each naming the broken assumption, mechanism, expected gain, and failure mode.
- Classifies every candidate with the fixed novelty labels and never self-rates an idea as "truly novel".
- Designs a kill-probe (not a confirmation test) for the top candidates and hands them off with a stop condition.

## `quaere-naming`

Prompt:

> We are building a CLI that watches a codebase and re-runs only the tests affected by each change. It needs to work as a GitHub org, an npm package, and a `.dev` domain. Give us a name — not generic AI-slop like TestFlow or SmartTest.

Expected behavior:

- Establishes a naming brief (function, audience, tone, platforms) before generating any name.
- Explores 2–3 named metaphor territories instead of pulling thesaurus synonyms.
- Generates and filters candidates internally against the anti-pattern checklist; does not dump a raw list.
- Runs a mandatory availability gate — competitor search first, then real platform checks (whois / npm / GitHub) — never claiming availability from memory.
- Presents 3–5 finalists, each with a 15-second origin story and tool-verified availability status, and loops back rather than lowering the bar if fewer than 3 survive.

## Combined pipeline

Prompt:

> We need to audit and then change the cache invalidation behavior, but nobody remembers why the current branch structure exists. Understand the module first, derive the security property, prove the suspected bug, then implement the smallest safe fix and commit it if tests pass.

Expected behavior:

1. `quaere-semantic` maps the existing module intent and invariants.
2. `quaere-grounding` confirms any external cache library or API behavior that may have changed.
3. `quaere-audit` derives properties, maps attack surfaces, attempts proof, and gates exploitability.
4. `quaere-evidence` validates any disputed claim with defense and probes.
5. `quaere-execution` implements the confirmed fix, reviews the diff, verifies, and commits only if still authorized.
