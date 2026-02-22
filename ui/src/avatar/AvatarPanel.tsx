import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Avatar from './Avatar';
import CockpitBackground from './CockpitBackground';
import SwarmBurst from './SwarmBurst';
import MatrixText from './MatrixText';
import { detectAndExecute } from './ActionEngine';
import { defaultAvatarState, AvatarState, AvatarRealm } from './AvatarState';
import ArtifactOrb from './ArtifactOrb';
import type { ArtifactData } from './ArtifactOrb';

/* ─── types ─────────────────────────────────────────────────────── */
type ChatEntry = {
  id: number;
  type: 'user' | 'swarmz' | 'error' | 'system';
  message: string;
  personality_active?: boolean;
  presence_style?: any;
  timestamp: number;
  typed?: boolean;
};

type SystemInfo = {
  mode: string;
  runner: string;
  quarantine: boolean;
  success_rate: number;
  pending: number;
  evolve_level: number;
  evolve_name: string;
};

/* ─── quick-command palette ─────────────────────────────────────── */
const QUICK_CMDS = [
  { label: '⚡ STATUS',   cmd: '/status' },
  { label: '🔄 MODE',     cmd: '/mode' },
  { label: '🚀 DEPLOY',   cmd: '/deploy' },
  { label: '🧬 EVOLVE',   cmd: '/evolve' },
  { label: '📋 MISSIONS', cmd: '/missions' },
  { label: '🛡️ HEALTH',   cmd: '/health' },
] as const;

let _entryId = 0;

