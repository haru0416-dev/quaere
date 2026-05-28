# Stale Risk Catalogue

Referenced from `quaere-grounding/SKILL.md` Step 2. Use this catalogue to articulate *why* model memory is unsafe for the specific external surface in scope. A vague "things may have changed" is not a stale-risk record; the agent should name which class of staleness applies and what would surface it.

## Class A — Versioned artifact churn

The package, library, framework, runtime, or CLI being relied on has had recent version activity that may have changed the relevant surface.

Triggers:

- The package has had a major release since the agent's training cutoff.
- A migration guide exists and the local project may be on the pre-migration version.
- The relevant function / class / namespace appears in changelog entries for breaking changes.
- The CLI added or renamed a subcommand or flag.

Example: `@anthropic-ai/sdk` shipped a major version that renames `messages.create` to `responses.create`; an agent that was trained before that release will offer the old shape unless grounded.

Example: AWS CLI `s3 sync --checksum-mode` was added in v2.something; pre-that-version, the flag fails.

What surfaces it: lockfile / installed types / CLI `--version`; cross-checked against the current changelog.

## Class B — Latest-vs-pinned divergence

Documentation defaults to `latest` but the local project is pinned to an older version. Latest docs are authoritative for the latest release, not for the local project.

Triggers:

- Docs URL contains no version segment (or contains `latest`).
- The project's lockfile pins a version older than the current `latest`.
- The doc page references a feature flag or config key whose introduction year/version is not stated.

What surfaces it: anchor the local version first; then either find version-tagged docs (`docs.example.com/v1.4/...`) or accept the latest docs only after confirming version-fit by changelog.

## Class C — Time-sensitive security guidance

Security guidance — advisories, recommended cipher suites, header configurations, cookie policies, JWT algorithm choices — depends on dates and affected-version ranges.

Triggers:

- A CVE/GHSA entry names the package and a version range; the local project's version may or may not be in range.
- A blog post is undated and recommends a security setting that may now be deprecated (e.g., `SameSite=None` without `Secure`, RS256 vs ES256 trade-offs, TLS 1.0 enablement).
- A vendor's hardening checklist has been superseded by a newer one.

What surfaces it: GHSA / vendor advisory with explicit affected versions; changelog of relevant deprecations; date the guidance was last reviewed.

## Class D — Local rejects what docs allow

The agent reads documentation that says a parameter, option, or behavior is supported, but the local type checker, runtime, or CLI rejects the exact form.

Triggers:

- TypeScript reports the parameter as not assignable.
- Python `import` succeeds but `pkg.method` raises `AttributeError`.
- CLI `cli help <subcommand>` does not list the documented flag.
- Runtime returns a deprecation warning the docs do not mention.

What surfaces it: the local probe itself. This is the case where Step 7 (executable probe) is most load-bearing — the local artifact disagrees with the doc, and resolving that disagreement is the entire point of grounding.

## Class E — Provider-side change outside the repo

The cloud provider, SaaS API, or SDK can change behavior outside any artifact in the repository. The repo's lockfile and types are silent on these.

Triggers:

- The provider's API has versioning headers (`Anthropic-Version`, `OpenAI-Beta`, AWS API version dates) that the local code may not pin.
- The provider has soft-deprecated an endpoint without removing it; behavior changes silently for unauthenticated or beta-flagged callers.
- A SaaS rate-limit, default behavior, or quota was adjusted in a release note the agent did not read.

What surfaces it: pinned API version in headers / config; explicit cite of the provider's changelog for the local pinned version; runtime probe against a non-production endpoint when authorized.

## Class F — Knowledge-cutoff bias

Distinct from the others: the *agent itself* is the stale source. The agent's training data has a cutoff date, and recent SDK / model / API names may be unfamiliar. The failure mode is the agent "correcting" a current fact back to a stale prior — flagging a real new identifier as a typo because it doesn't appear in training data.

Triggers:

- The user mentions a model / package / API name the agent does not recognize.
- The agent finds a discrepancy between local types and its memory of the SDK shape.
- A version number looks "too high" relative to the agent's prior.

What surfaces it: explicitly assume the user's reference is correct until disconfirmed by an executable probe or a primary source. Cite Anthropic's `claude-api/SKILL.md` guidance: "if any model strings look unfamiliar, that's expected — they were released after your training cutoff."

This class is empirically reinforced by:

- *GitChameleon 2.0* (Misra et al. 2025) and *VersiCode* (Wu et al. 2024): SOTA models hit only 48–51% on version-conditioned generation.
- *RustEvo²* (Liang et al. 2025): performance gap between RAG-augmented and parametric responses persists; models follow internal priors even when retrieved docs disagree.

The empirical conclusion: retrieval helps, but does not eliminate the prior. An executable probe is required to break the bias when the cost of being wrong is high.

## How to record stale risk

In the SKILL.md output, record stale risk as one or more of these classes plus the trigger:

```text
Stale risk:
- Class A (versioned artifact churn): @anthropic-ai/sdk had a major in 2025; local lockfile pins 0.x; changelog mentions messages → responses rename.
- Class F (knowledge-cutoff bias): the user named "claude-opus-4-7", which post-dates my training cutoff; I will not flag it as a typo.
```

A vague "the docs may have changed" is not a stale-risk record and does not justify any of the dual-axis gates downstream.
