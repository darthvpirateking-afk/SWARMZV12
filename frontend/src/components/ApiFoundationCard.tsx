import type { CSSProperties } from "react";
import type {
  ApiFoundationDomains,
  ApiFoundationStatus,
} from "../types/apiFoundation";

interface ApiFoundationCardProps {
  status: ApiFoundationStatus | null;
  domains: ApiFoundationDomains | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function ApiFoundationCard({
  status,
  domains,
  loading,
  error,
  onRefresh,
}: ApiFoundationCardProps) {
  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>API Foundation</h2>
        <button
          style={styles.button}
          onClick={onRefresh}
          disabled={loading}
          type="button"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {error ? <p style={styles.error}>{error}</p> : null}

      {status ? (
        <>
          <p style={styles.meta}>
            API {status.api_version} · routes {status.route_count}
          </p>
          <p style={styles.meta}>
            Capabilities: {status.capabilities.join(", ")}
          </p>
        </>
      ) : (
        <p style={styles.meta}>No API status loaded yet.</p>
      )}

      <p style={styles.domainLabel}>Domains:</p>
      <p style={styles.domainText}>
        {(domains?.domains ?? status?.domains ?? []).join(", ") || "none"}
      </p>
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
  domainLabel: {
    margin: "2px 0 0",
    color: "#d8e2ec",
    fontWeight: 600,
  },
  domainText: {
    margin: 0,
    color: "#c8d5e2",
  },
  error: {
    margin: 0,
    color: "#ff9b9b",
  },
};
