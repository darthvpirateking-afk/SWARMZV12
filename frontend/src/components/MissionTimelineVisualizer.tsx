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

export function MissionTimelineVisualizer() {
  const [missions, setMissions] = useState<MissionStatus[]>([]);

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

  if (missions.length === 0) return null;

  return (
    <section style={styles.card}>
      <h2 style={styles.title}>Mission Timeline</h2>
      <div style={styles.list}>
        {missions.slice(-10).map((mission) => (
          <div key={mission.mission_id} style={styles.mission}>
            <div style={styles.missionHeader}>
              <span style={styles.missionId}>{mission.mission_id}</span>
              <span
                style={{
                  ...styles.state,
                  color: STATE_COLOR[mission.state] ?? colors.textSecondary,
                }}
              >
                {mission.state}
              </span>
            </div>
            <div style={styles.timeline}>
              {mission.history.map((h, i) => (
                <div key={i} style={styles.event}>
                  <div
                    style={{
                      ...styles.dot,
                      background: STATE_COLOR[h.state] ?? colors.textSecondary,
                    }}
                  />
                  {i < mission.history.length - 1 && (
                    <div style={styles.line} />
                  )}
                  <div style={styles.eventInfo}>
                    <span
                      style={{
                        color: STATE_COLOR[h.state] ?? colors.textSecondary,
                        fontSize: typography.fontSizeSm,
                        fontWeight: typography.fontWeightBold,
                      }}
                    >
                      {h.state}
                    </span>
                    <span style={styles.eventTime}>
                      {new Date(h.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
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
  list: { display: "grid", gap: spacing.md },
  mission: {
    padding: spacing.md,
    background: "#0a0f1c",
    borderRadius: radii.md,
    border: `1px solid ${colors.borderColor}`,
    display: "grid",
    gap: spacing.sm,
  },
  missionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  missionId: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
  },
  state: {
    fontSize: typography.fontSizeSm,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
  },
  timeline: {
    display: "flex",
    alignItems: "flex-start",
    gap: 0,
    overflowX: "auto",
    paddingBottom: spacing.xs,
  },
  event: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    position: "relative",
    flex: "0 0 auto",
    marginRight: spacing.md,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    flexShrink: 0,
  },
  line: {
    position: "absolute",
    top: 4,
    left: 8,
    width: spacing.md,
    height: 1,
    background: colors.borderColor,
  },
  eventInfo: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 2,
    marginTop: spacing.xs,
  },
  eventTime: {
    color: colors.textSecondary,
    fontSize: "0.65rem",
    fontFamily: "monospace",
    whiteSpace: "nowrap",
  },
};
