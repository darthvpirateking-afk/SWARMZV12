# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Companion â€” persistent AI companion session ("MASTER SWARMZ").

Manages:
- companion_memory.json (summary, preferences, mission outcomes, constraints)
- AI-powered replies via model_router (falls back to rule engine when offline)
- Memory compaction to keep token count low

Policy: prepare_only â€” the companion never executes; only plans/proposes.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "runtime.json"
DATA_DIR = ROOT / "data"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
PROMPT_DIR = Path(__file__).resolve().parent / "prompt_templates"

# import sibling
from core.model_router import call as model_call, is_offline, record_call, get_model_config

# lazy write_jsonl import
try:
    import sys
    sys.path.insert(0, str(ROOT))
    from jsonl_utils import write_jsonl
except ImportError:
    def write_jsonl(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")


# â”€â”€ Config helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _companion_config() -> Dict[str, Any]:
    return _load_config().get("companion", {})


# â”€â”€ Memory file â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _memory_path() -> Path:
    cfg = _companion_config()
    rel = cfg.get("memoryFile", "data/companion_memory.json")
    return ROOT / rel


def load_memory() -> Dict[str, Any]:
    """Load companion memory from disk. Create default if missing."""
    p = _memory_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    default = {
        "sessionId": _companion_config().get("sessionId", "main_companion"),
        "summary": "No interactions yet.",
        "preferences": {},
        "mission_outcomes": [],
        "learned_constraints": [],
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
    }
    save_memory(default)
    return default


def save_memory(mem: Dict[str, Any]) -> None:
    """Persist companion memory to disk."""
    p = _memory_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    mem["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    p.write_text(json.dumps(mem, indent=2), encoding="utf-8")


# â”€â”€ Memory compaction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

MAX_OUTCOMES = 50


def record_mission_outcome(mission_id: str, intent: str, status: str, summary: str = "") -> None:
    """Append a mission outcome to companion memory (capped at MAX_OUTCOMES)."""
    mem = load_memory()
    outcomes = mem.get("mission_outcomes", [])
    outcomes.append({
        "mission_id": mission_id,
        "intent": intent,
        "status": status,
        "summary": summary[:200],
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    })
    # prune oldest if over limit
    if len(outcomes) > MAX_OUTCOMES:
        outcomes = outcomes[-MAX_OUTCOMES:]
    mem["mission_outcomes"] = outcomes
    mem["version"] = mem.get("version", 0) + 1
    save_memory(mem)


def update_summary(new_summary: str) -> None:
    """Replace the companion summary (e.g. after an AI-generated compaction)."""
    mem = load_memory()
    mem["summary"] = new_summary[:2000]
    mem["version"] = mem.get("version", 0) + 1
    save_memory(mem)


# â”€â”€ System prompt builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _load_system_prompt() -> str:
    p = PROMPT_DIR / "companion_system.txt"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "You are MASTER SWARMZ, the AI companion. Policy: prepare_only."


def _build_context_block(mem: Dict[str, Any]) -> str:
    """Build a short context block from memory for the system prompt."""
    parts = []
    parts.append(f"SESSION: {mem.get('sessionId', '?')}")
    parts.append(f"SUMMARY: {mem.get('summary', 'none')}")
    outcomes = mem.get("mission_outcomes", [])
    if outcomes:
        recent = outcomes[-5:]
        lines = [f"  - {o.get('intent','?')} â†’ {o.get('status','?')}" for o in recent]
        parts.append("RECENT OUTCOMES:\n" + "\n".join(lines))
    constraints = mem.get("learned_constraints", [])
    if constraints:
        parts.append("CONSTRAINTS: " + "; ".join(constraints[-10:]))
    return "\n".join(parts)


# â”€â”€ Main chat function â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def chat(user_text: str) -> Dict[str, Any]:
    """
    Send a message to the companion and get a reply.

    If online + API key set: uses model_router.
    Otherwise: falls back to deterministic rule engine.

    Returns: {"ok": bool, "reply": str, "source": "ai"|"rule_engine"|"offline",
              "provider"?: str, "model"?: str, "latencyMs"?: int}
    """
    now = datetime.utcnow().isoformat() + "Z"
    mem = load_memory()

    # â”€â”€ Offline / no-key fallback â”€â”€
    if is_offline():
        reply = _rule_engine(user_text, mem)
        _audit_companion(now, user_text, reply, "offline")
        return {"ok": True, "reply": reply, "source": "offline"}

    cfg = get_model_config()
    prov = cfg.get("provider", "anthropic")
    prov_cfg = cfg.get(prov, {})
    key_env = prov_cfg.get("apiKeyEnv", "")
    has_key = bool(os.environ.get(key_env)) if key_env else False

    if not has_key:
        reply = _rule_engine(user_text, mem)
        _audit_companion(now, user_text, reply, "rule_engine")
        return {"ok": True, "reply": reply, "source": "rule_engine"}

    # â”€â”€ AI call â”€â”€
    system = _load_system_prompt() + "\n\n--- CONTEXT ---\n" + _build_context_block(mem)
    messages = [{"role": "user", "content": user_text}]

    result = model_call(messages, system=system)
    record_call(now, result.get("error"))

    # audit the model call
    _audit_model_call(now, result)

    if result.get("ok"):
        reply_text = result.get("text", "(empty)")
        _audit_companion(now, user_text, reply_text, "ai")
        return {
            "ok": True,
            "reply": reply_text,
            "source": "ai",
            "provider": result.get("provider"),
            "model": result.get("model"),
            "latencyMs": result.get("latencyMs"),
        }
    else:
        # AI failed â€” fall back to rule engine
        reply = _rule_engine(user_text, mem) + "\n[AI unavailable: " + (result.get("error", "?"))[:100] + "]"
        _audit_companion(now, user_text, reply, "rule_engine_fallback")
        return {"ok": True, "reply": reply, "source": "rule_engine_fallback"}


# â”€â”€ Rule engine (deterministic fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _rule_engine(text: str, mem: Dict[str, Any]) -> str:
    """Simple keyword-based replies when AI is not available."""
    lower = text.lower().strip()
    if "status" in lower:
        outcomes = mem.get("mission_outcomes", [])
        if not outcomes:
            return "NO MISSION OUTCOMES RECORDED YET"
        recent = outcomes[-5:]
        lines = [f"{o.get('intent','?')} â†’ {o.get('status','?')}" for o in recent]
        return "RECENT OUTCOMES:\n" + "\n".join(lines)
    if "help" in lower:
        return "COMMANDS: status | help | mode | missions | memory"
    if "memory" in lower:
        return f"SUMMARY: {mem.get('summary', 'none')}\nOUTCOMES: {len(mem.get('mission_outcomes', []))}\nCONSTRAINTS: {len(mem.get('learned_constraints', []))}"
    if "mode" in lower:
        return "Use the mode tabs in the HUD to switch COMPANION / BUILD."
    if "mission" in lower:
        outcomes = mem.get("mission_outcomes", [])
        return f"TRACKED OUTCOMES: {len(outcomes)}"
    return "ACKNOWLEDGED: " + text[:120]


# â”€â”€ Audit helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _audit_companion(timestamp: str, user_text: str, reply: str, source: str) -> None:
    text_hash = hashlib.sha256(user_text.encode("utf-8")).hexdigest()[:16]
    write_jsonl(AUDIT_FILE, {
        "timestamp": timestamp,
        "event": "companion_message",
        "source": source,
        "text_sha256": text_hash,
        "reply_len": len(reply),
    })


def _audit_model_call(timestamp: str, result: Dict[str, Any]) -> None:
    entry = {
        "timestamp": timestamp,
        "event": "model_call",
        "provider": result.get("provider", ""),
        "model": result.get("model", ""),
        "latencyMs": result.get("latencyMs", 0),
        "ok": result.get("ok", False),
    }
    usage = result.get("usage", {})
    if usage:
        entry["input_tokens"] = usage.get("input_tokens", usage.get("prompt_tokens", 0))
        entry["output_tokens"] = usage.get("output_tokens", usage.get("completion_tokens", 0))
    if result.get("error"):
        entry["error"] = str(result["error"])[:200]
    write_jsonl(AUDIT_FILE, entry)

