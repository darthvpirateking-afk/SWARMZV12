import React, {
  useState,
  useMemo,
  useEffect,
  useRef,
  useCallback,
  type CSSProperties,
  type FormEvent,
} from "react";
import { makeMessage, type ChatMessage } from "./utils/makeMessage";
import { apiPost } from "./utils/api";
import { CockpitTopBar } from "./components/CockpitTopBar";
import { CompanionAvatarDock } from "./components/CompanionAvatarDock";
import { RuntimeControlCard } from "./components/RuntimeControlCard";
import { MissionLifecycleCard } from "./components/MissionLifecycleCard";
import { KernelLogsViewer } from "./components/KernelLogsViewer";
import { AppStoreTracker } from "./components/AppStoreTracker";
import { OperatorIdentityPanel } from "./components/OperatorIdentityPanel";
import { ArtifactVaultPanel } from "./components/ArtifactVaultPanel";
import { NexusmonEntityPanel } from "./components/NexusmonEntityPanel";
import { CompanionCorePage } from "./pages/CompanionCorePage";
import { BootstrapPage } from "./pages/BootstrapPage";
import { BuildMilestonesPage } from "./pages/BuildMilestonesPage";
import { DatabaseLayerPage } from "./pages/DatabaseLayerPage";
import { OperatorAuthPage } from "./pages/OperatorAuthPage";
import { ApiFoundationPage } from "./pages/ApiFoundationPage";
import { systemApi } from "./api/system";
import { colors, spacing, radii, typography, shadows } from "./theme/cosmicTokens";

type CompanionResponse = {
  ok: boolean;
  reply: string;
  error?: string;
  detail?: string;
};

type PageId =
  | "nexusmon"
  | "companion"
  | "runtime"
  | "missions"
  | "logs"
  | "database"
  | "bootstrap"
  | "build"
  | "auth"
  | "api"
  | "vault"
  | "appstore"
  | "chat";

