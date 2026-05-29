---
name: quaere-execution
description: "This skill should be used whenever the user authorizes multi-step coding implementation: applying a plan, finishing a feature, implementing review feedback, writing tests, making a refactor, or turning a specification into working code. It enforces a Plan → Do → Study → Act implementation loop with scoped units, fresh verification evidence, diff review, fix loops, and commit/push discipline so the agent does not blind-patch, batch unrelated changes, claim success without tests, or commit unless explicitly authorized. Do not use for trivial one-line edits, command-only requests, or pure explanations."
compatibility: Designed for Claude Code, Codex, Opencode, and Agent Skills-compatible coding agents with file, shell, test, and git access.
license: MIT
---

# Execution Loop

## Iron Law

**No implementation success claim without fresh verification evidence and a reviewed diff that maps every changed line to the authorized scope.**

This is not a paperwork rule. Implementation drift usually happens after the edit: the agent sees a green-looking result, forgets which requirement justified each change, and declares done before studying the actual diff. The loop is Plan → Do → Study → Act: predict what will prove the unit, make the smallest scoped edit, compare the observed result to the prediction, then either fix, split, or hand off. A passing broad suite is useful, but it does not replace the targeted check or the scope review.


## When to use

- The user asks to implement, build, finish, apply a plan, execute a TODO list, refactor, add tests, or address review feedback.
- The work has more than one meaningful step, touches several files, or needs targeted and final checks.
- A confirmed claim from `quaere-evidence`, constraints from `quaere-grounding`, or invariants from `quaere-semantic` are ready to implement.

## When NOT to use

- Trivial one-line edits, typo/format-only changes, pure explanations, or single command requests.
- Unclear bugs, flaky tests, risky review claims, security-sensitive causes, or production-side effects whose cause is not confirmed; use `quaere-evidence` first (or the `quaere-audit` extension for property-driven security work, if installed).
- Current SDK/API/CLI behavior that has not been anchored; use `quaere-grounding` first.

## Handoff triggers (when to switch out)

Stop and hand off when the blocker is no longer implementation:

- Cause of a failing test or regression is unclear → `quaere-evidence`.
- Implementation depends on current SDK / API / CLI / cloud / advisory behavior that is not yet anchored → `quaere-grounding`.
- Existing module intent or invariants are unclear → `quaere-semantic`.
- Security properties or auth / tenancy / parser / concurrency / crypto / payment / sandbox risks come up → stop before patching beyond a confirmed fix. If the `quaere-audit` extension is installed, hand off to it; otherwise flag the security risk and escalate to the user.

The standard handoff payload (Confirmed inputs / Inconclusive inputs / Required next skill / Stop condition) is documented at the end of this file under "Handoff to other skills".

## Core model

```text
Contract       requested outcome, authorization, constraints, non-goals, safety limits
Plan           smallest reviewable units with prediction and check
Do             minimal scoped edit for one unit; no drive-by refactors
Study          targeted verification + diff review against contract and prediction
Fix            smallest correction, then re-run the failed check and review again
Act            finish, split, hand off, or commit only if explicitly authorized
Handoff        what changed, evidence, residual risks, commit status
```

Prefer small, reviewable changes. Behavior changes, refactors, tests, dependency/config updates, and generated artifacts should be separate units unless keeping them together is the smallest coherent change. If the diff becomes hard to review, pause and split instead of continuing.

## Depth control

Choose the lightest loop that protects correctness:

- **Micro loop (one small unit; human equivalent ~5–15 min)** — one local edit or test-only addition. State the target, success check, edit, diff review, and verification. No full unit table needed.
- **Standard loop (feature/fix/review feedback; ~30–90 min)** — several ordered units. Use a checklist or todo list, one unit in progress at a time, targeted checks per unit, final gate at the end.
- **Persistent execution log (large/risky/batched; 2h+)** — many units, migrations, generated files, or likely handoff. Keep durable notes of units, checks, review findings, and open items.

Do not let the checklist become the work. Scale output down for small tasks, but never skip: contract → scoped plan → edit → study diff/checks → act.

## Preconditions

- Read the user request, existing plan/spec/review comments, `CONTEXT.md` if present, relevant repository instructions, and nearby code before editing.
- Read files before editing them.
- Confirm whether implementation and commit are authorized. Implementation authorization is not commit or push authorization.
- Do not refactor adjacent code unless the plan or confirmed fix requires it.
- Do not broaden scope silently. If a larger design decision appears, stop and ask.

**Stop now — hard stops (full list under "Stop condition" at the end):** stop and ask before broadening scope or making a larger design decision; commit or push only when explicitly authorized; do not declare done until the final verification gate passes; stop after the fix-loop budget rather than re-running the same failing check.

## Workflow

