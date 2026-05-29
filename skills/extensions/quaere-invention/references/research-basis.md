# Research basis for the invention probe

Why this skill forces structured escape from a named default instead of asking the
model to "be creative." Each claim below is grounded in published work; the
SKILL.md Iron Law cites the two load-bearing ones inline.

## The default-basin problem (why "be creative" is not enough)

- **LLM output homogenizes.** Anderson, Shah & Kreminski (2024), "Homogenization
  Effects of Large Language Models on Human Creative Ideation," *Creativity &
  Cognition '24* (arXiv:2402.01536). A 36-participant, 1271-idea study found that
  using an LLM makes ideas more similar *across different users* — assistance pulls
  people toward a shared mean rather than widening the space.
- **Novel but not diverse.** Si, Yang & Hashimoto (2024), "Can LLMs Generate Novel
  Research Ideas?" (arXiv:2409.04109). With 100+ researchers, LLM-generated ideas
  were rated more novel than human ones but lacked diversity in generation (the
  model keeps proposing variations on the same few directions).

Together these motivate step 1 (name the default basin) and step 4 (force *different*
mechanisms, not more samples of the same one).

## Novelty is its own axis, not a synonym for quality

- **Multi-axis evaluation.** CreativityPrism — Hou et al. (2025), "A Holistic
  Evaluation Framework for Large Language Model Creativity" (arXiv:2510.20091).
  Evaluates creativity on **quality, novelty, and diversity**; finds performance
  rarely transfers across axes and novelty correlates weakly or negatively with the
  others. Grounds the rule that novelty must be scored separately (step 5's fixed
  labels), not folded into "this looks good."

This is why the novelty filter uses five flat labels and forbids self-rated "truly
novel" language: a model that scores its own originality will conflate
impressive-sounding with novel.

## Novelty alone is not creativity — appropriateness is required

- **The standard definition.** Runco & Jaeger (2012), "The Standard Definition of
  Creativity," *Creativity Research Journal* 24(1):92–96 (DOI
  10.1080/10400419.2012.650092). Creativity requires *both* originality and
  effectiveness/appropriateness; credits Stein (1953) as the origin. A weird answer
  that does not fit the constraints is not creative — it is just wrong.
- **Operationalized for LLMs.** Nakajima, Zuiderveld & Pezzelle (2026), "Beyond
  Divergent Creativity: A Human-Based Evaluation of Creativity in Large Language
  Models," *Findings of EACL 2026* (arXiv:2601.20546). Argues divergence metrics
  ignore appropriateness and proposes conditioning novelty on appropriateness; notes
  alignment can make outputs more appropriate but less creative.

This grounds step 2 (constraint frame) and step 6 (kill-probe): a candidate is only
worth promoting if it both escapes the default *and* could survive contact with the
real constraints.

## Structured operators beat free-form prompting

- "Examining and Addressing Barriers to Diversity in LLM-Generated Ideas"
  (arXiv:2602.20408): chain-of-thought reduces fixation and persona conditioning
  improves coverage; combined, structured prompting exceeds human idea diversity.
  Supports the use of named mutation operators (step 4) over an open "brainstorm"
  prompt. (Classic human SCAMPER-vs-brainstorming evidence is statistically weak, so
  the skill grounds this in LLM-era work, not SCAMPER folklore.)

## Optional mechanistic note

- Verbalized Sampling (arXiv:2510.01171) traces LLM mode collapse to typicality bias
  in preference data — a mechanism-level account of *why* the default basin is so
  deep. Useful background; not required reading for the skill.

## Verification status

All citations above were checked against arXiv / ACL Anthology. CreativityPrism and
Beyond Divergent Creativity were fetched directly (title, authors, abstract
confirmed); the rest were confirmed via search with lateral corroboration. The
CreativityPrism title is "Evaluation Framework" (the earlier "Benchmark" wording was
a v1 title) — cite the framework form.
