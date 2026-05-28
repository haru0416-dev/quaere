---
name: quaere-grounding
description: "This skill should be used whenever implementation or review depends on external, version-sensitive facts: libraries, SDKs, APIs, CLIs, cloud services, security advisories, changelogs, release notes, or documentation that may have changed. The skill anchors local versions, ranks source quality, runs an executable probe and a lateral corroborator before promoting any claim to `confirmed`, and turns confirmed facts into implementation constraints. Trigger when the task depends on any external surface whose freshness binds correctness — model memory is not evidence."
compatibility: "Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, shell, web, and git access. If web access is unavailable, use local package source/types, lockfiles, vendored docs (with mtime check), CLI help/version output, and mark external facts inconclusive when the dual-axis gate cannot be satisfied."
license: MIT
---

# External Grounding

## Iron Law

**No claim becomes `confirmed` without (a) an executable probe AND (b) a lateral corroborator. Otherwise the claim stays `inconclusive`.**

This is not a stylistic rule. Model memory is not evidence for version-sensitive external facts: SOTA LLMs reach only 48–51% on version-conditioned generation, and even retrieval-augmented setups follow internal priors when retrieved docs disagree with parametric memory *(GitChameleon 2.0 — Misra et al. 2025; VersiCode — Wu et al. 2024; RustEvo² — Liang et al. 2025)*. Authority alone is also insufficient: lateral-reading research shows that single-source acceptance — even of high-authority sources — is the dominant failure mode of internet-era literacy *(Wineburg & McGrew 2017, Stanford History Education Group; Caulfield 2019, SIFT)*. The two-axis structure (source axis from the ranking, claim-credibility axis from probe + lateral check) follows the NATO Admiralty Code (STANAG 2511, source reliability A–F × information credibility 1–6); Anthropic's Citations API is a contemporary engineering instance of the same separation, evaluating output on factual accuracy and source-supports-claim as independent axes.


## Boundary with quaere-evidence

`quaere-grounding` confirms external facts: package versions, SDK method names, API contracts, CLI options, cloud-service behavior, deprecation dates, affected versions, security guidance.

`quaere-evidence` uses those facts to evaluate claims: whether a reviewer is right, whether a bug cause is confirmed, whether a CI failure is explained, whether a proposed fix closes the risk.

The handoff from this skill should be a set of external constraints. The handoff from `quaere-evidence` should be a decision about claims, causes, or fixes.

As of 2026-05, Anthropic's official documentation does not provide guidance for resolving "docs say X / installed types say Y" conflicts. The closest precedent is the `claude-api` skill's "add alongside, don't replace" rule for version-tied state, which this skill extends.

## When to use

- Library, SDK, framework, runtime, or CLI behavior may have changed.
- The task depends on official docs, changelogs, release notes, migration guides, deprecation notices, cloud-provider behavior, API schemas, or security advisories.
- Local code and remote docs appear to disagree.
- The user says not to trust model memory, asks for current docs, or mentions stale knowledge risk.
- A security, compatibility, or migration decision depends on affected versions or dates.

## When NOT to use

- Stable language basics or pure local code semantics.
- Trivial edits where no external fact changes the answer.
- User-provided specifications that are the source of truth and do not depend on external services or libraries.
- General code review claims that can be proven entirely from local code and tests; use `quaere-evidence` instead.

## Handoff triggers (which skill comes after this one)

Once the external fact is labeled, hand off to the skill that uses it:

- Implementation is the next step → `quaere-execution` with `Use / Do not use / Verification needed` constraints and the probe results that confirmed each one.
- A bug cause, review comment, CI failure, or security claim still needs proof using the grounded facts → `quaere-evidence`.
- The grounded facts are advisories / CVEs / deprecation notices feeding a property-driven audit → if the `quaere-audit` extension is installed, hand off to it; otherwise pass the grounded facts back with a flag that a security audit is needed.
- The blocking question turned out to be code intent rather than external facts → `quaere-semantic`.

