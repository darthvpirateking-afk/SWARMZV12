import type { ChatMessage } from "../types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  isSending: boolean;
}

export function MessageList({ messages, isSending }: MessageListProps) {
  return (
    <section className="messages" aria-live="polite" aria-label="Chat messages">
      {messages.map((message) => (
        <article key={message.id} className={`message message-${message.role}`}>
          <p className="message-role">{message.role === "user" ? "You" : "SWARMZ"}</p>
          <p className="message-text">{message.text}</p>
        </article>
      ))}

      {isSending ? (
        <article className="message message-assistant">
          <p className="message-role">SWARMZ</p>
          <p className="message-text">Thinking...</p>
        </article>
      ) : null}
    </section>
  );
}
