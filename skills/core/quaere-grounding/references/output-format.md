# Output format for external grounding

The standard report template for an external-grounding pass. See `../SKILL.md` for what each field captures and which decisions justify each label.


```text
External grounding
- External surface:
- Stale risk:
- Local anchor:
- No-network fallback strategy: applied|not needed
  1. cached/vendored content (path + cache date) or N/A
  2. user-facing stale-data notice or N/A
  3. canonical URL(s) for the user to fetch and report back, or N/A

Claims
- EG-001:
  Claim:
  Source:
  Source quality:
  Version fit:
  Conflict check:
  Executable probe:
  Lateral check:
  Decision:

Implementation constraints
- Use:
- Do not use:
- Required migration or compatibility note:
- Verification needed during quaere-execution:

Handoff
- Confirmed facts:
- Conflicted or inconclusive facts:
- URLs / local paths:
- Required next skill:
- Stop condition:
```

When the handoff crosses to another skill, also emit the full inter-skill payload block (From skill / Blocking question / Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) from `../SKILL.md`'s "Handoff to other skills" section.
