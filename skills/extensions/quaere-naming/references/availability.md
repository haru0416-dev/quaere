# Availability checking

Distilled from the upstream naming skill's `availability.md`, plus the platform table covered by `scripts/check-availability.sh`. The Iron Law's "tool-verified, never from memory" rule lives here in full.

## Contents

- [Availability decision framework](#availability-decision-framework)
- [Step 1 — Competitor conflict search (do this first)](#step-1--competitor-conflict-search-do-this-first)
- [Dictionary word shortcut](#dictionary-word-shortcut)
- [Platform-specific checks](#platform-specific-checks)
- [Decision gate](#decision-gate)

## Availability decision framework

Check in sequence, stop early on failure:
**Quick disqualification → Domain → Code platforms → Social media → Trademarks**

Domain priority order: `.com` (credibility standard) → `.dev` (developer tools) → `.io` (tech, uncertain long-term) → `.app` (consumer apps) → `.co` / `.sh` / `.so` (alternatives).

Product-type priority matrix (must-have vs. nice-to-have — this maps to the brief's Step-1 platform answer):

| Product type | Must have | Nice to have |
|---|---|---|
| **SaaS** | Domain, GitHub | X/Twitter, LinkedIn |
| **Developer tool** | GitHub org/repo, package registry | Domain, X/Twitter |
| **Consumer app** | Domain, app store name | Instagram, X/Twitter |
| **Open source** | GitHub org, package name | Domain |

## Step 1 — Competitor conflict search (do this first)

Quick disqualification (~30 seconds): search for direct competitor conflicts *before* spending time on domain/package checks. A name controlled by a competitor in your category is dead. Names used by large brands in *different* industries may still be viable but require accepting ongoing search-visibility challenges.

WebSearch queries (run both):

- `[name] + your industry/category` — surfaces direct competitors in your space
- `[name]` (bare term) — surfaces large brands / Wikipedia collisions affecting searchability

Searchability scoring: **5/5** unique, immediate first-page ranking, no Wikipedia collision · **3/5** manageable disambiguation with a category qualifier · **1/5** common word dominated by Wikipedia, essentially unsearchable.

## Dictionary word shortcut

Common English words are essentially all taken on `.com` / `.dev` / `.io`. **Skip the exact-match checks** for them and go straight to variants: `get[name].com`, `use[name].com`, `try[name].com`, `[name]hq.com`, `[name]app.com`. Run exact-match TLD checks only for invented words, uncommon words, or compounds.

## Platform-specific checks

Run whichever the brief requires. `scripts/check-availability.sh` automates the first eight; use WebSearch for app stores and remaining social handles.

| Platform | Command / method | Available = |
|---|---|---|
| **Domain** | `whois [name].com` (and `.dev` / `.io`) | "no match / not found / no data found" |
| **npm** | `npm view [name]` | "not found" / 404 |
| **PyPI** | `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/project/[name]/` | 404 |
| **GitHub org** | `curl -s -o /dev/null -w "%{http_code}" https://github.com/[name]` | 404 |
| **GitHub repo** | `gh repo view [org]/[name]` | "not found" |
| **crates.io** | `curl -s -o /dev/null -w "%{http_code}" https://crates.io/api/v1/crates/[name]` | 404 |
| **RubyGems** | `curl -s -o /dev/null -w "%{http_code}" https://rubygems.org/api/v1/gems/[name].json` | 404 |
| **WP plugin** | `curl -s "https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&slug=[name]"` | "Plugin not found" in body |
| **Telegram** | `curl -sL https://t.me/[name]` | no `tgme_page_title` in body (verify in app) |
| **App stores** | WebSearch `"[name]" site:apps.apple.com` / `site:play.google.com` | no matching listing |
| **Social handles** | WebSearch `site:x.com/[name]`, `site:instagram.com/[name]` | no profile |

Social-handle fallback when the exact handle is taken: `@get[name]` / `@use[name]`, `@[name]hq`, `@[name]_official`.

If `whois` is not installed, fall back to `curl -s -o /dev/null -w "%{http_code}" https://[name].com` — but note this only detects a live site, not domain registration. The bundled script already handles this fallback.

## Decision gate

- **Drop** candidates that fail critical (must-have) availability: a direct competitor controls the name, multiple must-have platforms are unavailable, a squatter demands a large sum, or a trademark conflict exists in your category.
- **Flag but keep** a name strong enough to justify a workaround — exact `.com` taken but a prefix variant is free, or one social handle is taken.
- **Loop back, do not lower the bar.** If fewer than 3 candidates survive this gate, return to Step 3 and generate more in the surviving territories. (This 3-candidate floor is this skill's rule, not an upstream quote.)

> Automated checks can give false positives (caching, rate limits, registrar privacy). Always verify a finalist manually before the user commits.
