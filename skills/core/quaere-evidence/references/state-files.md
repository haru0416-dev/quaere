# State files for durable investigations

For investigations that span sessions or carry many claims, persist the useful
subset of a per-target ledger. See `../SKILL.md` for the workflow these files record.

```text
.agent-state/
  targets/
    <task-or-issue-slug>/
      findings.md
      hypotheses.md
      review-claims.md
      defenses.md
      probes.md
      session-log.md
      handoff.md
```

Use the templates in `../templates/`. Do not create all seven by default;
`findings.md`, `probes.md`, and `handoff.md` are often enough. If the user does not
want files written, keep the same structure in the response.

## Git handling for state files

Treat `.agent-state/` as local investigation state by default:

- Do not commit `.agent-state/` unless the user explicitly wants the investigation
  ledger preserved as a project artifact.
- Prefer adding `.agent-state/` to `.gitignore` when state files are useful but
  local-only.
- Before committing, inspect status and ensure no private logs, credentials,
  production data, or noisy scratch files from `.agent-state/` are staged.
- If handoff notes are part of the deliverable, ask whether they should live under
  `.agent-state/`, project docs, an issue/PR comment, or the final response.
