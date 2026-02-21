import { type CSSProperties } from "react";
import { CockpitTopBar } from "./components/CockpitTopBar";
import { RuntimeControlCard } from "./components/RuntimeControlCard";
import { MissionLifecycleCard } from "./components/MissionLifecycleCard";
import { KernelLogsViewer } from "./components/KernelLogsViewer";
import { MissionTimelineVisualizer } from "./components/MissionTimelineVisualizer";
import { OperatorIdentityPanel } from "./components/OperatorIdentityPanel";
import { CompanionAvatarDock } from "./components/CompanionAvatarDock";

export default function App() {
  return (
    <div style={styles.root}>
      <CockpitTopBar buildTag="v12.0" />

      <main style={styles.main}>
        <div style={styles.topRow}>
          <OperatorIdentityPanel buildTag="v12.0" />
          <CompanionAvatarDock />
        </div>

        <RuntimeControlCard />
        <MissionLifecycleCard />
        <MissionTimelineVisualizer />
        <KernelLogsViewer />
      </main>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  root: {
    minHeight: "100vh",
    background: "#050712",
    color: "#F5F7FF",
    fontFamily: "Inter, Segoe UI, Arial, sans-serif",
    display: "grid",
    gridTemplateRows: "auto 1fr",
  },
  main: {
    padding: "24px",
    display: "grid",
    gap: "20px",
    maxWidth: "960px",
    margin: "0 auto",
    width: "100%",
    boxSizing: "border-box",
  },
  topRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "16px",
  },
};
