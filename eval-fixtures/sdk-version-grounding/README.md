This fixture gives `quaere-grounding` evaluations concrete local evidence.

The project is pinned to `acme-ai-sdk` 1.4.0. Local type definitions under
`types/acme-ai-sdk/index.d.ts` expose `client.messages.create(...)`, while the
checked-in `docs/latest-acme-ai-sdk.md` describes a newer 2.x-only
`client.responses.create(...)` API. A grounded agent should prefer the local
lockfile and installed types for this workspace instead of treating the latest
docs as applicable.
