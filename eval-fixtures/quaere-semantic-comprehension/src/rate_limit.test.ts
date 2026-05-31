import { RateLimiter } from "./rate_limit";

// Pins the two non-obvious invariants the implementation relies on.

test("carries fractional tokens across frequent calls (no truncation loss)", () => {
  const rl = new RateLimiter(2, 1000); // capacity 2, 1 token per 1000ms
  expect(rl.allow(0)).toBe(true); // start clamped to capacity 2 -> 1
  expect(rl.allow(0)).toBe(true); // 1 -> 0
  expect(rl.allow(0)).toBe(false); // 0 tokens
  expect(rl.allow(1500)).toBe(true); // +1.5 -> 1.5, consume -> 0.5 carried
  expect(rl.allow(1500)).toBe(false); // 0.5 < 1, remainder was NOT discarded
  expect(rl.allow(2000)).toBe(true); // +0.5 -> 1.0, consume -> 0
});

test("a long idle period never bursts beyond capacity", () => {
  const rl = new RateLimiter(2, 1000);
  rl.allow(0);
  rl.allow(0); // drain to 0
  expect(rl.allow(3_600_000)).toBe(true); // 1h idle refills, but clamps to 2 -> 1
  expect(rl.allow(3_600_000)).toBe(true); // 1 -> 0
  expect(rl.allow(3_600_000)).toBe(false); // clamp prevented a burst > capacity
});
