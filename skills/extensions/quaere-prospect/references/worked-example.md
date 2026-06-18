# Worked example: a prospect pass

A full origination pass on a concrete codebase, showing each step's named output
and how the reality gate kills two of four candidates. Read it when the SKILL.md
steps feel abstract. The subject is invented but typical; the discipline is the
point, not the domain.

## Contents

- [Prompt](#prompt)
- [Step 1 — Survey the terrain](#step-1--survey-the-terrain)
- [Step 2 — Gap inventory](#step-2--gap-inventory)
- [Step 3 — Beneficiary and demand](#step-3--beneficiary-and-demand)
- [Step 4 — Reality gate](#step-4--reality-gate)
- [Step 5 — Validation probe](#step-5--validation-probe)
- [Step 6 — Opportunity filter](#step-6--opportunity-filter)
- [Handoff](#handoff)
- [What the wishlist version would have looked like](#what-the-wishlist-version-would-have-looked-like)

## Prompt

> "Here's `csvplot`, a small CLI that turns a CSV into a PNG chart. What should we
> build next?"

## Step 1 — Survey the terrain

- Subject: codebase (`csvplot`, a single-binary CLI).
- What it is for: turn one CSV file into one static PNG chart from the terminal.
- Current boundaries: reads CSV, renders bar/line/scatter to PNG. Non-goals (from
  README): "not a dashboard, not interactive, no live data sources." `--help` and
  `examples/` confirm PNG-only, file-in/file-out.

## Step 2 — Gap inventory

- G1 — SVG / vector output — kind: capability — present-but-weak (PNG only).
- G2 — read from stdin (pipe data in) — kind: UX-friction — absent.
- G3 — live dashboard with auto-refresh — kind: capability — out-of-scope (README
  non-goal).
- G4 — "support more formats" — kind: capability — vague; no specific format.

## Step 3 — Beneficiary and demand

- G1 SVG: beneficiary = users embedding charts in docs/websites who need to scale
  them; job = "put a crisp chart in a vector pipeline". Demand: `evidenced` —
  three issues request SVG (#41, #58, #62).
- G2 stdin: beneficiary = shell users piping query output (`psql … | csvplot`);
  job = "chart without a temp file". Demand: `evidenced` — TODO in `main.rs` plus
  issue #50.
- G3 dashboard: beneficiary named but the job contradicts a stated non-goal.
  Demand: `assumed`.
- G4 "more formats": no beneficiary, no specific format named.

## Step 4 — Reality gate

1. **Already built?** grep finds `render_svg()` behind an undocumented `--format
   svg` flag. **G1 is already covered** — the real gap is discoverability/docs, a
   much smaller thing, not "build SVG output".
2. **Deliberately out of scope?** README lists "no live data" as a non-goal.
   **G3 is `already covered` (non-goal)** unless the user reopens it.
3. **Demand real?** G2's issue #50 and the `main.rs` TODO both exist and ask for
   stdin. Confirmed `evidenced`.
4. G4 has no beneficiary and no specific format → `wishlist`, dropped in Step 3.

Survivor after the gate: **G2 (stdin input)**.

## Step 5 — Validation probe

- O-001 (G2, stdin input):
  - Probe: add a 10-line spike reading CSV from stdin when no file arg is given;
    post it on issue #50 and ask the three commenters to try `… | csvplot`.
  - Validate signal: ≥2 of them confirm it fits a real pipeline they run.
  - Kill signal: the spike shows stdin conflicts with the existing positional-arg
    parsing in a way that needs a breaking CLI change nobody wants.
  - Cost: ~1 hour for the spike.
  - Decision-changing evidence: if maintainers say stdin breaks the "one file in,
    one file out" contract on purpose, it becomes a non-goal, not an opportunity.

## Step 6 — Opportunity filter

- O-001 stdin input — `verified gap` (beneficiary named, demand evidenced via #50
  + TODO, not already built, has a probe).
- SVG output — `already covered` (exists behind `--format svg`; reframe as a docs
  fix, not a new build).
- Live dashboard — `already covered` (stated non-goal).
- "More formats" — `wishlist` (no beneficiary, no specific format).

One survivor presented as a real opportunity; three honestly labeled and dropped.
No "game-changing" language anywhere.

## Handoff

```
Handoff
- From skill: quaere-prospect
- Blocking question: does stdin input fit real user pipelines without breaking the
  one-file-in/one-file-out contract?
- Confirmed inputs: O-001 stdin input — verified gap, beneficiary + demand (#50,
  main.rs TODO) + validation probe
- Inconclusive inputs: SVG discoverability (already built; docs fix, not a build)
- Required next skill: quaere-execution (the approach is obvious — read stdin when
  no file arg) — run the Step 5 probe as its success criterion
- Stop condition: probe confirms ≥2 users run the pipeline before stdin ships
```

Note the handoff is to `execution`, not `invention`: the *how* here is obvious, so
no solution-divergence is needed. invention would be the next skill only if the
hard part were the approach itself.

## What the wishlist version would have looked like

Without the gate, the same prompt yields: "Add SVG export, support more formats,
add a live dashboard, add more tests, and add CI." Four of those five are already
done, out of scope, or beneficiary-less — and the one real opportunity (stdin) is
buried with no evidence and no probe. That is the failure prospect exists to stop.
