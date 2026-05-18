/**
 * Per-key token-bucket rate limiter.
 *
 * Used by API gateway middleware to throttle calls per tenant. Each tenant
 * gets its own bucket on first request; subsequent calls refill the bucket
 * at a constant rate up to a fixed capacity.
 */
class RateLimitCache {
  private buckets = new Map<string, { tokens: number; lastRefill: number }>();
  private readonly capacity: number;
  private readonly refillRatePerMs: number;

  constructor(capacity: number, refillRatePerSecond: number) {
    this.capacity = capacity;
    this.refillRatePerMs = refillRatePerSecond / 1000;
  }

  consume(key: string, weight: number = 1): boolean {
    const now = Date.now();
    const bucket =
      this.buckets.get(key) ?? { tokens: this.capacity, lastRefill: now };

    const elapsed = now - bucket.lastRefill;
    bucket.tokens = Math.min(
      this.capacity,
      bucket.tokens + elapsed * this.refillRatePerMs,
    );
    bucket.lastRefill = now;

    if (bucket.tokens < weight) {
      this.buckets.set(key, bucket);
      return false;
    }

    bucket.tokens -= weight;
    this.buckets.set(key, bucket);
    return true;
  }

  reset(key: string): void {
    this.buckets.delete(key);
  }
}

export { RateLimitCache };
