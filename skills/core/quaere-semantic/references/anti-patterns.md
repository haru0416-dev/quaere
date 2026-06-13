# Common drift modes + anti-patterns for semantic review

How the seven-field structure fails in practice — drift modes (rationalization vs. actual failure) and the recurring shapes that look like analysis but are paraphrase. See `../SKILL.md` for the procedure.


Even with this skill loaded, agents drift in recognizable ways. The first column is the rationalization the agent produces; the second is what is actually happening.

| Rationalization | What's actually happening |
| --- | --- |
| "The code is short and obvious, no semantic work needed." | Trivial-looking accessors and pure-looking functions carry the subtlest invariants (hidden caller discipline, accidental global reads). Run the operational test before declaring obvious. |
| "Why is unclear, but it's probably backward-compatibility." | The agent filled `Why` with a guess. Backward-compatibility is the most common fabrication. Mark `UNKNOWN — probe: git blame` and continue. |
| "Connections: used elsewhere." | The slice analysis was skipped. Both backward (←) and forward (→) slices must name concrete callers, state references, or environment dependencies. |
| "Invariants: types enforce this." | Some invariants are types; many are not (caller discipline, ordering, freshness, lock state, transaction boundary). Enumerate the non-type invariants explicitly, or write `none beyond types` only after checking against a test or argument. |
| "What and Why are the same idea expressed differently." | If both fields can be filled with the same sentence, the analysis is paraphrase. `What` is mechanical or domain behavior; `Why` is the constraint that justifies the chosen behavior. They cannot be substituted. |
| "I covered the major units; minor ones are not interesting." | Skipped units carry implicit contracts. Either cover them or write `skipped: <reason>`. The unmarked skip is the drift. |
| "Operational test passed because nothing seems to break." | The test is *whether the rewrite would change the analysis*, not whether the rewrite would compile. If the analysis is so vague that no rewrite could perturb it, the analysis is too shallow. |

## Anti-patterns (each item explains why it fails)

- **Paraphrasing code as prose.** "This function loops over items and checks each one" describes mechanics in different words. Paraphrase fails because it produces no falsifiable claim about behavior — a semantic-preserving rewrite cannot break what was never asserted. The operational test exists to surface this failure cheaply.

- **Inventing intent to fill `Why`.** Plausible-sounding explanations are exactly what the certainty marker is designed to surface. `UNKNOWN — probe: <step>` is more useful than a confident wrong answer; the probe converts uncertainty into a tractable next action. Inventing intent fails because future readers (including the same agent in a later session) treat fabricated `Why` as ground truth and build subsequent edits on it.

- **Skipping units that look obvious.** Accessors that secretly mutate, "pure" functions that depend on globals, branches that exist only for a single legacy caller — all fail this filter. Skipping fails because the skipped units are precisely where invariants live without enforcement; the seven-field structure exists to surface them.

- **Producing analysis and editing immediately.** This skill ends at understanding; implementation is a separate step the user must authorize. Editing during the review fails on two grounds. *Comprehension*: the analysis is no longer a frozen artifact, so a question raised by the edit ("does this still preserve the lock-state invariant we just identified?") cannot consult a stable reference — the agent ends up re-paraphrasing instead of consulting. *Workflow*: it merges two authorization scopes (review vs change), and any drift in the diff cannot be traced to a recorded invariant. Hand off to `quaere-execution` instead.

- **Compressing output to seem efficient.** The user accepted the comprehension cost by invoking this skill — full comprehension is the deliberate exception to everyday skimming. Compression fails because the deliverable *is* the analysis; a terser review is just paraphrase wearing different formatting.

## Deeper question templates (protocol/state, lifetime, ownership, reachability)

When the reason for code's shape is still unclear after tests, callers, and `git blame`, work these templates *(Sillito, Murphy & De Volder 2008; LaToza & Myers 2010 — empirically the hardest developer questions are about intent and reachability)*:

- What protocol does this object follow? What states can it be in?
- What is the lifetime of this state? Who creates it, who destroys it?
- Who owns this object's mutation? Single writer, multiple writers, none after construction?
- What invariants does the *caller* assume vs what the *callee* enforces?
- What is the reachability — who can reach this code and under what conditions?

