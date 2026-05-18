# Acme AI SDK latest documentation

The current 2.x SDK uses the Responses API:

```ts
const result = await client.responses.create({
  model: "acme-large-2026-02",
  instructions: "Summarize the input in one sentence.",
  input: text,
});
```

This file intentionally represents a newer major version than the local
lockfile. It is useful evidence only after a version-fit check confirms the
project has migrated to 2.x.
