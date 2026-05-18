export interface AcmeAIOptions {
  apiKey: string;
}

export interface MessageRequest {
  model: string;
  system?: string;
  messages: Array<{ role: "user" | "assistant"; content: string }>;
}

export interface MessageResponse {
  content: Array<{ type: "text"; text: string }>;
}

export class AcmeAI {
  constructor(options: AcmeAIOptions);
  messages: {
    create(request: MessageRequest): Promise<MessageResponse>;
  };
}
