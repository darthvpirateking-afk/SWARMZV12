import {
  type CSSProperties,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  colors,
  radii,
  shadows,
  spacing,
  typography,
} from "../theme/cosmicTokens";
import {
  swarmApi,
  organismApi,
  signalApi,
  operatorApi,
  cognitionApi,
  awarenessApi,
  evolutionApi,
  type SwarmRunnerStatus,
  type SwarmUnit,
  type OrganismStatusResponse,
  type SignalModulesResponse,
  type SignalStatusResponse,
  type OperatorRank,
  type CognitionStatus,
  type AwarenessAlerts,
  type AwarenessTopology,
  type EvolutionStatus,
} from "../api/swarm";
import { systemApi, type LogEntry } from "../api/system";
import { artifactsApi, type ArtifactStats } from "../api/artifacts";

const POLL_MS = 4000;

interface SwarmSnapshot {
  runner: SwarmRunnerStatus | null;
  units: SwarmUnit[];
  organism: OrganismStatusResponse | null;
  signalStatus: SignalStatusResponse | null;
  signalModules: SignalModulesResponse | null;
  rank: OperatorRank | null;
  cognition: CognitionStatus | null;
  alerts: AwarenessAlerts | null;
  topology: AwarenessTopology | null;
  evolution: EvolutionStatus | null;
  logs: LogEntry[];
  vaultStats: ArtifactStats | null;
  lastUpdated: Date;
}

