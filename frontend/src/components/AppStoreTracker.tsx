import {
  type CSSProperties,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AppRanking {
  rank: number;
  previous_rank: number;
  delta: number;
  id: string;
  name: string;
  category: string;
  developer: string;
  rating: number;
  reviews: number;
}

interface RankingsResponse {
  rankings: AppRanking[];
  total: number;
  timestamp: string;
  category: string;
  next_update_in: number;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const MATRIX_GREEN = "#00FF41";
const MATRIX_DIM = "#003B12";
const MATRIX_MID = "#00A82A";
const MATRIX_GOLD = "#FFD700";
const MATRIX_RED = "#FF3333";
const MATRIX_BG = "#020D02";
const MATRIX_CARD = "#050F05";
const MATRIX_BORDER = "#0A2E0A";
const FONT_MONO = "'Courier New', 'Lucida Console', monospace";

const REFRESH_MS = 5_000;
/** Minimum number of matrix rain columns (actual count is canvas-width-based). */
const MATRIX_RAIN_MIN_COLS = 24;

// ── Matrix Rain Canvas ────────────────────────────────────────────────────────

function MatrixRain({ height }: { height: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.offsetWidth;
    const H = height;
    canvas.width = W;
    canvas.height = H;

    const FONT_SIZE = 13;
    const cols = Math.max(MATRIX_RAIN_MIN_COLS, Math.floor(W / FONT_SIZE));
    const drops: number[] = Array(cols).fill(1);
    const CHARS =
      "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモ";

    ctx.font = `${FONT_SIZE}px ${FONT_MONO}`;

    const tick = () => {
      ctx.fillStyle = "rgba(2, 13, 2, 0.06)";
      ctx.fillRect(0, 0, W, H);

      for (let i = 0; i < drops.length; i++) {
        const ch = CHARS[Math.floor(Math.random() * CHARS.length)];
        const x = i * FONT_SIZE;
        const y = drops[i] * FONT_SIZE;

        // Brighter leading character
        ctx.fillStyle = drops[i] * FONT_SIZE < 2 ? "#AFFFAF" : MATRIX_GREEN;
        ctx.fillText(ch, x, y);

        if (y > H && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };

    const id = setInterval(tick, 40);
    return () => clearInterval(id);
  }, [height]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height,
        opacity: 0.55,
        pointerEvents: "none",
      }}
    />
  );
}

// ── Delta badge ───────────────────────────────────────────────────────────────

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) {
    return <span style={{ ...styles.delta, color: MATRIX_MID }}>—</span>;
  }
  const up = delta > 0;
  return (
    <span
      style={{
        ...styles.delta,
        color: up ? MATRIX_GREEN : MATRIX_RED,
      }}
    >
      {up ? "▲" : "▼"} {Math.abs(delta)}
    </span>
  );
}

// ── Stars ─────────────────────────────────────────────────────────────────────

function Stars({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span style={{ color: MATRIX_GOLD, fontSize: "0.7rem" }}>
      {"★".repeat(full)}
      {half ? "⯨" : ""}
      <span style={{ color: MATRIX_DIM }}>
        {"★".repeat(5 - full - (half ? 1 : 0))}
      </span>
      <span style={{ color: MATRIX_MID, marginLeft: 4 }}>
        {rating.toFixed(1)}
      </span>
    </span>
  );
}

// ── Row ───────────────────────────────────────────────────────────────────────

function RankRow({ app, flash }: { app: AppRanking; flash: boolean }) {
  const rankColor =
    app.rank === 1 ? MATRIX_GOLD : app.rank <= 3 ? MATRIX_GREEN : MATRIX_MID;

  return (
    <div
      style={{
        ...styles.row,
        background: flash ? "#001A00" : "transparent",
        transition: "background 0.6s",
      }}
    >
      <span style={{ ...styles.rankNum, color: rankColor }}>
        {String(app.rank).padStart(2, "0")}
      </span>
      <div style={styles.appInfo}>
        <span style={styles.appName}>{app.name}</span>
        <span style={styles.appMeta}>
          {app.developer} · {app.category}
        </span>
      </div>
      <Stars rating={app.rating} />
      <DeltaBadge delta={app.delta} />
    </div>
  );
}

// ── Blinking cursor ───────────────────────────────────────────────────────────

