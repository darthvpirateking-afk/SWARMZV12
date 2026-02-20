import { useState, type CSSProperties } from "react";
import type {
  CompanionCoreMessageResponse,
  CompanionCoreStatus,
} from "../types/companionCore";

interface CompanionCoreCardProps {
  status: CompanionCoreStatus | null;
  messageResult: CompanionCoreMessageResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onMessage: (text: string) => void;
}

export function CompanionCoreCard({
  status,
  messageResult,
  loading,
  error,
  onRefresh,
  onMessage,
}: CompanionCoreCardProps) {
  const [text, setText] = useState("");

  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>Companion Core</h2>
        <button
          style={styles.button}
          onClick={onRefresh}
          disabled={loading}
          type="button"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {status ? (
        <p style={styles.meta}>
          Source: {status.source} · memory: v{status.memory_version} · outcomes:{" "}
          {status.outcomes_count}
        </p>
      ) : null}

      {status?.summary ? (
        <p style={styles.meta}>Summary: {status.summary}</p>
      ) : null}

      <div style={styles.row}>
        <input
          type="text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Message companion core"
          style={styles.input}
        />
        <button
          type="button"
          style={styles.button}
          disabled={loading || text.trim().length === 0}
          onClick={() => onMessage(text)}
        >
          Send
        </button>
      </div>

      {messageResult ? (
        <p style={messageResult.ok ? styles.ok : styles.error}>
          {messageResult.reply}
        </p>
      ) : null}

      {error ? <p style={styles.error}>{error}</p> : null}
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  card: {
    border: "1px solid #2e3b4a",
    borderRadius: "12px",
    padding: "12px",
    background: "#131b24",
    display: "grid",
    gap: "8px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    margin: 0,
    fontSize: "1rem",
  },
  row: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
    flexWrap: "wrap",
  },
  input: {
    flex: "1 1 180px",
    borderRadius: "8px",
    border: "1px solid #3a4f64",
    background: "#111922",
    color: "#e9edf3",
    padding: "10px",
    minHeight: "44px",
    font: "inherit",
  },
  button: {
    border: "1px solid #3d6e9e",
    background: "#24527a",
    color: "#f3f8ff",
    borderRadius: "8px",
    padding: "10px 14px",
    minHeight: "44px",
    cursor: "pointer",
    font: "inherit",
    flexShrink: 0,
  },
  meta: {
    margin: 0,
    color: "#b2c1d1",
  },
  ok: {
    margin: 0,
    color: "#9df5bf",
  },
  error: {
    margin: 0,
    color: "#ff9b9b",
  },
};
