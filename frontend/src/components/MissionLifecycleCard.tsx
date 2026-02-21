import { type CSSProperties, useCallback, useEffect, useState } from "react";
import { colors, radii, spacing, typography } from "../theme/cosmicTokens";
import { missionApi, type MissionStatus } from "../api/system";

const STATE_COLOR: Record<string, string> = {
  IDLE: colors.textSecondary,
  QUEUED: colors.warning,
  INITIALIZING: colors.restarting,
  RUNNING: colors.running,
  PAUSED: colors.warning,
  COMPLETED: colors.running,
  FAILED: colors.error,
  ABORTED: colors.error,
};

const PHASES = ["IDLE", "QUEUED", "INITIALIZING", "RUNNING", "PAUSED", "COMPLETED"];

export function MissionLifecycleCard() {
  const [missions, setMissions] = useState<MissionStatus[]>([]);
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMissions = useCallback(async () => {
    try {
      const data = await missionApi.status();
      setMissions(data.missions);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    void fetchMissions();
    const id = setInterval(() => void fetchMissions(), 5000);
    return () => clearInterval(id);
  }, [fetchMissions]);

  const handleStart = useCallback(async () => {
    if (!goal.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await missionApi.start(goal);
      setGoal("");
      await fetchMissions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setLoading(false);
    }
  }, [goal, fetchMissions]);

  const handleAction = useCallback(
    async (action: "stop" | "pause" | "resume", missionId: string) => {
      try {
        await missionApi[action](missionId);
        await fetchMissions();
      } catch {
        // silent
      }
    },
    [fetchMissions],
  );

  return (
    <section style={styles.card}>
      <h2 style={styles.title}>Mission Lifecycle</h2>

      <div style={styles.startRow}>
        <input
          style={styles.input}
          placeholder="Mission goal..."
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          disabled={loading}
        />
        <button
          style={styles.startBtn}
          onClick={() => void handleStart()}
          disabled={loading || !goal.trim()}
          aria-label={loading ? "Launching mission" : "Launch mission"}
          aria-busy={loading}
        >
          {loading ? "…" : "Launch"}
        </button>
      </div>

      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.stepper}>
        {PHASES.map((phase, i) => (
          <div key={phase} style={styles.stepItem}>
            <div
              style={{
                ...styles.stepDot,
                background: STATE_COLOR[phase] ?? colors.textSecondary,
              }}
            />
            <span style={{ ...styles.stepLabel, color: STATE_COLOR[phase] ?? colors.textSecondary }}>
              {phase}
            </span>
            {i < PHASES.length - 1 && <div style={styles.stepLine} />}
          </div>
        ))}
      </div>

      <div style={styles.missions}>
        {missions.length === 0 ? (
          <p style={styles.empty}>No active missions.</p>
        ) : (
          missions.slice(-5).map((m) => (
            <div key={m.mission_id} style={styles.missionRow}>
              <span style={{ ...styles.missionId }}>{m.mission_id}</span>
              <span
                style={{
                  ...styles.missionState,
                  color: STATE_COLOR[m.state] ?? colors.textSecondary,
                }}
              >
                {m.state}
              </span>
              <div style={styles.missionActions}>
                {m.state === "RUNNING" && (
                  <button style={styles.actionBtn} onClick={() => void handleAction("pause", m.mission_id)}>
                    Pause
                  </button>
                )}
                {m.state === "PAUSED" && (
                  <button style={styles.actionBtn} onClick={() => void handleAction("resume", m.mission_id)}>
                    Resume
                  </button>
                )}
                {!["COMPLETED", "FAILED", "ABORTED"].includes(m.state) && (
                  <button style={{ ...styles.actionBtn, color: colors.error }} onClick={() => void handleAction("stop", m.mission_id)}>
                    Abort
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
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
  },
  title: {
    margin: 0,
    fontSize: typography.fontSizeXl,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  startRow: {
    display: "flex",
    gap: spacing.sm,
    flexWrap: "wrap",
  },
  input: {
    flex: "1 1 200px",
    padding: `${spacing.sm} ${spacing.md}`,
    background: "#111922",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.md,
    color: colors.textPrimary,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    minHeight: "44px",
  },
  startBtn: {
    padding: `${spacing.sm} ${spacing.lg}`,
    background: `${colors.primaryAccent}20`,
    border: `1px solid ${colors.primaryAccent}`,
    borderRadius: radii.md,
    color: colors.primaryAccent,
    cursor: "pointer",
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    minHeight: "44px",
  },
  stepper: {
    display: "flex",
    alignItems: "center",
    gap: 0,
    overflowX: "auto",
    padding: `${spacing.xs} 0`,
  },
  stepItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    position: "relative",
    flex: "0 0 auto",
  },
  stepDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    margin: `0 ${spacing.md}`,
  },
  stepLabel: {
    fontSize: "0.6rem",
    fontFamily: typography.fontFamily,
    marginTop: spacing.xs,
    letterSpacing: "0.06em",
  },
  stepLine: {
    position: "absolute",
    top: 5,
    right: `-${spacing.md}`,
    width: spacing.md,
    height: 1,
    background: colors.borderColor,
  },
  missions: {
    display: "grid",
    gap: spacing.sm,
  },
  missionRow: {
    display: "grid",
    gridTemplateColumns: "1fr auto auto",
    gap: spacing.sm,
    alignItems: "center",
    padding: `${spacing.xs} ${spacing.sm}`,
    background: "#0a0f1c",
    borderRadius: radii.sm,
    border: `1px solid ${colors.borderColor}`,
  },
  missionId: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  missionState: {
    fontSize: typography.fontSizeSm,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.05em",
  },
  missionActions: {
    display: "flex",
    gap: spacing.xs,
  },
  actionBtn: {
    padding: `2px ${spacing.sm}`,
    background: "transparent",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.sm,
    color: colors.textPrimary,
    cursor: "pointer",
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
  error: {
    margin: 0,
    color: colors.error,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
  empty: {
    margin: 0,
    color: colors.textSecondary,
    textAlign: "center",
    padding: spacing.md,
    fontFamily: typography.fontFamily,
  },
};
