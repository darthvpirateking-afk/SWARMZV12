import type { CSSProperties } from "react";
import type {
  BuildMilestonesPromoteResponse,
  BuildMilestonesStatus,
} from "../types/buildMilestones";

interface BuildMilestonesCardProps {
  status: BuildMilestonesStatus | null;
  promoteResult: BuildMilestonesPromoteResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onPromote: (targetStage: number) => void;
}

export function BuildMilestonesCard({
  status,
  promoteResult,
  loading,
  error,
  onRefresh,
  onPromote,
}: BuildMilestonesCardProps) {
  return (
    <section style={styles.card}>
      <header style={styles.header}>
        <h2 style={styles.title}>BUILD Milestones</h2>
        <div style={styles.actions}>
          <button style={styles.button} onClick={onRefresh} disabled={loading} type="button">
            {loading ? "Refreshing..." : "Refresh"}
          </button>
          <button
            style={styles.button}
            onClick={() => onPromote(30)}
            disabled={loading || status?.current_stage === 30}
            type="button"
          >
            Promote to 30
          </button>
        </div>
      </header>

      {status ? (
        <p style={styles.meta}>
          Current: {status.current_stage} · Target: {status.target_stage} · Total: {status.total_stages}
        </p>
      ) : null}

      {status ? (
        <div style={styles.grid}>
          {status.stages.map((stage) => (
            <div key={stage.stage} style={styles.stageCard}>
              <p style={styles.stageTitle}>{stage.title}</p>
              <p style={styles.stageMeta}>{stage.status}</p>
            </div>
          ))}
        </div>
      ) : null}

      {promoteResult ? <p style={styles.ok}>{promoteResult.message}</p> : null}
      {promoteResult && promoteResult.applied_stages.length > 0 ? (
        <p style={styles.meta}>
          Applied this run: BUILD {promoteResult.applied_stages[0].stage} → BUILD {promoteResult.applied_stages[promoteResult.applied_stages.length - 1].stage}
        </p>
      ) : null}

      {status && status.history.length > 0 ? (
        <div style={styles.historyList}>
          {status.history.slice(-8).reverse().map((entry) => (
            <p key={`${entry.stage}-${entry.executed_at}`} style={styles.historyItem}>
              {entry.title} · {entry.status} · {new Date(entry.executed_at).toLocaleString()}
            </p>
          ))}
        </div>
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
    gap: "8px",
  },
  title: {
    margin: 0,
    fontSize: "1rem",
  },
  actions: {
    display: "flex",
    gap: "8px",
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
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
    gap: "8px",
    maxHeight: "220px",
    overflowY: "auto",
  },
  stageCard: {
    border: "1px solid #2e3b4a",
    borderRadius: "8px",
    padding: "8px",
    background: "#111922",
  },
  stageTitle: {
    margin: 0,
    color: "#dbe8f6",
    fontSize: "0.85rem",
    fontWeight: 600,
  },
  stageMeta: {
    margin: "4px 0 0",
    color: "#9fb2c8",
    fontSize: "0.8rem",
    textTransform: "uppercase",
  },
  ok: {
    margin: 0,
    color: "#9df5bf",
  },
  historyList: {
    border: "1px solid #2e3b4a",
    borderRadius: "8px",
    padding: "8px",
    background: "#0f161f",
    display: "grid",
    gap: "4px",
    maxHeight: "150px",
    overflowY: "auto",
  },
  historyItem: {
    margin: 0,
    color: "#a8bbcf",
    fontSize: "0.8rem",
  },
  error: {
    margin: 0,
    color: "#ff9b9b",
  },
};