interface NavItem {
  id: PageId;
  icon: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "nexusmon",  icon: "⬡", label: "NEXUSMON" },
  { id: "companion", icon: "🤖", label: "Companion" },
  { id: "runtime",   icon: "⚡", label: "Runtime" },
  { id: "missions",  icon: "🎯", label: "Missions" },
  { id: "vault",     icon: "🗃️", label: "Artifact Vault" },
  { id: "logs",      icon: "📋", label: "Kernel Logs" },
  { id: "database",  icon: "🗄️", label: "Database" },
  { id: "bootstrap", icon: "🚀", label: "Bootstrap" },
  { id: "build",     icon: "🏗️", label: "Build" },
  { id: "auth",      icon: "🔐", label: "Auth" },
  { id: "api",       icon: "🌐", label: "API" },
  { id: "appstore",  icon: "📦", label: "App Store" },
  { id: "chat",      icon: "💬", label: "Chat" },
];

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("nexusmon");
  const [runtimeStatus, setRuntimeStatus] = useState<
    "running" | "stopped" | "restarting" | "degraded"
  >("running");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const poll = async () => {
      try {
        const s = await systemApi.status();
        setRuntimeStatus(
          (s.status as "running" | "stopped" | "restarting" | "degraded") ??
            "running",
        );
      } catch (err) {
        // Status polling failures are expected during startup — log for debugging
        if (import.meta.env.DEV) {
          console.warn("[App] Runtime status poll failed:", err);
        }
      }
    };
    void poll();
    const id = setInterval(() => void poll(), 8000);
    return () => clearInterval(id);
  }, []);

  const heartbeatState =
    runtimeStatus === "running"
      ? "healthy"
      : runtimeStatus === "restarting"
        ? "high_load"
        : runtimeStatus === "degraded"
          ? "degraded"
          : ("desync" as const);

  return (
    <div style={shell.root}>
      <style>{globalCss}</style>

      {/* ── Top Bar ── */}
      <CockpitTopBar buildTag="v12.0" />

      <div style={shell.body}>
        {/* ── Sidebar ── */}
        <aside
          style={{
            ...shell.sidebar,
            width: sidebarOpen ? 220 : 64,
            transition: "width 0.25s ease",
          }}
        >
          {/* Collapse toggle */}
          <button
            style={shell.collapseBtn}
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            {sidebarOpen ? "◀" : "▶"}
          </button>

          {/* Avatar Dock */}
          <div style={shell.avatarWrap}>
            <CompanionAvatarDock
              heartbeatState={heartbeatState}
              runtimeStatus={runtimeStatus}
            />
            {sidebarOpen && (
              <span style={shell.avatarLabel}>NEXUSMON</span>
            )}
          </div>

          {/* Nav */}
          <nav style={shell.nav}>
            {NAV_ITEMS.map((item) => {
              const active = activePage === item.id;
              return (
                <button
                  key={item.id}
                  style={{
                    ...shell.navBtn,
                    background: active
                      ? `${colors.primaryAccent}18`
                      : "transparent",
                    borderLeft: active
                      ? `3px solid ${colors.primaryAccent}`
                      : "3px solid transparent",
                    color: active
                      ? colors.primaryAccent
                      : colors.textSecondary,
                    justifyContent: sidebarOpen ? "flex-start" : "center",
                  }}
                  onClick={() => setActivePage(item.id)}
                  title={item.label}
                >
                  <span style={shell.navIcon}>{item.icon}</span>
                  {sidebarOpen && (
                    <span style={shell.navLabel}>{item.label}</span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Operator identity at bottom */}
          {sidebarOpen && (
            <div style={shell.identityWrap}>
              <OperatorIdentityPanel buildTag="v12.0" />
            </div>
          )}
        </aside>

        {/* ── Main Content ── */}
        <main style={shell.main}>
          <PageContent activePage={activePage} />
        </main>
      </div>
    </div>
  );
}

function PageContent({ activePage }: { activePage: PageId }) {
  switch (activePage) {
    case "nexusmon":
      return <NexusmonEntityPanel />;
    case "companion":
      return <CompanionCorePage />;
    case "runtime":
      return <RuntimeControlCard />;
    case "missions":
      return <MissionLifecycleCard />;
    case "vault":
      return <ArtifactVaultPanel />;
    case "logs":
      return <KernelLogsViewer />;
    case "database":
      return <DatabaseLayerPage />;
    case "bootstrap":
      return <BootstrapPage />;
    case "build":
      return <BuildMilestonesPage />;
    case "auth":
      return <OperatorAuthPage />;
    case "api":
      return <ApiFoundationPage />;
    case "appstore":
      return <AppStoreTracker />;
    case "chat":
      return <ChatPanel />;
    default:
      return <NexusmonEntityPanel />;
  }
}

// ── Inline Chat Panel (preserved from previous App) ──────────────────────────

function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    makeMessage("assistant", "🧠 SWARMZ chat ready. Type to begin."),
  ]);
  const [text, setText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const canSend = useMemo(
    () => !isSending && text.trim().length > 0,
    [isSending, text],
  );

  const onSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const outbound = text.trim();
      if (!outbound || isSending) return;
      setText("");
      setError(null);
      setIsSending(true);
      setMessages((prev) => [...prev, makeMessage("user", outbound)]);
      try {
        const payload = await apiPost<CompanionResponse>(
          "/v1/companion/message",
          { text: outbound },
        );
        if (payload.ok === false) {
          throw new Error(payload.error ?? payload.detail ?? "Request failed");
        }
        setMessages((prev) => [
          ...prev,
          makeMessage(
            "assistant",
            typeof payload.reply === "string"
              ? payload.reply
              : "No reply returned.",
          ),
        ]);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Request failed.");
      } finally {
        setIsSending(false);
      }
    },
    [isSending, text],
  );

  const handleReset = useCallback(() => {
    setMessages([
      makeMessage("assistant", "🧠 SWARMZ chat reset. Ready again."),
    ]);
    setError(null);
    setText("");
  }, []);

  return (
    <div style={chat.wrap}>
      <div style={chat.header}>
        <span style={chat.headerTitle}>💬 Companion Chat</span>
        <span style={chat.headerSub}>
          endpoint: <code style={chat.code}>/v1/companion/message</code>
        </span>
      </div>

      <div style={chat.messagesBox}>
        {messages.map((m, i) => (
          <ChatBubble key={m.id} role={m.role} text={m.text} index={i} />
        ))}
        {isSending && (
          <ChatBubble
            role="assistant"
            text="Thinking..."
            index={messages.length}
            loading
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      <form style={chat.form} autoComplete="off" onSubmit={onSubmit}>
        <textarea
          placeholder="Type your message…"
          style={chat.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isSending}
          rows={2}
        />
        <div style={chat.buttonRow}>
          <button
            type="submit"
            style={{
              ...chat.sendBtn,
              opacity: canSend ? 1 : 0.45,
              cursor: canSend ? "pointer" : "not-allowed",
            }}
            disabled={!canSend}
          >
            {isSending ? "•••" : "🚀 Send"}
          </button>
          <button
            type="button"
            onClick={handleReset}
            style={chat.actionBtn}
            disabled={isSending}
          >
            🔄 Reset
          </button>
        </div>
      </form>

      {error && <div style={chat.errorBanner}>{error}</div>}
    </div>
  );
}

function ChatBubble({
  role,
  text,
  index,
  loading = false,
}: {
  role: "user" | "assistant";
  text: string;
  index: number;
  loading?: boolean;
}) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        animationDelay: `${index * 0.03 + 0.05}s`,
        animation: "floatIn 0.4s cubic-bezier(0.32,1.56,0.56,1) both",
      }}
    >
      {!isUser && (
        <span
          style={{
            marginRight: 8,
            fontSize: "1.4rem",
            alignSelf: "flex-end",
            filter: `drop-shadow(0 0 6px ${colors.primaryAccent}88)`,
          }}
        >
          ⬡
        </span>
      )}
      <div
        style={{
          maxWidth: "62%",
          padding: "10px 14px",
          borderRadius: isUser
            ? "14px 14px 4px 14px"
            : "14px 14px 14px 4px",
          background: isUser
            ? `linear-gradient(135deg, ${colors.primaryAccent}28, ${colors.secondaryAccent}18)`
            : `${colors.cardBg}`,
          border: `1px solid ${isUser ? colors.primaryAccent : colors.borderColor}44`,
          color: colors.textPrimary,
          fontSize: typography.fontSizeMd,
          fontFamily: typography.fontFamily,
          lineHeight: 1.55,
          opacity: loading ? 0.7 : 1,
          animation: loading ? "pulse 1.4s ease-in-out infinite" : undefined,
        }}
      >
        <span
          style={{
            display: "block",
            fontSize: "0.68rem",
            fontWeight: typography.fontWeightBold,
            color: isUser ? colors.primaryAccent : colors.secondaryAccent,
            marginBottom: 4,
            letterSpacing: "0.08em",
          }}
        >
          {isUser ? "YOU" : "SWARMZ"}
        </span>
        {text}
        {loading && <span style={{ marginLeft: 4, opacity: 0.6 }}>▯▯▯</span>}
      </div>
      {isUser && (
        <span style={{ marginLeft: 8, fontSize: "1.2rem", alignSelf: "flex-end" }}>
          🧑
        </span>
      )}
    </div>
  );
}

