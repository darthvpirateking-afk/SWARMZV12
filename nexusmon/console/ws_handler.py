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
        greeting_context = entity.get_greeting_context(operator_id)

        # Run blocking call in thread pool so the event loop stays free
        greeting_text = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: intel.generate_greeting(
                entity_state=entity_state,
                operator_context=greeting_context,
            ),
        )

        await websocket.send_json(
            {
                "type": "greeting",
                "text": greeting_text,
                "entity": _entity_payload(entity_state),
            }
        )

    except Exception as exc:
        logger.exception("WS: greeting generation failed")
        await websocket.send_json(
            {
                "type": "greeting",
                "text": "Systems online. Ready.",
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

    reply_frame = {
        "type": "reply",
        "reply": reply_text,
        "entity": _entity_payload(fresh_state),
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
