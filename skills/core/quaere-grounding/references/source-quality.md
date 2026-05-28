# Source Quality Ranking

This is the 14-tier source ranking referenced from `quaere-grounding/SKILL.md` Step 5. The ranking separates **applicability** (does the source describe the local anchor?) from **authority** (does the source carry weight?).

A high-authority source that does not match the local version is *less useful* than a lower-authority source that does. Authority is necessary; version fit is what makes authority binding.

## Local applicability anchors

These tiers describe sources that already match the local project by construction.

1. **Installed package source, generated client code, type definitions, lockfile, runtime version, CLI `--version` or `help` output.** What the project compiles and runs against. Ground truth for "what does my code see right now."
2. **Repository-pinned specs or vendored docs**, such as OpenAPI schemas, SDK-generated files, checked-in migration guides. Trustworthy *only when* `mtime(doc) > mtime(symbol)` — vendored docs decay; staleness is the empirical default. *(Tan, Wagner & Treude 2024; Wen et al. 2019.)* If the doc was checked in years ago and the symbol was recently refactored, demote this tier to "stale."

## High-authority external sources

Authority is the *vendor or maintainer of the artifact* speaking on the record about the artifact's behavior at a specific version.

3. **Official documentation for the exact local version.** Version-tagged docs (e.g., `docs.example.com/v1.4/...`).
4. **Official API reference for the exact local version.** Generated reference for the exact tag.
5. **Official changelog, release notes, migration guide, deprecation notice.** What changed between versions.
6. **Vendor security advisory, GHSA, CVE entry, vendor bulletin, or cloud-provider security notice.** Time-sensitive: an advisory is only authoritative for the affected versions and dates it names.

## Medium-authority sources

Maintainer-level statements that are not the official artifact.

7. **Maintainer-authored GitHub issue, PR, discussion, or comment.** Strong when the maintainer is named and the comment includes a version reference.
8. **Official examples that declare compatible versions.** Often outdated; trust only when the example pins a version that overlaps the local anchor.
9. **Framework sample apps tied to the target release.** Same caveat as 8.

## Low-authority sources

Treat as hints, not authority. They suggest avenues for verification but do not promote a claim to `confirmed`.

10. **Blog posts.** Even from well-known authors. Always undated for the version-fit check unless the post explicitly states one.
11. **StackOverflow or Q&A answers.** Vote count is not version proof.
12. **Tutorials without date or version.** Unversioned tutorials never satisfy the version-fit gate.
13. **Docs for `latest` when the local project is not on `latest`.** Latest docs describe the latest release; they do not describe yours.
14. **Remote `main` branch source unless matched to the installed tag or commit.** A `main` branch is the future, not the present.

## Authority does not equal correctness — claim credibility is a separate axis

The NATO Admiralty Code (STANAG 2511) separates *source reliability* (A–F) from *information credibility* (1–6) because reliable sources can repeat disinformation and unreliable sources can deliver truth. Stanford History Education Group's lateral-reading research (Wineburg & McGrew 2017; Caulfield's SIFT, 2019) reaches the same conclusion empirically: a static source ladder loses to *behavior* — leave the page and triangulate via independent corroboration.

The 14-tier ranking is a *source-axis* heuristic. It tells you which sources are likely to carry weight. It does **not** tell you whether the claim is true. The `confirmed` label requires both axes to pass:

- **Source axis**: an item from tier 1–6 (or tier 7–9 with explicit version match).
- **Claim axis**: a lateral cross-check (independent source) **and** an executable probe (type check, runtime check, CLI `--version`) when the claim is version-sensitive.

A tier-3 source that is contradicted by a tier-1 runtime probe is *conflicted*, not *confirmed*. A tier-3 source with no lateral corroborator is *inconclusive*, not *confirmed*. See `quaere-grounding/SKILL.md` Step 7 (executable probe) and Step 8 (lateral cross-check) for the gates.

## Ecosystem priors (footnote)

Empirical SemVer compliance varies by ecosystem. Decan & Mens (TSE 2021) cross-ecosystem study (data from circa 2019) found Cargo (Rust) > npm (JavaScript) > Composer (PHP) > RubyGems in declared-vs-actual SemVer compliance. When weighing an "official changelog says no breaking change" claim, weight that claim against the ecosystem's empirical compliance prior. A patch-version bump in RubyGems carries more residual blast-radius risk than a patch bump in Cargo.

The ranking itself is dated; ecosystem behavior may have shifted in the years since the study, and a fresh empirical re-survey is the correct response to important decisions that depend on this prior. Treat the ranking as a starting hypothesis, not a current measurement. This is a *secondary* weighting; do not let it override an executable probe result. If the probe shows a break, the ecosystem prior is moot.

## When a claim is excluded by the ranking

A claim sourced only from tiers 10–14 — or sourced from tiers 1–9 but failing version fit — cannot be `confirmed`. It can be:

- recorded as a *hint* that justifies a probe ("a 2023 blog post claims this option was added in v2.x; run `cli help` to verify"),
- handed off to `quaere-evidence` if the question goes beyond external fact ("does the maintainer's comment imply a security risk?"),
- or marked `inconclusive` if the available evidence does not survive the dual-axis gate.

Never silently substitute "this looks plausible" for the gate.

## References

- NATO STANAG 2511 / AJP-2.1, Admiralty Code (source reliability vs information credibility).
- Wineburg & McGrew (2017), "Lateral Reading: Reading Less and Learning More When Evaluating Digital Information", Stanford History Education Group.
- Caulfield (2019), SIFT method (Stop, Investigate the source, Find better coverage, Trace claims).
- Tan, Wagner & Treude (2024), *Empirical Software Engineering* — outdated code-element references in 3,000+ GitHub repos.
- Wen, Nagy, Bavota & Lanza (2019), ICPC — code/comment drift after refactoring.
- Decan & Mens (2021), IEEE TSE — cross-ecosystem SemVer compliance.