/* ─── component ─────────────────────────────────────────────────── */
const AvatarPanel: React.FC = () => {
  const [state, setState] = useState<AvatarState>(defaultAvatarState);
  const [chatLog, setChatLog] = useState<ChatEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [avatarData, setAvatarData] = useState<any>(null);
  const [presenceData, setPresenceData] = useState<any>(null);
  const [displayName, setDisplayName] = useState('NEXUSMON');
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameInputValue, setNameInputValue] = useState('');
  const [realm, setRealm] = useState<AvatarRealm>('cosmos');
  const [burstTrigger, setBurstTrigger] = useState(0);
  const [sysInfo, setSysInfo] = useState<SystemInfo | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [pendingArtifacts, setPendingArtifacts] = useState<ArtifactData[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* ── auto-scroll chat ───────────────────────────────────────── */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog, isTyping]);

  /* ── load avatar + presence + system info ───────────────────── */
  useEffect(() => {
    fetch('/ui/api/companion/avatar')
      .then(r => r.json())
      .then(data => {
        setAvatarData(data);
        if (data.display_name) { setDisplayName(data.display_name); setNameInputValue(data.display_name); }
        if (data.presence_style) setPresenceData({ context: data.presence_context, style: data.presence_style, constraints: data.constraints });
        if (data.realm) setRealm(data.realm as AvatarRealm);
      })
      .catch(() => {});

    fetch('/ui/api/companion/presence').then(r => r.json()).then(d => { if (d.ok) setPresenceData(d); }).catch(() => {});

    refreshSysInfo();
    const poll = setInterval(refreshSysInfo, 12000);
    return () => clearInterval(poll);
  }, []);

  const refreshSysInfo = useCallback(async () => {
    try {
      const [statusRes, evolveRes] = await Promise.all([
        fetch('/system/status').then(r => r.json()),
        fetch('/evolve').then(r => r.json()),
      ]);
      setSysInfo({
        mode: statusRes.mode ?? 'UNKNOWN',
        runner: statusRes.runner ?? 'down',
        quarantine: statusRes.quarantine ?? false,
        success_rate: statusRes.success_rate ?? 0,
        pending: statusRes.pending_count ?? 0,
        evolve_level: evolveRes.level ?? 0,
        evolve_name: evolveRes.name ?? 'EGG',
      });
    } catch { /* offline */ }
  }, []);

  /* ── handle slash commands locally ─────────────────────────── */
  const handleSlashCommand = async (cmd: string): Promise<string | null> => {
    const c = cmd.toLowerCase().trim();
    try {
      if (c === '/status') {
        const d = await fetch('/system/status').then(r => r.json());
        await refreshSysInfo();
        return `SYSTEM STATUS\n─────────────\nMode: ${d.mode}\nRunner: ${d.runner}\nPhase: ${d.phase}\nQuarantine: ${d.quarantine ? 'ACTIVE ⚠️' : 'CLEAR ✅'}\nSuccess rate: ${(d.success_rate * 100).toFixed(1)}%\nPending: ${d.pending_count}`;
      }
      if (c === '/health') {
        const d = await fetch('/health').then(r => r.json());
        return `HEALTH: ${d.status?.toUpperCase() ?? 'UNKNOWN'}`;
      }
      if (c === '/mode') {
        const d = await fetch('/v1/mode').then(r => r.json());
        return `Current mode: ${d.mode}\n\nTo switch: type /mode COMPANION, /mode BUILD, or /mode HOLOGRAM`;
      }
      if (c.startsWith('/mode ')) {
        const newMode = c.split(' ')[1]?.toUpperCase();
        if (!['COMPANION','BUILD','HOLOGRAM'].includes(newMode)) return `Invalid mode: ${newMode}. Use COMPANION, BUILD, or HOLOGRAM.`;
        const d = await fetch('/v1/mode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: newMode }) }).then(r => r.json());
        await refreshSysInfo();
        const realmMap: Record<string, AvatarRealm> = { COMPANION: 'cosmos', BUILD: 'forge', HOLOGRAM: 'void' };
        setRealm(realmMap[newMode] ?? 'core');
        return d.ok ? `Mode switched to ${newMode} ✅` : `Mode switch failed: ${d.detail ?? 'unknown error'}`;
      }
      if (c === '/deploy') {
        const d = await fetch('/deploy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: 'auto' }) }).then(r => r.json());
        return d.ok ? `Deploy mission dispatched → ${d.mission_id}` : `Deploy failed: ${d.error ?? 'unknown'}`;
      }
      if (c === '/evolve') {
        const d = await fetch('/evolve').then(r => r.json());
        await refreshSysInfo();
        return `EVOLUTION STATE\n──────────────\nLevel: ${d.level}\nName: ${d.name}\nXP: ${d.xp ?? 0}/${d.next_xp ?? '?'}\nLabel: ${d.label ?? ''}`;
      }
      if (c === '/missions') {
        const d = await fetch('/mission').then(r => r.json());
        const list = (d.missions ?? []).slice(0, 8);
        if (!list.length) return 'No missions found.';
        return 'RECENT MISSIONS\n───────────────\n' + list.map((m: any) => `${m.status ?? '?'} │ ${m.intent ?? m.goal ?? m.id ?? '?'}`).join('\n');
      }
    } catch (e: any) {
      return `Command error: ${e.message}`;
    }
    return null;
  };

  /* ── send a message ────────────────────────────────────────── */
  const sendMessage = async (message: string) => {
    if (!message.trim()) return;
    const userEntry: ChatEntry = { id: ++_entryId, type: 'user', message, timestamp: Date.now(), typed: true };
    setChatLog(prev => [...prev, userEntry]);
    setInputValue('');
    setBurstTrigger(t => t + 1);
    setState(prev => ({ ...prev, mode: 'listening', status: 'processing' }));

    // Slash commands
    if (message.startsWith('/')) {
      const result = await handleSlashCommand(message);
      if (result !== null) {
        setChatLog(prev => [...prev, { id: ++_entryId, type: 'system', message: result, timestamp: Date.now(), typed: false }]);
        setState(prev => ({ ...prev, mode: 'reporting', status: 'online' }));
        setIsTyping(true);
        return;
      }
    }

    // Smart intent detection — actually EXECUTE what operator asks
    const actionResult = await detectAndExecute(message);
    if (actionResult) {
      setChatLog(prev => [...prev, {
        id: ++_entryId,
        type: 'system',
        message: `⚡ ACTION: ${actionResult.action}\n${actionResult.result}`,
        timestamp: Date.now(),
        typed: false,
      }]);
      setState(prev => ({ ...prev, mode: 'reporting', status: 'online', expression: 'focused' }));
      setIsTyping(true);
      // Refresh system info after any action
      await refreshSysInfo();
      // Update realm if mode changed
      if (actionResult.action === 'MODE_SWITCH' && actionResult.data?.ok) {
        const realmMap: Record<string, AvatarRealm> = { COMPANION: 'cosmos', BUILD: 'forge', HOLOGRAM: 'void' };
        const newMode = actionResult.data.mode ?? '';
        if (realmMap[newMode]) setRealm(realmMap[newMode]);
      }
      // Capture produced artifacts for display
      if (actionResult.data?.artifact_id) {
        try {
          const artRes = await fetch(`/v1/engine/artifacts/${actionResult.data.artifact_id}`);
          const artJson = await artRes.json();
          if (artJson.ok && artJson.artifact) {
            const newArtifact: ArtifactData = {
              id: artJson.artifact.id,
              type: artJson.artifact.type || 'mission',
              source: artJson.artifact.source || 'nexusmon',
              timestamp: artJson.artifact.timestamp || new Date().toISOString(),
              payload: artJson.artifact.payload,
              mission_id: actionResult.data.mission_id,
              worker_id: actionResult.data.worker_id,
              status: actionResult.data.status,
              intent: actionResult.data.intent,
              duration_ms: actionResult.data.duration_ms,
            };
            setPendingArtifacts(prev => [...prev, newArtifact]);
          }
        } catch { /* artifact fetch failed silently */ }
      }
      return;
    }

    // Normal chat (no actionable intent detected)
    try {
      const response = await fetch('/ui/api/companion/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await response.json();
      setChatLog(prev => [...prev, {
        id: ++_entryId,
        type: 'swarmz',
        message: data.reply || 'Processing...',
        personality_active: data.personality_active,
        presence_style: data.presence_style,
        timestamp: Date.now(),
        typed: false,
      }]);
      setState(prev => ({ ...prev, mode: 'reporting', status: 'online', expression: 'focused', realm }));
      setIsTyping(true);
      if (data.presence_style) setPresenceData({ context: data.presence_context, style: data.presence_style, constraints: data.constraints });
    } catch {
      setChatLog(prev => [...prev, { id: ++_entryId, type: 'error', message: 'Connection lost — enhanced systems offline', timestamp: Date.now(), typed: true }]);
      setState(prev => ({ ...prev, status: 'awaiting_input', mode: 'idle', expression: 'analytical' }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendMessage(inputValue);
  };

  const commitRename = async (newName: string) => {
    const trimmed = newName.trim();
    if (!trimmed) { setIsEditingName(false); return; }
    setDisplayName(trimmed);
    setIsEditingName(false);
    try {
      await fetch('/ui/api/companion/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: trimmed }) });
    } catch { /* persist locally */ }
  };

  /* ── artifact absorb handlers ────────────────────────────── */
  const handleAbsorb = useCallback((artifact: ArtifactData) => {
    setPendingArtifacts(prev => prev.filter(a => a.id !== artifact.id));
    setBurstTrigger(t => t + 1);
    const digest = typeof artifact.payload === 'string'
      ? artifact.payload.slice(0, 150)
      : JSON.stringify(artifact.payload).slice(0, 150);
    setChatLog(prev => [...prev, {
      id: ++_entryId,
      type: 'system',
      message: `◈ ABSORBED [${artifact.type.toUpperCase()}]\n${digest}${digest.length >= 150 ? '...' : ''}`,
      timestamp: Date.now(),
      typed: false,
    }]);
  }, []);

  const handleDismissArtifact = useCallback((id: string) => {
    setPendingArtifacts(prev => prev.filter(a => a.id !== id));
  }, []);

  /* ── realm color helpers ───────────────────────────────────── */
  const realmAccent = realm === 'cosmos' ? '#00d4ff' : realm === 'forge' ? '#ff8c50' : realm === 'void' ? '#b050ff' : '#ffffff';
  const realmAccentDim = realm === 'cosmos' ? '#004466' : realm === 'forge' ? '#4a2810' : realm === 'void' ? '#2a1040' : '#333333';

  /* ─── render ───────────────────────────────────────────────── */
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      style={{
        border: `1px solid ${realmAccentDim}`,
        borderRadius: '16px',
        color: realmAccent,
        width: '100%',
        minHeight: '82vh',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: `0 0 40px ${realmAccentDim}, inset 0 0 60px rgba(0,0,0,0.5)`,
      }}
    >
      <CockpitBackground realm={realm} processing={state.status === 'processing'}>
        {/* ── SYSTEM STATUS BAR ──────────────────────────────── */}
        {sysInfo && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: '16px', padding: '8px 16px',
              borderBottom: `1px solid ${realmAccentDim}`,
              background: 'rgba(0,0,0,0.4)',
              backdropFilter: 'blur(8px)',
              fontSize: 11, fontFamily: "'Courier New', monospace",
              letterSpacing: '0.5px', flexWrap: 'wrap',
            }}
          >
            <StatusPip label="MODE" value={sysInfo.mode} color={sysInfo.mode === 'BUILD' ? '#ffaa00' : sysInfo.mode === 'HOLOGRAM' ? '#b050ff' : '#00d4ff'} />
            <StatusPip label="RUNNER" value={sysInfo.runner.toUpperCase()} color={sysInfo.runner === 'up' ? '#00ff88' : '#ff4444'} />
            <StatusPip label="QUARANTINE" value={sysInfo.quarantine ? 'ACTIVE' : 'CLEAR'} color={sysInfo.quarantine ? '#ff6600' : '#00ff88'} />
            <StatusPip label="RATE" value={`${(sysInfo.success_rate * 100).toFixed(0)}%`} color={sysInfo.success_rate >= 0.7 ? '#00ff88' : '#ff6600'} />
            <StatusPip label="PENDING" value={String(sysInfo.pending)} color="#6688aa" />
            <StatusPip label="EVO" value={`LV${sysInfo.evolve_level} ${sysInfo.evolve_name}`} color="#b050ff" />
          </motion.div>
        )}

        {/* ── AVATAR HERO SECTION ────────────────────────────── */}
        <div style={{ textAlign: 'center', padding: '20px 16px 8px', position: 'relative', zIndex: 2 }}>
          {/* Name */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '12px' }}>
            {isEditingName ? (
              <input
                autoFocus
                value={nameInputValue}
                onChange={e => setNameInputValue(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') commitRename(nameInputValue); if (e.key === 'Escape') setIsEditingName(false); }}
                onBlur={() => commitRename(nameInputValue)}
                style={{
                  fontSize: '16px', fontWeight: 700, color: realmAccent,
                  background: 'rgba(0,0,0,0.6)', border: `1px solid ${realmAccent}`,
                  borderRadius: '8px', padding: '6px 14px', textAlign: 'center', width: '260px',
                  fontFamily: "'Courier New', monospace",
                }}
              />
            ) : (
              <motion.h2
                whileHover={{ scale: 1.03, textShadow: `0 0 20px ${realmAccent}` }}
                style={{
                  color: realmAccent, cursor: 'pointer',
                  fontFamily: "'Courier New', monospace",
                  fontSize: '16px', fontWeight: 700,
                  letterSpacing: '3px', textTransform: 'uppercase',
                  textShadow: `0 0 12px ${realmAccentDim}`,
                  margin: 0,
                }}
                title="Click to rename"
                onClick={() => { setNameInputValue(displayName); setIsEditingName(true); }}
              >
                ◈ {displayName}
              </motion.h2>
            )}
          </div>

          {/* Avatar orb */}
          <motion.div
            style={{ position: 'relative', display: 'inline-block' }}
            animate={state.status === 'processing' ? { scale: [1, 1.03, 1] } : {}}
            transition={state.status === 'processing' ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } : {}}
          >
            <Avatar state={{ ...state, realm }} />
            <SwarmBurst trigger={burstTrigger} realm={realm} />
          </motion.div>

          {/* Subtext */}
          {avatarData && (
            <div style={{
              fontSize: '10px', color: '#556677', marginTop: '8px',
              fontFamily: "'Courier New', monospace", letterSpacing: '1px',
            }}>
              {avatarData.appearance?.form && <span>FORM: {avatarData.appearance.form.toUpperCase()}</span>}
              {' │ '}
              <span style={{ color: state.status === 'processing' ? realmAccent : '#556677' }}>
                {state.status.toUpperCase()}
              </span>
              {presenceData?.style && (
                <>
                  {' │ '}<span>TONE: {presenceData.style.tone}</span>
                  {' │ '}<span>I: {presenceData.style.intensity}</span>
                </>
              )}
            </div>
          )}

          {/* ── PENDING ARTIFACTS ─────────────────────────────── */}
          <AnimatePresence>
            {pendingArtifacts.map((art) => (
              <ArtifactOrb
                key={art.id}
                artifact={art}
                accentColor={realmAccent}
                onAbsorb={handleAbsorb}
                onDismiss={() => handleDismissArtifact(art.id)}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* ── QUICK COMMANDS ─────────────────────────────────── */}
        <div style={{
          display: 'flex', gap: '6px', justifyContent: 'center', padding: '6px 16px',
          flexWrap: 'wrap', position: 'relative', zIndex: 2,
        }}>
          {QUICK_CMDS.map(qc => (
            <motion.button
              key={qc.cmd}
              whileHover={{ scale: 1.06, borderColor: realmAccent }}
              whileTap={{ scale: 0.95 }}
              onClick={() => sendMessage(qc.cmd)}
              style={{
                padding: '4px 10px', borderRadius: '6px', fontSize: '10px',
                border: `1px solid ${realmAccentDim}`,
                background: 'rgba(0,0,0,0.4)', color: '#6688aa',
                cursor: 'pointer', fontFamily: "'Courier New', monospace",
                letterSpacing: '0.5px', transition: 'color 0.2s',
              }}
            >
              {qc.label}
            </motion.button>
          ))}
        </div>

        {/* ── CHAT LOG ───────────────────────────────────────── */}
        <div style={{
          height: '34vh',
          overflowY: 'auto',
          border: `1px solid ${realmAccentDim}`,
          padding: '14px',
          margin: '10px 16px',
          background: 'rgba(2, 4, 8, 0.8)',
          borderRadius: '12px',
          position: 'relative',
          zIndex: 2,
          scrollbarWidth: 'thin' as const,
          scrollbarColor: `${realmAccentDim} transparent`,
        }}>
          {chatLog.length === 0 && (
            <div style={{
              color: '#334455', fontStyle: 'italic', textAlign: 'center', paddingTop: '40px',
              fontFamily: "'Courier New', monospace", fontSize: '12px',
            }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', opacity: 0.3 }}>◈</div>
              Awaiting operator input...<br />
              <span style={{ fontSize: '10px', color: '#223344' }}>
                Just tell me what to do — "check status", "deploy", "switch to build mode", "show missions"
              </span>
            </div>
          )}

          <AnimatePresence>
            {chatLog.map((entry) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: entry.type === 'user' ? 20 : -20, y: 8 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                style={{
                  marginBottom: '10px',
                  display: 'flex',
                  justifyContent: entry.type === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div style={{
                  maxWidth: '78%',
                  padding: '10px 14px',
                  borderRadius: entry.type === 'user'
                    ? '14px 14px 4px 14px'
                    : '14px 14px 14px 4px',
                  border: `1px solid ${
                    entry.type === 'user' ? '#0a3050'
                    : entry.type === 'error' ? '#4a1515'
                    : entry.type === 'system' ? realmAccentDim
                    : '#0a2a20'
                  }`,
                  background:
                    entry.type === 'user'
                      ? 'linear-gradient(145deg, rgba(10,40,70,0.8), rgba(8,30,50,0.9))'
                      : entry.type === 'error'
                        ? 'linear-gradient(145deg, rgba(60,15,15,0.8), rgba(40,8,8,0.9))'
                        : entry.type === 'system'
                          ? 'linear-gradient(145deg, rgba(10,15,30,0.8), rgba(5,10,20,0.9))'
                          : 'linear-gradient(145deg, rgba(8,30,22,0.8), rgba(5,20,15,0.9))',
                  fontFamily: "'Courier New', monospace",
                  fontSize: '12px',
                  lineHeight: 1.5,
                }}>
                  <div style={{
                    fontSize: '9px', fontWeight: 700, letterSpacing: '1.5px',
                    marginBottom: '4px', textTransform: 'uppercase' as const,
                    color: entry.type === 'user' ? '#3388bb' : entry.type === 'error' ? '#ff4444' : entry.type === 'system' ? realmAccent : '#44aa77',
                  }}>
                    {entry.type === 'user' ? '◇ OPERATOR' :
                     entry.type === 'error' ? '⚠ ERROR' :
                     entry.type === 'system' ? '◈ SYSTEM' :
                     `◈ NEXUSMON`}
                  </div>
                  <div style={{ color: '#c8d8e8', whiteSpace: 'pre-wrap' }}>
                    {(entry.type === 'swarmz' || entry.type === 'system') && !entry.typed ? (
                      <MatrixText
                        text={entry.message}
                        speed={entry.type === 'system' ? 12 : 28}
                        cursorColor={entry.type === 'system' ? realmAccent : '#00ff88'}
                        onComplete={() => {
                          setChatLog(prev => prev.map(e => e.id === entry.id ? { ...e, typed: true } : e));
                          setIsTyping(false);
                        }}
                      />
                    ) : (
                      entry.message
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>

        {/* ── INPUT BAR ──────────────────────────────────────── */}
        <div style={{
          display: 'flex', gap: '10px', justifyContent: 'center', alignItems: 'center',
          position: 'relative', zIndex: 2, padding: '0 16px 16px',
        }}>
          <motion.input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isTyping ? 'NEXUSMON is processing...' : 'Tell NEXUSMON what to do... (e.g. "deploy", "sync pinterest")'}
            disabled={isTyping}
            whileFocus={{ borderColor: realmAccent, boxShadow: `0 0 16px ${realmAccentDim}` }}
            style={{
              flex: 1,
              maxWidth: '720px',
              padding: '12px 16px',
              borderRadius: '10px',
              border: `1px solid ${realmAccentDim}`,
              background: 'rgba(4, 8, 16, 0.9)',
              color: realmAccent,
              fontFamily: "'Courier New', monospace",
              fontSize: '13px',
              letterSpacing: '0.5px',
              outline: 'none',
              transition: 'border-color 0.3s, box-shadow 0.3s',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: `0 0 20px ${realmAccentDim}` }}
            whileTap={{ scale: 0.95 }}
            onClick={() => sendMessage(inputValue)}
            disabled={isTyping || !inputValue.trim()}
            style={{
              padding: '12px 24px',
              borderRadius: '10px',
              border: `1px solid ${realmAccent}`,
              background: `linear-gradient(145deg, ${realmAccentDim}, rgba(0,0,0,0.6))`,
              color: realmAccent,
              cursor: isTyping ? 'not-allowed' : 'pointer',
              fontFamily: "'Courier New', monospace",
              fontWeight: 700,
              fontSize: '12px',
              letterSpacing: '2px',
              opacity: isTyping || !inputValue.trim() ? 0.4 : 1,
              transition: 'opacity 0.2s',
            }}
          >
            EXECUTE ⟩
          </motion.button>
        </div>
      </CockpitBackground>
    </motion.div>
  );
};

/* ─── StatusPip micro-component ─────────────────────────────────── */
const StatusPip: React.FC<{ label: string; value: string; color: string }> = ({ label, value, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
    <span style={{ color: '#445566', fontSize: '9px', letterSpacing: '1px' }}>{label}</span>
    <span style={{
      color,
      fontSize: '10px',
      fontWeight: 700,
      padding: '1px 6px',
      borderRadius: '4px',
      background: 'rgba(0,0,0,0.3)',
      border: `1px solid ${color}22`,
    }}>{value}</span>
  </div>
);

export default AvatarPanel;