### 1. Contract

Restate the working contract:

- outcome requested
- files/systems likely involved
- explicit constraints, non-goals, and safety limits
- source-of-truth inputs: plan, issue, spec, review comment, prior skill handoff
- expected checks and success criteria
- implementation authorized? commit authorized? push authorized?

If implementation authorization is absent or ambiguous, stop and ask; do not edit files. If commit or push authorization is absent, implementation may proceed only if authorized, but those side effects must not happen.

**Conditional authorization.** When the user's authorization is conditioned on a check (e.g., "commit if all tests pass", "commit if the diff stays under N lines", "push only if I confirm"), the side effect is permitted only when *recorded fresh evidence in this session* shows the condition holds. State the condition, run the checks that resolve it, and quote the result in the Study/Commit sections. If the evidence is missing, partial, or stale, the condition is unverified — do not perform the side effect, and report the missing evidence rather than declaring the condition met. Conditional authorization is not pre-authorization; it is "authorization upon proof," and the proof is the agent's job.

If the source of truth is an ordered plan or review checklist, preserve its order unless code evidence proves a dependency requires reordering. Say why when you reorder.

### 2. Plan smallest reviewable units

For each non-trivial unit, record:

```text
Unit: <what will change>
Reason: <requirement / confirmed claim / invariant / constraint>
Prediction: <what should be true after this unit>
Check: <targeted command, test, typecheck, lint, manual check, or "not run because ...">
Depends on: <prior unit or handoff, if any>
```

Use a todo list or markdown checklist for multi-step work. Keep exactly one unit in progress. If a unit mixes behavior change and cleanup, split it unless the cleanup is mechanically required to make the behavior change compile.

### 3. Do one unit

Before editing, re-read the unit's Reason and Prediction. Make the smallest change that satisfies the unit. Avoid drive-by cleanup, broad renames, formatting churn, unrelated dependency changes, generated artifacts, or local-only files.

If verification fails and the cause is unclear, switch to `quaere-evidence` with the failing command and suspected hypothesis. Do not stack speculative patches.

### 4. Study: targeted check + diff review

A unit is not complete when the edit is done. Study both evidence channels:

**Verification contract.** Record the check result with one of these labeled forms:

```
Before check:
  FAIL: <command / result>        ← shows the defect existed before the fix
  PASS baseline: <command>        ← baseline passing suite is still clean
  N/A: <reason>                   ← if no before-state check was possible

After check:
  PASS: <command / result>
  FAIL: <command / result and remaining issue>
```

Success claim is allowed only when: diff was reviewed, final verification is fresh, and unrelated or generated changes are either justified or reverted.

**Generated files, lockfiles, snapshots, and build output** are allowed in the commit only when named in the Contract or required by the verification. If a tool modifies them as a side effect, either justify the inclusion or revert and re-stage without them.

1. **Targeted check:** run the unit's check when feasible. Use the verification contract above. For test-only changes, confirm the test asserts behavior rather than implementation trivia.
2. **Compare observed result to the unit's Prediction.** The Plan step recorded what should be true after this unit; the Study step is where that prediction is tested. If the observed result matches the prediction, the unit's mental model held. If it diverges in an *unexpected* way (the test passes for a different reason than predicted, or fails for a cause the prediction did not name), the divergence is information about the model — record it and either route to the Fix loop with a corrected prediction or hand off to `quaere-evidence` if the cause is unclear. PDSA's value is in this comparison, not in running the check; running without comparing reduces the loop to Plan-Do-Commit.
3. **Diff review:** inspect the actual diff and ask:
   - Does every changed line map to the unit Reason or a dependency?
   - Did the change preserve behavior outside the requested scope?
   - Did any secret, generated artifact, local state, or unrelated file enter the diff?
   - Is the change small enough for a reviewer to understand and roll back?

For risky, security-sensitive, database, concurrency, external API, flaky-test, or multi-file changes, use a fresh reviewer/subagent when available before finalizing.

### 5. Fix loop

If a check or review finds a problem:

```text
Finding: <concrete mismatch>
Cause: <known cause, or UNKNOWN -> quaere-evidence>
Fix: <smallest correction>
Re-check: <targeted check to rerun>
```

Apply one fix, rerun the relevant check, and review the new diff. If the same class of issue repeats or two fix attempts fail, stop and hand off with evidence instead of looping indefinitely.

### 6. Final verification gate

After all units pass their targeted checks, run the final gate appropriate to the project and risk:

- targeted checks for changed behavior
- integration checks for interacting units
- typecheck/lint/build when conventional for the repository
- full suite when feasible for multi-file or high-risk work
- final diff-vs-contract review

**The Study section MUST end with a labeled `Final gate:` line** that names the command run and its result, or explicitly records the skip. Emit it even when the gate did not run:

