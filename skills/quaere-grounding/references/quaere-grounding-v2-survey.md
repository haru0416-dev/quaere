# External Grounding v2 Survey

Survey date: 2026-05-08.

Purpose: document the ADR-0003 external survey and quaere-grounding labels behind the v2 rewrite of `skills/quaere-grounding/SKILL.md`. This artifact is retroactive — the convention of recording survey provenance per skill was established later in quaere-evidence v2 and back-applied here for cross-skill consistency. The commit history (commits up to and including `a0160c1`, plus review fixes through `8da2305`) is the primary source for what actually shipped.

## Source-quality note

The survey concerns skill-writing patterns, dependency-management literature, and source-criticism methodology, not version-sensitive SDK/API behavior of any specific package. Local executable probes were therefore replaced by artifact checks: Anthropic guidance was read against current docs URLs (web search/fetch tool versions are dated 2026-02), public skills were inspected as full SKILL.md files, and academic citations were checked against abstracts and prior knowledge. arXiv preprints and unpublished working papers were imported only with explicit caveat. Single-vendor or single-Anthropic sources were imported only when the claim was procedural rather than empirical.

## Anthropic guidance axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| `web_search` and `web_fetch` are Anthropic's official freshness mechanism for going past the knowledge cutoff. | confirmed | Anthropic web search tool docs (current 2026-02 tool version `web_search_20260209`); Anthropic web search API release. | Step 4 names them as sanctioned fetchers carrying citation metadata. |
| `skill-creator` does not model fact staleness; this skill fills a real gap. | absence | anthropics/skills `skill-creator/SKILL.md`; tracked in anthropics/skills issue #202. | Boundary section records the gap with project provenance. |
| `claude-api` skill is the canonical Anthropic worked example of version-tied external state. | confirmed | anthropics/skills `claude-api/shared/model-migration.md`; `claude-opus-4-5-migration` plugin. | Step 6 cites `claude-api`'s "add alongside, don't replace" rule for version-tied state. |
| Citations API encodes a dual-axis verification contract (factual accuracy AND source-supports-claim). | confirmed | Anthropic Citations API docs and announcement; multi-agent research engineering post. | Step 9 dual-axis gate (`confirmed` requires source axis + executable probe + lateral check) cites Citations API as a contemporary engineering instance. |
| Progressive disclosure: long skills should split variants into `references/<name>.md`. | confirmed | Anthropic engineering blog "Equipping agents for the real world with Agent Skills" (Oct 16 / Dec 18 2025). | `references/source-quality.md` (14-tier ranking) and `references/stale-risk.md` (6-class catalogue). |
| No official Anthropic guidance for "docs say X / installed types say Y" conflict resolution. | absence | (none located) | The 14-tier ranking and dual-axis gate are project-original; closest Anthropic precedent is `claude-api`'s "add alongside" pattern. Recorded in Boundary section. |

Representative URLs:

- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool
- https://www.anthropic.com/news/web-search-api
- https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/model-migration.md
- https://docs.anthropic.com/en/docs/build-with-claude/citations
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

## Public skill ecosystem axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Separate "live-sources" registry: a sibling file mapping each topic to a canonical URL plus per-URL extraction prompt. | confirmed | anthropics/skills `claude-api/shared/live-sources.md`. | Adopted partial pattern via `references/source-quality.md`; not as a strict mirror because we are domain-agnostic, not Anthropic-SDK-specific. |
| "Never guess SDK usage" rule with named binding categories (function/class/namespace/method/import). | confirmed | anthropics/skills `claude-api`. | "Categories of facts that must be grounded" section enumerates SDK names, API shapes, CLI flags, advisories, etc. |
| Knowledge-cutoff acknowledgment line ("if any model strings look unfamiliar, that's expected — they were released after your training cutoff"). | confirmed | anthropics/skills `claude-api`. | Step 2 knowledge-cutoff acknowledgment with explicit verify-before-correcting framing. |
| 3-step "Fallback Strategy" block for no-web-access (cached content with date / inform user data may be outdated / point to canonical URLs). | confirmed | anthropics/skills `claude-api/shared/live-sources.md`. | No-network fallback section adapted directly. |
| Risk-criteria taxonomy with per-criterion Justification field. | partially confirmed | trailofbits/skills `supply-chain-risk-auditor`. | Drift mode entries explain the failure mode per row in parallel structure; per-criterion Justification field itself was not adopted (5 decision labels carry implied justification). |
| "Phrases that signal failure" 2-column drift-mode table format. | confirmed | obra/superpowers `verification-before-completion`. | Common drift modes table format (rationalization → reality). |
| Extract reusable taxonomies into `resources/` or `references/`. | confirmed | trailofbits/skills `variant-analysis`. | `references/` split for `source-quality.md` and `stale-risk.md`. |

Representative URLs:

- https://github.com/anthropics/skills/blob/main/skills/claude-api/SKILL.md
- https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/live-sources.md
- https://github.com/trailofbits/skills/blob/main/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/trailofbits/skills/blob/main/plugins/variant-analysis/skills/variant-analysis/SKILL.md

## Domain research axis

