# Profile separation — layered skills, assembled per agent

Status: Implemented for `quaere-evidence` (pilot); remaining skills follow after
eval gates. 2026-07-27.

## The problem, measured

Three independent measurements against the same skill set (2026-07-27, ward
harness on `gpt-5.6-sol-fast` for the GPT rows, `claude -p` on Sonnet 5 for the
Claude rows; n=1 per cell; injection format identical to `run_skill_evals.py`):

| measurement | result |
| --- | --- |
| Full skill set, 6 scenarios, GPT | weighted cost **×1.83** vs baseline; worst single skill `quaere-evidence` at ×4.1 input |
| `quaere-evidence` full vs gate+method-only (61 lines), 2 scenarios, GPT | **×3.04 → ×1.31**, identical verdicts on every run |
| Same A/B on Sonnet 5 | full ×4.01, lean ×2.65 — and **baseline already produced the correct verdict in all 6 runs** |
| Discovery test (token-bucket fixture), Sonnet 5 | baseline found all three invariants unaided; the skill added only the marker vocabulary, at ×1.5 |

Two conclusions:

1. **The gate carries the effect; the ceremony carries the cost.** On GPT, the
   61-line gate+method subset reached the same decisions as the 260-line
   original at 43% of the cost. This matches OpenAI's published guidance that
   leaner prompts score higher (their figure: +10–15% while cutting 41–66% of
   tokens) and that rigid output-format over-specification hurts performance.
2. **Skill needs are model-dependent.** Claude 5-generation models already carry
   the restraint and grounding discipline the core skills teach; what they
   lack is only the shared reporting vocabulary.

Historical note: the Codex ~220-line read cap (`docs/Codex skill read
depth.md`) originally motivated shorter bodies, but the upstream cause was
fixed (openai/codex#16479, closed 2026-06-19). The lean profile does not rest
on it: the measured cost, OpenAI's lean-prompt guidance, and length-dependent
degradation (context rot — model-agnostic, no hard truncation required) are
the standing reasons. The validator's 200-line anchor checks are now a house
length budget rather than a workaround, and relaxing them is a separate
decision.

## The design

Skills stay **single-source**: one `SKILL.md` per skill, with sections wrapped
in layer tags that render as plain HTML comments:

```markdown
<!-- quaere:layer gate -->
## Iron Law
...
<!-- /quaere:layer -->
```

| layer | content | who needs it |
| --- | --- | --- |
| `gate` | the load-bearing rule, the claim shape, decision labels | everyone — this is also the output contract |
| `method` | probe budgets, ordering, autonomy policy, handoffs | GPT-family agents |
| `pedagogy` | deep forms (6-field / 10-field), state files, worked-example pointers | humans, and agents doing Deep-tier investigations |

`quaere install` assembles a **profile** from those layers at install time:

| profile | layers | intended target |
| --- | --- | --- |
| `full` (default) | gate + method + pedagogy | unchanged behavior; the canonical text |
| `lean` | gate + method | Codex / GPT agents (assembles to ~115 lines) |
| `contract` | gate | Claude-family agents |
| `auto` | per target dir | codex → lean, claude → contract |

```bash
quaere install --profile auto        # codex gets lean, claude gets contract
quaere install codex --profile lean
```

Untagged skills install identically under every profile, so conversion can
proceed skill by skill. The installed profile is recorded in the manifest and a
profile change forces reinstallation.

## Delivery-layer note for Claude

Claude 5-generation models weight always-on instruction files less than
before (observed in the field; n=1 reports), while content that arrives
on-demand — a loaded skill — is followed faithfully (our A/B: the marker
vocabulary was adopted in 100% of skill-loaded runs). The `contract` profile
targets exactly that delivery layer: a short skill whose value is a shared
reporting vocabulary, not process instruction. Rules that must hold on *every*
turn belong in a hook (e.g. `UserPromptSubmit`, ~50 tokens/message) rather
than in a skill; that wiring is documentation, not installer behavior.

## Eval gates before rollout

The in-tree assertions currently match label lines (`Warrant:`, `C-\d+`) and so
are coupled to the pedagogy-layer forms. Before converting further skills or
flipping any default:

1. Rewrite assertions process-first (does a falsifier exist and was a probe
   run), so `lean`/`contract` outputs grade on substance.
2. Sweep {codex, claude} × {full, lean, contract} on the suite; the existing
   Phase B/C/D invariance bands apply (±5pp).
3. Only then consider making `auto` the default.

## Follow-ups

- Convert the remaining core skills and `quaere-audit` to tagged sources.
- Process-first assertion rewrite (above).
- A `claude` hook snippet for the always-on contract, shipped as documentation.
