# Metaphor, principles, and anti-patterns

Distilled from the upstream naming skill's `principles.md`, `metaphor-mapping.md`, `phonosemantics.md`, `anti-patterns.md`, and `cultural-references.md`.

## Contents

- [Foundational gates (principles)](#foundational-gates-principles)
- [Metaphor exploration](#metaphor-exploration)
- [Phonosemantics](#phonosemantics)
- [Anti-patterns](#anti-patterns)
- [Cultural references](#cultural-references)

## Foundational gates (principles)

Every candidate should pass these before serious consideration. Priority order: story and imagery over practical concerns.

- **Metaphor test** — Can you visualize it? The most memorable names map a concrete metaphor to an abstract function (Sentry = guard, Docker = dock worker, Vault = secure room).
- **Real-words-win** — Real words score ~68.8% recall vs 38.1% for invented names. When inventing, anchor to a recognizable morpheme (Grafana has a visible "graph"; Nexagen has no roots and fails).
- **Compound rule** — Both halves must carry meaning. Generic prefixes (Smart, Cloud, Auto, AI) are filler that communicate nothing.
- **Length** — Aim for 1–3 syllables / 4–6 characters. Longer names get abbreviated, so either go short or ensure the abbreviation works.
- **Phone test** — Repeatable, spellable, and memorable after one hearing. Intentional misspellings signal "the real spelling was taken."
- **Origin story** — Every name needs a concise explanation linking it to purpose (internal clarity + marketing).
- **Distinctiveness** — Stand apart from category descriptors. Slack/Discord/Notion became distinctive through use, not literal description.

## Metaphor exploration

Move from "what does it do?" to "what else works like this?" via four steps.

1. **Distill** the product to a single functional sentence, stripping features to the core job. The simplified version reveals metaphor territory — e.g. "watches the web" → spiders, sentries, radar.
2. **Ask the six discovery questions** (verbatim):
   1. What performs this task in the physical world?
   2. What handles this in nature?
   3. What tool or machine does equivalent work?
   4. What profession embodies this function?
   5. What's the extreme/dramatic version?
   6. What's the understated/subtle version?
3. **Map territories, not names.** Cluster related metaphors into conceptual neighborhoods (Military/Security, Nature, Detection, …) to find the richest regions before picking words.
4. **Cross-pollinate.** Combine elements from distinct territories for the most distinctive results — e.g. "Canary" for error monitoring borrows mining imagery instead of overused security terms.

## Phonosemantics

Sounds carry inherent meaning (~2:1 preference when a name's sounds align with product attributes). **A perfect metaphor with imperfect sound beats perfect sound with no story.**

**Consonants**

| Class | Conveys | Examples |
|---|---|---|
| Plosives (p b t d k g) | Strength, impact, authority, solidity | Kafka, Docker, Bolt, Git |
| Fricatives (f v s z sh th) | Speed, smoothness, flow, elegance | Figma, Vercel, Stripe, Zoom |
| Nasals (m n ng) | Warmth, continuity, approachability | Miro, Notion, -ing endings |
| Liquids (l, r) | l = fluidity/clarity; r = energy/roughness | Linear, Loom / React, Rust |

**Vowels** — Front (ee i e ay) = small, fast, sharp, light (Stripe, Vite, Wiz). Back (oo o aw uh) = large, powerful, deep, serious (Vault, Zoom, Docker, Drone).

**Bouba/Kiki** — 90–95% across languages map "bouba" to round shapes, "kiki" to spiky.

**Rhythm & stress** — First-syllable stress (trochaic) feels decisive (Sentry, Docker); second-syllable (iambic) feels flowing (Redis, Vercel); monosyllabic = maximum impact (Vault, Slack, Rust). Endings: hard stop (t/k/p) = clean/decisive; open vowel = expansive/friendly; nasal = warm/lingering; fricative = trailing/continuous.

**Initial clusters** — gl- (light: glow, gleam), sn- (nose/quick: snap, snare), sl- (smooth/negative: slide, slick), cr- (breaking/hard: crack, crypt), str- (tension/strength: strong, stripe), fl- (movement/light: flow, flash), sw- (sweeping: sweep, swift), gr- (rough/holding: grip, grind), sp- (dispersal: spark, spread), tr- (crossing: track, transfer).

**Match sound to product** — Powerful/infra → plosives + back vowels. Fast → fricatives + front vowels. Friendly → nasals, open vowels, liquids. Developer/precise → hard consonants, short front-vowel syllables. Secure → plosives + back vowels, monosyllabic.

**Apply** — Say it aloud 5×; match dominant sounds to product character; check vowel weight; listen to the ending; try it in a sentence; consider the audience's primary language.

## Anti-patterns

**AI-slop patterns** (each fails because LLMs remix existing training data and can't produce genuinely novel names):

- Suffix addiction (-ly, -ify, -able) — thousands already deployed
- Meaningless portmanteau — unique but indistinguishable
- Thesaurus extraction — overused synonyms, no distinctive power
- Category + modifier — descriptive but forgettable
- Vacant corporate language (Solutions, Labs, Platform)
- Excessive misspelling — signals the real spelling was taken
- Fake Latin/Greek mashups — impressive briefly, means nothing
- Aspirational adjectives — generic positivity fits anything

**Five fatal flaws:** (1) boring descriptive, (2) invented mashups with no meaning, (3) thesaurus-derived, (4) empty corporate language, (5) extremeness for its own sake.

**Compound traps** — Filler first-positions: Smart, Auto, Cloud, AI, Data, Cyber, Next, Digital, True, Pure, Open, Fast, Easy, Pro, Ultra, Hyper, Super, Meta, Omni, Core. Generic second-positions: Hub, Lab, Base, Flow, Sync, Link, Stack, Forge, Shift, Scape, Verse, Craft, Wise, Path, Nest, Box.

**Red flags — kill if two or more apply:**

- Sounds like ten other products?
- Can't explain the story in 15 seconds?
- Requires letter-by-letter spelling?
- Only works visually, awkward spoken?
- Just a "cool word" with no metaphor connection?
- Works equally well for different products/categories?
- Generic without stylization?
- Matches three+ AI slop patterns?
- Would you cringe introducing it professionally?
- Domain availability was the primary appeal?
- Common meaning conflicts with the product's purpose?

**"So what?" test** — After explaining the origin: "That's clever" → works; "Oh, I see" → acceptable; "So what?" / "I don't get it" / "Isn't that already a thing?" → fails.

**AI-product-specific:** "AI" prefix/suffix (dates instantly); "Co-"/"-pilot" imitation (Copilot owns it); human names (only when the AI *is* the interface); "Magic" cliché (saturated); "Smart" prefix (redundant filler); "Neural"/"Neuro" (decoration, no user-facing meaning). When a category converges on one pattern within 18 months, it stops signaling membership and starts signaling "me too."

## Cultural references

High-risk, high-reward. When it works the name carries centuries of meaning; when it fails it's costume jewelry. A reference earns its place only if it passes **all four**:

1. **Story maps to function** — The backstory must do work a random word couldn't. Good: Prometheus (fire/visibility to dark systems), Kafka (bureaucratic labyrinths → complex pipelines), Bluetooth (king who united factions → unites protocols), Ansible (Le Guin's instant-comms device → config across any number of servers). Bad: "Zeus / Titan / Medusa for a cooking app" — "powerful/strong" is an adjective, not a mapping.
2. **Works without the reference** — Sounds good and is pronounceable even to those who don't know the backstory (Jira, Asus, Kafka). The cultural layer is a bonus, not a requirement.
3. **Specific, not obvious** — Pick the 2nd/3rd thing, not the headliner. Overused → better depth: Greek (Zeus/Apollo/Athena → Prometheus/Icarus/Mnemosyne/Argos); Norse (Thor/Odin/Loki → Huginn/Bifrost/Yggdrasil); Science (Einstein/Newton/Tesla → Curie/Faraday/Kepler/Lovelace); Literature (Sherlock/Gandalf → Ansible/Neuromancer/Panopticon); Space (Apollo/Nova → Lagrange/Aphelion/Sidereal). **Saturation check:** search "[name] + tech/app" — if dozens appear, the territory is occupied.
4. **Passes "So what?"** — "That's clever" → ship; "Oh, I see" → acceptable; "So what?" → too thin; "I don't get it" → too obscure.

**Underused source domains** (escape over-pillaged Greek): Norse (world tree, scout-ravens, realm-bridges), Japanese (Kaizen, Kintsugi, Ikigai), Arabic/Persian (algorithm, zenith, cipher), Latin (nexus/apex — but already overused), Maritime (helm, anchor, bearing, keel), Architecture (keystone, buttress, vault, cornerstone), Music (cadence, tempo, resonance, timbre), Geology (bedrock, obsidian, basalt, flint), Celtic (Druid, Ogham, Sidhe — distinctive phonetics, low saturation).

**Multi-level names** reward discovery on three levels — sound, surface meaning, cultural depth (e.g. Bluetooth, Kafka). Not every name needs all three, but those that achieve them become legendary.
