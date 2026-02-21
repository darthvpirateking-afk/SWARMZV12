import type { CompanionResponse } from "../types/chat";

const baseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const operatorKey = (import.meta.env.VITE_OPERATOR_KEY as string | undefined) ?? "";

export async function sendCompanionMessage(text: string): Promise<string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(operatorKey ? { "x-operator-key": operatorKey } : {}),
  };

  const response = await fetch(`${baseUrl}/v1/companion/message`, {
    method: "POST",
    headers,
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status} ${response.statusText}`);
  }

  const data: CompanionResponse = await response.json();

  if (!data.ok) {
    throw new Error(`Companion API error: ${data.error ?? data.detail ?? "Unknown error"}`);
  }

  return data.reply;
}
