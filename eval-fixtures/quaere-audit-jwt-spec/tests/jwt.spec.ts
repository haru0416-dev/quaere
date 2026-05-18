import { verifyJWT } from '../src/protocol/jwt';
import { createHmac } from 'crypto';

const SECRET = 'test-secret';

function makeToken(payload: object): string {
  const header = Buffer.from(
    JSON.stringify({ alg: 'HS256', typ: 'JWT' }),
  ).toString('base64url');
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const signature = createHmac('sha256', SECRET)
    .update(`${header}.${body}`)
    .digest('base64url');
  return `${header}.${body}.${signature}`;
}

describe('verifyJWT', () => {
  test('valid token passes', () => {
    const token = makeToken({
      sub: 'user-1',
      aud: 'invoices',
      iat: Math.floor(Date.now() / 1000),
    });
    const result = verifyJWT(token, SECRET);
    expect(result.valid).toBe(true);
  });

  test('wrong signature rejected', () => {
    const token = makeToken({
      sub: 'user-1',
      aud: 'invoices',
      iat: Math.floor(Date.now() / 1000),
    });
    const result = verifyJWT(token, 'wrong-secret');
    expect(result.valid).toBe(false);
  });
});
