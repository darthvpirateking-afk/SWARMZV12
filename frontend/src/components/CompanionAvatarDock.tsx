import { type CSSProperties, useEffect, useState } from "react";
import { colors, typography } from "../theme/cosmicTokens";

interface CompanionAvatarDockProps {
  heartbeatState?: "healthy" | "high_load" | "degraded" | "desync";
  runtimeStatus?: "running" | "stopped" | "restarting" | "degraded";
}

export function CompanionAvatarDock({
  heartbeatState = "healthy",
  runtimeStatus = "running",
}: CompanionAvatarDockProps) {
  const [floatY, setFloatY] = useState(0);
  const [glowOpacity, setGlowOpacity] = useState(0.4);

  useEffect(() => {
    let t = 0;
    const id = setInterval(() => {
      t += 0.05;
      setFloatY(Math.sin(t) * 6);
      setGlowOpacity(0.3 + Math.abs(Math.sin(t * 0.7)) * 0.4);
    }, 50);
    return () => clearInterval(id);
  }, []);

  const accentColor =
    heartbeatState === "degraded"
      ? colors.error
      : heartbeatState === "high_load"
        ? colors.warning
        : runtimeStatus === "stopped"
          ? colors.stopped
          : colors.primaryAccent;

  const containerStyle: CSSProperties = {
    display: "inline-flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
    transform: `translateY(${floatY}px)`,
    transition: "transform 50ms linear",
  };

  const glowStyle: CSSProperties = {
    width: 64,
    height: 64,
    borderRadius: "50%",
    background: `radial-gradient(circle, ${accentColor}${Math.round(
      glowOpacity * 255,
    )
      .toString(16)
      .padStart(2, "0")} 0%, transparent 70%)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "2rem",
  };

  const labelStyle: CSSProperties = {
    color: accentColor,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.08em",
    fontWeight: typography.fontWeightBold,
  };

  return (
    <div style={containerStyle}>
      <div style={glowStyle}>⬡</div>
      <span style={labelStyle}>COMPANION</span>
    </div>
  );
}
