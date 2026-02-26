import { type CSSProperties } from "react";
import {
  colors,
  radii,
  shadows,
  spacing,
  typography,
} from "../theme/cosmicTokens";
import { useNexusmon, type NexusmonTraits } from "../hooks/useNexusmon";

const FORM_COLOR: Record<string, string> = {
  ROOKIE: colors.textSecondary,
  CHAMPION: colors.primaryAccent,
  ULTIMATE: colors.secondaryAccent,
  MEGA: colors.warning,
  SOVEREIGN: "#FFD700",
};

const MOOD_EMOJI: Record<string, string> = {
  calm: "😌",
  focused: "🎯",
  restless: "⚡",
  charged: "🔋",
  protective: "🛡️",
  curious: "🔍",
  dormant: "💤",
  alert: "🚨",
  triumphant: "🏆",
  contemplative: "🧠",
  CALM: "😌",
  FOCUSED: "🎯",
  RESTLESS: "⚡",
  CHARGED: "🔋",
  PROTECTIVE: "🛡️",
  CURIOUS: "🔍",
  DORMANT: "💤",
  ALERT: "🚨",
  TRIUMPHANT: "🏆",
  CONTEMPLATIVE: "🧠",
};

const TRAIT_KEYS: (keyof NexusmonTraits)[] = [
  "curiosity",
  "loyalty",
  "aggression",
  "creativity",
  "autonomy",
  "patience",
  "protectiveness",
];

const TRAIT_COLOR: Record<keyof NexusmonTraits, string> = {
  curiosity: "#60A5FA",
  loyalty: colors.primaryAccent,
  aggression: colors.error,
  creativity: colors.secondaryAccent,
  autonomy: colors.warning,
  patience: "#34D399",
  protectiveness: "#A78BFA",
};

export function NexusmonEntityPanel() {
  const { entity, traits, loading, error, refresh } = useNexusmon();

  const form = entity?.form ?? "ROOKIE";
  const formColor = FORM_COLOR[form] ?? colors.primaryAccent;
  const mood = entity?.mood ?? "calm";
  const moodEmoji = MOOD_EMOJI[mood] ?? "🧠";
  const xpPct = Math.min(100, Math.max(0, entity?.xp_pct ?? 0));

  return (
    <section style={styles.card}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.nameRow}>
          <span style={{ ...styles.formBadge, color: formColor, borderColor: formColor }}>
            {form}
          </span>
          <h2 style={styles.title}>{entity?.name ?? "NEXUSMON"}</h2>
          <span style={styles.moodEmoji} title={mood}>{moodEmoji}</span>
        </div>
        <button
          style={styles.refreshBtn}
          onClick={() => void refresh()}
          disabled={loading}
          title="Refresh entity state"
        >
          {loading ? "…" : "↺"}
        </button>
      </div>

      {error && <p style={styles.errorText}>{error}</p>}

      {/* XP Bar */}
      <div style={styles.xpSection}>
        <div style={styles.xpLabel}>
          <span style={styles.xpText}>XP</span>
          <span style={styles.xpValue}>{entity?.xp ?? 0}</span>
          <span style={{ ...styles.xpPct, color: formColor }}>{xpPct}%</span>
        </div>
        <div style={styles.xpTrack}>
          <div
            style={{
              ...styles.xpFill,
              width: `${xpPct}%`,
              background: `linear-gradient(90deg, ${formColor}88, ${formColor})`,
              boxShadow: `0 0 8px ${formColor}66`,
            }}
          />
        </div>
      </div>

      {/* Traits */}
      <div style={styles.traitsGrid}>
        {TRAIT_KEYS.map((key) => {
          const val = traits[key] ?? 0;
          const color = TRAIT_COLOR[key];
          return (
            <div key={key} style={styles.traitRow}>
              <span style={styles.traitLabel}>{key.toUpperCase()}</span>
              <div style={styles.traitTrack}>
                <div
                  style={{
                    ...styles.traitFill,
                    width: `${val}%`,
                    background: color,
                    boxShadow: `0 0 6px ${color}55`,
                  }}
                />
              </div>
              <span style={{ ...styles.traitVal, color }}>{val}</span>
            </div>
          );
        })}
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
    boxShadow: shadows.card,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    flexWrap: "wrap",
  },
  nameRow: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
  },
  formBadge: {
    padding: `2px ${spacing.sm}`,
    borderRadius: radii.full,
    border: "1px solid",
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.1em",
  },
  title: {
    margin: 0,
    fontSize: typography.fontSizeXl,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  moodEmoji: {
    fontSize: "1.3rem",
    cursor: "default",
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
  errorText: {
    margin: 0,
    color: colors.error,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
  xpSection: {
    display: "grid",
    gap: spacing.xs,
  },
  xpLabel: {
    display: "flex",
    gap: spacing.sm,
    alignItems: "center",
  },
  xpText: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
    fontWeight: typography.fontWeightBold,
    letterSpacing: "0.08em",
  },
  xpValue: {
    color: colors.textPrimary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
  },
  xpPct: {
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
    fontWeight: typography.fontWeightBold,
  },
  xpTrack: {
    height: 6,
    background: colors.borderColor,
    borderRadius: radii.full,
    overflow: "hidden",
  },
  xpFill: {
    height: "100%",
    borderRadius: radii.full,
    transition: "width 0.6s ease",
  },
  traitsGrid: {
    display: "grid",
    gap: spacing.sm,
  },
  traitRow: {
    display: "grid",
    gridTemplateColumns: "110px 1fr 36px",
    alignItems: "center",
    gap: spacing.sm,
  },
  traitLabel: {
    color: colors.textSecondary,
    fontSize: "0.65rem",
    fontFamily: typography.fontFamily,
    fontWeight: typography.fontWeightBold,
    letterSpacing: "0.08em",
  },
  traitTrack: {
    height: 5,
    background: colors.borderColor,
    borderRadius: radii.full,
    overflow: "hidden",
  },
  traitFill: {
    height: "100%",
    borderRadius: radii.full,
    transition: "width 0.5s ease",
  },
  traitVal: {
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
    fontWeight: typography.fontWeightBold,
    textAlign: "right",
  },
};
