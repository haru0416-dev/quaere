---
name: quaere-naming
description: This skill should be used whenever the user needs to name a product, SaaS tool, brand, library, open source project, CLI, bot, or app, or asks to rename something, find a brand name, pick a product name, or escape generic AI-slop names. It enforces a metaphor-driven process that establishes a naming brief before generating anything, explores conceptual territories instead of thesaurus synonyms, filters anti-patterns, verifies availability with real tool checks instead of guessing from memory, and presents only vetted finalists that each carry a metaphor origin story. Trigger when the user says name this, what should we call it, we need a brand name, give me naming ideas, or the current names sound generic. Do not use for naming code symbols, variables, or functions inside an existing codebase.
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, search, web, and shell access.
license: MIT
---

# Naming Probe

## Iron Law

**No name reaches the user without three things named: the metaphor it compresses (its origin story), a tool-verified availability status (real `whois` / `curl` / `npm` / WebSearch checks, never recalled from memory), and the anti-pattern gate it survived. A name that is only a nice-sounding word with none of the three is `slop`, not a candidate — do not present it.**

This is not a branding ritual. Asked to name something, a model regresses toward the mean of its training distribution and emits plausible-sounding `-ly` / `-ify` slop, thesaurus synonyms, and empty compounds (Smart-, Cloud-, -Hub) that sound finished but carry no metaphor and were never checked for availability. The gate changes the question from *does this sound like a product name* to *which concrete image does it compress, and is it actually free to use*. Presenting names from memory is the failure this skill exists to stop — an unavailable name shipped as available is worse than no name. Full method: `references/metaphor.md` and `references/availability.md`.

**Stop now —** do not present any name you have not run a real availability check on (competitor search + platform commands); memory is not evidence. If fewer than 3 candidates survive the gate, loop back and generate more — do not lower the bar. Full conditions: `## Stop condition`.

## When to use

- The user needs to name a product, SaaS, brand, library, open source project, CLI, bot, or app.
- The user wants to rename something, find a brand name, or escape generic / AI-slop names.
- A name must work across platforms: domain, npm, PyPI, GitHub, app store, or social handles.

## When NOT to use

- Naming code symbols, variables, functions, or files inside a codebase — use `quaere-semantic` / `quaere-execution`, not brand naming.
- The name is already chosen and only needs an availability check — run the availability gate (Step 4) directly and skip metaphor exploration.
- Pure factual lookup of whether one specific name is taken — use `quaere-grounding`.

## Handoff triggers (which skill comes after this one)

Naming ends at vetted finalists with origin stories and availability status, not at a committed choice. Hand off when the next step changes discipline:

- A finalist's availability or trademark status needs authoritative confirmation → `quaere-grounding`.
- The chosen name must be wired into code, configs, package manifests, or repo metadata → `quaere-execution`.
- A naming claim ("X is taken", "Y is a competitor") is disputed and needs proof → `quaere-evidence`.
- No name survives the gate → stop and report the territories explored and why they failed; do not present slop.

