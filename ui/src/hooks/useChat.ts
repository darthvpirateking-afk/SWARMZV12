import { useMemo, useState } from "react";
import { sendCompanionMessage } from "../lib/api";
import type { ChatMessage } from "../types/chat";

function createMessage(role: ChatMessage["role"], text: string): ChatMessage {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    role,
    text,
    timestamp: new Date().toISOString(),
  };
}

const initialMessages: ChatMessage[] = [
  createMessage("assistant", "SWARMZ Companion ready. Ask me anything."),
];

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSend = useMemo(() => !isSending, [isSending]);

  async function sendMessage(text: string) {
    if (!canSend) {
      return;
    }

    const userText = text.trim();
    if (!userText) {
      return;
    }

    setError(null);
    setIsSending(true);

    setMessages((prev) => [...prev, createMessage("user", userText)]);

    try {
      const reply = await sendCompanionMessage(userText);
      setMessages((prev) => [...prev, createMessage("assistant", reply)]);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Failed to send message.";
      setError(message);
    } finally {
      setIsSending(false);
    }
  }

  return {
    messages,
    isSending,
    error,
    sendMessage,
  };
}
