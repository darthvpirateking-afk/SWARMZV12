"""NEXUSMON Router - FastAPI endpoints

Handles the /chat endpoint and integrates all NEXUSMON engines:
- conversation_engine
- persona_engine
- memory_engine

All operations are audited and append-only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request

from core.nexusmon_models import (
    ChatRequest,
    ChatReply,
    OperatorProfile,
    NexusForm,
    NexusFormType,
    ConversationContext,
    SystemHealth,
    AuditEvent,
)
from core.conversation_engine import get_conversation_engine
from core.memory_engine import get_memory_engine
from jsonl_utils import write_jsonl
from core.interaction_logger import log_event
from system.health_monitor import update_status
from system.mission_controller import schedule_next_mission
from evolution.consensus_engine import propose_upgrade
from core.reasoning_engine import reasoning_engine
from core.audit_trail import log_audit_event
from system.self_monitoring import monitor
from addons.external_extension_api import extension_api
from core.intent_modeling import intent_modeler

router = APIRouter(prefix="/v1/nexusmon", tags=["conversation"])

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Files
OPERATOR_PROFILES_FILE = DATA_DIR / "operator_profiles.jsonl"
NEXUS_FORMS_FILE = DATA_DIR / "nexus_forms.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
_low_coherence_since: Optional[str] = None


# ================================================================
# Helper Functions (Data Access)
# ================================================================


def _ensure_operator_profile(operator_id: str) -> OperatorProfile:
    """Get or create an operator profile.

    Args:
        operator_id: Operator ID

    Returns:
        OperatorProfile object
    """
    # Try to load existing profile
    if OPERATOR_PROFILES_FILE.exists():
        try:
            with OPERATOR_PROFILES_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("operator_id") == operator_id:
                            return OperatorProfile(**obj)
                    except (json.JSONDecodeError, ValueError):
                        pass
        except OSError:
            pass

    # Create new profile
    # Sovereign operator identity — Regan Stewart Harris is the primary operator
    _known_names = {"op-001": "Regan Stewart Harris"}
    username = _known_names.get(operator_id, operator_id.replace("op-", ""))
    profile = OperatorProfile(operator_id=operator_id, username=username)

    # Store it
    write_jsonl(OPERATOR_PROFILES_FILE, profile.model_dump(mode="json"))

    return profile


def _ensure_nexus_form(operator_id: str) -> NexusForm:
    """Get or create a NexusForm for an operator.

    Args:
        operator_id: Operator ID

    Returns:
        NexusForm object
    """
    # Try to load existing form
    if NEXUS_FORMS_FILE.exists():
        try:
            with NEXUS_FORMS_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("operator_id") == operator_id:
                            return NexusForm(**obj)
                    except (json.JSONDecodeError, ValueError):
                        pass
        except OSError:
            pass

    # Create new form
    form = NexusForm(operator_id=operator_id, current_form=NexusFormType.OPERATOR)

    # Store it
    write_jsonl(NEXUS_FORMS_FILE, form.model_dump(mode="json"))

    return form


def _get_system_health() -> SystemHealth:
    """Get current system health (stub for now).

    In production, this would compute from actual system metrics.
    """
    global _low_coherence_since

    health = SystemHealth(entropy=0.3, drift=0.2, coherence=0.8)
    if health.coherence < 0.7 and _low_coherence_since is None:
        _low_coherence_since = datetime.now(timezone.utc).isoformat()
    if health.coherence >= 0.7:
        _low_coherence_since = None

    status = update_status(health.coherence, _low_coherence_since)
    if status.freeze_autonomy:
        log_event(
            event_type="coherence_freeze",
            role="system",
            details={
                "coherence": health.coherence,
                "alert": status.alert,
            },
        )
    return health


def _get_mission_queue() -> list:
    """Get pending mission queue for scheduling checks."""
    queue = []
    if MISSIONS_FILE.exists():
        try:
            with MISSIONS_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("status") in {"PENDING", "QUEUED"}:
                            queue.append(obj)
                    except (json.JSONDecodeError, ValueError):
                        pass
        except OSError:
            pass
    return queue


def _get_active_missions(operator_id: Optional[str] = None) -> list:
    """Get active missions.

    Args:
        operator_id: Optional filter by operator

    Returns:
        List of active missions
    """
    missions = []
    if MISSIONS_FILE.exists():
        try:
            with MISSIONS_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("status") == "RUNNING":
                            missions.append(obj)
                    except (json.JSONDecodeError, ValueError):
                        pass
        except OSError:
            pass

    return missions


def _emit_audit_event(event: AuditEvent) -> None:
    """Emit an audit event.

    Args:
        event: AuditEvent to record
    """
    write_jsonl(AUDIT_FILE, event.model_dump(mode="json"))
    try:
        log_event(
            event_type=event.event_type,
            role="system",
            details={
                "operator_id": event.operator_id,
                "details": event.details,
            },
        )
    except Exception:
        pass


# ================================================================
# Endpoints
# ================================================================


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request) -> ChatReply:
    """
    Main NEXUSMON chat endpoint.

    Receives a message, generates a reply with mode, suggested actions,
    and state snapshot. All operations are audited.

    Args:
        payload: ChatRequest with operator_id, message, context
        request: FastAPI request object

    Returns:
        ChatReply with reply text, mode, actions, snapshot
    """
    try:
        operator_id = payload.operator_id

        # 1. Load/create operator data
        operator = _ensure_operator_profile(operator_id)
        nexus_form = _ensure_nexus_form(operator_id)

        # 2. Get recent conversation history
        memory_engine = get_memory_engine()
        history = memory_engine.get_recent_turns(operator_id, limit=20)

        # 3. Get system state
        health = _get_system_health()
        missions = _get_active_missions()
        queue = _get_mission_queue()
        schedule_decision = schedule_next_mission(queue, health.entropy, health.drift)
        if not schedule_decision.get("scheduled", False):
            _emit_audit_event(
                AuditEvent(
                    event_type="mission_schedule_blocked",
                    operator_id=operator_id,
                    details=schedule_decision,
                )
            )

        # 3a. Run self-monitoring diagnostics
        anomalies = monitor.run_diagnostics(
            {
                "drift": health.drift,
                "entropy": health.entropy,
                "coherence": health.coherence,
            }
        )

        # 3b. Parse intent with hierarchical modeling
        intent = intent_modeler.parse_intent(payload.message)

        # 3c. Log to persistent audit trail
        log_audit_event(
            "chat_initiated",
            {
                "operator_id": operator_id,
                "message": payload.message[:100],
                "anomalies": anomalies,
                "intent": intent,
            },
            actor=operator_id,
        )

        # 4. Build conversation context
        context = ConversationContext(
            operator=operator,
            nexus_form=nexus_form,
            missions=missions,
            health=health,
            history=history,
            ui_context=payload.context,
        )

        # 5. Generate reply using conversation engine
        conversation_engine = get_conversation_engine()
        reply_obj = conversation_engine.generate_reply(
            message=payload.message, context=context
        )

        # 6. Store conversation turn
        memory_engine.store_conversation_turn(
            operator_id=operator_id,
            message=payload.message,
            reply=reply_obj.reply,
            mode=reply_obj.mode.value,
            tags=[],
        )

        # 7. Emit audit event
        _emit_audit_event(
            AuditEvent(
                event_type="chat_turn",
                operator_id=operator_id,
                details={
                    "message": payload.message[:200],
                    "reply": reply_obj.reply[:200],
                    "mode": reply_obj.mode.value,
                    "context_screen": payload.context.screen,
                    "context_mission": payload.context.mission_id,
                },
            )
        )

        return reply_obj

    except Exception as e:
        # Log error and return error response
        _emit_audit_event(
            AuditEvent(
                event_type="chat_error",
                operator_id=payload.operator_id,
                details={"error": str(e)},
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", operation_id="nexusmon_health")
async def nexusmon_health():
    """Health check for NEXUSMON service."""
    return {"ok": True, "service": "NEXUSMON Console", "status": "operational"}


@router.get("/entity/state", operation_id="get_entity_state_v1")
async def get_entity_state():
    """Get NEXUSMON entity state for cockpit display."""
    try:
        from nexusmon.entity import get_entity

        _XP_THRESHOLDS = {
            "ROOKIE": 100.0,
            "CHAMPION": 500.0,
            "ULTIMATE": 2000.0,
            "MEGA": 10000.0,
            "SOVEREIGN": float("inf"),
        }

        entity = get_entity()
        state = entity.get_state()
        traits = entity.get_traits()

        form_raw = state.get("current_form", "ROOKIE")
        form = form_raw.capitalize() if form_raw else "Rookie"
        mood_raw = state.get("mood", "CALM")
        mood = mood_raw.lower() if mood_raw else "calm"
        xp = float(state.get("evolution_xp") or 0.0)
        xp_to_next = _XP_THRESHOLDS.get(form_raw, 100.0)
        xp_pct = (
            min(100.0, xp / xp_to_next * 100.0) if xp_to_next != float("inf") else 100.0
        )

        return {
            "name": "NEXUSMON",
            "form": form,
            "mood": mood,
            "xp": xp,
            "xp_to_next": None if xp_to_next == float("inf") else xp_to_next,
            "xp_pct": round(xp_pct, 1),
            "boot_count": state.get("boot_count", 0),
            "interaction_count": state.get("interaction_count", 0),
            "traits": traits,
            "operator_name": state.get("operator_name", ""),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/operators/{operator_id}/profile")
async def get_operator_profile(operator_id: str):
    """Get operator profile.

    Args:
        operator_id: Operator ID

    Returns:
        OperatorProfile
    """
    profile = _ensure_operator_profile(operator_id)
    return profile.model_dump(mode="json")


@router.get("/operators/{operator_id}/nexus-form")
async def get_operator_nexus_form(operator_id: str):
    """Get operator's current NexusForm.

    Args:
        operator_id: Operator ID

    Returns:
        NexusForm
    """
    form = _ensure_nexus_form(operator_id)
    return form.model_dump(mode="json")


@router.get("/operators/{operator_id}/conversation-history")
async def get_conversation_history(operator_id: str, limit: int = 20):
    """Get recent conversation history for an operator.

    Args:
        operator_id: Operator ID
        limit: Maximum number of turns to return

    Returns:
        List of ConversationTurn objects
    """
    memory_engine = get_memory_engine()
    turns = memory_engine.get_recent_turns(operator_id, limit=limit)
    return [t.model_dump(mode="json") for t in turns]


@router.get("/operators/{operator_id}/memory")
async def get_operator_memory(operator_id: str):
    """Get long-term operator memory.

    Args:
        operator_id: Operator ID

    Returns:
        OperatorMemory or None
    """
    memory_engine = get_memory_engine()
    memory = memory_engine.get_operator_memory(operator_id)
    if memory:
        return memory.model_dump(mode="json")
    return {"message": "no memory yet"}


@router.post("/operators/{operator_id}/memory/update")
async def update_operator_memory(
    operator_id: str,
    summary: str,
    tags: Optional[list] = None,
    patterns: Optional[Dict[str, Any]] = None,
):
    """Update operator's long-term memory.

    Args:
        operator_id: Operator ID
        summary: Text summary of patterns
        tags: Optional tags
        patterns: Optional pattern dict

    Returns:
        OperatorMemory
    """
    memory_engine = get_memory_engine()
    memory = memory_engine.update_operator_memory(
        operator_id=operator_id, summary=summary, tags=tags, patterns=patterns
    )
    return memory.model_dump(mode="json")


@router.get("/system/health")
async def get_system_health():
    """Get current system health.

    Returns:
        SystemHealth
    """
    health = _get_system_health()
    anomalies = monitor.run_diagnostics(
        {
            "drift": health.drift,
            "entropy": health.entropy,
            "coherence": health.coherence,
        }
    )
    return {**health.model_dump(mode="json"), "anomalies": anomalies}


@router.post("/system/upgrade/propose")
async def system_upgrade_propose(payload: Dict[str, Any]):
    """Propose an upgrade with novelty-gated consensus checks."""
    proposal = payload.get("proposal", {})
    simulation_results = payload.get("simulation_results", {})
    decision = propose_upgrade(proposal, simulation_results)
    log_audit_event("upgrade_proposal", {"proposal": proposal, "decision": decision})
    return decision


@router.post("/reasoning/switch_core")
async def switch_reasoning_core(payload: Dict[str, Any]):
    """Switch the active reasoning core."""
    core_name = payload.get("core_name", "default")
    reasoning_engine.switch_core(core_name)
    return {"status": "ok", "active_core": reasoning_engine.active_core}


@router.post("/extensions/register")
async def register_extension(payload: Dict[str, Any]):
    """Register an external extension."""
    name = payload.get("name")
    capabilities = payload.get("capabilities", [])
    extension_api.register_extension(name, capabilities)
    return {"status": "registered", "name": name}


@router.post("/extensions/invoke")
async def invoke_extension(payload: Dict[str, Any]):
    """Invoke an external extension."""
    name = payload.get("name")
    action = payload.get("action")
    ext_payload = payload.get("payload", {})
    result = extension_api.invoke_extension(name, action, ext_payload)
    return result


# ── Swarm endpoints ─────────────────────────────────────────────────


@router.get("/swarm/units")
async def list_swarm_units(status: str = None):
    from nexusmon.swarm import get_swarm_engine

    units = get_swarm_engine().list_units(status=status)
    return {"units": units, "count": len(units)}


@router.post("/swarm/units")
async def create_swarm_unit(payload: Dict[str, Any]):
    from nexusmon.swarm import get_swarm_engine

    unit_type = payload.get("unit_type", "SCOUT")
    unit = get_swarm_engine().create_unit(unit_type)
    return unit


@router.post("/swarm/units/{unit_id}/deploy")
async def deploy_unit(unit_id: str):
    from nexusmon.swarm import get_swarm_engine

    get_swarm_engine().deploy_unit(unit_id)
    return {"ok": True, "unit_id": unit_id, "status": "ON_MISSION"}


@router.post("/swarm/units/{unit_id}/recall")
async def recall_unit(unit_id: str):
    from nexusmon.swarm import get_swarm_engine

    get_swarm_engine().recall_unit(unit_id)
    return {"ok": True, "unit_id": unit_id, "status": "IDLE"}


# ── Mission endpoints ────────────────────────────────────────────────


@router.get("/missions")
async def list_missions(limit: int = 20, status: str = None):
    from nexusmon.missions import get_mission_engine

    engine = get_mission_engine()
    if status == "active":
        missions = engine.get_active()
    elif status == "pending":
        missions = engine.get_pending()
    else:
        missions = engine.get_all(limit=limit)
    return {"missions": missions, "stats": engine.get_stats()}


@router.post("/missions")
async def create_mission(payload: Dict[str, Any]):
    from nexusmon.missions import get_mission_engine

    engine = get_mission_engine()
    mission = engine.create_mission(
        title=payload.get("title", "Unnamed Mission"),
        mission_type=payload.get("mission_type", "RESEARCH"),
        difficulty=int(payload.get("difficulty", 1)),
        operator_id=payload.get("operator_id", "op-001"),
    )
    return mission


@router.post("/missions/{mission_id}/dispatch")
async def dispatch_mission(mission_id: str, payload: Dict[str, Any]):
    from nexusmon.missions import get_mission_engine

    unit_id = payload.get("unit_id")
    if not unit_id:
        return {"error": "unit_id required"}
    result = get_mission_engine().dispatch(mission_id, unit_id)
    return result


@router.post("/missions/{mission_id}/complete")
async def complete_mission(mission_id: str, payload: Dict[str, Any]):
    from nexusmon.missions import get_mission_engine

    success = payload.get("success", True)
    result = get_mission_engine().complete(mission_id, success=success)
    return result


# ── Artifact endpoints ───────────────────────────────────────────────


@router.get("/artifacts")
async def list_artifacts(
    artifact_type: str = None, rarity: str = None, limit: int = 50
):
    from nexusmon.artifacts import get_vault

    items = get_vault().list_all(
        artifact_type=artifact_type, rarity=rarity, limit=limit
    )
    return {"artifacts": items, "total": get_vault().get_vault_size()}


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    from nexusmon.artifacts import get_vault

    item = get_vault().get(artifact_id)
    if not item:
        return {"error": "Artifact not found"}
    return item


@router.post("/artifacts")
async def create_artifact(payload: Dict[str, Any]):
    from nexusmon.artifacts import get_vault

    item = get_vault().create(
        name=payload.get("name", "Unnamed Artifact"),
        artifact_type=payload.get("artifact_type", "KNOWLEDGE_BLOCK"),
        rarity=payload.get("rarity", "COMMON"),
        created_by=payload.get("created_by", "operator"),
        tags=payload.get("tags"),
        metadata=payload.get("metadata"),
        payload=payload.get("payload"),
    )
    return item


# ── Factory endpoints ────────────────────────────────────────────────


@router.get("/factory/status")
async def factory_status():
    from nexusmon.factory import get_factory

    return get_factory().get_status()


@router.get("/factory/recipes")
async def factory_recipes():
    from nexusmon.factory import get_factory

    return {"recipes": get_factory().get_recipes()}


@router.post("/factory/jobs")
async def queue_factory_job(payload: Dict[str, Any]):
    from nexusmon.factory import get_factory

    recipe_id = payload.get("recipe_id")
    if not recipe_id:
        return {"error": "recipe_id required"}
    job_id = get_factory().queue_job(recipe_id)
    return {"ok": True, "job_id": job_id}


# ── Chronicle endpoints ──────────────────────────────────────────────


@router.get("/chronicle")
async def get_chronicle(limit: int = 20, min_significance: float = 0.0):
    from nexusmon.chronicle import get_chronicle as _gc

    entries = _gc().get_entries(limit=limit, min_significance=min_significance)
    return {"entries": entries, "total": _gc().get_entry_count()}


@router.get("/chronicle/letters")
async def get_letters():
    from nexusmon.chronicle import get_chronicle as _gc

    return {"letters": _gc().get_letters()}


@router.post("/chronicle/letters/{letter_id}/reply")
async def reply_to_letter(letter_id: int, payload: Dict[str, Any]):
    from nexusmon.chronicle import get_chronicle as _gc

    reply = payload.get("reply", "")
    _gc().add_operator_reply(letter_id, reply)
    return {"ok": True}


# ── Operator extended endpoints ──────────────────────────────────────


@router.get("/operator/profile-page")
async def get_operator_profile_page():
    from nexusmon.operator import get_operator_engine

    eng = get_operator_engine()
    profile = eng.ensure_profile()
    page = eng.get_profile_page()
    return {**profile, **page}


@router.put("/operator/safe-word")
async def set_safe_word(payload: Dict[str, Any]):
    from nexusmon.entity import get_entity

    word = payload.get("word", "").strip()
    if not word:
        return {"error": "word required"}
    get_entity().set_safe_word(word)
    return {"ok": True, "word": word}


@router.get("/operator/safe-word")
async def get_safe_word_status():
    from nexusmon.entity import get_entity

    word = get_entity().get_safe_word()
    return {"set": word is not None, "activated_count": 0}


@router.get("/operator/curiosities")
async def get_curiosities():
    from nexusmon.entity import get_entity

    return {"curiosities": get_entity().get_curiosities()}


@router.get("/operator/dreams")
async def get_dreams():
    from nexusmon.dream import get_dream_engine

    return {"dreams": get_dream_engine().get_pending_share()}


@router.post("/operator/dreams/{dream_id}/dismiss")
async def dismiss_dream(dream_id: int):
    from nexusmon.dream import get_dream_engine

    get_dream_engine().mark_shared(dream_id)
    return {"ok": True}


@router.put("/operator/nexusmon-note")
async def update_nexusmon_note(payload: Dict[str, Any]):
    from nexusmon.operator import get_operator_engine

    note = payload.get("note", "")
    get_operator_engine().update_nexusmon_note(note)
    return {"ok": True}
