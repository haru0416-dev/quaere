import { createHmac } from 'crypto';

export interface JWTPayload {
  sub: string;
  aud?: string;
  iat?: number;
  exp?: number;
  [key: string]: unknown;
}

/**
 * Verify a JWT signed with HS256 and return its payload if valid.
 * Returns { valid: false } if the signature does not verify.
 */
export function verifyJWT(
  token: string,
  secret: string,
): { valid: boolean; payload?: JWTPayload } {
  const parts = token.split('.');
  if (parts.length !== 3) return { valid: false };
  const [header, payload, signature] = parts;

  const expectedSignature = createHmac('sha256', secret)
    .update(`${header}.${payload}`)
    .digest('base64url');

  if (signature !== expectedSignature) {
    return { valid: false };
  }

  const decoded: JWTPayload = JSON.parse(
    Buffer.from(payload, 'base64url').toString('utf-8'),
  );

  return { valid: true, payload: decoded };
}
