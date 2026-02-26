import React, {
  useState,
  useMemo,
  useEffect,
  useRef,
  type CSSProperties,
  FormEvent,
} from "react";
import { makeMessage, type ChatMessage } from "./utils/makeMessage";
import { apiPost } from "./utils/api";

type CompanionResponse = {
  ok: boolean;
  reply: string;
  error?: string;
  detail?: string;
};

// Avatar paths (ensure these exist in public/assets/)
const userAvatar = "/assets/my-avatar.png";
const assistantAvatar = "/assets/swarmz-assistant.png";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    makeMessage("assistant", "🧠 SWARMZ chat ready. Type to begin."),
  ]);
  const [text, setText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const canSend = useMemo(
    () => !isSending && text.trim().length > 0,
    [isSending, text]
  );

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const outbound = text.trim();
    if (!outbound || isSending) return;

    setText("");
    setError(null);
    setIsSending(true);
    setMessages((prev) => [...prev, makeMessage("user", outbound)]);

    try {
      const payload = await apiPost<CompanionResponse>(
        "/v1/companion/message",
        { text: outbound }
      );

      if (payload.ok === false) {
        throw new Error(payload.error || payload.detail || "Request failed");
      }

      const replyText =
        typeof payload.reply === "string"
          ? payload.reply
          : "No reply returned.";

      setMessages((prev) => [
        ...prev,
        makeMessage("assistant", replyText),
      ]);
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Request failed.";
      setError(message);
    } finally {
      setIsSending(false);
    }
  }

  function handleReset() {
    setMessages([makeMessage("assistant", "🧠 SWARMZ chat reset. Ready again.")]);
    setError(null);
    setText("");
  }

  function handleAttachFile() {
    alert("📎 File attachment coming soon!");
  }

  return (
    <div style={styles.bg}>
      <style>{globalAnimations}</style>
      <div style={styles.shell}>
        <header style={styles.header}>
          <h1 style={styles.title}>
            <span style={styles.gradientText}>🧠 SWARMZ</span> Future Chat
          </h1>
          <div style={styles.subline}>
            Next-gen assistant at{" "}
            <span style={styles.endpoint}>/v1/companion/message</span>
          </div>
        </header>

        <section style={styles.chatCard}>
          <div style={styles.messagesBox}>
            {messages.map((m, i) => (
              <FutureMessage
                key={m.id}
                role={m.role}
                text={m.text}
                index={i}
              />
            ))}
            {isSending && (
              <FutureMessage
                role="assistant"
                text="Thinking..."
                index={messages.length}
                loading
              />
            )}
            <div ref={messagesEndRef} />
          </div>

          <form
            style={styles.form}
            autoComplete="off"
            onSubmit={onSubmit}
            spellCheck={false}
          >
            <textarea
              placeholder="Type your message of the future…"
              style={styles.textarea}
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isSending}
              rows={2}
            />
            <div style={styles.buttonRow}>
              <button
                type="submit"
                style={{
                  ...styles.sendButton,
                  opacity: canSend ? 1 : 0.5,
                  cursor: canSend ? "pointer" : "not-allowed",
                }}
                disabled={!canSend}
              >
                {isSending ? "•••" : "🚀 Send"}
              </button>
              <button
                type="button"
                onClick={handleReset}
                style={styles.actionButton}
                disabled={isSending}
                title="Reset Chat"
              >
                🔄 Reset
              </button>
              <button
                type="button"
                onClick={handleAttachFile}
                style={styles.actionButton}
                disabled={isSending}
                title="Attach file (coming soon)"
              >
                📎
              </button>
            </div>
          </form>

          {error && <div style={styles.errorBanner}>{error}</div>}
        </section>

        <footer style={styles.footer}>
          <span style={{ color: "#606060" }}>
            © {new Date().getFullYear()} SWARMZ | v12.0 | MATRIX Edition
          </span>
        </footer>
      </div>
    </div>
  );
}