function Cursor() {
  const [on, setOn] = useState(true);
  useEffect(() => {
    const id = setInterval(() => setOn((v) => !v), 530);
    return () => clearInterval(id);
  }, []);
  return (
    <span
      style={{
        display: "inline-block",
        width: "0.6em",
        height: "1em",
        background: on ? MATRIX_GREEN : "transparent",
        verticalAlign: "text-bottom",
        marginLeft: 2,
      }}
    />
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AppStoreTracker() {
  const [data, setData] = useState<RankingsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<string>("all");
  const [categories, setCategories] = useState<string[]>([]);
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());
  const [countdown, setCountdown] = useState(0);
  const prevRanks = useRef<Map<string, number>>(new Map());

  const fetchCategories = useCallback(async () => {
    try {
      const r = await fetch("/v1/appstore/categories");
      if (r.ok) {
        const d = (await r.json()) as { categories: string[] };
        setCategories(["all", ...d.categories]);
      }
    } catch {
      // ignore
    }
  }, []);

  const fetchRankings = useCallback(async () => {
    try {
      const qs =
        category !== "all" ? `?category=${encodeURIComponent(category)}` : "";
      const r = await fetch(`/v1/appstore/rankings${qs}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = (await r.json()) as RankingsResponse;

      // Detect changed positions for flash
      const newFlash = new Set<string>();
      for (const app of d.rankings) {
        const prev = prevRanks.current.get(app.id);
        if (prev !== undefined && prev !== app.rank) {
          newFlash.add(app.id);
        }
      }
      prevRanks.current = new Map(d.rankings.map((a) => [a.id, a.rank]));

      setFlashIds(newFlash);
      setData(d);
      setCountdown(d.next_update_in);
      setError(null);
      setTimeout(() => setFlashIds(new Set()), 1500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [category]);

  useEffect(() => {
    void fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    void fetchRankings();
    const id = setInterval(() => void fetchRankings(), REFRESH_MS);
    return () => clearInterval(id);
  }, [fetchRankings]);

  // Countdown ticker
  useEffect(() => {
    if (countdown <= 0) return;
    const id = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [countdown]);

  return (
    <section style={styles.root}>
      {/* Matrix rain header */}
      <div style={styles.headerWrap}>
        <MatrixRain height={72} />
        <div style={styles.headerContent}>
          <span style={styles.headerLabel}>APP STORE TRACKER</span>
          <Cursor />
          <span style={styles.headerSub}>LIVE RANKINGS v2.0</span>
        </div>
      </div>

      {/* Category filter */}
      <div style={styles.filterRow}>
        <span style={styles.filterLabel}>&gt; CATEGORY_FILTER:</span>
        <div style={styles.filterBtns}>
          {(categories.length > 0 ? categories : ["all"]).map((cat) => (
            <button
              key={cat}
              style={{
                ...styles.catBtn,
                color: category === cat ? MATRIX_BG : MATRIX_GREEN,
                background: category === cat ? MATRIX_GREEN : "transparent",
                borderColor: MATRIX_GREEN,
              }}
              onClick={() => setCategory(cat)}
            >
              {cat.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Status bar */}
      <div style={styles.statusBar}>
        <span style={styles.statusText}>
          REFRESHING IN{" "}
          <span style={{ color: MATRIX_GREEN }}>{countdown}s</span>
        </span>
        {data && (
          <span style={styles.statusText}>
            LAST_SYNC:{" "}
            <span style={{ color: MATRIX_GREEN }}>
              {new Date(data.timestamp).toLocaleTimeString()}
            </span>
          </span>
        )}
      </div>

      {/* Table header */}
      <div style={styles.tableHeader}>
        <span style={{ ...styles.colHeader, width: 36 }}>RNK</span>
        <span style={{ ...styles.colHeader, flex: 1 }}>APPLICATION</span>
        <span style={{ ...styles.colHeader, width: 80 }}>RATING</span>
        <span
          style={{
            ...styles.colHeader,
            width: 60,
            textAlign: "right" as const,
          }}
        >
          DELTA
        </span>
      </div>

      {/* Rankings list */}
      <div style={styles.list}>
        {error ? (
          <div style={styles.errorMsg}>
            <span style={{ color: MATRIX_RED }}>⚠ ERROR:</span> {error}
            <br />
            <span style={{ color: MATRIX_MID, fontSize: "0.75rem" }}>
              Ensure the SWARMZ backend is running on port 8000
            </span>
          </div>
        ) : data ? (
          data.rankings.map((app) => (
            <RankRow key={app.id} app={app} flash={flashIds.has(app.id)} />
          ))
        ) : (
          <div style={styles.loading}>
            <span style={{ color: MATRIX_MID }}>FETCHING RANKINGS</span>
            <Cursor />
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <span style={{ color: MATRIX_DIM }}>
          ■ SWARMZ / APP STORE INTEL MODULE / SIMULATED DATA
        </span>
        <span style={{ color: MATRIX_DIM }}>
          {MATRIX_RAIN_MIN_COLS}+ NODES ACTIVE
        </span>
      </div>
    </section>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, CSSProperties> = {
  root: {
    background: MATRIX_BG,
    border: `1px solid ${MATRIX_BORDER}`,
    borderRadius: 4,
    overflow: "hidden",
    fontFamily: FONT_MONO,
    display: "flex",
    flexDirection: "column",
    boxShadow: `0 0 32px ${MATRIX_DIM}`,
  },
  headerWrap: {
    position: "relative",
    height: 72,
    background: MATRIX_CARD,
    borderBottom: `1px solid ${MATRIX_BORDER}`,
    overflow: "hidden",
  },
  headerContent: {
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "0 20px",
    zIndex: 1,
  },
  headerLabel: {
    color: MATRIX_GREEN,
    fontSize: "1.2rem",
    fontWeight: 700,
    letterSpacing: "0.2em",
    textShadow: `0 0 12px ${MATRIX_GREEN}`,
  },
  headerSub: {
    color: MATRIX_MID,
    fontSize: "0.7rem",
    letterSpacing: "0.15em",
    marginLeft: 8,
  },
  filterRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "10px 16px",
    borderBottom: `1px solid ${MATRIX_BORDER}`,
    flexWrap: "wrap",
  },
  filterLabel: {
    color: MATRIX_MID,
    fontSize: "0.72rem",
    letterSpacing: "0.1em",
    whiteSpace: "nowrap",
  },
  filterBtns: {
    display: "flex",
    gap: 6,
    flexWrap: "wrap",
  },
  catBtn: {
    padding: "3px 10px",
    border: "1px solid",
    borderRadius: 2,
    cursor: "pointer",
    fontSize: "0.68rem",
    fontFamily: FONT_MONO,
    letterSpacing: "0.08em",
    transition: "all 0.15s",
  },
  statusBar: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 16px",
    background: MATRIX_CARD,
    borderBottom: `1px solid ${MATRIX_BORDER}`,
    flexWrap: "wrap",
    gap: 8,
  },
  statusText: {
    color: MATRIX_DIM,
    fontSize: "0.68rem",
    letterSpacing: "0.1em",
  },
  tableHeader: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "8px 16px",
    borderBottom: `1px solid ${MATRIX_BORDER}`,
    background: MATRIX_CARD,
  },
  colHeader: {
    color: MATRIX_MID,
    fontSize: "0.65rem",
    letterSpacing: "0.15em",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    minHeight: 120,
  },
  row: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "9px 16px",
    borderBottom: `1px solid ${MATRIX_BORDER}`,
    cursor: "default",
  },
  rankNum: {
    fontSize: "1rem",
    fontWeight: 700,
    width: 36,
    flexShrink: 0,
    textShadow: `0 0 8px currentColor`,
  },
  appInfo: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 2,
    minWidth: 0,
  },
  appName: {
    color: MATRIX_GREEN,
    fontSize: "0.85rem",
    fontWeight: 600,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  appMeta: {
    color: MATRIX_MID,
    fontSize: "0.65rem",
    letterSpacing: "0.05em",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  delta: {
    width: 60,
    textAlign: "right",
    fontSize: "0.8rem",
    fontWeight: 700,
    flexShrink: 0,
  },
  loading: {
    padding: "32px 16px",
    color: MATRIX_MID,
    fontSize: "0.85rem",
    display: "flex",
    alignItems: "center",
    gap: 6,
    letterSpacing: "0.1em",
  },
  errorMsg: {
    padding: "20px 16px",
    fontSize: "0.8rem",
    lineHeight: 1.7,
    color: MATRIX_MID,
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 16px",
    borderTop: `1px solid ${MATRIX_BORDER}`,
    background: MATRIX_CARD,
    flexWrap: "wrap",
    gap: 8,
  },
};
