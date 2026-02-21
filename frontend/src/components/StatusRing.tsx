import { type CSSProperties, useEffect, useRef, useState } from "react";
import { colors } from "../theme/cosmicTokens";

type RuntimeState = "running" | "stopped" | "restarting" | "degraded";

interface StatusRingProps {
  status: RuntimeState;
  size?: number;
}

const STATE_COLOR: Record<RuntimeState, string> = {
  running: colors.running,
  stopped: colors.stopped,
  restarting: colors.restarting,
  degraded: colors.degraded,
};

const CIRCUMFERENCE = 2 * Math.PI * 42; // r=42

export function StatusRing({ status, size = 96 }: StatusRingProps) {
  const color = STATE_COLOR[status] ?? colors.textSecondary;
  const [offset, setOffset] = useState(CIRCUMFERENCE);
  const [glowing, setGlowing] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Sweep animation on state change
    setOffset(status === "stopped" ? CIRCUMFERENCE * 0.25 : 0);

    // Glow pulse
    setGlowing(true);
    intervalRef.current = setInterval(() => setGlowing((g) => !g), 900);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status]);

  const containerStyle: CSSProperties = {
    width: size,
    height: size,
    position: "relative",
    display: "inline-block",
    filter: glowing ? `drop-shadow(0 0 8px ${color})` : "none",
    transition: "filter 900ms cubic-bezier(0.4, 0, 0.2, 1)",
  };

  return (
    <div style={containerStyle}>
      <svg width={size} height={size} viewBox="0 0 96 96">
        {/* Track */}
        <circle
          cx={48}
          cy={48}
          r={42}
          fill="none"
          stroke={`${color}22`}
          strokeWidth={6}
        />
        {/* Animated arc */}
        <circle
          cx={48}
          cy={48}
          r={42}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{
            transition: `stroke-dashoffset 450ms cubic-bezier(0.16, 1, 0.3, 1), stroke 450ms`,
            transform: "rotate(-90deg)",
            transformOrigin: "48px 48px",
          }}
        />
        {/* Center dot */}
        <circle cx={48} cy={48} r={8} fill={color} />
      </svg>
      <div
        style={{
          position: "absolute",
          bottom: -20,
          left: "50%",
          transform: "translateX(-50%)",
          color,
          fontSize: "0.65rem",
          fontWeight: 700,
          letterSpacing: "0.1em",
          whiteSpace: "nowrap",
          fontFamily: "Inter, sans-serif",
        }}
      >
        {status.toUpperCase()}
      </div>
    </div>
  );
}
