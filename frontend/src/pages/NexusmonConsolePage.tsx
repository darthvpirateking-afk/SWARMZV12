import { useState, useEffect, useRef, useCallback } from "react";

const MODULES = [
  { id: "cognition",   label: "COGNITION",   icon: "◈", desc: "Reasoning & Planning",  health: 98,  activity: "scaffolding trajectory",       color: "#00f0ff" },
  { id: "linguistics", label: "LINGUISTICS", icon: "◎", desc: "Language I/O",           health: 100, activity: "parsing operator input",        color: "#a78bfa" },
  { id: "mentality",   label: "MENTALITY",   icon: "◉", desc: "Decision Style",         health: 95,  activity: "stable — methodical",           color: "#f472b6" },
  { id: "hologram",    label: "HOLOGRAM",    icon: "⬡", desc: "State Visualization",    health: 100, activity: "rendering coherence map",       color: "#34d399" },
  { id: "signal",      label: "SIGNAL",      icon: "◇", desc: "Stream Processing",      health: 97,  activity: "monitoring 3 channels",         color: "#fbbf24" },
  { id: "performance", label: "PERFORMANCE", icon: "◆", desc: "Optimization Layer",     health: 99,  activity: "nominal",                       color: "#f87171" },
];

const AGENTS = [
  { id: "atengic", label: "ATENGIC", role: "Trajectory Engineer", status: "active",   trigger: "plan: scaffold: diff:" },
  { id: "daemon",  label: "DAEMON",  role: "Background Runner",   status: "idle",     trigger: "auto-invoked" },
  { id: "doctor",  label: "DOCTOR",  role: "Diagnostics",         status: "active",   trigger: "health: diagnose:" },
  { id: "auditor", label: "AUDITOR", role: "Governance",          status: "watching", trigger: "audit: verify:" },
  { id: "builder", label: "BUILDER", role: "Code Synthesis",      status: "idle",     trigger: "build: emit:" },
];

type Severity = "info" | "warn" | "success";

interface MissionEvent {
  type: string;
  msg: string;
  agent: string;
  severity: Severity;
  ts: string;
}

const EVENT_TEMPLATES: Omit<MissionEvent, "ts">[] = [
  { type: "mission",      msg: "Mission M-0042 cycle complete — 3 tasks resolved",              agent: "DAEMON",   severity: "info" },
  { type: "governance",   msg: "Tool gate: shell_executor blocked (policy: no-rm-rf)",           agent: "AUDITOR",  severity: "warn" },
  { type: "cognition",    msg: "ATENGIC scaffold emitted — 7 steps, 0 ambiguity flags",         agent: "ATENGIC",  severity: "info" },
  { type: "verification", msg: "Verification sweep: 806 passed, 0 failed, 1 skipped",           agent: "DOCTOR",   severity: "success" },
  { type: "swarm",        msg: "Swarm runner: autoloop cycle 117 — state persisted",            agent: "DAEMON",   severity: "info" },
  { type: "upgrade",      msg: "Additive diff proposed: db.py legacy schema compat",            agent: "ATENGIC",  severity: "info" },
  { type: "signal",       msg: "Signal processor: new input stream detected (text/utf-8)",      agent: "BUILDER",  severity: "info" },
  { type: "governance",   msg: "Governance pipeline: decision recorded to audit log",           agent: "AUDITOR",  severity: "info" },
  { type: "hologram",     msg: "Hologram integrity: coherence 0.97, drift 0.02",               agent: "DOCTOR",   severity: "success" },
  { type: "mission",      msg: "Mission M-0043 queued — operator approval pending",             agent: "DAEMON",   severity: "warn" },
  { type: "cognition",    msg: "Decomposition complete: 4 sub-goals identified",               agent: "ATENGIC",  severity: "info" },
  { type: "verification", msg: "Rollback plan verified for diff #291",                          agent: "AUDITOR",  severity: "success" },
];

