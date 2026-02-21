import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cosmic: {
          bg: "#050712",
          "primary-accent": "#4EF2C5",
          "secondary-accent": "#FF6FD8",
          warning: "#FFB020",
          error: "#FF4B4B",
          "text-primary": "#F5F7FF",
          "text-secondary": "#9CA3AF",
          running: "#4EF2C5",
          stopped: "#FF4B4B",
          restarting: "#FFB020",
          degraded: "#FF6FD8",
          "log-info": "#60A5FA",
          "log-warn": "#FFB020",
          "log-error": "#FF4B4B",
          card: "#0C1020",
          border: "#1E2A40",
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Arial", "sans-serif"],
      },
      borderRadius: {
        cosmic: {
          sm: "6px",
          md: "10px",
          lg: "14px",
          xl: "20px",
        },
      },
      boxShadow: {
        "cosmic-card": "0 4px 24px rgba(0,0,0,0.5)",
        "cosmic-topbar": "0 2px 16px rgba(0,0,0,0.6)",
        "cosmic-glow-green": "0 0 12px #4EF2C540, 0 0 24px #4EF2C520",
        "cosmic-glow-pink": "0 0 12px #FF6FD840, 0 0 24px #FF6FD820",
      },
      animation: {
        "glow-pulse": "glow-pulse 900ms cubic-bezier(0.4, 0, 0.2, 1) infinite",
        "heartbeat-healthy": "heartbeat-healthy 950ms cubic-bezier(0.22, 0.61, 0.36, 1) infinite",
        "heartbeat-degraded": "heartbeat-degraded 1750ms cubic-bezier(0.22, 0.61, 0.36, 1) infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