// ── CSS ───────────────────────────────────────────────────────────────────────

const globalCss = `
  *, *::before, *::after { box-sizing: border-box; }
  html, body, #root { margin: 0; padding: 0; height: 100%; }
  body { background: ${colors.bg}; color: ${colors.textPrimary}; font-family: ${typography.fontFamily}; }
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: ${colors.borderColor}; border-radius: 4px; }

  @keyframes floatIn {
    from { opacity: 0; transform: translateY(10px) scale(0.96); }
    to   { opacity: 1; transform: translateY(0)   scale(1);    }
  }
  @keyframes pulse {
    0%, 100% { opacity: 0.55; }
    50%       { opacity: 1;    }
  }
`;

const shell: Record<string, CSSProperties> = {
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: colors.bg,
    overflow: "hidden",
  },
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    background: `${colors.cardBg}cc`,
    borderRight: `1px solid ${colors.borderColor}`,
    backdropFilter: "blur(10px)",
    WebkitBackdropFilter: "blur(10px)",
    overflow: "hidden",
    flexShrink: 0,
    boxShadow: shadows.card,
  },
  collapseBtn: {
    background: "transparent",
    border: "none",
    color: colors.textSecondary,
    cursor: "pointer",
    padding: `${spacing.sm} ${spacing.md}`,
    textAlign: "right",
    fontSize: "0.75rem",
    fontFamily: typography.fontFamily,
    alignSelf: "flex-end",
  },
  avatarWrap: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: `${spacing.md} ${spacing.sm}`,
    borderBottom: `1px solid ${colors.borderColor}`,
    gap: spacing.xs,
  },
  avatarLabel: {
    color: colors.primaryAccent,
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.14em",
    marginTop: spacing.xs,
  },
  nav: {
    flex: 1,
    overflowY: "auto",
    padding: `${spacing.sm} 0`,
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  navBtn: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    padding: `${spacing.sm} ${spacing.md}`,
    border: "none",
    borderRadius: 0,
    cursor: "pointer",
    fontFamily: typography.fontFamily,
    fontSize: typography.fontSizeMd,
    fontWeight: typography.fontWeightMedium,
    transition: "background 0.15s, color 0.15s",
    whiteSpace: "nowrap",
    minHeight: 40,
  },
  navIcon: {
    fontSize: "1.1rem",
    flexShrink: 0,
  },
  navLabel: {
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  identityWrap: {
    padding: spacing.sm,
    borderTop: `1px solid ${colors.borderColor}`,
  },
  main: {
    flex: 1,
    overflowY: "auto",
    padding: spacing.lg,
    display: "flex",
    flexDirection: "column",
    gap: spacing.lg,
    background: `radial-gradient(ellipse at 50% 0%, ${colors.primaryAccent}08 0%, transparent 60%), ${colors.bg}`,
  },
};

