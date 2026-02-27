// SWARMZ Cosmic Theme Tokens
export const colors = {
  bg: "#050712",
  primaryAccent: "#4EF2C5",
  secondaryAccent: "#FF6FD8",
  warning: "#FFB020",
  error: "#FF4B4B",
  textPrimary: "#F5F7FF",
  textSecondary: "#9CA3AF",
  running: "#4EF2C5",
  stopped: "#FF4B4B",
  restarting: "#FFB020",
  degraded: "#FF6FD8",
  logInfo: "#60A5FA",
  logWarn: "#FFB020",
  logError: "#FF4B4B",
  cardBg: "#0C1020",
  borderColor: "#1E2A40",
} as const;

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
  xxl: "48px",
} as const;

export const radii = {
  sm: "6px",
  md: "10px",
  lg: "14px",
  xl: "20px",
  full: "9999px",
} as const;

export const shadows = {
  glow: (color: string) => `0 0 12px ${color}40, 0 0 24px ${color}20`,
  card: "0 4px 24px rgba(0,0,0,0.5)",
  topbar: "0 2px 16px rgba(0,0,0,0.6)",
} as const;

export const typography = {
  fontFamily: "Inter, Segoe UI, Arial, sans-serif",
  fontSizeSm: "0.78rem",
  fontSizeMd: "0.9rem",
  fontSizeLg: "1rem",
  fontSizeXl: "1.3rem",
  fontWeightNormal: 400,
  fontWeightMedium: 500,
  fontWeightBold: 700,
} as const;

export const animations = {
  statusSweep: "450ms cubic-bezier(0.16, 1, 0.3, 1)",
  glowPulse: "900ms cubic-bezier(0.4, 0, 0.2, 1)",
  heartbeatHealthy: "950ms cubic-bezier(0.22, 0.61, 0.36, 1)",
  heartbeatHighLoad: "600ms cubic-bezier(0.22, 0.61, 0.36, 1)",
  heartbeatDegraded: "1750ms cubic-bezier(0.22, 0.61, 0.36, 1)",
  desyncShake: "120ms cubic-bezier(0.36, 0, 0.66, 1)",
} as const;
