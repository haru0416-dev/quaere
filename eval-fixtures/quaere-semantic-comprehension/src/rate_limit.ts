// Token-bucket limiter. Refill is lazy and CONTINUOUS: on each check we add
// (elapsed_ms / refillIntervalMs) tokens — a fractional amount — and keep the
// fractional remainder, so many small frequent checks don't lose tokens to
// integer truncation. `capacity` is a hard clamp so a long idle period can never
// produce a burst larger than `capacity`.
export class RateLimiter {
  private tokens: number;
  private last: number;

  constructor(
    private readonly capacity: number,
    private readonly refillIntervalMs: number,
  ) {
    this.tokens = capacity;
    this.last = 0;
  }

  allow(now: number): boolean {
    const elapsed = now - this.last;
    this.last = now;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed / this.refillIntervalMs);
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }
    return false;
  }
}