The standard handoff payload (Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is at the end of this file under "Handoff to other skills".

## Core procedure

Run in order. Steps 3–4 are internal — the user sees nothing until Step 5.

### 1. Naming brief (never skip)

Before generating ANY name, establish context. Ask:

1. What does it do? (one sentence)
2. Who is it for? (audience)
3. What should it feel like? (technical / warm / playful / authoritative)
4. Standalone, or part of an existing brand family?
5. Any off-limits words, concepts, or styles?
6. Which platforms must the name work on? (domain, npm, PyPI, GitHub, app store, social) — this answer decides which availability checks are mandatory in Step 4.

A brief prevents wasted exploration. Do not generate before you have it.

### 2. Metaphor territories (not thesaurus)

Distill the product to one functional sentence, then work the six discovery questions in `references/metaphor.md` to find conceptual territories: what performs this task in the physical world, in nature, as a machine, as a profession, at its dramatic extreme, at its subtle minimum. Pick 2–3 territories. When the brief gives clear tone / audience / function, select territories autonomously; only ask the user when the brief is genuinely ambiguous. Carry the territory rationale into Step 5.

### 3. Generate and filter (internal)

Generate 30–50+ candidates within the chosen territories — single words, compounds, modified (truncated / blended / suffixed), foreign words, sound-first. Then cut to ~10 against the anti-pattern checklist in `references/metaphor.md`: kill suffix-addiction, meaningless portmanteaus, thesaurus synonyms, filler compounds, fake Latin/Greek, and anything failing two or more red flags. Do not show this working list to the user.

### 4. Availability gate (internal, MANDATORY, blocking)

Do NOT present any name that has not passed this. Memory and guesses are not evidence — run real checks.

1. **Competitor search FIRST** (cheapest kill): WebSearch `"[name]" [category]` and `"[name]" software/app`. A direct competitor in the same space = dead. Drop it immediately; skip platform checks.
2. **Platform checks** for survivors, scoped to the brief's Step-1 answer. Use the bundled script:

   ```bash
   bash ${CLAUDE_SKILL_DIR}/scripts/check-availability.sh [name] domain npm pypi github telegram
   ```

   It batch-checks domain (whois for .com/.dev/.io), npm, PyPI, GitHub org, crates.io, RubyGems, WP plugin, and Telegram. Run survivors in parallel Bash calls. For app stores and social handles, use WebSearch. Full command table, dictionary-word shortcut, and decision framework: `references/availability.md`.
3. **Decision:** drop names failing critical (must-have) platforms or with a direct competitor; flag-but-keep a strong name needing a workaround (exact `.com` taken but `get[name].com` free). If fewer than 3 survive, return to Step 3 — do not lower the bar.

### 5. Present and decide (first user-facing output)

This is the first time the user sees candidates. Present 3–5 finalists, each with: the name; a 15-second origin story (the metaphor it compresses); which principles it satisfies; tool-verified availability status (confirmed-free platforms and any workarounds); risks / trade-offs. Score with the rubric in `references/worked-example.md` when finalists are close. Recommend sitting with finalists 24h before committing.

### Loop back, do not lower the bar

- All candidates fail anti-patterns → Step 2 (new territories, not more names from exhausted ones).
- Fewer than 3 survive availability → Step 3 (more candidates in surviving territories).
- User rejects all finalists → Step 1 (revisit the brief — tone, audience, constraints).

## Output format

```text
Naming brief
- Function / audience / tone / family / off-limits / platforms

Territories explored: <2-3 named conceptual territories + why each fits>

Finalists (3-5, all availability-checked)
- N-001: <name>
  Origin: <15-sec story — the metaphor it compresses>
  Why it works: <principles satisfied>
  Availability: <platform: free | taken | workaround>  (tool-verified)
  Risks: <trade-offs>
- N-002: ...

Recommendation: <lead candidate + why> · sit with these 24h before deciding
```

## Common drift modes and anti-patterns

The recurring ways a naming pass collapses into slop — presenting names from memory without checking, thesaurus-diving instead of metaphor, filler compounds, lowering the bar when few survive — map to the Anti-patterns section of `references/metaphor.md`. Read it when output starts to feel like a name generator rather than vetted finalists.

## Worked example

A full pass (brief → territories → candidates → anti-pattern rejects → availability gate → finalists with origin stories), plus the scoring rubric, is in `references/worked-example.md`. Read it when the steps feel abstract.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-naming
- Blocking question: <what naming alone cannot decide>
- Confirmed inputs: <finalists with origin stories and tool-verified availability>
- Inconclusive inputs: <names still needing trademark/availability confirmation>
- Required next skill: <quaere-grounding | quaere-evidence | quaere-execution>
- Stop condition: <what the next skill must return before the name is committed>
```

- A finalist needs authoritative availability or trademark confirmation → `quaere-grounding` with the name and the unconfirmed claim.
- A disputed "taken" / "competitor" claim needs proof → `quaere-evidence` with the claim and a disconfirming probe.
- The chosen name is authorized to wire into code / configs / manifests → `quaere-execution` with the name and the platforms it must occupy.

Naming ends at vetted finalists. It does not pick the winner for the user and it does not commit the name.

## Stop condition

The skill is complete when:

- A naming brief was established before any name was generated (Step 1).
- Candidates came from named metaphor territories, not a thesaurus (Step 2).
- Every presented name passed the anti-pattern filter (Step 3) and a real, tool-verified availability check (Step 4) — none from memory.
- 3–5 finalists are presented, each with an origin story and an availability status (Step 5).
- A handoff or an explicit "no name survived" stop is stated.

Do not present a name you have not checked. Do not lower the bar to reach a count — looping back to an earlier step beats shipping slop. An unavailable name presented as available is the worst outcome; the availability gate exists to prevent exactly that.
