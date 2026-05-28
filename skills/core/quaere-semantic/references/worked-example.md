# Worked example — semantic review applied to `TokenCache.get`

A full-shape illustration of the seven-field analysis under the operational test. See `../SKILL.md` for the procedure that this example enacts.


**Input** (`src/cache.ts`):

```typescript
class TokenCache {
  private entries = new Map<string, { value: string; expiry: number }>();

  get(key: string): string | undefined {
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    if (entry.expiry < Date.now()) {
      this.entries.delete(key);
      return undefined;
    }
    return entry.value;
  }
}
```

### Bad output (paraphrase)

```text
TokenCache.get @ src/cache.ts:5
  What:        Looks up an entry, deletes if expired, returns the value.
  Why:         Caching for performance.
  Invariants:  Map is non-null.
  Failure:     Returns undefined on miss.
  Connections: Used elsewhere.
```

Why this fails: apply genuine semantic-preserving rewrites — rename `expiry` to `validUntil`, hoist `Date.now()` to `const now = Date.now()`, swap `entry.expiry < Date.now()` to its mirror `Date.now() > entry.expiry` (mirror, not negation: `>=` would change boundary behavior at `expiry == now`) — every line of this Bad analysis still applies unchanged. The agent never engaged the semantics. `Why: caching for performance` is a fabricated guess (no certainty marker, no probe). `Used elsewhere` skips the slice analysis. `Returns undefined on miss` describes the success path, not a failure mode.

### Good output

```text
TokenCache.get @ src/cache.ts:5
  What (mechanical):    Look up the key in the map. If a stored entry exists and has not yet expired (eviction triggers when stored expiry is strictly less than the current clock reading; the boundary `expiry == now` returns the value), return the entry's value. Otherwise delete the entry and return undefined.
  What (domain intent): Single-process TTL cache read with read-time eviction.
  Why:                  plausible — read-time eviction (vs background sweep) keeps the hot path simple but limits us to single-process.
                        confident — `expiry` comparison must use the same clock as the writer; no skew tolerance is encoded.
                        UNKNOWN — probe: `git blame src/cache.ts:11` to confirm whether read-time eviction was deliberate or a leftover from a removed background sweeper.
  Invariants:           expiry is wall-clock ms; writers and readers share a clock. Map access is single-threaded (no lock taken). Eviction is best-effort: a concurrent reader may observe `entry` after another reader's delete.
  Failure:              Stale entry returned across machine clock skew (multi-process deployment). Memory growth if a key is written but never re-read — eviction is read-driven, not time-driven. No iteration safety: a caller iterating `entries` while `get` runs would see a concurrent delete (no current caller does, but the type does not forbid it).
  Connections (←):      `Date.now()` (clock dependency); writes from `set()` and `delete()`; constructor (allocates a fresh Map per instance).
  Connections (→):      Direct callers (grep): `AuthMiddleware.verify` (rejects on undefined), `RefreshScheduler.shouldRefresh` (returns true on undefined). No cache-invalidation bus; downstream readers never see eviction events.
```

Operational test verdict: the semantic-preserving rewrites listed above (rename `expiry` → `validUntil`, hoist `Date.now()` to a local, mirror `<` to `>`) do not change any of these seven answers — the mechanical line refers to roles ("the key", "the entry", "the current clock reading"), not literal identifiers. The analysis is anchored on what the code *means*, not on how it is *spelled*.

