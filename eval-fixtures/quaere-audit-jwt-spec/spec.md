# Protocol: API Authentication Tokens

## Token format

All inter-service requests carry a JWT signed with HS256 using a shared per-service secret.

## Required claims

Tokens MUST include:

- `sub` — the calling user's identifier.
- `aud` — the receiving service's identifier (e.g., `"invoices"`, `"billing"`).
- `iat` — issued-at timestamp in Unix seconds.

## Validation requirements

A receiver MUST reject a token if any of the following hold:

1. The HS256 signature does not verify against the receiver's secret.
2. The `aud` claim does not match the receiver's own service identifier.
3. The token is older than 1 hour: `iat + 3600 < now()`.
4. The `aud` claim is absent or is not a string.
5. The `iat` claim is absent or is not a number.

A token failing any of conditions 1–5 MUST NOT be treated as authenticating any user.
