# Common drift modes and anti-patterns for the invention probe

A divergence skill collapses back into hype in recognizable ways. The first column is
the rationalization the agent produces; the second is what is actually happening. See
`../SKILL.md` for the procedure each entry is contrasting against.

| Rationalization | What's actually happening |
| --- | --- |
| "This idea is genuinely novel / groundbreaking." | Self-rated originality. The model conflates impressive-sounding with novel. Use the five fixed labels; a real general-novelty claim is a `quaere-grounding` prior-art task, not a self-assessment. |
| "I generated ten ideas, that's plenty of divergence." | Volume, not divergence. Ten variations on one operator explore one axis. The gate is *at least four different operators against different assumptions*, not a high count. |
| "The default is obviously bad, no need to state it." | Skipping step 1. If the default basin is not named, "escaping it" is unauditable — and the model usually drifts back to a relative of the unnamed default anyway. |
| "This recombination of X and Y is a new invention." | Overselling recombination. A new mix of known parts is `recombination`, a real and useful label — but calling it invention removes the honest signal the classification exists to give. |
| "It's a great idea; the test can come later." | Skipping the kill-probe. A candidate with no disconfirming test is `genuinely uncertain`, not promotable. The probe is what separates an invention from a nicer-sounding default. |
| "I'll design a probe that shows it works." | Confirmation probe, not a kill-probe. Step 6 asks for the smallest test that could *kill* the idea. A test that can only succeed proves nothing. |
| "It breaks the assumption, so the constraints don't matter." | Divergence without appropriateness. An idea that escapes the default but violates a hard constraint is not creative, it is wrong (Runco & Jaeger 2012). Check it against step 2's hard constraints before promoting. |
| "I picked the best candidate for the user." | Overreach. Invention ends at a small set of candidates with kill-probes and a handoff. Choosing the winner and building it is `quaere-execution`'s job after the user decides. |

## Anti-patterns (each explains why it fails)

- **Producing impressive prose instead of named mechanisms.** "A revolutionary
  paradigm shift in how we think about X" asserts novelty without naming what default
  it left or how. It fails because there is nothing to audit or kill — it is the
  average answer in a louder voice.
- **Treating divergence as the deliverable.** Stopping after step 4 ships a pile of
  options with no novelty labels and no probes. It fails because unfiltered
  divergence is just sampling; the value is in the honest classification and the
  kill-probe.
- **Inventing where the obvious answer is correct.** Running this skill on a task whose
  best solution is the standard one adds risk and noise. It fails because invention is
  a gate against *settling too early*, not a mandate to be different when different is
  worse.
