import { type CSSProperties, useEffect, useRef, useState } from "react";
import { colors } from "../theme/cosmicTokens";

type HeartbeatState = "healthy" | "high_load" | "degraded" | "desync";

interface HeartbeatPulseProps {
  state?: HeartbeatState;
  size?: number;
}

const STATE_CONFIG: Record<
  HeartbeatState,
  { color: string; duration: number; scale: number }
> = {
  healthy: { color: colors.running, duration: 950, scale: 1.12 },
  high_load: { color: colors.warning, duration: 600, scale: 1.1 },
  degraded: { color: colors.error, duration: 1750, scale: 1.08 },
  desync: { color: colors.secondaryAccent, duration: 120, scale: 1.05 },
};

export function HeartbeatPulse({
  state = "healthy",
  size = 24,
}: HeartbeatPulseProps) {
  const config = STATE_CONFIG[state];
  const [pulsing, setPulsing] = useState(false);
  const frozenRef = useRef(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    frozenRef.current = false;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    if (state === "desync") {
      // Freeze after 5s on desync
      timeoutRef.current = setTimeout(() => {
        frozenRef.current = true;
      }, 5000);
    }

    const tick = () => {
      if (frozenRef.current) return;
      setPulsing((p) => !p);
    };

    const id = setInterval(tick, config.duration / 2);
    return () => {
      clearInterval(id);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [state, config.duration]);

  const baseStyle: CSSProperties = {
    width: size,
    height: size,
    borderRadius: "50%",
    background: config.color,
    boxShadow: `0 0 ${size / 2}px ${config.color}80`,
    transform: pulsing ? `scale(${config.scale})` : "scale(1)",
    transition: `transform ${config.duration / 2}ms cubic-bezier(0.22, 0.61, 0.36, 1)`,
    display: "inline-block",
  };

  return <span style={baseStyle} title={`Heartbeat: ${state}`} />;
}
