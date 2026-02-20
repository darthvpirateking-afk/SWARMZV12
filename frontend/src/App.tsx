import { FormEvent, useMemo, useState, type CSSProperties } from "react";
import { apiPost } from "./api/client";
import { BootstrapPage } from "./pages/BootstrapPage";
import { ApiFoundationPage } from "./pages/ApiFoundationPage";
import { DatabaseLayerPage } from "./pages/DatabaseLayerPage";
import { OperatorAuthPage } from "./pages/OperatorAuthPage";
import { CompanionCorePage } from "./pages/CompanionCorePage";
import { BuildMilestonesPage } from "./pages/BuildMilestonesPage";

type Role = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: Role;
  text: string;
}

interface CompanionResponse {
  ok?: boolean;
  reply?: string;
  error?: string;
  detail?: string;
}

function makeMessage(role: Role, text: string): ChatMessage {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    role,
    text,
  };
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    makeMessage("assistant", "SWARMZ chat ready."),
  ]);
  const [text, setText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSend = useMemo(
    () => !isSending && text.trim().length > 0,
    [isSending, text],
  );

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const outbound = text.trim();
    if (!outbound || isSending) {
      return;
    }

    setError(null);
    setIsSending(true);
    setText("");
    setMessages((prev) => [...prev, makeMessage("user", outbound)]);

    try {
      const payload = await apiPost<CompanionResponse>(
        "/v1/companion/message",
        { text: outbound },
      );

      if (payload.ok === false) {
        throw new Error(payload.error || payload.detail || "Request failed");
      }

      const replyText =
        typeof payload.reply === "string"
          ? payload.reply
          : "No reply returned.";
      setMessages((prev) => [...prev, makeMessage("assistant", replyText)]);
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Request failed.";
      setError(message);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <header>
          <h1 style={styles.title}>SWARMZ Frontend Chat</h1>
          <p style={styles.subtitle}>
            Companion endpoint: /v1/companion/message
          </p>
        </header>

        <BootstrapPage />
        <ApiFoundationPage />
        <DatabaseLayerPage />
        <OperatorAuthPage />
        <CompanionCorePage />
        <BuildMilestonesPage />

        <section style={styles.messages}>
          {messages.map((message) => (
            <article
              key={message.id}
              style={{
                ...styles.message,
                ...(message.role === "user"
                  ? styles.userMessage
                  : styles.assistantMessage),
              }}
            >
              <p style={styles.role}>
                {message.role === "user" ? "You" : "SWARMZ"}
              </p>
              <p style={styles.text}>{message.text}</p>
            </article>
          ))}
          {isSending ? (
            <article style={{ ...styles.message, ...styles.assistantMessage }}>
              <p style={styles.role}>SWARMZ</p>
              <p style={styles.text}>Thinking...</p>
            </article>
          ) : null}
        </section>

        <form onSubmit={onSubmit} style={styles.form}>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Type a message"
            rows={4}
            disabled={isSending}
            style={styles.textarea}
          />
          <button type="submit" disabled={!canSend} style={styles.button}>
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>

        {error ? <p style={styles.error}>{error}</p> : null}
      </section>
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: "100vh",
    margin: 0,
    padding: "clamp(12px, 4vw, 24px)",
    display: "grid",
    placeItems: "center start",
    background: "#0d1218",
    color: "#e9edf3",
    fontFamily: "Inter, Segoe UI, Arial, sans-serif",
  },
  card: {
    width: "min(860px, 100%)",
    background: "#17202a",
    border: "1px solid #2e3b4a",
    borderRadius: "14px",
    padding: "clamp(12px, 3vw, 18px)",
    display: "grid",
    gap: "14px",
  },
  title: {
    margin: 0,
    fontSize: "1.3rem",
  },
  subtitle: {
    margin: "6px 0 0",
    color: "#9fb2c8",
    fontSize: "0.9rem",
  },
  messages: {
    display: "grid",
    gap: "10px",
    maxHeight: "56vh",
    overflowY: "auto",
  },
  message: {
    borderRadius: "10px",
    padding: "10px",
  },
  userMessage: {
    background: "#2b4054",
  },
  assistantMessage: {
    background: "#232d38",
  },
  role: {
    margin: "0 0 6px",
    fontSize: "0.78rem",
    textTransform: "uppercase",
    color: "#9bc6ef",
  },
  text: {
    margin: 0,
    whiteSpace: "pre-wrap",
    lineHeight: 1.4,
  },
  form: {
    display: "grid",
    gap: "10px",
  },
  textarea: {
    width: "100%",
    resize: "vertical",
    minHeight: "96px",
    borderRadius: "9px",
    border: "1px solid #3a4f64",
    background: "#111922",
    color: "#e9edf3",
    padding: "10px",
    font: "inherit",
  },
  button: {
    justifySelf: "end",
    border: "1px solid #3d6e9e",
    background: "#24527a",
    color: "#f3f8ff",
    borderRadius: "8px",
    padding: "10px 16px",
    minHeight: "44px",
    cursor: "pointer",
    font: "inherit",
  },
  error: {
    margin: 0,
    color: "#ff9b9b",
  },
};