function useLiveSnapshot(): { data: SwarmSnapshot; tick: number } {
  const [tick, setTick] = useState(0);
  const [data, setData] = useState<SwarmSnapshot>({
    runner: null, units: [], organism: null, signalStatus: null,
    signalModules: null, rank: null, cognition: null, alerts: null,
    topology: null, evolution: null, logs: [], vaultStats: null,
    lastUpdated: new Date(),
  });

  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([
      swarmApi.runnerStatus(),
      swarmApi.units(),
      organismApi.status(),
      signalApi.status(),
      signalApi.modules(),
      operatorApi.rank(),
      cognitionApi.status(),
      awarenessApi.alerts(),
      awarenessApi.topology(),
      evolutionApi.full(),
      systemApi.logs({ limit: 30 }),
      artifactsApi.stats(),
    ]);

    setData({
      runner:        results[0].status === "fulfilled" ? results[0].value : null,
      units:         results[1].status === "fulfilled" ? results[1].value.units : [],
      organism:      results[2].status === "fulfilled" ? results[2].value : null,
      signalStatus:  results[3].status === "fulfilled" ? results[3].value : null,
      signalModules: results[4].status === "fulfilled" ? results[4].value : null,
      rank:          results[5].status === "fulfilled" ? results[5].value : null,
      cognition:     results[6].status === "fulfilled" ? results[6].value : null,
      alerts:        results[7].status === "fulfilled" ? results[7].value : null,
      topology:      results[8].status === "fulfilled" ? results[8].value : null,
      evolution:     results[9].status === "fulfilled" ? results[9].value : null,
      logs:          results[10].status === "fulfilled" ? results[10].value.entries : [],
      vaultStats:    results[11].status === "fulfilled" ? results[11].value : null,
      lastUpdated:   new Date(),
    });
    setTick(t => t + 1);
  }, []);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  return { data, tick };
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function SwarmWatchPage() {
  const { data, tick } = useLiveSnapshot();
  const { runner, units, organism, signalStatus, signalModules, rank,
          cognition, alerts, topology, evolution, logs, vaultStats } = data;

  return (
    <div style={s.root}>
      <style>{css}</style>

      {/* ─ Top bar ─ */}
      <div style={s.topBar}>
        <span style={s.topBarTitle}>⬡ SWARMWATCH — LIVE COMMAND CENTRE</span>
        <span style={s.topBarSub}>
          {data.lastUpdated.toLocaleTimeString()} · tick #{tick}
        </span>
      </div>

      {/* ─ Grid ─ */}
      <div style={s.grid}>

        {/* ── 1. Swarm Runner + Mission Topology ── */}
        <Card title="⚡ Swarm Runner" accent={colors.primaryAccent}>
          {runner ? (
            <div style={s.runnerGrid}>
              <Stat label="Runner" value={runner.runner.toUpperCase()} color={colors.running} />
              <Stat label="Pending" value={runner.pending_count} color={colors.warning} />
              <Stat label="Running" value={runner.running_count} color={colors.primaryAccent} />
              <Stat label="Done" value={runner.success_count} color={colors.running} />
              <Stat label="Failed" value={runner.failure_count} color={colors.error} />
            </div>
          ) : <Spinner />}
          {topology && topology.topology.nodes.length > 0 && (
            <div style={s.section}>
              <div style={s.sectionLabel}>ACTIVE TOPOLOGY</div>
              {topology.topology.nodes.map(n => (
                <div key={n.mission_id} style={s.topRow}>
                  <span style={{ ...s.badge, background: riskColor(n.risk) + "30", color: riskColor(n.risk) }}>
                    RISK {Math.round(n.risk * 100)}%
                  </span>
                  <span style={s.muted}>{n.mission_id.slice(0, 16)}</span>
                  <span style={{ ...s.badge, color: colors.warning }}>{n.status}</span>
                  <span style={s.muted}>{n.resources.slice(0, 2).join(", ")}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* ── 2. Swarm Units ── */}
        <Card title="🐝 Swarm Units" accent={colors.secondaryAccent}>
          {units.length === 0 ? <Empty text="No units deployed" /> :
            units.map(u => <UnitRow key={u.id} unit={u} />)}
        </Card>

        {/* ── 3. Organism ── */}
        <Card title="🧬 Organism" accent="#A78BFA">
          {organism ? <OrganismPanel org={organism} /> : <Spinner />}
        </Card>

        {/* ── 4. Evolution ── */}
        <Card title="🌱 Evolution" accent="#34D399">
          {evolution ? <EvolutionPanel ev={evolution} /> : <Spinner />}
        </Card>

        {/* ── 5. Operator Rank ── */}
        <Card title="🏅 Operator Rank" accent={colors.warning}>
          {rank ? <RankPanel rank={rank} /> : <Spinner />}
        </Card>

        {/* ── 6. Signal Modules ── */}
        <Card title="📡 Signal Modules" accent={colors.primaryAccent} wide>
          {signalStatus && (
            <div style={s.runnerGrid}>
              <Stat label="Total" value={signalStatus.total_modules} color={colors.primaryAccent} />
              <Stat label="Enabled" value={signalStatus.enabled_modules} color={colors.running} />
              {Object.entries(signalStatus.dials).map(([k, v]) => (
                <DialStat key={k} name={k} value={v} />
              ))}
            </div>
          )}
          {signalModules && (
            <div style={s.modulesGrid}>
              {Object.values(signalModules.modules).map(m => (
                <ModuleChip key={m.module_id} module={m} />
              ))}
            </div>
          )}
        </Card>

        {/* ── 7. Cognition ── */}
        <Card title="🧠 Cognition" accent="#60A5FA">
          {cognition ? <CognitionPanel cog={cognition} /> : <Spinner />}
        </Card>

        {/* ── 8. Awareness ── */}
        <Card title="👁️ Awareness" accent={colors.warning}>
          {alerts ? <AlertsPanel alerts={alerts} /> : <Spinner />}
        </Card>

        {/* ── 9. Vault ── */}
        <Card title="🗃️ Artifact Vault" accent={colors.secondaryAccent}>
          {vaultStats ? <VaultPanel stats={vaultStats} /> : <Spinner />}
        </Card>

        {/* ── 10. Live Log Feed ── */}
        <Card title="📋 Kernel Log Feed" accent={colors.logInfo} wide>
          <LogFeed logs={logs} />
        </Card>

      </div>
    </div>
  );
}

// ─── Sub-panels ────────────────────────────────────────────────────────────────

function UnitRow({ unit }: { unit: SwarmUnit }) {
  const statusColor =
    unit.status === "DEPLOYED" ? colors.running :
    unit.status === "IDLE"     ? colors.textSecondary :
    colors.error;

  return (
    <div style={s.unitRow}>
      <span style={{ ...s.unitType, color: colors.secondaryAccent }}>{unit.unit_type}</span>
      <span style={s.unitName}>{unit.name}</span>
      <span style={{ ...s.badge, color: statusColor, borderColor: statusColor }}>{unit.status}</span>
      <span style={s.muted}>Lv {unit.level} · {unit.missions_completed} done</span>
      <span style={{ ...s.muted, color: "#34D399" }}>XP {unit.xp}</span>
    </div>
  );
}

function OrganismPanel({ org }: { org: OrganismStatusResponse }) {
  const ev = org.evolution;
  return (
    <div style={{ display: "grid", gap: spacing.sm }}>
      <div style={s.runnerGrid}>
        <Stat label="Stage" value={ev.stage} color={ev.stage_color} />
        <Stat label="Level" value={ev.level} color={colors.primaryAccent} />
        <Stat label="XP" value={ev.xp} color="#34D399" />
        <Stat label="Missions" value={ev.total_missions} color={colors.warning} />
        <Stat label="Workers" value={org.workers.active_count} color={colors.secondaryAccent} />
      </div>
      <div style={s.sectionLabel}>ACTIVE TRAITS</div>
      <div style={s.traitList}>
        {ev.active_traits.map(t => (
          <span key={t.id} style={{ ...s.traitChip, background: `${colors.primaryAccent}18`, color: colors.primaryAccent }}
            title={t.desc}>
            {t.label}
          </span>
        ))}
      </div>
      {ev.recent_events.length > 0 && (
        <>
          <div style={s.sectionLabel}>RECENT EVENTS</div>
          {ev.recent_events.slice(0, 4).map((e, i) => (
            <div key={i} style={s.eventRow}>
              <span style={{ ...s.badge, color: "#A78BFA" }}>{e.type}</span>
              <span style={s.muted}>{e.label ?? `${e.from ?? ""} → ${e.to ?? ""}`}</span>
              <span style={s.ts}>{new Date(e.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function EvolutionPanel({ ev }: { ev: EvolutionStatus }) {
  const pct = ev.total_missions > 0 ? Math.round(ev.success_rate * 100) : 0;
  return (
    <div style={{ display: "grid", gap: spacing.sm }}>
      <div style={s.runnerGrid}>
        <Stat label="Stage" value={ev.current_stage} color="#34D399" />
        <Stat label="Level" value={ev.level} color={colors.primaryAccent} />
        <Stat label="XP" value={ev.xp} color={colors.warning} />
        <Stat label="Success %" value={`${pct}%`} color={pct > 50 ? colors.running : colors.error} />
      </div>
      <div style={s.sectionLabel}>UNLOCKED TRAITS</div>
      <div style={s.traitList}>
        {ev.active_traits.map(t => (
          <span key={t.id} style={{ ...s.traitChip, background: `#34D39918`, color: "#34D399" }}
            title={t.desc}>
            {t.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function RankPanel({ rank }: { rank: OperatorRank }) {
  const pct = Math.min(100, Math.round(rank.progress * 100));
  const rankColor =
    rank.rank === "S" ? "#FFD700" :
    rank.rank === "A" ? "#FF6FD8" :
    rank.rank === "B" ? "#4EF2C5" :
    rank.rank === "C" ? "#60A5FA" :
    colors.textSecondary;

  return (
    <div style={{ display: "grid", gap: spacing.sm }}>
      <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
        <span style={{ fontSize: "2.5rem", color: rankColor, fontWeight: 900 }}>{rank.rank}</span>
        <div>
          <div style={{ color: colors.textPrimary, fontSize: typography.fontSizeMd }}>
            {rank.xp} XP → {rank.next_rank} ({rank.xp_needed} needed)
          </div>
          <div style={s.xpTrack}>
            <div style={{ ...s.xpFill, width: `${pct}%`, background: rankColor }} />
          </div>
        </div>
      </div>
      <div style={s.sectionLabel}>PERMISSIONS</div>
      <div style={s.permGrid}>
        {Object.entries(rank.permissions).map(([k, v]) => (
          <span key={k} style={{
            ...s.permChip,
            color: v ? colors.running : colors.textSecondary,
            opacity: v ? 1 : 0.4,
          }}>
            {v ? "✓" : "✗"} {k.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

function ModuleChip({ module: m }: { module: { module_id: string; title: string; enabled: boolean; status: string } }) {
  return (
    <div style={{
      ...s.moduleChip,
      borderColor: m.enabled ? `${colors.primaryAccent}44` : colors.borderColor,
      opacity: m.enabled ? 1 : 0.55,
    }}>
      <span style={{ color: m.enabled ? colors.primaryAccent : colors.textSecondary, fontSize: "0.7rem", fontWeight: 700 }}>
        {m.enabled ? "●" : "○"}
      </span>
      <span style={{ color: colors.textPrimary, fontSize: "0.7rem", fontFamily: typography.fontFamily }}>
        {m.title}
      </span>
    </div>
  );
}

function CognitionPanel({ cog }: { cog: CognitionStatus }) {
  return (
    <div style={s.runnerGrid}>
      <Stat label="Predictions" value={cog.predictions.total} color="#60A5FA" />
      <Stat label="Resolved" value={cog.predictions.resolved} color={colors.running} />
      <Stat label="Beliefs" value={cog.beliefs.graph_nodes} color={colors.secondaryAccent} />
      <Stat label="Edges" value={cog.beliefs.graph_edges} color={colors.warning} />
      <Stat label="Errors" value={cog.errors.total} color={cog.errors.total > 0 ? colors.error : colors.textSecondary} />
      <Stat label="Memory" value={cog.memory.total} color="#A78BFA" />
    </div>
  );
}

function AlertsPanel({ alerts }: { alerts: AwarenessAlerts }) {
  const al = alerts.alerts;
  const items = [
    { label: "Variance Rising", active: al.variance_rising },
    { label: "Coupling Detected", active: al.coupling_detected },
    { label: "Bounded Results", active: al.bounded_results },
  ];
  return (
    <div style={{ display: "grid", gap: spacing.sm }}>
      <div style={s.runnerGrid}>
        <Stat label="Total Missions" value={al.total_missions} color={colors.primaryAccent} />
        <Stat label="Success Rate" value={`${Math.round(al.success_rate * 100)}%`}
          color={al.success_rate > 0.5 ? colors.running : colors.warning} />
      </div>
      <div style={s.traitList}>
        {items.map(item => (
          <span key={item.label} style={{
            ...s.traitChip,
            background: item.active ? `${colors.error}18` : `${colors.running}12`,
            color: item.active ? colors.error : colors.running,
          }}>
            {item.active ? "⚠" : "✓"} {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function VaultPanel({ stats }: { stats: ArtifactStats }) {
  return (
    <div style={{ display: "grid", gap: spacing.sm }}>
      <div style={s.runnerGrid}>
        <Stat label="Total" value={stats.total} color={colors.primaryAccent} />
        <Stat label="Pending" value={stats.pending_review} color={colors.warning} />
        <Stat label="Approved" value={stats.by_status["APPROVED"] ?? 0} color={colors.running} />
        <Stat label="Rejected" value={stats.by_status["REJECTED"] ?? 0} color={colors.error} />
      </div>
      {Object.keys(stats.by_type).length > 0 && (
        <div style={s.traitList}>
          {Object.entries(stats.by_type).map(([type, count]) => (
            <span key={type} style={{ ...s.traitChip, background: `${colors.secondaryAccent}18`, color: colors.secondaryAccent }}>
              {type}: {count}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function LogFeed({ logs }: { logs: LogEntry[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  const levelColor = (l: string) =>
    l === "ERROR" || l === "CRITICAL" ? colors.logError :
    l === "WARN" || l === "WARNING"   ? colors.logWarn :
    colors.logInfo;

  if (logs.length === 0) return <Empty text="No log entries yet" />;
  return (
    <div ref={ref} style={s.logBox}>
      {logs.slice(-25).map((entry, i) => (
        <div key={i} style={s.logLine}>
          <span style={{ color: colors.textSecondary, fontFamily: "monospace", fontSize: "0.65rem", flexShrink: 0 }}>
            {new Date(entry.timestamp).toLocaleTimeString()}
          </span>
          <span style={{ color: levelColor(entry.level), fontFamily: "monospace", fontSize: "0.65rem", flexShrink: 0, fontWeight: 700 }}>
            {entry.level}
          </span>
          <span style={{ color: colors.primaryAccent, fontFamily: "monospace", fontSize: "0.65rem", flexShrink: 0 }}>
            [{entry.source}]
          </span>
          <span style={{ color: colors.textPrimary, fontSize: "0.72rem", fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {entry.message}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Atoms ─────────────────────────────────────────────────────────────────────

function Card({ title, accent, children, wide = false }: {
  title: string; accent: string; children: React.ReactNode; wide?: boolean
}) {
  return (
    <div style={{ ...s.card, gridColumn: wide ? "1 / -1" : undefined, borderTopColor: accent }}>
      <div style={{ ...s.cardTitle, color: accent }}>{title}</div>
      {children}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div style={s.statBox}>
      <span style={{ ...s.statVal, color }}>{value}</span>
      <span style={s.statLabel}>{label}</span>
    </div>
  );
}

function DialStat({ name, value }: { name: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div style={s.statBox}>
      <span style={{ ...s.statVal, color: colors.warning }}>{pct}%</span>
      <span style={s.statLabel}>{name.replace(/_/g, " ")}</span>
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ color: colors.textSecondary, fontSize: "0.78rem", padding: spacing.md, fontFamily: "monospace" }}>
      ⟳ loading…
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div style={{ color: colors.textSecondary, fontSize: "0.78rem", padding: spacing.md, textAlign: "center", fontFamily: typography.fontFamily }}>
      {text}
    </div>
  );
}

function riskColor(risk: number) {
  if (risk > 0.7) return colors.error;
  if (risk > 0.4) return colors.warning;
  return colors.running;
}

// ─── Styles ────────────────────────────────────────────────────────────────────

const css = `
  @keyframes swPulse { 0%,100%{opacity:.5} 50%{opacity:1} }
`;

const s: Record<string, CSSProperties> = {
  root: {
    display: "grid",
    gap: spacing.md,
    maxWidth: 1400,
    width: "100%",
  },
  topBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: `${spacing.sm} ${spacing.md}`,
    background: `${colors.primaryAccent}0a`,
    borderRadius: radii.md,
    border: `1px solid ${colors.primaryAccent}30`,
  },
  topBarTitle: {
    color: colors.primaryAccent,
    fontSize: typography.fontSizeLg,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.06em",
  },
  topBarSub: {
    color: colors.textSecondary,
    fontSize: "0.72rem",
    fontFamily: "monospace",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: spacing.md,
    alignItems: "start",
  },
  card: {
    background: colors.cardBg,
    border: `1px solid ${colors.borderColor}`,
    borderTop: "2px solid",
    borderRadius: radii.lg,
    padding: spacing.md,
    display: "grid",
    gap: spacing.sm,
    boxShadow: shadows.card,
  },
  cardTitle: {
    fontSize: typography.fontSizeMd,
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.06em",
  },
  runnerGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  statBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    minWidth: 56,
    background: "#08101e",
    borderRadius: radii.sm,
    padding: `${spacing.xs} ${spacing.sm}`,
    border: `1px solid ${colors.borderColor}`,
  },
  statVal: {
    fontSize: typography.fontSizeLg,
    fontWeight: typography.fontWeightBold,
    fontFamily: "monospace",
  },
  statLabel: {
    fontSize: "0.6rem",
    color: colors.textSecondary,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.06em",
    textTransform: "uppercase" as const,
    marginTop: 2,
  },
  unitRow: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    padding: `${spacing.xs} ${spacing.sm}`,
    background: "#060c18",
    borderRadius: radii.sm,
    border: `1px solid ${colors.borderColor}`,
    flexWrap: "wrap" as const,
  },
  unitType: {
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: "monospace",
    letterSpacing: "0.06em",
  },
  unitName: {
    color: colors.textPrimary,
    fontSize: typography.fontSizeMd,
    fontFamily: typography.fontFamily,
    fontWeight: typography.fontWeightMedium,
    flex: 1,
  },
  badge: {
    padding: `1px ${spacing.xs}`,
    borderRadius: radii.full,
    border: "1px solid",
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: "monospace",
    letterSpacing: "0.04em",
    flexShrink: 0,
  },
  muted: {
    color: colors.textSecondary,
    fontSize: typography.fontSizeSm,
    fontFamily: "monospace",
  },
  ts: {
    color: colors.textSecondary,
    fontSize: "0.62rem",
    fontFamily: "monospace",
    flexShrink: 0,
    marginLeft: "auto",
  },
  section: {
    display: "grid",
    gap: 4,
  },
  sectionLabel: {
    color: colors.textSecondary,
    fontSize: "0.6rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    letterSpacing: "0.1em",
    paddingTop: 4,
  },
  topRow: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    flexWrap: "wrap" as const,
  },
  traitList: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: spacing.xs,
  },
  traitChip: {
    padding: `2px ${spacing.sm}`,
    borderRadius: radii.full,
    fontSize: "0.65rem",
    fontWeight: typography.fontWeightBold,
    fontFamily: typography.fontFamily,
    cursor: "default",
  },
  eventRow: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    flexWrap: "wrap" as const,
  },
  xpTrack: {
    height: 4,
    background: colors.borderColor,
    borderRadius: radii.full,
    overflow: "hidden",
    width: 120,
    marginTop: 4,
  },
  xpFill: {
    height: "100%",
    borderRadius: radii.full,
    transition: "width 0.5s ease",
  },
  permGrid: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 4,
  },
  permChip: {
    fontSize: "0.6rem",
    fontFamily: "monospace",
    padding: `1px ${spacing.xs}`,
  },
  modulesGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
    gap: spacing.xs,
  },
  moduleChip: {
    display: "flex",
    alignItems: "center",
    gap: spacing.xs,
    padding: `${spacing.xs} ${spacing.sm}`,
    background: "#06101e",
    borderRadius: radii.sm,
    border: "1px solid",
  },
  logBox: {
    display: "grid",
    gap: 3,
    maxHeight: 280,
    overflowY: "auto" as const,
    background: "#03080f",
    borderRadius: radii.md,
    padding: spacing.sm,
    border: `1px solid ${colors.borderColor}`,
  },
  logLine: {
    display: "flex",
    alignItems: "center",
    gap: spacing.sm,
    minWidth: 0,
  },
};
