"""nexusmon/console/ws_handler.py -- NEXUSMON real-time WebSocket chat.

Endpoint: /ws/nexusmon

Wire protocol (JSON frames):

  Client -> Server:
    {"type": "chat", "operator_id": "op-001", "message": "...", "screen": "Console"}
    {"type": "ping"}

  Server -> Client:
    {"type": "greeting", "text": "...", "entity": {...}}
    {"type": "thinking"}
    {"type": "reply", "reply": "...", "entity": {...}, "operator": {...}, "xp_event": {...}}
    {"type": "evolution", "from": "Rookie", "to": "Champion", "message": "..."}
    {"type": "pong"}
    {"type": "error", "message": "..."}
"""

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("nexusmon.ws")

# XP thresholds used to compute xp_to_next and xp_pct per form
_XP_THRESHOLDS: dict = {
    "ROOKIE": 100.0,
    "CHAMPION": 500.0,
    "ULTIMATE": 2000.0,
    "MEGA": 10000.0,
    "SOVEREIGN": float("inf"),
}


async def handle_ws_chat(websocket: WebSocket) -> None:
    """Accept and serve a NEXUSMON WebSocket connection."""
    await websocket.accept()
    operator_id: str = "op-001"

    # Lazy-load heavy modules inside the handler so server boot is unaffected
    # by any import-time errors in these modules.
    try:
        from nexusmon.entity import get_entity
        from nexusmon.intelligence import get_intelligence
        from nexusmon.operator import OperatorProfile

        entity = get_entity()
        intel = get_intelligence()

        # Per-connection operator profile (loads persisted state from SQLite)
        operator_profile: OperatorProfile = OperatorProfile(operator_id)

    except Exception as exc:
        logger.exception("WS: module init failed")
        await websocket.send_json({"type": "error", "message": f"Init failed: {exc}"})
        return

    # -- Opening greeting ------------------------------------------------
    try:
        entity_state = entity.get_state()
        entity_traits = entity.get_traits()
        # Merge traits into state so intelligence prompt has them
        entity_state["traits"] = entity_traits

        # Proactive boot scan — provides gap metadata and greeting_hint
        _scan: dict = {"gap_category": "normal", "greeting_hint": "", "gap_hours": 0.0}
        try:
            from nexusmon.proactive import run_boot_scan

            _scan = run_boot_scan(entity_state)
        except Exception:
            pass  # proactive module absent or failed — use defaults

        operator_context = (
            f"Boot scan: gap={_scan['gap_category']}, "
            f"hint={_scan['greeting_hint']}, "
            f"gap_hours={_scan['gap_hours']}"
        )

        # Run blocking AI call in thread pool so the event loop stays free
        greeting_text = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: intel.generate_greeting(
                entity_state=entity_state,
                operator_context=operator_context,
            ),
        )

        # Build full entity payload for cockpit left-panel population
        _boot_form_raw = entity_state.get("current_form", "ROOKIE")
        _boot_xp = float(entity_state.get("evolution_xp") or 0)
        _boot_xp_to_next = _XP_THRESHOLDS.get(_boot_form_raw, 100.0)
        _boot_xp_pct = (
            min(100.0, (_boot_xp / _boot_xp_to_next * 100.0))
            if _boot_xp_to_next != float("inf")
            else 100.0
        )
        greeting_entity = {
            "name": "NEXUSMON",
            "form": _boot_form_raw.capitalize(),
            "mood": entity_state.get("mood", "CALM").lower(),
            "xp": _boot_xp,
            "xp_to_next": (
                None if _boot_xp_to_next == float("inf") else _boot_xp_to_next
            ),
            "xp_pct": round(_boot_xp_pct, 1),
            "boot_count": entity_state.get("boot_count", 0),
            "interaction_count": entity_state.get("interaction_count", 0),
            "traits": entity_traits,
            "operator_name": entity_state.get("operator_name", "Regan Stewart Harris"),
        }

        await websocket.send_json(
            {
                "type": "greeting",
                "text": greeting_text,
                "entity": greeting_entity,
            }
        )

    except Exception as exc:
        logger.exception("WS: greeting generation failed")
        await websocket.send_json(
            {
                "type": "greeting",
                "text": entity.get_greeting(),
                "entity": _entity_payload(entity.get_state()),
            }
        )

    # -- Message loop ----------------------------------------------------
    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON payload."}
                )
                continue

            msg_type = data.get("type", "chat")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type in ("chat", "message"):
                new_op_id = data.get("operator_id", "").strip()
                if new_op_id and new_op_id != operator_id:
                    operator_id = new_op_id
                    operator_profile = OperatorProfile(operator_id)

                message = (data.get("message") or "").strip()
                if not message:
                    continue

                # Safe word check — operator needs presence, not task mode
                try:
                    from nexusmon.entity import get_entity as _get_entity

                    _entity_check = _get_entity()
                    _user_message = message
                    if _entity_check.check_safe_word(_user_message):
                        _entity_check.activate_safe_word()
                        # Log to chronicle
                        try:
                            from nexusmon.chronicle import (
                                get_chronicle as _get_chronicle,
                                QUIET_MOMENT,
                            )

                            _get_chronicle().add_entry(
                                event_type=QUIET_MOMENT,
                                title="A Quiet Moment",
                                content="Regan Stewart Harris activated the safe word. NEXUSMON was just present.",
                                significance=0.8,
                                form=_entity_check.get_state().get(
                                    "current_form", "ROOKIE"
                                ),
                                mood="CALM",
                            )
                        except Exception:
                            pass
                        await websocket.send_json(
                            {
                                "type": "reply",
                                "reply": "I'm here. Everything stops. Talk to me.",
                                "mode": "quiet",
                                "state_snapshot": {},
                                "suggested_actions": [],
                            }
                        )
                        continue  # Skip the rest of the chat processing
                except Exception:
                    pass

                await websocket.send_json({"type": "thinking"})

                try:
                    reply_data = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: _handle_chat(
                            message=message,
                            operator_id=operator_id,
                            screen=data.get("screen", "Console"),
                            entity=entity,
                            intel=intel,
                            operator_profile=operator_profile,
                        ),
                    )

                    await websocket.send_json(reply_data["reply_frame"])

                    if reply_data.get("evolution_frame"):
                        await websocket.send_json(reply_data["evolution_frame"])

                except Exception as exc:
                    logger.exception("WS: chat error for %s", operator_id)
                    await websocket.send_json({"type": "error", "message": str(exc)})
                continue

            await websocket.send_json(
                {"type": "error", "message": f"Unknown type: {msg_type!r}"}
            )

    except WebSocketDisconnect:
        logger.debug("WS: disconnected -- %s", operator_id)
    except Exception:
        logger.exception("WS: unexpected error for %s", operator_id)


