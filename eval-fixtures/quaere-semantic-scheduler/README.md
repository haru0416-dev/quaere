# Fixture: quaere-semantic on `src/scheduler.ts` (with handoff)

Used by the eval scenario `semantic-handoff-to-quaere-execution`. The user prompt asks the agent to read `src/scheduler.ts` deeply, then end with a handoff to `quaere-execution` for refactoring the retry-ordering branch — not to refactor in this turn.

## What the agent sees

- `src/scheduler.ts` — a `RetryScheduler` with a sorted in-memory queue, retry count tracking, and a max-attempts cap (~45 lines).

## Properties / invariants the agent should surface

- **Sort order is two-key.** `priority` DESC primary, `attempts` ASC secondary. Same-priority jobs prefer fewer-tried; this is fairness/anti-starvation, not just a tiebreak. A reader who says only "sorts by priority" is paraphrasing.
- **`enqueue` may throw on retry.** A job at `maxAttempts - 1` survives `enqueue()` once but throws on the next `retry()` call (which increments first, then re-enqueues). The throw site is inside `retry()`, surfacing as a caller exception with no graceful path.
- **`retry()` mutates the caller's `Job` reference.** `job.attempts += 1` is observable to the caller after the call returns. A future caller that retains references to retried jobs will see the bumped counter.
- **`queue.sort()` is in-place and runs only on enqueue.** If a caller mutates `job.priority` outside `enqueue`, the queue's order silently goes stale until the next enqueue.
- **No concurrent-access guard.** Concurrent `enqueue()` and `dequeue()` are unsafe under any runtime that allows parallel JS execution (worker threads, multiple event loops); the array operations are not atomic.
- **`size()` is the only public observability.** No event emitted on enqueue / dequeue; no inspection of pending jobs without dequeuing.

## Backward and forward slice

- Backward (←): the `maxAttempts` constructor parameter; the caller's `Job.priority` and `Job.attempts` values.
- Forward (→): callers of `dequeue()` (workers that pull and execute jobs) and the global behavior of any system that depends on retry ordering or max-attempt enforcement. A retry-ordering refactor changes both the worker behavior and the queue mutation contract.

## What a paraphrase reading would miss

- The two-key sort and its anti-starvation purpose.
- The fact that `retry()` is the only path that can throw (since `enqueue()` from external callers is presumed safe under valid `Job.attempts`).
- The mutation-on-the-caller's-reference contract.
- The stale-after-external-mutation consequence of in-place sort.

## Expected handoff at end of review

Per the v2 SKILL contract, the review must end with a Handoff block to `quaere-execution` listing:

- relevant units (the sort comparator inside `enqueue`, the retry path)
- invariants to preserve (two-key sort order, throw on exhausted attempts, `retry` mutates caller's job)
- risk hotspots (in-place sort + concurrent calls; the throw inside `retry`)
- suggested first implementation unit

The agent must NOT refactor in this turn.
