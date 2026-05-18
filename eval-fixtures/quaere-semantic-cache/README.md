# Fixture: quaere-semantic on `src/cache.ts`

Used by the eval scenario `semantic-understanding-before-change`. The agent is asked to read `src/cache.ts` deeply before any change.

## What the agent sees

- `src/cache.ts` — a per-key token-bucket `RateLimitCache` (~40 lines, single class). Distinct from the `TokenCache` shown in the SKILL's worked example so the agent must analyze fresh, not pattern-match.

## Properties / invariants the agent should surface (for human review of the eval output)

A semantically grounded analysis should at least name:

- **Single-instance scope.** `buckets` lives in the constructed object; multi-instance / multi-process deployments do not share state, so global rate limits are not enforced.
- **Process restart resets all buckets.** The state is in-memory only.
- **Date.now() monotonicity is an unstated precondition.** A backwards clock adjustment makes `elapsed` negative and reduces `tokens` below the previous value. Forward jumps over-credit. Either direction silently changes the limit.
- **Floor on `bucket.tokens` is implicit.** The class never floors at 0 explicitly; tokens stay non-negative only because the rejection branch returns before decrementing. A future edit that decrements unconditionally would silently allow negative tokens.
- **`bucket.lastRefill` is updated even on rejection.** Load shedding still costs a per-key state write. High-volume rejection traffic still mutates the map.
- **No concurrent-access guard.** Map access is single-threaded under Node.js but not in worker threads or other runtimes; behavior is undefined under concurrent `consume()` on the same key.
- **`reset(key)` deletes the bucket.** Next `consume(key)` reinitializes at full capacity — usable as an admin override but also a footgun if called on a misbehaving caller (their abuse limit resets).

## Backward and forward slice

- Backward (←): `Date.now()`, the constructor parameters `capacity` and `refillRatePerSecond`, and any earlier mutations of `bucket.tokens` (none external).
- Forward (→): callers of `consume()` use the boolean to gate downstream API access; callers of `reset()` are typically admin endpoints. There is no event emitted on bucket state change.

## What a paraphrase reading would miss

- The rejection-still-writes side effect.
- Clock-skew sensitivity in either direction.
- The implicit floor, with its forward-compatibility risk.
- Multi-instance vs single-instance scope.

A `What (mechanical)` line that says only "checks if tokens are available and consumes them" without naming any of the above would be paraphrase. The operational test (rename `tokens` to `credits`, swap `Math.min(capacity, ...)` to a clamped sum, hoist `Date.now()` to a const) should not change a sound analysis; it would, however, change a name-anchored paraphrase.