function generateMissionEvent(tick: number): MissionEvent {
  const base = EVENT_TEMPLATES[tick % EVENT_TEMPLATES.length];
  return { ...base, ts: new Date().toISOString().split("T")[1].split(".")[0] };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Pulse({ color, size = 8 }: { color: string; size?: number }) {
  return (
    <span style={{ position: "relative", display: "inline-block", width: size, height: size, marginRight: 8 }}>
      <span style={{ position: "absolute", inset: 0, borderRadius: "50%", backgroundColor: color, animation: "pulse 2s ease-in-out infinite" }} />
      <span style={{ position: "absolute", inset: -2, borderRadius: "50%", border: `1px solid ${color}`, opacity: 0.4, animation: "pulse-ring 2s ease-in-out infinite" }} />
    </span>
  );
}

function severityColor(s: Severity) {
  return s === "success" ? "#34d399" : s === "warn" ? "#fbbf24" : "#64748b";
}

const STATUS_COLORS: Record<string, string> = { active: "#34d399", idle: "#64748b", watching: "#fbbf24" };

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "#64748b";
  return (
    <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1.5, color, display: "flex", alignItems: "center", gap: 6 }}>
      <Pulse color={color} size={6} />
      {status}
    </span>
  );
}

// ── Terminal entry types ──────────────────────────────────────────────────────

type TermEntryType = "system" | "input" | "output" | "atengic" | "error" | "success";
interface TermEntry { type: TermEntryType; text: string; }

const TERM_COLORS: Record<TermEntryType, string> = {
  input:   "#00f0ff",
  atengic: "#a78bfa",
  error:   "#f87171",
  success: "#34d399",
  system:  "#475569",
  output:  "#94a3b8",
};

// ── Main component ────────────────────────────────────────────────────────────