function FutureMessage({
  role,
  text,
  index,
  loading = false,
}: {
  role: "user" | "assistant";
  text: string;
  index: number;
  loading?: boolean;
}) {
  const avatarSrc = role === "user" ? userAvatar : assistantAvatar;

  return (
    <div
      style={{
        ...styles.messageRow,
        justifyContent: role === "user" ? "flex-end" : "flex-start",
        animation: `floatIn 0.5s cubic-bezier(0.32, 1.56, 0.56, 1) both`,
        animationDelay: `${index * 0.03 + 0.1}s`,
      }}
    >
      {role === "assistant" && (
        <img
          src={avatarSrc}
          alt="Assistant"
          style={{
            width: 38,
            height: 38,
            borderRadius: "50%",
            marginRight: 10,
            filter: "drop-shadow(0 1px 4px #24f7ff66)",
            background: "#1b2e41",
            objectFit: "cover",
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      )}
      <div
        style={{
          ...styles.bubble,
          ...(role === "user" ? styles.userBubble : styles.assistantBubble),
          ...(loading ? styles.loadingBubble : {}),
        }}
      >
        <span style={styles.meta}>
          {role === "user" ? "🧑 You" : "🤖 SWARMZ"}
        </span>
        <span style={styles.msgText}>{text}</span>
        {loading && <span style={styles.dots}>▯▯▯</span>}
      </div>
      {role === "user" && (
        <img
          src={avatarSrc}
          alt="User"
          style={{
            width: 38,
            height: 38,
            borderRadius: "50%",
            marginLeft: 10,
            filter: "drop-shadow(0 1px 4px #56c5fd66)",
            background: "#1b2e41",
            objectFit: "cover",
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      )}
    </div>
  );
}

const globalAnimations = `
  @keyframes floatIn {
    from {
      opacity: 0;
      transform: translateY(8px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }

  * {
    box-sizing: border-box;
  }

  html, body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  }
`;

const styles: Record<string, CSSProperties> = {
  bg: {
    background: "linear-gradient(135deg, #0a0e27 0%, #1b2e41 50%, #0f1929 100%)",
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "20px",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },

  shell: {
    width: "100%",
    maxWidth: "900px",
    background: "rgba(15, 25, 41, 0.6)",
    backdropFilter: "blur(20px)",
    border: "1px solid rgba(36, 247, 255, 0.2)",
    borderRadius: "16px",
    boxShadow:
      "0 8px 32px rgba(0, 0, 0, 0.3), 0 0 60px rgba(36, 247, 255, 0.1)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },

  header: {
    padding: "24px 28px",
    background: "linear-gradient(90deg, rgba(36, 247, 255, 0.05), rgba(86, 197, 253, 0.05))",
    borderBottom: "1px solid rgba(36, 247, 255, 0.15)",
  },

  title: {
    margin: "0 0 8px 0",
    fontSize: "24px",
    fontWeight: "700",
    color: "#ffffff",
  },

  gradientText: {
    background: "linear-gradient(90deg, #24f7ff, #56c5fd)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },

  subline: {
    fontSize: "13px",
    color: "#9ca3af",
    margin: 0,
  },

  endpoint: {
    color: "#24f7ff",
    fontFamily: "monospace",
    fontWeight: "600",
  },

  chatCard: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    overflow: "hidden",
    padding: "24px",
  },

  messagesBox: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    marginBottom: "20px",
    paddingRight: "8px",
  },

  messageRow: {
    display: "flex",
    alignItems: "flex-end",
    gap: "8px",
    animation: "floatIn 0.5s ease-out",
  },

  bubble: {
    maxWidth: "60%",
    padding: "12px 16px",
    borderRadius: "12px",
    wordBreak: "break-word",
    lineHeight: "1.5",
  },

  userBubble: {
    background: "linear-gradient(135deg, rgba(86, 197, 253, 0.2), rgba(36, 247, 255, 0.15))",
    border: "1px solid rgba(86, 197, 253, 0.4)",
    color: "#e0f2fe",
  },

  assistantBubble: {
    background: "linear-gradient(135deg, rgba(36, 247, 255, 0.1), rgba(59, 130, 246, 0.1))",
    border: "1px solid rgba(36, 247, 255, 0.3)",
    color: "#d1e7f7",
  },

  loadingBubble: {
    animation: "pulse 1.5s ease-in-out infinite",
  },

  meta: {
    fontSize: "11px",
    fontWeight: "600",
    color: "#64748b",
    display: "block",
    marginBottom: "4px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  msgText: {
    fontSize: "14px",
    display: "block",
  },

  dots: {
    fontSize: "10px",
    color: "#9ca3af",
    marginLeft: "4px",
    display: "inline-block",
    animation: "pulse 1.2s ease-in-out infinite",
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    borderTop: "1px solid rgba(36, 247, 255, 0.15)",
    paddingTop: "16px",
  },

  textarea: {
    width: "100%",
    padding: "12px 14px",
    background: "rgba(30, 41, 59, 0.5)",
    border: "1px solid rgba(36, 247, 255, 0.2)",
    borderRadius: "8px",
    color: "#e0f2fe",
    fontSize: "14px",
    fontFamily: "inherit",
    resize: "none",
    outline: "none",
    transition: "all 0.2s ease",
  },

  buttonRow: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },

  sendButton: {
    flex: 1,
    padding: "10px 16px",
    background: "linear-gradient(135deg, #24f7ff, #56c5fd)",
    color: "#0a0e27",
    border: "none",
    borderRadius: "8px",
    fontWeight: "600",
    fontSize: "14px",
    cursor: "pointer",
    transition: "all 0.2s ease",
    boxShadow: "0 4px 16px rgba(36, 247, 255, 0.3)",
  },

  actionButton: {
    padding: "10px 14px",
    background: "rgba(36, 247, 255, 0.1)",
    border: "1px solid rgba(36, 247, 255, 0.3)",
    color: "#24f7ff",
    borderRadius: "8px",
    font: "inherit",
    fontWeight: "500",
    fontSize: "14px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },

  errorBanner: {
    padding: "12px 14px",
    background: "rgba(239, 68, 68, 0.1)",
    border: "1px solid rgba(239, 68, 68, 0.3)",
    borderRadius: "8px",
    color: "#fca5a5",
    fontSize: "13px",
    marginTop: "8px",
  },

  footer: {
    padding: "12px 28px",
    borderTop: "1px solid rgba(36, 247, 255, 0.1)",
    textAlign: "center",
    fontSize: "12px",
    background: "rgba(10, 14, 39, 0.3)",
  },
};
