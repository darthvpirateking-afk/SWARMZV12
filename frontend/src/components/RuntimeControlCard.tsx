import { type CSSProperties, useCallback, useEffect, useState } from "react";
import { colors, radii, shadows, spacing, typography } from "../theme/cosmicTokens";
import { systemApi, type RuntimeStatus } from "../api/system";

const STATUS_COLOR: Record<string, string> = {
  running: colors.running,
  stopped: colors.stopped,
  restarting: colors.restarting,
  degraded: colors.degraded,
};

export function RuntimeControlCard() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await systemApi.status();
      setStatus(s);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    void fetchStatus();
    const interval = setInterval(() => void fetchStatus(), 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleAction = useCallback(
    async (action: "start" | "stop" | "restart") => {
      setLoading(action);
      setError(null);
      try {
        const fn = systemApi[action];
        const result = await fn();
        setStatus(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Action failed");
      } finally {
        setLoading(null);
      }
    },
    [],
  );

  const runtimeStatus = status?.status ?? "unknown";
  const accentColor = STATUS_COLOR[runtimeStatus] ?? colors.textSecondary;
  const isLoading = loading !== null;

  return (
    <section style={styles.card}>
      <div style={styles.header}>
        <h2 style={styles.title}>Runtime Control</h2>
        <span style={{ ...styles.badge, color: accentColor, borderColor: accentColor }}>
          {runtimeStatus.toUpperCase()}
        </span>
      </div>

      {status && (
        <div style={styles.meta}>
          <span style={styles.metaText}>
            Restarts: {status.details.restart_count ?? 0}
          </span>
          {status.details.started_at && (
            <span style={styles.metaText}>
              Started: {new Date(status.details.started_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      <div style={styles.buttons}>
        {(["start", "stop", "restart"] as const).map((action) => (
          <button
            key={action}
            style={{
              ...styles.btn,
              opacity: isLoading ? 0.5 : 1,
              borderColor: action === "stop" ? colors.error : action === "restart" ? colors.warning : colors.running,
              color: action === "stop" ? colors.error : action === "restart" ? colors.warning : colors.running,
            }}
            disabled={isLoading}
            onClick={() => void handleAction(action)}
          >
            {loading === action ? "…" : action.charAt(0).toUpperCase() + action.slice(1)}
          </button>
        ))}
      </div>

      {error && <p style={styles.error}>{error}</p>}
    </section>
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
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    flexWrap: "wrap",
  },
  title: {
    margin: 0,
    fontSize: typography.fontSizeXl,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  badge: {
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: radii.full,
    border: "1px solid",
    fontSize: typography.fontSizeSm,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.08em",
  },
  meta: {
    display: "flex",
    gap: spacing.lg,
    flexWrap: "wrap",
  },
  metaText: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
  },
  buttons: {
    display: "flex",
    gap: spacing.sm,
    flexWrap: "wrap",
  },
  btn: {
    flex: "1 1 80px",
    padding: `${spacing.sm} ${spacing.md}`,
    background: "transparent",
    border: "1px solid",
    borderRadius: radii.md,
    cursor: "pointer",
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    fontWeight: typography.fontWeightMedium,
    transition: "opacity 0.2s",
    minHeight: "44px",
  },
  error: {
    margin: 0,
    color: colors.error,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
};
