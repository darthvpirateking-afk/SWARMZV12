import { type CSSProperties, useEffect, useState } from "react";
import { colors, shadows, spacing, typography } from "../theme/cosmicTokens";
import { systemApi, type RuntimeStatus } from "../api/system";
import { StatusRing } from "./StatusRing";
import { HeartbeatPulse } from "./HeartbeatPulse";

interface CockpitTopBarProps {
  buildTag?: string;
}

export function CockpitTopBar({ buildTag = "v12.0" }: CockpitTopBarProps) {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setStatus(await systemApi.status());
      } catch {
        // silent
      }
    };
    void fetch();
    const id = setInterval(() => void fetch(), 5000);
    return () => clearInterval(id);
  }, []);

  const runtimeStatus = (status?.status ?? "running") as
    | "running"
    | "stopped"
    | "restarting"
    | "degraded";

  return (
    <header style={styles.bar}>
      {/* Left: Logo */}
      <div style={styles.left}>
        <span style={styles.logo}>⬡ SWARMZ</span>
        <span style={styles.buildTag}>{buildTag}</span>
      </div>

      {/* Center: Status Ring + Heartbeat */}
      <div style={styles.center}>
        <StatusRing status={runtimeStatus} size={56} />
        <HeartbeatPulse
          state={
            runtimeStatus === "running"
              ? "healthy"
              : runtimeStatus === "restarting"
                ? "high_load"
                : runtimeStatus === "degraded"
                  ? "degraded"
                  : "desync"
          }
        />
      </div>

      {/* Right: Operator info */}
      <div style={styles.right}>
        <span style={styles.operatorLabel}>OPERATOR</span>
        <span style={styles.operatorId}>Local</span>
      </div>
    </header>
  );
}

const styles: Record<string, CSSProperties> = {
  bar: {
    position: "sticky",
    top: 0,
    zIndex: 100,
    display: "grid",
    gridTemplateColumns: "1fr auto 1fr",
    alignItems: "center",
    height: 68,
    padding: `0 ${spacing.lg}`,
    background: `${colors.bg}cc`,
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    borderBottom: `1px solid ${colors.borderColor}`,
    boxShadow: shadows.topbar,
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
  },
  logo: {
    color: colors.primaryAccent,
    fontSize: typography.fontSizeXl,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.04em",
  },
  buildTag: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
    padding: `2px ${spacing.xs}`,
    border: `1px solid ${colors.borderColor}`,
    borderRadius: "4px",
  },
  center: {
    display: "flex",
    alignItems: "center",
    gap: spacing.md,
    justifyContent: "center",
    paddingBottom: spacing.md,
  },
  right: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    gap: 2,
  },
  operatorLabel: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.1em",
  },
  operatorId: {
    color: colors.primaryAccent,
    fontSize: typography.fontSizeMd,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
  },
};
