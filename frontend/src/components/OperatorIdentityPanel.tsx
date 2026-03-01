import { type CSSProperties } from "react";
import { colors, radii, spacing, typography } from "../theme/cosmicTokens";

interface OperatorIdentityPanelProps {
  operatorName?: string;
  sessionId?: string;
  buildTag?: string;
}

export function OperatorIdentityPanel({
  operatorName = "Local Operator",
  sessionId,
  buildTag = "v12.0",
}: OperatorIdentityPanelProps) {
  const sid =
    sessionId ?? `SID-${Math.random().toString(36).slice(2, 10).toUpperCase()}`;

  return (
    <section style={styles.card}>
      <div style={styles.avatar}>
        <img src="/assets/my-avatar.png" alt="Operator Avatar" style={styles.avatarImage} />
      </div>
      <div style={styles.info}>
        <span style={styles.name}>{operatorName}</span>
        <span style={styles.detail}>Session: {sid}</span>
        <span style={styles.detail}>Build: {buildTag}</span>
      </div>
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  card: {
    background: colors.cardBg,
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.lg,
    padding: spacing.md,
    display: "flex",
    alignItems: "center",
    gap: spacing.md,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: "50%",
    background: `${colors.primaryAccent}30`,
    border: `2px solid ${colors.primaryAccent}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    overflow: "hidden",
  },
  avatarImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
  info: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  name: {
    color: colors.textPrimary,
    fontSize: typography.fontSizeLg,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
  },
  detail: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
  },
};
