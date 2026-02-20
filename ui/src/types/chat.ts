export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
  timestamp: string;
}

export interface CompanionSuccessResponse {
  ok: true;
  reply: string;
  source?: string;
  provider?: string;
  model?: string;
  latencyMs?: number;
  warning?: string;
}

export interface CompanionErrorResponse {
  ok: false;
  error?: string;
  detail?: string;
}

export type CompanionResponse = CompanionSuccessResponse | CompanionErrorResponse;