| Finding | Label | Sources | Imported as |
| --- | --- | --- | --- |
| Source reliability and information credibility are separate axes (A–F × 1–6). Reliable sources can repeat disinformation; unreliable sources can deliver truth. | partially confirmed (challenges single-axis ranking) | NATO STANAG 2511 / AJP-2.1, Admiralty Code. | Iron Law two-axis structure (source axis from 14-tier ranking, claim-credibility axis from probe + lateral check). The Admiralty 2D table itself was not adopted wholesale; the lateral check axis substitutes for the credibility column. |
| Static checklist evaluation (CRAAP) loses to lateral cross-check via independent corroborator. | confirmed | Wineburg & McGrew 2017, Stanford History Education Group; Caulfield 2019, SIFT method. | Step 8 lateral cross-check MANDATORY before `confirmed`. |
| ~⅓ of Maven releases break SemVer; ~20% of non-major upgrades break in declared compliance. | confirmed | Raemaekers, van Deursen & Visser 2014/2017; Ochoa et al. 2022 EMSE replication. | Step 6 version-fit gate empirically validated; blast-radius sensitivity to non-major upgrades acknowledged. |
| Cross-ecosystem SemVer compliance varies (Cargo > npm > Composer > RubyGems, data circa 2019). | partially confirmed (data ages) | Decan & Mens 2021, *IEEE TSE*. | `references/source-quality.md` ecosystem priors footnote with year-of-data caveat. |
| Treat each dependency as code you adopted; evaluate provenance, maintenance, update lag explicitly. | confirmed | Cox 2019, *CACM*. | Supports the Step 3 "anchor locally first" directive. |
| Outdated code-element references in vendored / repo docs are endemic; `mtime(doc) > mtime(symbol)` is a useful staleness probe. | confirmed | Tan, Wagner & Treude 2024 EMSE; Wen et al. 2019 ICPC. | Step 7 mtime check for vendored docs; `references/source-quality.md` tier 2 caveat. |
| 43% of practitioners report docs are rarely updated yet still find them useful. | partially confirmed | Forward & Lethbridge 2002, DocEng. | Considered for splitting `stale` label into `stale-but-directional` vs `stale-and-misleading`; rejected during synthesis (label-set complexity). |
| SOTA LLMs hit only 48–51% on version-conditioned generation; even retrieval-augmented setups follow internal priors when retrieved docs disagree with parametric memory. | confirmed | Misra et al. 2025 GitChameleon 2.0; Wu et al. 2024 VersiCode; Liang et al. 2025 RustEvo². | Step 7 executable probe MANDATORY for `confirmed` on version-sensitive claims. The probe is what breaks parametric prior bias; without it, retrieval alone leaves the prior intact. |

Representative URLs / citations:

- https://en.wikipedia.org/wiki/Admiralty_code
- https://en.wikipedia.org/wiki/CRAAP_test
- https://arxiv.org/abs/1806.01545
- https://www.researchgate.net/publication/333333382
- https://dl.acm.org/doi/10.1007/s10664-021-10052-y
- https://dl.acm.org/doi/10.1145/3347446
- https://dl.acm.org/doi/10.1145/585058.585065
- https://arxiv.org/abs/2212.01479

## Rejected or scoped-down imports

- **Forward & Lethbridge `stale-but-directional` vs `stale-and-misleading` label split** — rejected. Adds label-set complexity for marginal value; the existing five labels already capture the relevant distinctions.
- **Per-criterion Justification fields (supply-chain-risk-auditor)** — rejected. Our 5 decision labels carry implied justification (`stale` is dated, `version-mismatched` is anchor-bound, etc.). A per-criterion Justification column would add ceremony without raising the bar.
- **`live-sources.md` as a topic-URL completion registry** — scoped down. We are domain-agnostic; a full mirror is Anthropic-SDK-specific. Adopted the *partial* pattern in `references/source-quality.md` (taxonomy + ranking, not topic-URL pairs).
- **Anthropic "all when-to-use info in description"** — rejected. Ecosystem practice plus length constraints favor body sections; `When to use` and `When NOT to use` retained.
- **Cross-skill handoffs as an Anthropic-blessed convention** — rejected. No Anthropic precedent; retained as project convention per ADR-0001.

## Subsequent review fixes

The independent review pass after `a0160c1` and the scenarios update at `b163fc1` produced the following corrections (commits `be11952` `5df632c` `81b93a5` `8da2305`):

- Removed the fabricated arXiv ID `2604.09515` (April 2026 = current/future month) from `references/stale-risk.md` — a citation hallucination caught by the reviewer is exactly the failure mode this skill exists to prevent.
- Removed the unsourced "+13.5% RACG survey 2025" precise figure; the empirical force is carried by the named GitChameleon / VersiCode / RustEvo² papers.
- Step 7 carve-out for *unprobeable* facts: when the claim is about deprecation dates, advisory affected-version ranges, vendor announcements, etc., the executable-probe requirement is replaced by a stricter source-axis requirement (two independent tier 1–6 sources agree).
- Worked example "Lateral check" rewritten to use the doc's own self-identification as 2.x (genuinely independent of the local probe), instead of falsely calling lockfile + installed types "independent corroborators" (they are co-generated by one `npm install`).
- Step 3 schema note: the local anchor is given (tier-1-by-construction); only claims *about* the anchor go through the dual-axis gate.
- Drift modes table consolidated 3 single-axis-acceptance rows into 1 + added 2 new distinct drift modes (Class F multi-turn persistence; transitive lockfile resolution).
- Iron Law re-led with NATO Admiralty Code; Citations API demoted to "contemporary engineering instance" rather than "contract this skill mirrors."
- "Industry baseline" section removed (content already in Iron Law); Step 2 inline 6-class enumeration trimmed (lives in `references/stale-risk.md`).
- Decan/Mens ecosystem ranking gained a "data circa 2019" temporal caveat in `references/source-quality.md`.

These corrections sharpened v2 against its own contract; only the two unverified-citation removals retracted findings (the citations were never load-bearing; the empirical claims they supported are still cited via the verified papers).
