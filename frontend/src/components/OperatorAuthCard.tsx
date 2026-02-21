import { useState, type CSSProperties } from "react";
import type {
  OperatorAuthStatus,
  OperatorAuthVerifyResponse,
} from "../types/operatorAuth";

interface OperatorAuthCardProps {
  status: OperatorAuthStatus | null;
  verifyResult: OperatorAuthVerifyResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onVerify: (operatorKey: string) => void;
}

export function OperatorAuthCard({
  status,
  verifyResult,
  loading,
  error,
  onRefresh,
  onVerify,
}: OperatorAuthCardProps) {
  const [operatorKey, setOperatorKey] = useState("");

  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>Operator Auth</h2>
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
          Mode: {status.auth_mode} · configured:{" "}
          {status.key_configured ? "yes" : "no"}
        </p>
      ) : null}

      <div style={styles.row}>
        <input
          type="password"
          value={operatorKey}
          onChange={(event) => setOperatorKey(event.target.value)}
          placeholder="Operator key"
          style={styles.input}
        />
        <button
          type="button"
          style={styles.button}
          disabled={loading || operatorKey.trim().length === 0}
          onClick={() => onVerify(operatorKey)}
        >
          Verify
        </button>
      </div>

      {verifyResult ? (
        <p style={verifyResult.authenticated ? styles.ok : styles.error}>
          {verifyResult.message}
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
  },
  input: {
    flex: 1,
    borderRadius: "8px",
    border: "1px solid #3a4f64",
    background: "#111922",
    color: "#e9edf3",
    padding: "8px",
    font: "inherit",
  },
  button: {
    border: "1px solid #3d6e9e",
    background: "#24527a",
    color: "#f3f8ff",
    borderRadius: "8px",
    padding: "6px 10px",
    cursor: "pointer",
    font: "inherit",
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