```text
Final gate: PASS — <command> (e.g. python -m unittest discover tests, cargo test, pnpm test)
Final gate: FAIL — <command>; <one-line cause>; routed to Fix loop or handed off
Final gate: skipped because <reason>; best next command: <command-to-run-later>
```

Do not say "done", "fixed", "passes", "ready", or commit based on stale or assumed results, and do not omit the `Final gate:` line.

### 7. Commit / push discipline

Commit only when the user explicitly authorized a commit. Push only when the user explicitly authorized push/publication.

Before committing:

- inspect status, staged/unstaged diff, and recent commit style
- stage only relevant files
- avoid secrets, local state, generated noise, and unrelated files
- use a message that explains the purpose of the change

**Pre-commit hooks.** When a pre-commit hook fails, the commit *did not happen*. Running `git --amend` at this point would modify the *previous* (unrelated) commit, not the failed-and-not-created one. The correct response is: read the hook's output, fix the underlying issue, re-stage the fix, and create a *new* commit. When a hook *modifies* files (formatter, linter autofix), the modifications are unstaged after the failed commit; review them, stage them if appropriate, and create the new commit. Do not amend, force-push, skip hooks (`--no-verify`), or rewrite history unless explicitly requested and safe.

### 8. Handoff

The output is the *workflow itself* — Contract / Plan / Study (with Final gate) / Commit sections from steps 1-7, in that order, with concrete content. Do not collapse them into a separate "Implemented / Verification" summary; the workflow IS the report. After the Commit section, append exactly one trailing section:

```text
Open items
- <remaining risk, skipped check, or next step>
- <or "none" if the loop closed cleanly>
```

The full output therefore reads top-to-bottom as:

```text
Contract
- ...

Plan
- Unit 1: ... Reason: ... Prediction: ... Check: ...
- Unit 2: ...

Study
- Unit 1 targeted check (before/after edit): ...
- Unit 2 targeted check: ...
- Diff review: ...
- Final gate: PASS — <command>   (or: Final gate: skipped because <reason>; best next command: <cmd>)

Commit
- <hash/message> or "not committed because <reason>"
- Push: not performed (or: "<reason if explicitly authorized>")

Open items
- ...
```

This is the same structure the worked example uses. There is no separate report template — the workflow's section headers are the report's section headers.

## Worked example

A bad-output (edit-first) vs good-output (full Contract → Plan → Do → Study → Act) example, applied to a `calculate_total` quantity fix, is at [`references/worked-example.md`](references/worked-example.md). Read it when the loop's section structure feels abstract — it shows what each section actually contains end-to-end.

## Common drift modes

Rationalizations that fragment the loop ("I'll just make all the edits, then test once.", "The broad suite passed, so the bug is fixed.", "Commit is part of finishing.", etc.) and the corresponding actual failures are at [`references/anti-patterns.md`](references/anti-patterns.md). Read it when a unit seems to be "done" but the diff or targeted check has not been confirmed.

## Handoff to other skills

When handing off, emit this standard block:

```
Handoff
- From skill: quaere-execution
- Blocking question: <what blocked implementation — unclear cause, ungrounded fact, or security risk>
- Confirmed inputs: <units completed, tests passing, diffs reviewed — safe to treat as done>
- Inconclusive inputs: <units deferred, skipped checks, or open risks — not safe to treat as complete>
- Required next skill: <quaere-evidence | quaere-grounding | quaere-semantic | (quaere-audit, if the extension is installed)>
- Stop condition: <what the next skill must return before implementation can resume>
```

Switch out when the blocker is no longer implementation:

- Cause of a failing test/regression becomes unclear → `quaere-evidence` with the failing command, Findings, and suspected hypothesis.
- Implementation depends on current SDK/API/CLI/cloud/advisory behavior → `quaere-grounding` with the unconfirmed external claim and local anchor.
- Existing module intent/invariants are unclear → `quaere-semantic` with the relevant files/symbols and intended change.
- Security properties, auth/tenancy/parser/concurrency/crypto/payments/sandbox risks arise → stop before patching beyond a confirmed fix. If the `quaere-audit` extension is installed, hand off to it; otherwise flag the security risk and escalate to the user.

Resume only after the companion skill returns an actionable decision, constraint, or invariant.

## Stop condition

This skill is complete when:

- every planned unit is completed, verified, reviewed, or explicitly deferred with a reason
- targeted checks are recorded as pass / fail / not run with reason
- final gate and final diff-vs-contract review are recorded
- commit/push side effects match explicit authorization
- the handoff names residual risks, skipped checks, and next steps

Do not extend into adjacent polish, broad cleanup, or opportunistic refactors. End the loop and report.