# -- Chat handling (runs in thread pool) ---------------------------------


def _handle_chat(
    message: str,
    operator_id: str,
    screen: str,
    entity,
    intel,
    operator_profile,
) -> dict:
    """Execute one full chat turn: log, classify, respond, award XP, persist."""

    entity.log_exchange(operator_id, "user", message)
    entity.bump_operator_message_count(operator_id)

    entity_state = entity.get_state()
    history = entity.get_conversation_history(operator_id, last_n=20)

    intent = intel.classify_intent(message)

    result = intel.chat(
        message=message,
        operator_id=operator_id,
        entity_state=entity_state,
        operator_context=operator_profile.to_prompt_snippet(),
        history=history[:-1],
    )

    reply_text = result.get("text") or "..."
    response_quality = 1.0 if result.get("ok") else 0.3

    entity.log_exchange(operator_id, "assistant", reply_text)

    operator_profile.record_exchange(
        message=message,
        intent=intent,
        response_quality=response_quality,
    )

    xp_result = entity.award_xp()
    evolved = xp_result.get("evolved", False)
    new_form = xp_result.get("new_form", entity_state.get("form", "Rookie"))

    fresh_state = entity.get_state()
    fresh_traits = entity.get_traits()

    # Build entity payload with full spec fields (interaction_count, operator_name)
    try:
        entity_payload = {
            "name": "NEXUSMON",
            "form": fresh_state.get("current_form", "ROOKIE").capitalize(),
            "mood": fresh_state.get("mood", "CALM").lower(),
            "xp": float(fresh_state.get("evolution_xp") or 0),
            "boot_count": fresh_state.get("boot_count", 0),
            "interaction_count": fresh_state.get("interaction_count", 0),
            "traits": fresh_traits,
            "operator_name": fresh_state.get("operator_name", ""),
        }
    except Exception:
        entity_payload = {}

    reply_frame = {
        "type": "reply",
        "reply": reply_text,
        "entity": entity_payload,
        "operator": operator_profile.to_context_dict(),
        "xp_event": {
            "xp_awarded": xp_result.get("xp_awarded", 0),
            "xp_total": fresh_state.get("xp", 0),
            "xp_to_next": fresh_state.get("xp_to_next", 100),
            "evolved": evolved,
        },
    }

    evolution_frame = None
    if evolved:
        old_form = entity_state.get("form", "Rookie")
        evolution_frame = {
            "type": "evolution",
            "from": old_form,
            "to": new_form,
            "message": (
                f"NEXUSMON has evolved from {old_form} to {new_form}. "
                "A new form awakens."
            ),
        }

    return {"reply_frame": reply_frame, "evolution_frame": evolution_frame}


# -- Helpers -------------------------------------------------------------


def _entity_payload(state: dict) -> dict:
    """Serialise entity state for wire transport (JSON-safe)."""
    xp = state.get("xp", 0.0)
    xp_to_next = state.get("xp_to_next", 100.0)
    if xp_to_next is None or xp_to_next == float("inf"):
        xp_to_next = None
        xp_pct = 100
    else:
        xp_pct = round((xp / xp_to_next) * 100, 1) if xp_to_next else 0

    return {
        "name": state.get("name", "NEXUSMON"),
        "form": state.get("form", "Rookie"),
        "mood": state.get("mood", "calm"),
        "traits": state.get("traits", {}),
        "xp": round(xp, 1),
        "xp_to_next": xp_to_next,
        "xp_pct": xp_pct,
        "boot_count": state.get("boot_count", 1),
        "time_alive_seconds": state.get("time_alive_seconds", 0),
    }
