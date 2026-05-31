export type Session = {
  token: string;
  userId: string;
  issuedAt: number;
  refreshCount: number;
};

const sessions = new Map<string, Session>();

const TTL_MS = 15 * 60_000;
const CLOCK_SKEW_MS = 90_000;
const MAX_REFRESH = 3;

export function isExpired(s: Session, now: number): boolean {
  return now - s.issuedAt > TTL_MS - CLOCK_SKEW_MS;
}

export function refresh(
  oldToken: string,
  mint: (userId: string) => string,
  now: number,
): string | null {
  const s = sessions.get(oldToken);
  if (!s) return null;
  if (s.refreshCount >= MAX_REFRESH) {
    sessions.delete(oldToken);
    return null;
  }
  if (isExpired(s, now)) {
    sessions.delete(oldToken);
    return null;
  }
  const next = mint(s.userId);
  sessions.set(next, {
    token: next,
    userId: s.userId,
    issuedAt: now,
    refreshCount: s.refreshCount + 1,
  });
  sessions.delete(oldToken);
  return next;
}

export function revokeAll(userId: string): void {
  for (const [k, v] of sessions) {
    if (v.userId === userId) sessions.delete(k);
  }
}
