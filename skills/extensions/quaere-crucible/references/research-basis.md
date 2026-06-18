# Research basis

Why crucible gates interrogation the way it does. Every citation below was
verified against its primary source before being used; the claims attached to
each are scoped to what the source actually supports.

## The grounded failure mode

Asked to pressure-test a held position, an RLHF-trained model does not reliably
attack it. Two measured behaviors define the failure:

- **Sycophancy under rebuttal.** Models endorse a user's counterargument more
  when it is framed as a follow-up than when evaluated neutrally, are *more*
  persuaded when the rebuttal carries detailed-but-incorrect reasoning, and cave
  more to casual than to formal feedback — a grill can land on turn 1 and fold
  on the very next turn under a single rebuttal *(Kim & Khashabi 2025,
  "Challenging the Evaluator: LLM Sycophancy Under User Rebuttal", Findings of
  EMNLP 2025, arXiv:2509.16533; a two-turn study — no multi-turn timeline is
  claimed)*. This is the
  direct basis for the flip rule: `survived` may be granted only on new evidence
  or a defended rebuttal, never on confident-but-unverified pushback.

- **The softball grill.** Absent a forced disconfirming move, the model asks
  confirmatory questions and signs off on plausibility. Telling it to "be
  skeptical" is the weak fix: an externally imposed *consider-the-opposite*
  produces correction where demand-laden "be fair and unbiased" instructions do
  not *(Lord, Lepper & Preston 1984, JPSP 47(6):1231-1243)*. So crucible
  mandates a named falsifier and a named alternative, rather than an exhortation
  to try harder.

## Why intensity is bounded (the opposite vice)

Maximal adversariality is its own failure. Two boundaries cap it:

- **Manufacturing doubt.** Naive self-challenge ("are you sure?") can flip a
  *correct* answer; the cure is demanding latent counter-evidence on
  load-bearing claims, not blanket doubt. crucible therefore triages by stakes
  and leaves trivial/already-verified claims alone.
- **Too-many-counterarguments backfire.** Asking for a long list of
  counterarguments reduces their impact, because the difficulty of generating
  many is misread as "there must be few" *(Sanna, Schwarz & Stocker 2002,
  JEP:LMM 28(3):497-502; cf. Hirt & Markman 1995)*. So challenges are capped to
  a few high-quality ones per claim. (Note: the ease-of-retrieval paradigm has
  replication debate — this is a design cap, not a load-bearing proof.)

## Adversariality is not the cure — the gate is

crucible does not claim that "red-teaming works." Structured analytic techniques
and dedicated red-teaming lack strong, sustained empirical support and can
introduce new distortions *(Chang, Berdini, Mandel & Tetlock 2018, Intelligence
and National Security 33(3):337-356)*. The value crucible adds is specific: a
*falsification gate with a verdict*. The popular "Grill Me" prompt *(Pocock,
aihero.dev)* is field-evidence of the appetite and contributes the anti-stall
mechanic (state your own recommended answer), but it stops at "shared
understanding" with no ruling — the gap the blessing vocabulary
(`blessed` / `blessed-narrowed` / `blocked` / `unresolved gap`) closes.

## Why the evidence spine

crucible reuses `quaere-evidence`'s Finding → Falsifier → Defense → Decision
discipline, turned outward: the falsifier becomes a *question put to a target*
and the Decision becomes a *per-claim Verdict + a terminal Blessing*. Same
falsifiability core, different locus (the target, not a claim the agent owns)
and stance (interrogate outward, before commitment, conversationally). When a
challenge needs an executed probe, crucible hands that one claim back to
`quaere-evidence` rather than running code itself.

## Dropped citation

An earlier draft attributed "a bare 'could you be wrong?' flips correct answers
and is phrasing-sensitive" to Hills 2025 (arXiv:2507.10124). Verification showed
that paper argues the opposite (generic metacognitive doubt helps *because* it
is unspecified), so the claim was removed rather than shipped misattributed —
the same standard the skill enforces on its targets.
