import { type CSSProperties, useState } from "react";
import {
  colors,
  radii,
  shadows,
  spacing,
  typography,
} from "../theme/cosmicTokens";
import { useArtifactVault } from "../hooks/useArtifactVault";
import type { ArtifactStatus } from "../api/artifacts";

const STATUS_COLOR: Record<ArtifactStatus, string> = {
  PENDING_REVIEW: colors.warning,
  APPROVED: colors.running,
  REJECTED: colors.error,
  ARCHIVED: colors.textSecondary,
};

const STATUS_FILTERS: { label: string; value: ArtifactStatus | undefined }[] =
  [
    { label: "All", value: undefined },
    { label: "Pending", value: "PENDING_REVIEW" },
    { label: "Approved", value: "APPROVED" },
    { label: "Rejected", value: "REJECTED" },
    { label: "Archived", value: "ARCHIVED" },
  ];

export function ArtifactVaultPanel() {
  const [filter, setFilter] = useState<ArtifactStatus | undefined>(undefined);
  const { artifacts, stats, loading, error, actionError, refresh, approve, reject } =
    useArtifactVault(filter);

  return (
    <section style={styles.card}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h2 style={styles.title}>🗃️ Artifact Vault</h2>
          {stats && (
            <div style={styles.statRow}>
              <StatBadge
                label="Total"
                value={stats.total}
                color={colors.primaryAccent}
              />
              <StatBadge
                label="Pending"
                value={stats.pending_review}
                color={colors.warning}
              />
              <StatBadge
                label="Approved"
                value={stats.by_status["APPROVED"] ?? 0}
                color={colors.running}
              />
              <StatBadge
                label="Rejected"
                value={stats.by_status["REJECTED"] ?? 0}
                color={colors.error}
              />
            </div>
          )}
        </div>
        <button
          style={styles.refreshBtn}
          onClick={() => void refresh()}
          disabled={loading}
          title="Refresh"
        >
          {loading ? "…" : "↺"}
        </button>
      </div>

      {/* Filter tabs */}
      <div style={styles.filterRow}>
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.label}
            style={{
              ...styles.filterBtn,
              background:
                filter === f.value
                  ? `${colors.primaryAccent}22`
                  : "transparent",
              color:
                filter === f.value ? colors.primaryAccent : colors.textSecondary,
              borderColor:
                filter === f.value ? colors.primaryAccent : colors.borderColor,
            }}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <p style={styles.errorText}>{error}</p>}
      {actionError && (
        <p style={{ ...styles.errorText, color: colors.warning }}>
          Action failed: {actionError}
        </p>
      )}

      {/* Artifact list */}
      <div style={styles.list}>
        {artifacts.length === 0 && !loading && (
          <p style={styles.empty}>No artifacts found.</p>
        )}
        {artifacts.map((a) => (
          <div key={a.id} style={styles.row}>
            <div style={styles.rowLeft}>
              <span style={styles.artifactType}>{a.type}</span>
              <span style={styles.artifactTitle}>{a.title}</span>
              {a.mission_id && (
                <span style={styles.missionTag}>
                  mission:{a.mission_id.slice(0, 8)}
                </span>
              )}
              {a.version > 1 && (
                <span style={{ ...styles.missionTag, color: colors.secondaryAccent }}>
                  v{a.version}
                </span>
              )}
            </div>
            <div style={styles.rowRight}>
              <span
                style={{
                  ...styles.statusBadge,
                  color: STATUS_COLOR[a.status],
                  borderColor: STATUS_COLOR[a.status],
                }}
              >
                {a.status.replace("_", " ")}
              </span>
              {a.status === "PENDING_REVIEW" && (
                <>
                  <button
                    style={{ ...styles.actionBtn, color: colors.running }}
                    onClick={() => void approve(a.id)}
                    title="Approve"
                  >
                    ✓
                  </button>
                  <button
                    style={{ ...styles.actionBtn, color: colors.error }}
                    onClick={() => void reject(a.id)}
                    title="Reject"
                  >
                    ✗
                  </button>
                </>
              )}
              <span style={styles.ts}>
                {new Date(a.created_at).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function StatBadge({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <span
      style={{
        padding: `2px ${spacing.sm}`,
        borderRadius: radii.full,
        border: `1px solid ${color}44`,
        background: `${color}12`,
        color,
        fontSize: typography.fontSizeSm,
        fontFamily: typography.fontFamily,
        fontWeight: typography.fontWeightBold,
      }}
    >
      {label}: {value}
    </span>
  );
}

const styles: Record<string, CSSProperties> = {
  card: {
    background: colors.cardBg,
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.lg,
    padding: spacing.lg,
    display: "grid",
    gap: spacing.md,
    boxShadow: shadows.card,
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: spacing.md,
    flexWrap: "wrap",
  },
  headerLeft: {
    display: "flex",
    flexDirection: "column",
    gap: spacing.sm,
  },
  title: {
    margin: 0,
    fontSize: typography.fontSizeXl,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  statRow: {
    display: "flex",
    gap: spacing.sm,
    flexWrap: "wrap",
  },
  refreshBtn: {
    background: "transparent",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.md,
    color: colors.primaryAccent,
    cursor: "pointer",
    fontFamily: typography.fontFamily,
    fontSize: "1.1rem",
    padding: `${spacing.xs} ${spacing.sm}`,
    minHeight: 36,
    minWidth: 36,
  },
  filterRow: {
    display: "flex",
    gap: spacing.xs,
    flexWrap: "wrap",
  },
  filterBtn: {
    padding: `${spacing.xs} ${spacing.sm}`,
    border: "1px solid",
    borderRadius: radii.full,
    cursor: "pointer",
    fontFamily: typography.fontFamily,
    fontSize: typography.fontSizeSm,
    fontWeight: typography.fontWeightMedium,
    transition: "all 0.15s",
    minHeight: 30,
  },
  list: {
    display: "grid",
    gap: spacing.xs,
    maxHeight: 480,
    overflowY: "auto",
  },
  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    padding: `${spacing.sm} ${spacing.md}`,
    background: "#080d18",
    borderRadius: radii.md,
    border: `1px solid ${colors.borderColor}`,
    flexWrap: "wrap",
  },
  rowLeft: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    flex: 1,
    minWidth: 0,
    overflow: "hidden",
  },
  rowRight: {
    display: "flex",
    alignItems: "center",
    gap: spacing.xs,
    flexShrink: 0,
  },
  artifactType: {
    color: colors.secondaryAccent,
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: "monospace",
    letterSpacing: "0.06em",
    background: `${colors.secondaryAccent}18`,
    padding: `1px ${spacing.xs}`,
    borderRadius: radii.sm,
    flexShrink: 0,
  },
  artifactTitle: {
    color: colors.textPrimary,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  missionTag: {
    color: colors.textSecondary,
    fontSize: "0.68rem",
    fontFamily: "monospace",
    flexShrink: 0,
  },
  statusBadge: {
    padding: `1px ${spacing.xs}`,
    border: "1px solid",
    borderRadius: radii.full,
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.05em",
    flexShrink: 0,
  },
  actionBtn: {
    background: "transparent",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.sm,
    cursor: "pointer",
    fontFamily: typography.fontFamily,
    fontSize: "0.8rem",
    padding: `2px ${spacing.xs}`,
    minWidth: 26,
    minHeight: 26,
    transition: "opacity 0.15s",
  },
  ts: {
    color: colors.textSecondary,
    fontSize: "0.65rem",
    fontFamily: "monospace",
    flexShrink: 0,
  },
  empty: {
    margin: 0,
    color: colors.textSecondary,
    textAlign: "center",
    padding: spacing.lg,
    fontFamily: typography.fontFamily,
  },
  errorText: {
    margin: 0,
    color: colors.error,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
};
