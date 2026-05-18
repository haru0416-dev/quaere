import type { Request, Response, NextFunction } from 'express';

export interface AuthRequest extends Request {
  user?: { id: string; orgId: string };
}

/**
 * Authenticate a request by validating the Bearer JWT and attaching the
 * decoded user (id + orgId) to req.user. Does not perform per-resource
 * authorization; that is the route handler's responsibility.
 */
export function authenticate(
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): void {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'unauthorized' });
    return;
  }
  const token = authHeader.slice(7);
  const user = verifyJWT(token);
  if (!user) {
    res.status(401).json({ error: 'invalid token' });
    return;
  }
  req.user = user;
  next();
}

function verifyJWT(token: string): { id: string; orgId: string } | null {
  // Stub for the audit fixture. In production this verifies HS256 signature
  // and decodes the payload. For the audit, assume any non-empty token is
  // valid and returns a user with both id and orgId populated.
  if (!token) return null;
  return { id: 'user-1', orgId: 'org-A' };
}
