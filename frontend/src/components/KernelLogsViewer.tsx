import {
  type CSSProperties,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { colors, radii, spacing, typography } from "../theme/cosmicTokens";
import { systemApi, type LogEntry } from "../api/system";

type TabKey = "all" | "warnings" | "errors" | "missions";

const TAB_FILTERS: Record<TabKey, (e: LogEntry) => boolean> = {
  all: () => true,
  warnings: (e) => e.level === "WARN" || e.level === "WARNING",
  errors: (e) => e.level === "ERROR" || e.level === "CRITICAL",
  missions: (e) => !!e.mission_id,
};

const LOG_COLORS: Record<string, string> = {
  INFO: colors.logInfo,
  WARN: colors.logWarn,
  WARNING: colors.logWarn,
  ERROR: colors.logError,
  CRITICAL: colors.logError,
};

export function KernelLogsViewer() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [tab, setTab] = useState<TabKey>("all");
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const data = await systemApi.logs({ limit: 200 });
      setEntries(data.entries);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    void fetchLogs();
    const id = setInterval(() => void fetchLogs(), 3000);
    return () => clearInterval(id);
  }, [fetchLogs]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries, autoScroll]);

  const filtered = entries.filter(TAB_FILTERS[tab]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 32;
    setAutoScroll(atBottom);
  };

  return (
    <section style={styles.card}>
      <div style={styles.header}>
        <h2 style={styles.title}>Kernel Logs</h2>
        <div style={styles.tabs}>
          {(["all", "warnings", "errors", "missions"] as TabKey[]).map((t) => (
            <button
              key={t}
              style={{
                ...styles.tab,
                ...(tab === t ? styles.tabActive : {}),
              }}
              onClick={() => setTab(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div style={styles.scroll} ref={scrollRef} onScroll={handleScroll}>
        {filtered.length === 0 ? (
          <p style={styles.empty}>No log entries.</p>
        ) : (
          filtered.map((entry, i) => {
            const levelColor = LOG_COLORS[entry.level] ?? colors.textSecondary;
            const isError =
              entry.level === "ERROR" || entry.level === "CRITICAL";
            return (
              <div
                key={i}
                style={{
                  ...styles.entry,
                  ...(isError ? styles.entryError : {}),
                }}
              >
                <span style={{ ...styles.level, color: levelColor }}>
                  {entry.level}
                </span>
                <span style={styles.source}>{entry.source}</span>
                <span style={styles.message}>{entry.message}</span>
                <span style={styles.timestamp}>
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
              </div>
            );
          })
        )}
      </div>

      {!autoScroll && (
        <button
          style={styles.scrollBtn}
          onClick={() => {
            setAutoScroll(true);
            if (scrollRef.current)
              scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
          }}
        >
          ↓ Resume auto-scroll
        </button>
      )}
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
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  title: {
    margin: 0,
    fontSize: typography.fontSizeXl,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  tabs: {
    display: "flex",
    gap: spacing.xs,
    flexWrap: "wrap",
  },
  tab: {
    padding: `${spacing.xs} ${spacing.sm}`,
    background: "transparent",
    border: `1px solid ${colors.borderColor}`,
    borderRadius: radii.sm,
    color: colors.textSecondary,
    cursor: "pointer",
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
  },
  tabActive: {
    borderColor: colors.primaryAccent,
    color: colors.primaryAccent,
  },
  scroll: {
    maxHeight: "280px",
    overflowY: "auto",
    display: "grid",
    gap: "2px",
  },
  entry: {
    display: "grid",
    gridTemplateColumns: "60px 100px 1fr auto",
    gap: spacing.sm,
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: radii.sm,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
    alignItems: "center",
  },
  entryError: {
    borderLeft: `3px solid ${colors.logError}`,
    paddingLeft: spacing.sm,
    background: `${colors.logError}10`,
  },
  level: {
    fontWeight: typography.fontWeightBold,
    letterSpacing: "0.05em",
  },
  source: {
    color: colors.textSecondary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  message: {
    color: colors.textPrimary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  timestamp: {
    color: colors.textSecondary,
    whiteSpace: "nowrap",
  },
  empty: {
    margin: 0,
    color: colors.textSecondary,
    textAlign: "center",
    padding: spacing.lg,
    fontFamily: typography.fontFamily,
  },
  scrollBtn: {
    background: `${colors.primaryAccent}20`,
    border: `1px solid ${colors.primaryAccent}`,
    borderRadius: radii.sm,
    color: colors.primaryAccent,
    cursor: "pointer",
    padding: `${spacing.xs} ${spacing.md}`,
    fontSize: typography.fontSizeSm,
    fontFamily: typography.fontFamily,
    justifySelf: "center",
  },
};
