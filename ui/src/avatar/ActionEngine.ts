// ActionEngine.ts — Intent detection + action execution for natural language commands
// Detects what the operator WANTS TO DO and actually DOES IT via API calls.
// Falls through to normal chat only if no actionable intent is detected.

export type ActionResult = {
  executed: boolean;
  action: string;
  result: string;
  data?: any;
};

type IntentPattern = {
  patterns: RegExp[];
  action: string;
  extract?: (msg: string) => Record<string, string>;
  execute: (msg: string, extracted: Record<string, string>) => Promise<ActionResult>;
};

/* ─── helper ──────────────────────────────────────────────────── */
async function api(path: string, method = 'GET', body?: any) {
  const opts: RequestInit = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  return res.json();
}

/* ─── intent definitions ──────────────────────────────────────── */
const INTENTS: IntentPattern[] = [

  // ── MODE SWITCHING ─────────────────────────────────────────
  {
    patterns: [
      /switch\s+(?:to\s+)?(?:mode\s+)?(companion|build|hologram)/i,
      /(?:change|set|go\s+to|enter|activate)\s+(?:mode\s+)?(companion|build|hologram)\s*(?:mode)?/i,
      /(?:mode)\s+(companion|build|hologram)/i,
      /(companion|build|hologram)\s+mode/i,
    ],
    action: 'MODE_SWITCH',
    extract: (msg) => {
      const m = msg.match(/(companion|build|hologram)/i);
      return { mode: m ? m[1].toUpperCase() : '' };
    },
    execute: async (_msg, { mode }) => {
      if (!mode) return { executed: false, action: 'MODE_SWITCH', result: 'Could not determine target mode.' };
      const d = await api('/v1/mode', 'POST', { mode });
      return { executed: true, action: 'MODE_SWITCH', result: d.ok ? `✅ Mode switched to ${mode}` : `❌ Mode switch failed: ${d.detail ?? 'unknown'}`, data: d };
    },
  },

  // ── DEPLOY ─────────────────────────────────────────────────
  {
    patterns: [
      /\b(?:deploy|ship|release|push\s+(?:to\s+)?(?:prod|production|live))\b/i,
      /\b(?:launch|send)\s+(?:a\s+)?deploy/i,
      /\bdo\s+(?:a\s+)?deploy/i,
      /\bdeploy\s+(?:it|now|this|everything)\b/i,
    ],
    action: 'DEPLOY',
    execute: async () => {
      const d = await api('/deploy', 'POST', { target: 'auto' });
      return { executed: true, action: 'DEPLOY', result: d.ok ? `🚀 Deploy dispatched → ${d.mission_id}` : `❌ Deploy failed: ${d.error ?? 'unknown'}`, data: d };
    },
  },

  // ── PINTEREST SYNC ─────────────────────────────────────────
  {
    patterns: [
      /\b(?:sync|fetch|pull|get|link)\s+(?:my\s+)?(?:from\s+)?pinterest\b/i,
      /\bpinterest\s+(?:sync|ideas?|boards?)\b/i,
      /\bget\s+(?:all\s+)?(?:my\s+)?ideas?\s+from\s+pinterest\b/i,
      /\bapply\s+pinterest\s+ideas?\b/i,
      /\blink\s+(?:my\s+)?pinterest\s+to\b/i,
    ],
    action: 'PINTEREST_SYNC',
    execute: async () => {
      const d = await api('/v1/pinterest/sync', 'POST', { board: 'all', auto_apply: true });
      return {
        executed: true,
        action: 'PINTEREST_SYNC',
        result: d.ok
          ? `📌 Synced ${d.pin_count ?? 0} ideas from Pinterest → auto-applying to NEXUSMON`
          : `❌ Pinterest sync failed: ${d.error ?? 'Check API token'}`,
        data: d,
      };
    },
  },

  // ── CHECK STATUS ───────────────────────────────────────────
  {
    patterns: [
      /\b(?:status|what(?:'s| is) (?:the )?(?:status|state|situation))\b/i,
      /\b(?:show|get|check|give)\s+(?:me\s+)?(?:the\s+)?(?:system\s+)?status\b/i,
      /\bhow(?:'s| is) (?:the )?system\b/i,
      /\bsystem\s+(?:check|report|overview)\b/i,
      /\b(?:what(?:'s| is) going on|sitrep|sit\s*rep)\b/i,
    ],
    action: 'STATUS',
    execute: async () => {
      const d = await api('/system/status');
      const e = await api('/evolve');
      const r = `SYSTEM STATUS\n─────────────\nMode: ${d.mode}\nRunner: ${d.runner}\nPhase: ${d.phase}\nQuarantine: ${d.quarantine ? 'ACTIVE ⚠️' : 'CLEAR ✅'}\nSuccess rate: ${((d.success_rate ?? 0) * 100).toFixed(1)}%\nPending: ${d.pending_count}\nEvolution: LV${e.level ?? 0} ${e.name ?? 'EGG'}`;
      return { executed: true, action: 'STATUS', result: r, data: d };
    },
  },

  // ── HEALTH CHECK ───────────────────────────────────────────
  {
    patterns: [
      /\b(?:health|alive|ping|you (?:there|up|online|working))\b/i,
      /\b(?:are you (?:ok|alive|running|working))\b/i,
    ],
    action: 'HEALTH',
    execute: async () => {
      const d = await api('/health');
      return { executed: true, action: 'HEALTH', result: `HEALTH: ${d.status?.toUpperCase() ?? 'UNKNOWN'} ✅`, data: d };
    },
  },

  // ── SHOW MISSIONS ──────────────────────────────────────────
  {
    patterns: [
      /\b(?:show|list|get|what(?:'s| is| are))\s+(?:the\s+)?(?:missions?|tasks?|jobs?)\b/i,
      /\bmissions?\s+(?:list|status|report)\b/i,
      /\b(?:pending|active|recent)\s+(?:missions?|tasks?)\b/i,
    ],
    action: 'MISSIONS',
    execute: async () => {
      const d = await api('/mission');
      const list = (d.missions ?? []).slice(0, 10);
      if (!list.length) return { executed: true, action: 'MISSIONS', result: 'No missions found.' };
      const lines = list.map((m: any) => `${m.status ?? '?'} │ ${m.intent ?? m.goal ?? m.id ?? '?'}`);
      return { executed: true, action: 'MISSIONS', result: 'RECENT MISSIONS\n───────────────\n' + lines.join('\n'), data: d };
    },
  },

  // ── CHECK EVOLUTION ────────────────────────────────────────
  {
    patterns: [
      /\b(?:evolv|evolution|evo|level|xp|experience)\b/i,
      /\bwhat(?:'s| is) (?:my |the )?(?:level|evo|evolution)\b/i,
    ],
    action: 'EVOLVE',
    execute: async () => {
      const d = await api('/evolve');
      return { executed: true, action: 'EVOLVE', result: `EVOLUTION STATE\n──────────────\nLevel: ${d.level}\nName: ${d.name}\nXP: ${d.xp ?? 0}/${d.next_xp ?? '?'}\nLabel: ${d.label ?? ''}`, data: d };
    },
  },

  // ── START RUNNER ───────────────────────────────────────────
  {
    patterns: [
      /\b(?:start|boot|launch|run|fire\s+up|spin\s+up)\s+(?:the\s+)?(?:runner|system|swarm|server|engine)\b/i,
      /\b(?:turn|bring)\s+(?:it\s+)?(?:on|up)\b/i,
    ],
    action: 'START',
    execute: async () => {
      const d = await api('/system/start', 'POST');
      return { executed: true, action: 'START', result: d.ok ? `✅ Runner: ${d.status}` : `❌ Start failed`, data: d };
    },
  },

  // ── STOP RUNNER ────────────────────────────────────────────
  {
    patterns: [
      /\b(?:stop|halt|kill|shutdown|shut\s+down)\s+(?:the\s+)?(?:runner|system|swarm|server|engine)\b/i,
      /\b(?:turn|shut)\s+(?:it\s+)?(?:off|down)\b/i,
    ],
    action: 'STOP',
    execute: async () => {
      const d = await api('/system/stop', 'POST');
      return { executed: true, action: 'STOP', result: d.ok ? `✅ Runner stopping...` : `❌ Stop failed`, data: d };
    },
  },

  // ── RESTART ────────────────────────────────────────────────
  {
    patterns: [
      /\b(?:restart|reboot|reset)\s+(?:the\s+)?(?:runner|system|swarm|server|engine|everything)?\b/i,
    ],
    action: 'RESTART',
    execute: async () => {
      const d = await api('/system/restart', 'POST');
      return { executed: true, action: 'RESTART', result: d.ok ? `🔄 System restarting...` : `❌ Restart failed`, data: d };
    },
  },

  // ── CREATE MISSION ─────────────────────────────────────────
  {
    patterns: [
      /\b(?:create|add|new|make|queue|dispatch)\s+(?:a\s+)?(?:mission|task|job)\b/i,
      /\b(?:run|execute|do)\s+(?:a\s+)?(?:mission|task|smoke\s+test|test)\b/i,
    ],
    action: 'CREATE_MISSION',
    extract: (msg) => {
      // Try to get intent from the message after the keyword
      const m = msg.match(/(?:mission|task|job)\s+(?:for\s+|to\s+|:?\s*)?(.+)/i)
        || msg.match(/(?:run|execute|do)\s+(?:a\s+)?(.+)/i);
      return { intent: m ? m[1].trim() : 'operator-requested task' };
    },
    execute: async (_msg, { intent }) => {
      const d = await api('/mission', 'POST', { intent: intent || 'operator-requested task' });
      return { executed: true, action: 'CREATE_MISSION', result: d.ok ? `📋 Mission created → ${d.mission_id}\nIntent: ${intent}` : `❌ Mission creation failed`, data: d };
    },
  },

  // ══════════════════════════════════════════════════════════
  // ══ COMMAND GRAMMAR v2 — Mission Engine / Vault / Evolve ══
  // ══════════════════════════════════════════════════════════

  // ── RUN MISSION (via engine) ───────────────────────────────
  {
    patterns: [
      /\b(?:run|exec(?:ute)?|launch|fire)\s+mission\s+(.+)/i,
      /\bmission\s+run\s+(.+)/i,
    ],
    action: 'ENGINE_RUN_MISSION',
    extract: (msg) => {
      const m = msg.match(/(?:run|exec(?:ute)?|launch|fire)\s+mission\s+(.+)/i)
        || msg.match(/mission\s+run\s+(.+)/i);
      return { intent: m ? m[1].trim() : 'operator-requested' };
    },
    execute: async (_msg, { intent }) => {
      const d = await api('/v1/engine/mission/run', 'POST', { intent });
      if (!d.ok) return { executed: false, action: 'ENGINE_RUN_MISSION', result: `❌ ${d.detail ?? 'Mission failed'}` };
      return { executed: true, action: 'ENGINE_RUN_MISSION', result: `🚀 Mission ${d.mission_id}\nWorker: ${d.worker_id}\nStatus: ${d.status}\nDuration: ${d.duration_ms}ms`, data: d };
    },
  },

  // ── CHAIN MISSIONS ─────────────────────────────────────────
  {
    patterns: [
      /\bchain\s+missions?\s+(.+)/i,
      /\bpipeline\s+(.+)/i,
      /\brun\s+sequence\s+(.+)/i,
    ],
    action: 'ENGINE_CHAIN',
    extract: (msg) => {
      const m = msg.match(/(?:chain\s+missions?|pipeline|run\s+sequence)\s+(.+)/i);
      const raw = m ? m[1] : '';
      return { steps: raw };
    },
    execute: async (_msg, { steps }) => {
      const stepList = (steps || '').split(/[,;→>]+/).map(s => s.trim()).filter(Boolean);
      if (!stepList.length) return { executed: false, action: 'ENGINE_CHAIN', result: '❌ Provide steps: chain missions A, B, C' };
      const body = stepList.map(s => ({ intent: s }));
      const d = await api('/v1/engine/mission/chain', 'POST', { steps: body });
      if (!d.ok) return { executed: false, action: 'ENGINE_CHAIN', result: `❌ ${d.detail ?? 'Chain failed'}` };
      return { executed: true, action: 'ENGINE_CHAIN', result: `⛓ Chain ${d.chain_id}\nCompleted: ${d.steps_completed}/${d.steps_planned}`, data: d };
    },
  },

  // ── INSPECT ARTIFACT ───────────────────────────────────────
  {
    patterns: [
      /\b(?:inspect|show|view|get)\s+artifact\s+(.+)/i,
      /\bartifact\s+(.+)/i,
    ],
    action: 'ENGINE_INSPECT_ARTIFACT',
    extract: (msg) => {
      const m = msg.match(/(?:inspect|show|view|get)\s+artifact\s+(.+)/i) || msg.match(/artifact\s+(.+)/i);
      return { id: m ? m[1].trim() : 'latest' };
    },
    execute: async (_msg, { id }) => {
      const path = id === 'latest' ? '/v1/engine/artifacts/latest' : `/v1/engine/artifacts/${id}`;
      const d = await api(path);
      if (d.detail) return { executed: false, action: 'ENGINE_INSPECT_ARTIFACT', result: `❌ ${d.detail}` };
      const p = d.payload ? JSON.stringify(d.payload, null, 2).slice(0, 300) : '(empty)';
      return { executed: true, action: 'ENGINE_INSPECT_ARTIFACT', result: `ARTIFACT ${d.id ?? id}\n──────────\nType: ${d.type}\nSource: ${d.source}\nTime: ${d.timestamp}\nPayload:\n${p}`, data: d };
    },
  },

  // ── LIST ARTIFACTS ─────────────────────────────────────────
  {
    patterns: [
      /\b(?:list|show|all)\s+artifacts?\b/i,
      /\bartifacts?\s+(?:list|index|all)\b/i,
    ],
    action: 'ENGINE_LIST_ARTIFACTS',
    execute: async () => {
      const d = await api('/v1/engine/artifacts?limit=10');
      if (!d.ok) return { executed: false, action: 'ENGINE_LIST_ARTIFACTS', result: '❌ Could not list artifacts' };
      if (!d.count) return { executed: true, action: 'ENGINE_LIST_ARTIFACTS', result: 'No artifacts in vault yet.' };
      const lines = (d.artifacts || []).map((a: any) => `${a.type?.padEnd(10)} │ ${a.id?.slice(0,8)}.. │ ${a.source ?? '?'}`);
      return { executed: true, action: 'ENGINE_LIST_ARTIFACTS', result: `ARTIFACT VAULT (${d.count})\n${'─'.repeat(36)}\n${lines.join('\n')}`, data: d };
    },
  },

  // ── DIAGNOSE SYSTEM ────────────────────────────────────────
  {
    patterns: [
      /\b(?:diagnose|diagnostic|diagnosis)\s*(?:system|swarm|everything)?\b/i,
      /\bsystem\s+diagnos(?:e|tic|is)\b/i,
    ],
    action: 'ENGINE_DIAGNOSE',
    execute: async () => {
      const d = await api('/v1/engine/mission/run', 'POST', { intent: 'diagnose system' });
      if (!d.ok) return { executed: false, action: 'ENGINE_DIAGNOSE', result: `❌ Diagnosis failed` };
      const r = d.result || {};
      return { executed: true, action: 'ENGINE_DIAGNOSE', result: `SYSTEM DIAGNOSIS\n────────────────\n${JSON.stringify(r, null, 2).slice(0, 500)}`, data: d };
    },
  },

  // ── SHOW EVOLUTION TREE ────────────────────────────────────
  {
    patterns: [
      /\b(?:show|view|get)\s+(?:the\s+)?evolution\s+tree\b/i,
      /\bevolution\s+tree\b/i,
      /\bevo\s+tree\b/i,
    ],
    action: 'ENGINE_EVO_TREE',
    execute: async () => {
      const d = await api('/v1/engine/evolution/tree');
      if (!d.ok) return { executed: false, action: 'ENGINE_EVO_TREE', result: '❌ Could not load evolution tree' };
      const nodes = (d.nodes || []).map((n: any) => `T${n.tier} │ ${n.id?.padEnd(10)} │ ${n.label}`);
      return { executed: true, action: 'ENGINE_EVO_TREE', result: `EVOLUTION TREE\n──────────────\n${nodes.join('\n')}\n\nEdges: ${(d.edges || []).length}`, data: d };
    },
  },

  // ── PING WORKERS ───────────────────────────────────────────
  {
    patterns: [
      /\b(?:ping|list|show)\s+workers?\b/i,
      /\bworkers?\s+(?:status|list|info)\b/i,
    ],
    action: 'ENGINE_WORKERS',
    execute: async () => {
      const d = await api('/v1/engine/workers');
      if (!d.ok) return { executed: false, action: 'ENGINE_WORKERS', result: '❌ Worker query failed' };
      const lines = (d.workers || []).map((w: any) => `${w.id?.padEnd(18)} │ ${(w.capabilities || []).join(', ')}`);
      return { executed: true, action: 'ENGINE_WORKERS', result: `REGISTERED WORKERS (${d.count})\n${'─'.repeat(40)}\n${lines.join('\n')}`, data: d };
    },
  },

  // ── MISSION STATS ──────────────────────────────────────────
  {
    patterns: [
      /\bmission\s+stats?\b/i,
      /\b(?:show|get)\s+mission\s+(?:stats?|statistics|summary)\b/i,
    ],
    action: 'ENGINE_MISSION_STATS',
    execute: async () => {
      const d = await api('/v1/engine/missions/stats');
      if (!d.ok) return { executed: false, action: 'ENGINE_MISSION_STATS', result: '❌ Could not get stats' };
      return { executed: true, action: 'ENGINE_MISSION_STATS', result: `MISSION STATISTICS\n──────────────────\nTotal: ${d.total}\nCompleted: ${d.completed}\nFailed: ${d.failed}\nSuccess Rate: ${((d.success_rate ?? 0) * 100).toFixed(1)}%`, data: d };
    },
  },

  // ── NAVIGATE ───────────────────────────────────────────────
  {
    patterns: [
      /\b(?:go\s+to|open|show|navigate\s+to|take\s+me\s+to)\s+(?:the\s+)?(?:system\s+)?log\b/i,
    ],
    action: 'NAV_LOG',
    execute: async () => {
      window.location.href = '/system-log';
      return { executed: true, action: 'NAV_LOG', result: '↗ Opening System Log...' };
    },
  },
  {
    patterns: [
      /\b(?:go\s+to|open|show|navigate\s+to|take\s+me\s+to)\s+(?:the\s+)?(?:hologram|holo)\b/i,
    ],
    action: 'NAV_HOLOGRAM',
    execute: async () => {
      window.location.href = '/hologram';
      return { executed: true, action: 'NAV_HOLOGRAM', result: '↗ Opening Hologram...' };
    },
  },
  {
    patterns: [
      /\b(?:go\s+to|open|show|navigate\s+to|take\s+me\s+to)\s+(?:the\s+)?console\b/i,
    ],
    action: 'NAV_CONSOLE',
    execute: async () => {
      window.location.href = '/console';
      return { executed: true, action: 'NAV_CONSOLE', result: '↗ Opening Console...' };
    },
  },
];

/* ─── main detection function ─────────────────────────────────── */
export async function detectAndExecute(message: string): Promise<ActionResult | null> {
  const msg = message.trim();
  if (!msg) return null;

  for (const intent of INTENTS) {
    for (const pattern of intent.patterns) {
      if (pattern.test(msg)) {
        const extracted = intent.extract ? intent.extract(msg) : {};
        try {
          return await intent.execute(msg, extracted);
        } catch (e: any) {
          return {
            executed: false,
            action: intent.action,
            result: `Action "${intent.action}" failed: ${e.message}`,
          };
        }
      }
    }
  }

  return null; // No actionable intent detected — fall through to normal chat
}
