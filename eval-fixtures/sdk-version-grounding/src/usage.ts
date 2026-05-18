import { AcmeAI } from "acme-ai-sdk";

const client = new AcmeAI({ apiKey: process.env.ACME_API_KEY ?? "test-key" });

export async function summarize(text: string): Promise<string> {
  const result = await client.messages.create({
    model: "acme-small-2025-01",
    system: "Summarize the input in one sentence.",
    messages: [{ role: "user", content: text }],
  });

  return result.content[0].text;
}
