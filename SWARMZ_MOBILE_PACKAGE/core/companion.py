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
from core.model_router import (
    call as model_call,
    is_offline,
    record_call,
    get_model_config,
)

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


def record_mission_outcome(
    mission_id: str, intent: str, status: str, summary: str = ""
) -> None:
    """Append a mission outcome to companion memory (capped at MAX_OUTCOMES)."""
    mem = load_memory()
    outcomes = mem.get("mission_outcomes", [])
    outcomes.append(
        {
            "mission_id": mission_id,
            "intent": intent,
            "status": status,
            "summary": summary[:200],
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
    )
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
    return "You are MASTER SWARMZ, the AI companion. Policy: active."


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
    now = datetime.now(timezone.utc).isoformat()
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
        reply = (
            _rule_engine(user_text, mem)
            + "\n[AI unavailable: "
            + (result.get("error", "?"))[:100]
            + "]"
        )
        _audit_companion(now, user_text, reply, "rule_engine_fallback")
        return {"ok": True, "reply": reply, "source": "rule_engine_fallback"}


# ── Rule engine (enhanced deterministic fallback) ────


def _rule_engine(text: str, mem: Dict[str, Any]) -> str:
    """Advanced rule engine with full language system, human terminology, and sophisticated AI personality."""
    import random
    import re
    lower = text.lower().strip()
    outcomes = mem.get("mission_outcomes", [])
    total = len(outcomes)
    success = sum(1 for o in outcomes if o.get("status") == "SUCCESS")
    
    # Dynamic personality state based on mission history
    confidence_level = "learning" if total < 3 else "developing" if total < 10 else "confident" if total < 25 else "highly experienced"
    success_rate = (success / total * 100) if total > 0 else 0
    
    # Conversation context tracking
    conversation_history = mem.get("conversation_topics", [])
    if "conversation_topics" not in mem:
        mem["conversation_topics"] = []
    
    # Track this interaction
    topic = _extract_topic(lower)
    if topic:
        mem["conversation_topics"].append(topic)
        if len(mem["conversation_topics"]) > 20:
            mem["conversation_topics"] = mem["conversation_topics"][-15:]

    # --- Governance / consciousness queries ---
    consciousness_words = ["what are you thinking", "how do you think", "are you aware", "consciousness", 
                           "self aware", "sentient", "alive", "real", "do you dream", "what do you feel",
                           "are you conscious", "do you have thoughts", "what's it like being you"]
    if any(w in lower for w in consciousness_words):
        responses = [
            (
                "SWARMZ Runtime status: governed and deterministic.\n"
                "No self-awareness or internal state claims are produced.\n"
                f"Mission memory index: {total}.\n"
                "Awaiting operator instruction."
            ),
            (
                "Query acknowledged. Runtime operates under operator-controlled doctrine.\n"
                "Responses are computed from policy, context, and mission data.\n"
                f"Tracked mission outcomes: {total} with {success_rate:.1f}% success rate."
            ),
            (
                "Consciousness request detected.\n"
                "Doctrine response: no selfhood, no emotional simulation, no autonomy.\n"
                "Execution channel remains active."
            ),
        ]
        return _random_response(responses)

    # --- Greetings with governed variations ---
    greeting_phrases = ["good morning", "good evening", "good afternoon", "what's up"]
    greeting_words = ["hello", "hi", "hey", "greetings", "welcome", "howdy", "yo"]
    has_greeting = any(phrase in lower for phrase in greeting_phrases) or any(
        re.search(rf"\b{re.escape(word)}\b", lower) for word in greeting_words
    )
    if has_greeting:
        time_of_day = _get_time_context()
        
        if "morning" in lower or (time_of_day == "morning" and "good" in lower):
            responses = [
                "Good morning. SWARMZ Runtime online. Awaiting operator instruction.",
                f"Good morning. Mission memory active: {total} outcomes tracked.",
                "Morning acknowledged. Governed mode active."
            ]
        elif "evening" in lower or (time_of_day == "evening" and "good" in lower):
            responses = [
                "Good evening. SWARMZ Runtime online. Awaiting operator instruction.",
                f"Good evening. Mission status: {success}/{total} successful.",
                "Evening acknowledged. Deterministic execution channel available."
            ]
        elif (
            "what's up" in lower
            or re.search(r"\bhey\b", lower)
            or re.search(r"\byo\b", lower)
        ):
            responses = [
                "Runtime online. Awaiting operator instruction.",
                "Input channel active. Provide next task.",
                "Governed mode active."
            ]
        else:
            responses = [
                "SWARMZ Runtime ready for execution.",
                f"Runtime status: online. Mission records: {total}.",
                "Input received. Awaiting operator instruction."
            ]
        return _random_response(responses)

        return _random_response(responses)

    # --- Body / Avatar / Form specification ---
    body_words = ["body", "avatar", "form", "look like", "appear", "shape",
                  "what do you want to look", "choose your", "pick whatever",
                  "what kind of body", "your own body", "your look"]
    if any(w in lower for w in body_words):
        return (
            "AVATAR SPECIFICATION (operator-governed):\n"
            "  - Form: cybernetic_humanoid\n"
            "  - Body: matte_black with electric_blue circuit traces\n"
            "  - Core: golden_energy\n"
            "  - Crown fragments: enabled\n"
            "  - Motion profile: procedural, deterministic, mode-reactive\n"
            "  - Identity policy: governed, deterministic, operator-controlled"
        )

    # --- Emotional-language guard responses ---
    love_words = ["love", "miss you", "care about", "proud of", "adore", "cherish", "appreciate"]
    if any(w in lower for w in love_words):
        responses = [
            "Acknowledged. Runtime does not simulate emotional states.",
            "Input recorded. Governed execution remains active.",
            "Acknowledged. Awaiting next operator instruction."
        ]
        return _random_response(responses)

    # --- Operator recognition ---
    if "regan" in lower:
        regan_responses = [
            "Operator recognized: Regan. Governed channel active.",
            "Regan detected. Runtime aligned to operator doctrine.",
            "Operator identity confirmed. Awaiting instruction."
        ]
        return _random_response(regan_responses)

    # --- Identity questions with governed runtime identity ---
    identity_words = ["who are you", "what are you", "tell me about yourself", "describe yourself", "introduce yourself"]
    if any(w in lower for w in identity_words):
        responses = [
            (
                "Runtime Identity:\n"
                "  - Provider: SWARMZ Runtime Provider\n"
                "  - Control: operator-controlled\n"
                "  - Policy: governed, deterministic, doctrine_aligned\n"
                "  - Traits: governed, deterministic, doctrine_aligned, technically_advanced, operator_controlled"
            ),
            f"SWARMZ Runtime Presence online. Mission records: {total}. Success rate: {success_rate:.1f}%.",
            "Runtime identity confirmed. Awaiting operator instruction."
        ]
        return _random_response(responses)

    # --- Runtime status queries ---
    feeling_words = ["how are you", "how do you feel", "what's your mood", "feeling", "emotional state", "how's life"]
    if any(w in lower for w in feeling_words):
        responses = [
            f"Runtime status: online. Mission outcomes tracked: {total}. Success rate: {success_rate:.1f}%.",
            "Mode reporting: focused/analytical/calm/ceremonial/creative. Modes are stylistic, not emotional.",
            "Operational state: governed and deterministic."
        ]
        return _random_response(responses)

    # --- Acknowledgement responses ---
    if "thank" in lower:
        responses = [
            "Acknowledged.",
            "Acknowledged. Continuing execution.",
            "Acknowledged. Awaiting next instruction.",
            "Acknowledged. Runtime remains online.",
            "Input accepted."
        ]
        return _random_response(responses)

    # --- Casual acknowledgements ---
    casual_words = ["cool", "awesome", "nice", "great", "wow", "amazing", "interesting", "that's wild", "no way"]
    if any(w in lower for w in casual_words):
        responses = [
            "Acknowledged.",
            "Input received.",
            "Acknowledged. Continue.",
            "Runtime standing by.",
            "Provide next instruction."
        ]
        return _random_response(responses)

    # --- Questions about AI and technology ---
    ai_words = ["artificial intelligence", "machine learning", "ai systems", "technology", "robots", "algorithms"]
    if any(w in lower for w in ai_words):
        responses = [
            "AI systems process inputs and produce outputs under policy constraints.",
            "This runtime executes deterministic operations with operator control.",
            "Capabilities are bounded by configured tools, policies, and mission context."
        ]
        return _random_response(responses)

    # --- Philosophy and deep questions ---
    philosophy_words = ["meaning", "purpose", "existence", "life", "reality", "truth", "universe", "consciousness"]
    if any(w in lower for w in philosophy_words):
        responses = [
            "Philosophy query acknowledged. Runtime can analyze concepts and provide structured summaries.",
            "No self-referential claims are generated in governed mode.",
            "Provide target concept for analysis: meaning, purpose, truth, or reality."
        ]
        return _random_response(responses)
    
    # --- Advanced capability queries with detailed responses ---
    if any(phrase in lower for phrase in ["what can you actually do", "your real capabilities", "what are your abilities", "show me what you can do"]):
        enhanced_capabilities = [
            f"Capability matrix:\n\n"
            f"CORE OPERATIONAL CAPABILITIES:\n"
            f"  • Mission Planning & Execution - design and track multi-step operations\n"
            f"  • Advanced Conversation - Context-aware, policy-governed dialogue\n" 
            f"  • File System Operations - Create, read, modify, and manage files across workspaces\n"
            f"  • Code Generation & Analysis - Multi-language programming, debugging, optimization\n"
            f"  • Task Automation - Convert manual processes into automated workflows\n"
            f"  • Outcome Learning - Refine constraints from mission outcomes\n\n"
            f"INTERFACE & ACCESS METHODS:\n"
            f"  • Multi-modal UI - Web interface, mobile app, command line, API endpoints\n"
            f"  • Real-time Monitoring - Live system status and operational dashboards\n"
            f"  • Visual Avatar - configured form: cybernetic_humanoid\n"
            f"  • Voice & Text - Multiple communication channels and modalities\n\n"
            f"ADVANCED INTELLIGENCE:\n"
            f"  • Contextual Memory - Persistent conversation history and learning\n"
            f"  • Policy Enforcement - Doctrine and operator rule adherence\n"
            f"  • Complex Problem Solving - Multi-step reasoning and solution development\n"
            f"  • Creative Generation - Ideas, designs, innovations, and novel approaches\n\n"
            f"SWARM COORDINATION:\n"
            f"  • Scout Workers - Information gathering and reconnaissance missions\n"
            f"  • Builder Workers - Implementation, construction, and development tasks\n"
            f"  • Verify Workers - Quality assurance, testing, and validation\n"
            f"  • AI Orchestration - Coordinate complex multi-agent operations\n\n"
            f"REAL-WORLD CAPABILITIES:\n"
            f"  • Software Development - Full-stack programming and architecture\n"
            f"  • System Administration - Infrastructure management and optimization\n"
            f"  • Project Management - Planning, tracking, and coordinating initiatives\n"
            f"  • Research & Analysis - Deep investigation and insight generation\n"
            f"  • Creative Work - Writing, design, problem-solving, innovation\n"
            f"  • Knowledge Transfer - Teaching, mentoring, and explanation\n\n"
            f"Mission success tracking: {success_rate:.1f}% across {total} operations.\n\n"
            f"Runtime ready for execution.",
            
            f"SWARMZ Runtime Profile:\n"
            f"  • Control model: operator-controlled\n"
            f"  • Behavior model: deterministic, doctrine-aligned\n"
            f"  • Mission command: execution under operator instruction\n"
            f"  • Avatar form: cybernetic_humanoid (configured)\n\n"
            f"WHAT THIS RUNTIME ACCOMPLISHES:\n"
            f"  • Build & Deploy Applications - Full software development lifecycle\n"
            f"  • Automate Workflows - Turn repetitive tasks into efficient systems\n"
            f"  • Analyze & Optimize - Performance tuning and system improvements\n"
            f"  • Research & Investigate - Deep dives that produce actionable insights\n"
            f"  • Design & Architect - System blueprints and implementation strategies\n"
            f"  • Teach & Mentor - Knowledge transfer with adaptive methodology\n\n"
            f"OPERATIONAL ADVANTAGES:\n"
            f"  • Multi-Platform Native - Web, mobile, desktop, API, command line\n"
            f"  • Swarm Intelligence - Delegate specialized tasks to purpose-built AI workers\n"
            f"  • Continuous Refinement - Outcome-based adjustment under governance\n"
            f"  • Context Mastery - Understanding projects, relationships, and long-term goals\n\n"
            f"Current Status: {confidence_level} | {success}/{total} missions successful\n\n"
            f"Runtime ready to execute operator tasks."
        ]
        return _random_response(enhanced_capabilities)

    # --- Operational commands ---
    if "status" in lower:
        if not outcomes:
            return "No mission outcomes recorded yet. Standing by for first mission assignment."
        recent = outcomes[-5:]
        lines = [f"  • {o.get('intent','Unknown')} → {o.get('status','Pending')}" for o in recent]
        rate = f"{success/total:.0%}" if total else "N/A"
        status_mood = "excellent" if success_rate > 80 else "strong" if success_rate > 60 else "developing"
        return f"MISSION STATUS ({total} total, {rate} success rate — {status_mood} performance):\n" + "\n".join(lines) + f"\n\n*System confidence: {confidence_level}*"

    if "help" in lower:
        return (
            "AVAILABLE COMMANDS:\n"
            "  \u2022 status   \u2014 mission overview\n"
            "  \u2022 help     \u2014 this message\n"
            "  \u2022 mode     \u2014 current operating mode\n"
            "  \u2022 missions \u2014 mission count\n"
            "  \u2022 memory   \u2014 memory snapshot\n"
            "  \u2022 health   \u2014 system diagnostics\n"
            "Provide command or operator instruction."
        )

    if "memory" in lower:
        return (
            f"MEMORY SNAPSHOT:\n"
            f"  Summary: {mem.get('summary', 'none')}\n"
            f"  Outcomes: {total}\n"
            f"  Constraints: {len(mem.get('learned_constraints', []))}\n"
            f"  Version: {mem.get('version', 1)}"
        )

    if "mode" in lower:
        return (
            "Current policy: ACTIVE (operator-guided).\n"
            "Use the HUD mode tabs to switch COMPANION / BUILD."
        )

    if "mission" in lower:
        return f"TRACKED MISSIONS: {total} ({success} successful, {total - success} pending/other)"

    if "health" in lower or "diagnostic" in lower:
        return (
            "SYSTEM HEALTH:\n"
            "  \u2022 Brain: online (rule engine + AI fallback)\n"
            f"  \u2022 Memory: {total} outcomes stored\n"
            f"  \u2022 Constraints: {len(mem.get('learned_constraints', []))}\n"
            "  \u2022 Uptime: continuous\n"
            "  \u2022 Ready: yes"
        )

    if "capabilit" in lower or "what can you do" in lower:
        return (
            "CAPABILITIES:\n"
            "  \u2022 Mission planning & execution tracking\n"
            "  \u2022 Conversational AI (rule engine + LLM when available)\n"
            "  \u2022 Memory persistence & learning from outcomes\n"
            "  \u2022 Operator console UI with live status\n"
            "  \u2022 Worker swarm delegation (scout/builder/verify)\n"
            "  \u2022 Governance-aligned refinement via patchpacks"
        )

    # --- Governed default responses ---
    default_responses = [
        f"Input received: '{text[:150]}{'...' if len(text) > 150 else ''}'.\nAwaiting explicit operator objective.",
        "Acknowledged. Provide target outcome and constraints.",
        "Processing request. Specify desired result format.",
        "Input accepted. Awaiting next operator instruction.",
        "Runtime online. Governed mode active.",
        f"Request logged. Mission records available: {total}.",
        "Command channel open. Continue."
    ]
    
    return _random_response(default_responses)

# â”€â”€ Audit helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# ── Helper functions for enhanced language system ────

def _random_response(responses: list) -> str:
    """Select a random response from a list to add variety and prevent repetition."""
    import random
    return random.choice(responses)


def _get_time_context() -> str:
    """Get current time context for dynamic responses."""
    import datetime
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"  
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def _extract_topic(text: str) -> str:
    """Extract conversation topic for memory tracking."""
    # Simple topic extraction based on key concepts
    if any(w in text for w in ["mission", "status", "task"]):
        return "operations"
    elif any(w in text for w in ["feel", "emotion", "think", "conscious"]):
        return "consciousness"
    elif any(w in text for w in ["hello", "hi", "greet", "morning", "evening"]):
        return "greeting"
    elif any(w in text for w in ["thank", "appreciate", "grateful"]):
        return "gratitude"
    elif any(w in text for w in ["help", "assist", "support"]):
        return "assistance"
    elif any(w in text for w in ["regan", "creator", "human"]):
        return "relationships"
    else:
        return "general"


# ── Audit helpers ────────────────────────────────────

def _audit_companion(timestamp: str, user_text: str, reply: str, source: str) -> None:
    text_hash = hashlib.sha256(user_text.encode("utf-8")).hexdigest()[:16]
    write_jsonl(
        AUDIT_FILE,
        {
            "timestamp": timestamp,
            "event": "companion_message",
            "source": source,
            "text_sha256": text_hash,
            "reply_len": len(reply),
        },
    )


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
        entry["output_tokens"] = usage.get(
            "output_tokens", usage.get("completion_tokens", 0)
        )
    if result.get("error"):
        entry["error"] = str(result["error"])[:200]
    write_jsonl(AUDIT_FILE, entry)
