import type { CSSProperties } from "react";
import type { BootstrapStatus } from "../types/bootstrap";

interface BootstrapStatusCardProps {
  status: BootstrapStatus | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function BootstrapStatusCard({ status, loading, error, onRefresh }: BootstrapStatusCardProps) {
  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>Project Bootstrap</h2>
        <button style={styles.button} onClick={onRefresh} disabled={loading} type="button">
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {error ? <p style={styles.error}>{error}</p> : null}

      {status ? (
        <>
          <p style={styles.meta}>
            {status.service} · {status.environment} · v{status.version}
          </p>
          <ul style={styles.list}>
            <li>data dir: {status.checks.data_dir_exists ? "ok" : "missing"}</li>
            <li>audit log: {status.checks.audit_log_exists ? "ok" : "missing"}</li>
            <li>missions log: {status.checks.missions_log_exists ? "ok" : "missing"}</li>
          </ul>
          {status.warnings.length ? <p style={styles.warning}>Warnings: {status.warnings.join("; ")}</p> : null}
        </>
      ) : (
        <p style={styles.meta}>No bootstrap status loaded yet.</p>
      )}
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
  list: {
    margin: 0,
    paddingLeft: "1rem",
    color: "#d8e2ec",
    display: "grid",
    gap: "4px",
  },
  error: {
    margin: 0,
    color: "#ff9b9b",
  },
  warning: {
    margin: 0,
    color: "#ffd58a",
  },
};