const chat: Record<string, CSSProperties> = {
  wrap: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    background: colors.cardBg,
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.lg,
    overflow: "hidden",
    boxShadow: shadows.card,
    maxWidth: 820,
    width: "100%",
    alignSelf: "center",
    minHeight: 520,
    maxHeight: "80vh",
  },
  header: {
    padding: `${spacing.md} ${spacing.lg}`,
    borderBottom: `1px solid ${colors.borderColor}`,
    background: `${colors.primaryAccent}08`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  headerTitle: {
    color: colors.textPrimary,
    fontWeight: typography.fontWeightBold,
    fontSize: typography.fontSizeLg,
    fontFamily: typography.fontFamily,
  },
  headerSub: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
  code: {
    color: colors.primaryAccent,
    fontFamily: "monospace",
    fontSize: "0.8rem",
  },
  messagesBox: {
    flex: 1,
    overflowY: "auto",
    padding: spacing.lg,
    display: "flex",
    flexDirection: "column",
    gap: spacing.md,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: spacing.sm,
    padding: spacing.md,
    borderTop: `1px solid ${colors.borderColor}`,
  },
  textarea: {
    background: "#0a0f1c",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.md,
    color: colors.textPrimary,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    padding: `${spacing.sm} ${spacing.md}`,
    resize: "none",
    outline: "none",
    width: "100%",
    transition: "border-color 0.2s",
  },
  buttonRow: {
    display: "flex",
    gap: spacing.sm,
  },
  sendBtn: {
    flex: 1,
    padding: `${spacing.sm} ${spacing.md}`,
    background: `linear-gradient(135deg, ${colors.primaryAccent}, ${colors.secondaryAccent}88)`,
    color: colors.bg,
    border: "none",
    borderRadius: radii.md,
    fontWeight: typography.fontWeightBold,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    cursor: "pointer",
    boxShadow: shadows.glow(colors.primaryAccent),
    transition: "opacity 0.2s",
    minHeight: 40,
  },
  actionBtn: {
    padding: `${spacing.sm} ${spacing.md}`,
    background: "transparent",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.md,
    color: colors.textSecondary,
    fontFamily: typography.fontFamily,
    fontSize: typography.fontSizeMd,
    cursor: "pointer",
    minHeight: 40,
  },
  errorBanner: {
    margin: spacing.sm,
    padding: `${spacing.sm} ${spacing.md}`,
    background: `${colors.error}18`,
    border: `1px solid ${colors.error}44`,
    borderRadius: radii.md,
    color: colors.error,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
};
