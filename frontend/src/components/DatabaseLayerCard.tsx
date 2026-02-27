import type { CSSProperties } from "react";
import type {
  DatabaseCollections,
  DatabaseStats,
  DatabaseStatus,
} from "../types/databaseLayer";

interface DatabaseLayerCardProps {
  status: DatabaseStatus | null;
  collections: DatabaseCollections | null;
  stats: DatabaseStats | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function DatabaseLayerCard({
  status,
  collections,
  stats,
  loading,
  error,
  onRefresh,
}: DatabaseLayerCardProps) {
  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>Database Layer</h2>
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
        <p style={styles.meta}>
          Engine: {status.engine} · Dir: {status.data_dir}
        </p>
      ) : null}

      {stats ? (
        <p style={styles.meta}>
          Missions: {stats.mission_rows} · Audit: {stats.audit_rows} ·
          Quarantined: {stats.quarantined_rows}
        </p>
      ) : null}

      <ul style={styles.list}>
        {(collections?.collections ?? []).map((entry) => (
          <li key={entry.name}>
            {entry.name}: {entry.exists ? "ok" : "missing"} ({entry.size_bytes}{" "}
            bytes)
          </li>
        ))}
      </ul>
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
};