The standard handoff payload (Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is documented at the end of this file under "Handoff to other skills".

## Categories of facts that must be grounded

Inputs that must never be inferred from training memory when they are version-sensitive:

- SDK / library / framework method names, class names, namespace hierarchies, type signatures.
- API parameter and response shapes; required headers; auth flows; rate-limit semantics.
- CLI flags, subcommand names, positional argument order, default behavior.
- Cloud service API versions and per-version behavior; default region/quota settings; soft-deprecated endpoints.
- Security advisories: CVE / GHSA dates, affected version ranges, mitigation steps, recommended cipher suites.
- Deprecation notices and migration timelines.
- Configuration key names; environment variable names; pinned API version headers.
- Lock-file resolution: which transitive dependency version is actually installed.

If the task depends on any of these and the surface may have changed, this skill applies.

## Core model

```text
External Surface   the external dependency, API, CLI, service, or security guidance in scope
Stale Risk         why model memory or unversioned docs may be unsafe (six classes; see references/stale-risk.md)
Local Anchor       local package/API/runtime/CLI/spec version and where it came from
External Claim     a claim from docs, changelog, source, advisory, issue, or example
Source Quality     authority level on a 14-tier ranking (see references/source-quality.md)
Version Fit        whether the claim applies to the local anchor
Conflict Check     docs vs local types/source/runtime/issues/advisories
Executable Probe   mandatory before `confirmed` on version-sensitive claims
Lateral Check      independent corroborator — single-source claims do not pass
Decision           confirmed / locally observed / version-mismatched / stale / conflicted / inconclusive
Handoff            implementation constraints, source URLs or local paths, and remaining uncertainty
```

Use the lightest version of this model that still satisfies the dual-axis gate.

## Claim result matrix

| Evidence available | Decision label |
|---|---|
| Executable probe + independent lateral corroborator + version fit | `confirmed` |
| Executable probe only (no independent lateral) | `locally observed` — not confirmed as external fact |
| Official docs only, no local probe | `documented` — not locally confirmed |
| Local anchor conflicts with docs | `version-mismatched` or `conflicted` |
| Single source, no probe | `inconclusive` |
| No network; local source + executable probe | `local-only` — external claim cannot be confirmed |

**`locally observed`** is a distinct intermediate label. It means the behavior was verified in the local environment but has not been corroborated by an independent external source. Use it when an executable probe succeeded but the claim depends on a broader external fact (API contract, package behavior across versions) that a single local run cannot fully cover. Do not promote to `confirmed` without a lateral corroborator.

Note: multiple sources that derive from the same resolution (e.g., `package.json`, lockfile, and installed types all reflect the same dependency graph) are not independent corroborators. Independence requires a structurally separate source — changelog, official docs, a different probe mechanism, or a commit-level reference.

## Workflow

### 1. Define the external surface

Name the exact external thing being relied on. Keep the scope narrow enough to verify.

Examples:

- `@anthropic-ai/sdk` message creation API, not "Anthropic docs"
- AWS CLI `s3 sync --checksum-mode`, not "AWS behavior"
- Cookie `SameSite` guidance for browser authentication, not "web security"
- A checked-in OpenAPI response schema, not "the API"

If multiple external surfaces matter, handle them as separate claims.

### 2. Record stale risk + knowledge-cutoff acknowledgment

Pick the relevant class(es) from `references/stale-risk.md`. State the class letter and the concrete trigger; do not record a generic "things may have changed."

**Knowledge-cutoff acknowledgment.** If a name (model, SDK, API, version, identifier) sounds unfamiliar, the default assumption is that it post-dates training cutoff — *verify before correcting the user*. Anthropic's `claude-api` skill phrases it as: "if any model strings look unfamiliar, that's expected — they were released after your training cutoff." Class F failures (treating a current identifier as a typo) are common and silent.

### 3. Anchor locally first

Before treating remote documentation as applicable, find the local anchor when possible:

- dependency manifest and lockfile version
- installed package source or type definitions
- runtime version, generated client, checked-in schema, vendored docs (subject to mtime check), or migration guide
- CLI `--version` / `help` output
- API version pinned in config, headers, environment, generated code, or docs

If there is no local anchor, record that explicitly. Do not silently substitute "latest".

**Schema note.** The local anchor is *given* — a tier-1-by-construction artifact of the project's current state. It does not require its own dual-axis gate (Steps 7 + 8); it is the precondition the gates run against. Claims *about* the anchor's meaning (e.g., "messages.create exists at 1.4.0") still require the gate. Keep the distinction visible in the output: `Local anchor:` lists the artifact (path, line, version) without going through `Decision`; `Claims` go through the gate and label.

### 4. Collect external claims via sanctioned fetchers

Use Anthropic-sanctioned fetchers as the primary mechanism for retrieval: `web_search`, `web_fetch`, MCP documentation servers. These tools carry citation metadata (URL + retrieval timestamp) that downstream steps can audit. Do not paraphrase remembered docs as if they were retrieved — that defeats the source axis before Step 5 even runs.

For each relevant source, write the claim as a narrow statement that could be wrong.

Good:

```text
EG-001: `client.messages.create` accepts `system` as a top-level parameter in @anthropic-ai/sdk v0.x/v1.x.
```

Bad:

```text
The SDK docs say how to use messages.
```

### 5. Rank source quality

The 14-tier ranking lives in `references/source-quality.md`. Summary: tiers 1–2 are local applicability anchors (installed types, vendored docs); tiers 3–6 are high-authority external (version-tagged official docs, changelog, security advisory); tiers 7–9 are medium (maintainer-authored issues, official examples); tiers 10–14 are low (blog posts, undated tutorials, latest-docs-on-non-latest-project, remote `main` branch).

The ranking is the **source axis** of the dual-axis gate. It tells you which sources are likely to carry weight. It does **not** tell you whether the claim is true — that is what Steps 7 and 8 are for.

### 6. Check version fit and conflicts

For each claim, compare the source against the local anchor:

- Does the source name the same major/minor version, API version, CLI version, or release range?
- Does a changelog or migration guide say the behavior changed?
- Do local installed types/source agree with the docs?
- Do security advisories list this project as affected or unaffected?
- Do examples declare a compatible version, or are they just current snippets?

**Anthropic precedent for version-tied state.** The `claude-api` skill encodes per-version migration rules (4.5 → 4.6 → 4.7) with an explicit "add alongside, don't replace" rule when multiple versions coexist: do not remove a capability gate just because the new version exists; old traffic may still depend on the old shape. Apply the same conservatism here. When local anchor and target version diverge, the claim about the target does not transfer to local without explicit migration evidence.

Prefer stronger local evidence over remote `latest` docs when they disagree about what this project can compile or run.

### 7. Run executable probes — MANDATORY for `confirmed` on version-sensitive claims

Empirical: SOTA LLMs follow internal priors even after retrieval (GitChameleon 2.0; VersiCode; RustEvo²). Retrieval enables the probe; the probe is what verifies. **For any claim in the categories listed above (SDK names, API shapes, CLI flags, advisory affected versions, etc.), an executable probe is required before the claim can reach `confirmed`.** Probes:

- inspect installed type definitions or generated clients
- run `tsc --noEmit`, a tiny compile check, or a language-specific type check
- run `python -c "import pkg; print(pkg.__version__)"` or equivalent
- run `cli --version` or `cli help <subcommand>`
- run a minimal non-network snippet against local code
- for vendored docs: `mtime(doc) > mtime(symbol)` — a year-old vendored doc next to a recently refactored symbol is `stale`, not authoritative *(Tan, Wagner & Treude 2024; Wen et al. 2019)*

Do not hit production endpoints, mutate cloud resources, replay payments, or call external services with side effects without explicit user approval.

**Carve-out for facts that cannot be probed locally.** Some claims are about historical or vendor-side state that no local probe can verify: deprecation dates, advisory affected-version ranges, vendor announcements, security guidance recommendations, contract changes that have not yet hit the local anchor. For these, the executable-probe requirement is replaced by a *stricter source-axis requirement*: at least two independent tier 1–6 sources must agree (e.g., the official changelog AND a maintainer-authored issue, or a GHSA entry AND the vendor's deprecation notice). Step 8's lateral cross-check still applies. The substitution does not lower the bar — it trades one form of proof (executable disambiguation) for another (multi-source agreement on facts that have no executable form). Record the substitution in the Decision: `confirmed (probe-substituted: two independent tier-N sources)`.

If neither an executable probe nor two independent tier 1–6 sources are available, the claim is `inconclusive`, not `confirmed`. The probe is the breaker for parametric prior bias on probeable facts; multi-source agreement is the breaker for non-probeable facts. Without either, retrieval alone leaves the prior intact.

### 8. Lateral cross-check — MANDATORY before `confirmed`

A single-source claim is `single-source`, not `confirmed`. Find one independent corroborator before promoting:

- a different official source for the same fact (e.g., changelog + API reference)
- a maintainer-authored issue or PR that confirms the behavior
- an executable probe that confirms the behavior independently of the doc
- a community resource that pins the same version and observes the same behavior

SIFT's lateral-reading principle: leave the page and triangulate. Static checklists (CRAAP and similar) lose to behavior-based cross-checking. The lateral-check axis is what distinguishes "the source has authority" from "the claim is true."

### 9. Decide and promote

Apply both axes — source axis (Step 5) and claim-credibility axis (Steps 7 + 8):

- **confirmed** — passes all three: a tier 1–6 (or 7–9 with version match) source supports it, an executable probe agrees (or, for unprobeable facts per the Step 7 carve-out, two independent tier 1–6 sources agree), AND a lateral corroborator exists. Anthropic's Citations API encodes the same dual requirement: the claim must be factually accurate *and* the cited source must actually support the claim.
- **version-mismatched** — claim may be true for another version, but not for the local anchor. Source axis passes; version-fit axis fails.
- **stale** — the source predates a relevant release, migration, advisory, or deprecation, or lacks date/version information for a time-sensitive fact.
- **conflicted** — credible sources disagree, or docs and local types/runtime disagree (Step 6 surfaced the disagreement).
- **locally observed** — executable probe succeeded locally, but no independent lateral corroborator has been applied. The behavior was seen, not confirmed as an external fact. Usable as local evidence, not as a grounded external claim.
- **inconclusive** — single-source (no lateral corroborator), no executable probe possible, or the needed fact could not be verified.

Only `confirmed` claims become implementation constraints. `locally observed`, `version-mismatched`, `stale`, `conflicted`, and `inconclusive` claims must not be used as if true.

### 10. No-network fallback strategy

When external access fails or is unavailable, apply these three steps **in order** *(adapted from Anthropic's `claude-api/shared/live-sources.md` Fallback Strategy)* before falling through to `inconclusive`:

1. **Cached / vendored content with explicit date.** Use the locally checked-in mirror (e.g. `docs/<name>-<version>.md`) and state the cache date verbatim. Do not hide staleness.
2. **Inform the user that data may be outdated.** The dual-axis gate now leans entirely on local evidence; flag every claim that depends on an unreachable external source.
3. **Name the canonical URLs the user can fetch and report back.** Provide the exact URL and what to look for, even though it could not be fetched here.

If none of these resolve the fact, mark `inconclusive`. Do not rely on model memory as a substitute. The output must show this fallback was attempted — emit a labeled `No-network fallback strategy:` block (see the Output format below) when web access is unavailable.

## Worked example

A bad-output (trust the docs) vs good-output (anchor → version fit → probe → lateral → decision) example, applied to an SDK 1.x ↔ 2.x docs/types mismatch, is at [`references/worked-example.md`](references/worked-example.md). Read it when the dual-axis gate feels abstract — the example shows the refusal to promote "docs say so" through as `confirmed`.

## Common drift modes and anti-patterns

The recurring shapes that produce `confirmed` labels without one of the two required axes ("docs say X — that's enough", "Single-axis acceptance", knowledge-cutoff "correction", treating retrieval as verification, etc.) are at [`references/anti-patterns.md`](references/anti-patterns.md). Read it before promoting a claim past `single-source` or `inconclusive`.

## Output format

The standard report template (External grounding header, Claims with the 9-line per-claim format, Implementation constraints, Handoff) is at [`references/output-format.md`](references/output-format.md). Use that template as the deliverable shape of this skill.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-grounding
- Blocking question: <what external fact could not be confirmed here>
- Confirmed inputs: <claims reaching "confirmed" status — safe to use as implementation constraints>
- Inconclusive inputs: <locally observed / inconclusive / version-mismatched / stale facts — not safe to use as true>
- Required next skill: <quaere-evidence | quaere-execution | quaere-semantic | (quaere-audit, if the extension is installed)>
- Stop condition: <what the next skill must do with the confirmed / inconclusive facts>
```

When implementation is next, hand off to `quaere-execution` with `Use / Do not use / Verification needed` constraints, plus the executable-probe results that confirmed each constraint. The quaere-execution should re-run the probes after edits to detect regression to docs-trust.

When a bug cause, review comment, CI failure, or security claim still needs proof, hand off to `quaere-evidence` with the confirmed external facts and the unresolved claims, naming which probes gave inconclusive results and what would resolve them.

When the grounded facts are security advisories, CVEs, deprecation notices, or vendor security guidance that feed a property-driven audit, hand off to the `quaere-audit` extension (if installed) with the affected version ranges, the lateral-corroboration evidence, and the threat-model frame the advisories assume. If the extension is not installed, return the grounded facts with a flag that a security audit is needed and escalate to the user.

When code intent — not external facts — is the blocking question, hand off to `quaere-semantic` for the units whose analysis depends on the external behavior. Do not paraphrase code as if it were external claim.

## Stop condition

This skill is complete when:

- every external surface in scope has a local anchor or explicit missing-anchor note
- every external claim has source quality (tier from `references/source-quality.md`), version fit, executable probe result (or explicit non-availability reason), lateral corroborator (or `inconclusive` flag), and a decision
- only `confirmed` claims (passing both source axis and claim-credibility axis) are listed as implementation constraints
- stale, version-mismatched, conflicted, single-source, and inconclusive facts are clearly separated from usable facts
- knowledge-cutoff bias is explicitly handled when the agent's prior disagrees with the user's reference

Do not proceed as though a fact is current merely because it matches model memory. Do not proceed as though a single source has been verified merely because it is highly authoritative.