export function NexusmonConsolePage() {
  const [events, setEvents]               = useState<MissionEvent[]>([]);
  const [tick, setTick]                   = useState(0);
  const [commandInput, setCommandInput]   = useState("");
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [organismPulse, setOrganismPulse] = useState(0);
  const [terminalHistory, setTerminalHistory] = useState<TermEntry[]>([
    { type: "system", text: "NEXUSMON Operator Console v2.1.0" },
    { type: "system", text: "ATENGIC kernel loaded — allegiance: operator-bound" },
    { type: "system", text: 'Type "help" for available commands. Ready.' },
  ]);

  const feedRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<HTMLDivElement>(null);

  // ── Tick / organism pulse ──
  useEffect(() => {
    const id = setInterval(() => {
      setTick((t) => t + 1);
      setOrganismPulse((p) => (p + 1) % 360);
    }, 3000);
    return () => clearInterval(id);
  }, []);

  // ── Feed new event on each tick ──
  useEffect(() => {
    if (tick > 0) {
      setEvents((prev) => [generateMissionEvent(tick), ...prev].slice(0, 50));
    }
  }, [tick]);

  // ── Auto-scroll ──
  useEffect(() => { if (feedRef.current) feedRef.current.scrollTop = 0; }, [events]);
  useEffect(() => { if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight; }, [terminalHistory]);

  // ── Command handler ──
  const handleCommand = useCallback((cmd: string) => {
    const c = cmd.trim().toLowerCase();
    const next: TermEntry[] = [...terminalHistory, { type: "input", text: `operator> ${cmd}` }];

    if (c === "help") {
      next.push({ type: "output", text: "Available commands:" });
      next.push({ type: "output", text: "  status        — organism health overview" });
      next.push({ type: "output", text: "  agents        — list active agents" });
      next.push({ type: "output", text: "  plan: <goal>  — invoke ATENGIC to scaffold" });
      next.push({ type: "output", text: "  verify        — run verification sweep" });
      next.push({ type: "output", text: "  missions      — list active missions" });
      next.push({ type: "output", text: "  clear         — clear terminal" });
    } else if (c === "status") {
      next.push({ type: "output", text: "ORGANISM STATUS: OPERATIONAL" });
      MODULES.forEach((m) => next.push({ type: "output", text: `  ${m.icon} ${m.label.padEnd(14)} ${m.health}%  ${m.activity}` }));
      next.push({ type: "output", text: `  Overall coherence: 0.97 | Drift: 0.02 | Uptime: ${Math.floor(tick * 3 / 60)}m ${(tick * 3) % 60}s` });
    } else if (c === "agents") {
      next.push({ type: "output", text: "SWARMZ AGENT GRAPH:" });
      AGENTS.forEach((a) => next.push({ type: "output", text: `  ${a.label.padEnd(10)} [${a.status.padEnd(8)}] ${a.role} — triggers: ${a.trigger}` }));
    } else if (c.startsWith("plan:") || c.startsWith("scaffold:")) {
      const goal = cmd.slice(cmd.indexOf(":") + 1).trim();
      next.push({ type: "atengic", text: "ATENGIC responding..." });
      next.push({ type: "atengic", text: `Decomposing: "${goal}"` });
      next.push({ type: "atengic", text: "Step 1: Identify constraints and inputs" });
      next.push({ type: "atengic", text: "Step 2: Map dependencies" });
      next.push({ type: "atengic", text: "Step 3: Generate additive diff" });
      next.push({ type: "atengic", text: "Step 4: Emit rollback plan" });
      next.push({ type: "atengic", text: '"I do not guess. I scaffold."' });
    } else if (c === "verify") {
      next.push({ type: "success", text: "Verification sweep initiated..." });
      next.push({ type: "success", text: "806 passed | 0 failed | 1 skipped | 2 warnings (non-blocking)" });
      next.push({ type: "success", text: "All systems nominal." });
    } else if (c === "missions") {
      next.push({ type: "output", text: "ACTIVE MISSIONS:" });
      next.push({ type: "output", text: "  M-0042  [complete]   Routine autoloop cycle" });
      next.push({ type: "output", text: "  M-0043  [pending]    Operator approval required" });
      next.push({ type: "output", text: "  M-0044  [queued]     Hologram coherence optimization" });
    } else if (c === "clear") {
      setTerminalHistory([{ type: "system", text: "Terminal cleared. Ready." }]);
      setCommandInput("");
      return;
    } else if (c !== "") {
      next.push({ type: "error", text: `Unknown command: "${cmd}". Type "help" for available commands.` });
    }

    setTerminalHistory(next);
    setCommandInput("");
  }, [terminalHistory, tick]);

  const overallHealth = Math.round(MODULES.reduce((sum, m) => sum + m.health, 0) / MODULES.length);

  return (
    <div style={{
      background: "#06080c", color: "#c8d6e5",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace",
      height: "100%", fontSize: 13, position: "relative", overflow: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&display=swap');
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes pulse-ring { 0% { transform: scale(1); opacity: 0.4; } 100% { transform: scale(2); opacity: 0; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes scanline { 0% { top: -100%; } 100% { top: 200%; } }
        .nx-module-card:hover { border-color: var(--nx-accent) !important; background: rgba(255,255,255,0.03) !important; }
        .nx-event-row { animation: fadeIn 0.3s ease-out; }
        .nx-cmd-input:focus { outline: none; }
        .nx-scan-line { position: absolute; width: 100%; height: 1px; background: linear-gradient(90deg, transparent, rgba(0,240,255,0.06), transparent); animation: scanline 8s linear infinite; pointer-events: none; z-index: 0; }
      `}</style>

      <div className="nx-scan-line" />

      {/* ── Top Bar ── */}
      <div style={{
        borderBottom: "1px solid #141a24", padding: "12px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "rgba(6,8,12,0.95)", position: "relative", zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            fontFamily: "'Orbitron', sans-serif", fontWeight: 800, fontSize: 18,
            letterSpacing: 4, color: "#00f0ff",
            textShadow: "0 0 20px rgba(0,240,255,0.3), 0 0 40px rgba(0,240,255,0.1)",
          }}>
            NEXUSMON
          </div>
          <div style={{ width: 1, height: 20, background: "#1e293b" }} />
          <span style={{ fontSize: 10, color: "#475569", letterSpacing: 2, textTransform: "uppercase" }}>
            Operator Console v2.1
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
            <Pulse color={overallHealth > 95 ? "#34d399" : "#fbbf24"} />
            <span style={{ color: overallHealth > 95 ? "#34d399" : "#fbbf24", fontWeight: 600 }}>
              ORGANISM {overallHealth > 95 ? "NOMINAL" : "DEGRADED"}
            </span>
            <span style={{ color: "#334155" }}>|</span>
            <span style={{ color: "#64748b" }}>Coherence 0.97</span>
            <span style={{ color: "#334155" }}>|</span>
            <span style={{ color: "#64748b" }}>Tests 806/806</span>
            <span style={{ color: "#334155" }}>|</span>
            <span style={{ color: "#64748b" }}>Agents {AGENTS.filter(a => a.status === "active").length}/{AGENTS.length}</span>
          </div>
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div style={{
        display: "grid", gridTemplateColumns: "280px 1fr 340px",
        height: "calc(100% - 49px)", gap: 0,
      }}>

        {/* ── Left: Organism Modules + Agents ── */}
        <div style={{ borderRight: "1px solid #141a24", padding: 16, overflowY: "auto", background: "rgba(6,8,12,0.6)" }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2.5, color: "#475569", textTransform: "uppercase", marginBottom: 16 }}>
            Organism Modules
          </div>

          {MODULES.map((mod) => (
            <div
              key={mod.id}
              className="nx-module-card"
              onClick={() => setSelectedModule(selectedModule === mod.id ? null : mod.id)}
              style={{
                ["--nx-accent" as string]: mod.color,
                border: `1px solid ${selectedModule === mod.id ? mod.color : "#141a24"}`,
                borderRadius: 6, padding: 12, marginBottom: 8, cursor: "pointer",
                background: selectedModule === mod.id ? "rgba(255,255,255,0.02)" : "transparent",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: mod.color, fontSize: 14 }}>{mod.icon}</span>
                  <span style={{ fontWeight: 600, fontSize: 11, letterSpacing: 1.5, color: "#e2e8f0" }}>{mod.label}</span>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 700, fontFamily: "'Orbitron', sans-serif",
                  color: mod.health >= 98 ? "#34d399" : mod.health >= 90 ? "#fbbf24" : "#f87171",
                }}>
                  {mod.health}%
                </span>
              </div>
              <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4 }}>{mod.desc}</div>
              <div style={{ fontSize: 10, color: mod.color, opacity: 0.7 }}>▸ {mod.activity}</div>

              {selectedModule === mod.id && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${mod.color}22`, fontSize: 10, color: "#94a3b8" }}>
                  <div style={{ marginBottom: 4 }}>Uptime: 99.9%</div>
                  <div style={{ marginBottom: 4 }}>Last cycle: {Math.floor(Math.random() * 5 + 1)}s ago</div>
                  <div style={{ marginBottom: 4 }}>Memory: {Math.floor(Math.random() * 40 + 20)}MB</div>
                  <div style={{ marginTop: 8, height: 3, borderRadius: 2, background: "#141a24", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${mod.health}%`, borderRadius: 2, background: `linear-gradient(90deg, ${mod.color}66, ${mod.color})` }} />
                  </div>
                </div>
              )}
            </div>
          ))}

          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2.5, color: "#475569", textTransform: "uppercase", marginTop: 24, marginBottom: 12 }}>
            SWARMZ Agents
          </div>

          {AGENTS.map((agent) => (
            <div key={agent.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid #0d1117" }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 11, color: "#e2e8f0", letterSpacing: 1 }}>{agent.label}</div>
                <div style={{ fontSize: 10, color: "#475569" }}>{agent.role}</div>
              </div>
              <StatusBadge status={agent.status} />
            </div>
          ))}
        </div>

        {/* ── Center: Organism Viz + Terminal ── */}
        <div style={{ display: "flex", flexDirection: "column", background: "#080b10", position: "relative" }}>
          {/* Organism Visualization */}
          <div style={{ height: 140, borderBottom: "1px solid #141a24", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", inset: 0, opacity: 0.03, background: "radial-gradient(ellipse at center, #00f0ff 0%, transparent 70%)" }} />
            <svg width="240" height="120" viewBox="0 0 240 120" style={{ opacity: 0.8 }}>
              {MODULES.map((mod, i) => {
                const cx = 40 + i * 36;
                const cy = 60 + Math.sin((organismPulse + i * 60) * Math.PI / 180) * 12;
                const nextCy = 60 + Math.sin((organismPulse + (i + 1) * 60) * Math.PI / 180) * 12;
                return (
                  <g key={mod.id}>
                    <circle cx={cx} cy={cy} r={14} fill="none" stroke={mod.color} strokeWidth={1} opacity={0.3 + (mod.health / 100) * 0.5} />
                    <circle cx={cx} cy={cy} r={6} fill={mod.color} opacity={0.2 + Math.sin((organismPulse + i * 40) * Math.PI / 180) * 0.3} />
                    <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fill={mod.color} fontSize={8} fontFamily="monospace">
                      {mod.icon}
                    </text>
                    {i < MODULES.length - 1 && (
                      <line x1={cx + 14} y1={cy} x2={cx + 22} y2={nextCy} stroke="#1e293b" strokeWidth={1} strokeDasharray="3,3" />
                    )}
                  </g>
                );
              })}
              <text x={120} y={108} textAnchor="middle" fill="#334155" fontSize={9} fontFamily="'Orbitron', monospace" letterSpacing={3}>
                ORGANISM STATE
              </text>
            </svg>
          </div>

          {/* Terminal */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: 16, overflow: "hidden" }}>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2.5, color: "#475569", textTransform: "uppercase", marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>Operator Terminal</span>
              <span style={{ color: "#334155", fontWeight: 400 }}>ATENGIC-bound</span>
            </div>

            <div ref={termRef} style={{ flex: 1, overflowY: "auto", marginBottom: 12, background: "#0a0d12", border: "1px solid #141a24", borderRadius: 6, padding: 12, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, lineHeight: 1.8 }}>
              {terminalHistory.map((entry, i) => (
                <div key={i} style={{ color: TERM_COLORS[entry.type], whiteSpace: "pre-wrap" }}>
                  {entry.text}
                </div>
              ))}
            </div>

            <div style={{ display: "flex", alignItems: "center", background: "#0a0d12", border: "1px solid #141a24", borderRadius: 6, padding: "8px 12px" }}>
              <span style={{ color: "#00f0ff", marginRight: 8, fontSize: 12, fontWeight: 600 }}>operator&gt;</span>
              <input
                className="nx-cmd-input"
                type="text"
                value={commandInput}
                onChange={(e) => setCommandInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleCommand(commandInput); }}
                placeholder="type a command..."
                style={{ flex: 1, background: "transparent", border: "none", color: "#e2e8f0", fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}
              />
            </div>
          </div>
        </div>

        {/* ── Right: Mission Feed + Verification ── */}
        <div style={{ borderLeft: "1px solid #141a24", display: "flex", flexDirection: "column", background: "rgba(6,8,12,0.6)" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid #141a24", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2.5, color: "#475569", textTransform: "uppercase" }}>
              Mission Feed
            </span>
            <span style={{ fontSize: 10, color: "#334155" }}>{events.length} events</span>
          </div>

          <div ref={feedRef} style={{ flex: 1, overflowY: "auto", padding: 12 }}>
            {events.length === 0 && (
              <div style={{ color: "#334155", fontSize: 11, textAlign: "center", marginTop: 40 }}>
                Awaiting mission events...
              </div>
            )}
            {events.map((ev, i) => (
              <div key={i} className="nx-event-row" style={{ padding: "10px 12px", marginBottom: 6, borderRadius: 4, background: "#0a0d12", borderLeft: `2px solid ${severityColor(ev.severity)}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: 1.5, textTransform: "uppercase", color: severityColor(ev.severity) }}>
                    {ev.type}
                  </span>
                  <span style={{ fontSize: 9, color: "#334155", fontFamily: "monospace" }}>{ev.ts}</span>
                </div>
                <div style={{ fontSize: 11, color: "#94a3b8", lineHeight: 1.5, marginBottom: 4 }}>{ev.msg}</div>
                <div style={{ fontSize: 9, color: "#475569" }}>agent: {ev.agent}</div>
              </div>
            ))}
          </div>

          {/* Verification Status */}
          <div style={{ borderTop: "1px solid #141a24", padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2.5, color: "#475569", textTransform: "uppercase", marginBottom: 12 }}>
              Verification
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {([
                { label: "PASSED",   value: "806", color: "#34d399" },
                { label: "FAILED",   value: "0",   color: "#34d399" },
                { label: "SKIPPED",  value: "1",   color: "#fbbf24" },
                { label: "WARNINGS", value: "2",   color: "#64748b" },
              ] as const).map((stat) => (
                <div key={stat.label} style={{ background: "#0a0d12", borderRadius: 4, padding: "8px 10px", border: "1px solid #141a24" }}>
                  <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: 16, fontWeight: 700, color: stat.color, marginBottom: 2 }}>
                    {stat.value}
                  </div>
                  <div style={{ fontSize: 9, letterSpacing: 1.5, color: "#475569" }}>{stat.label}</div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 12, padding: "8px 10px", background: "#0a0d12", borderRadius: 4, border: "1px solid #141a24", fontSize: 10 }}>
              <div style={{ color: "#475569", marginBottom: 4 }}>ATENGIC KERNEL</div>
              <div style={{ color: "#a78bfa", fontStyle: "italic" }}>"I do not guess. I scaffold."</div>
              <div style={{ color: "#334155", marginTop: 4, fontSize: 9 }}>allegiance: operator-bound | ethics: no hallucination</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
