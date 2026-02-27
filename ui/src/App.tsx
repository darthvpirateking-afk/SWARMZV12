import Cockpit from "./components/Cockpit";

const ACCENT = "#4EF2C5";
const BG = "#050712";
const CARD_BG = "#0C1020";
const BORDER = "#1E2A40";

export default function App() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: BG,
        color: "#F5F7FF",
        fontFamily: "Inter, Segoe UI, Arial, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top bar */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          background: `${CARD_BG}cc`,
          backdropFilter: "blur(10px)",
          borderBottom: `1px solid ${BORDER}`,
          padding: "0 24px",
          height: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            color: ACCENT,
            fontSize: "1.2rem",
            fontWeight: 700,
            letterSpacing: "0.04em",
          }}
        >
          ⬡ SWARMZ Cockpit
        </span>
        <span
          style={{
            color: "#9CA3AF",
            fontSize: "0.78rem",
            fontFamily: "monospace",
            border: `1px solid ${BORDER}`,
            borderRadius: 4,
            padding: "2px 8px",
          }}
        >
          v1.0
        </span>
      </header>

      {/* Main content */}
      <main
        style={{
          flex: 1,
          padding: 24,
          background: `radial-gradient(ellipse at 50% 0%, ${ACCENT}08 0%, transparent 60%)`,
        }}
      >
        <Cockpit />
      </main>
    </div>
  );
}
