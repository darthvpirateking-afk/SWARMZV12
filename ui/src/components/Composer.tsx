import { FormEvent, useState } from "react";

interface ComposerProps {
  onSend: (text: string) => Promise<void>;
  isSending: boolean;
}

export function Composer({ onSend, isSending }: ComposerProps) {
  const [text, setText] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const outgoing = text.trim();
    if (!outgoing || isSending) {
      return;
    }

    setText("");
    await onSend(outgoing);
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <label htmlFor="chat-input" className="sr-only">
        Message
      </label>
      <textarea
        id="chat-input"
        className="composer-input"
        placeholder="Type your message..."
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={3}
        disabled={isSending}
      />
      <button type="submit" className="composer-button" disabled={isSending || !text.trim()}>
        {isSending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}
