# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Zapier Universal Connector Bridge (v0.1)

Provides two FastAPI endpoints:
  POST /v1/zapier/inbound  â€” Zapier -> SWARMZ (creates a mission)
  POST /v1/zapier/emit     â€” SWARMZ -> Zapier (POSTs to Catch Hook)

Append-only JSONL logs in data/zapier/.
Fail-open: never crashes the runtime.
"""

from __future__ import annotations

import json
import uuid
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

# â”€â”€ paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "config" / "runtime.json"
_ZAPIER_DIR = _ROOT / "data" / "zapier"
_INBOUND_LOG = _ZAPIER_DIR / "inbound.jsonl"
_OUTBOUND_LOG = _ZAPIER_DIR / "outbound.jsonl"
_MISSIONS_FILE = _ROOT / "data" / "missions.jsonl"
_AUDIT_FILE = _ROOT / "data" / "audit.jsonl"

# â”€â”€ in-memory dedupe (simple TTL map) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_DEDUPE: Dict[str, float] = {}
_DEDUPE_TTL = 600  # 10 minutes


# â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _load_zapier_config() -> Dict[str, Any]:
    """Load the integrations.zapier block from config/runtime.json."""
    try:
        cfg = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("integrations", {}).get("zapier", {})
    except Exception:
        return {}


def _append_log(path: Path, obj: Dict[str, Any]) -> None:
    """Append one JSON line (fail-silent)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")
    except Exception:
        pass  # fail-open


def _write_mission(mission: Dict[str, Any]) -> None:
    """Append a mission to data/missions.jsonl (same format as existing)."""
    try:
        _MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_MISSIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(mission, separators=(",", ":")) + "\n")
    except Exception:
        pass


def _write_audit(event: Dict[str, Any]) -> None:
    """Append an audit event to data/audit.jsonl."""
    try:
        _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
    except Exception:
        pass


def _prune_dedupe() -> None:
    """Remove expired dedupe keys."""
    now = time.time()
    expired = [k for k, ts in _DEDUPE.items() if now - ts > _DEDUPE_TTL]
    for k in expired:
        _DEDUPE.pop(k, None)


def _check_secret(zcfg: Dict[str, Any], header_val: Optional[str]) -> None:
    """Raise 401 if shared_secret doesn't match the header."""
    secret = zcfg.get("shared_secret", "")
    if not secret:
        return  # no secret configured â†’ open (dev mode)
    if header_val != secret:
        raise HTTPException(
            status_code=401, detail="invalid or missing X-SWARMZ-SECRET"
        )


# â”€â”€ request models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class ZapierInboundBody(BaseModel):
    source: str = "zapier"
    type: str = "trigger.generic"
    payload: Dict[str, Any] = {}
    dedupe_key: Optional[str] = None


class ZapierEmitBody(BaseModel):
    type: str = "swarmz.notice"
    payload: Dict[str, Any] = {}


# â”€â”€ registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def register_zapier_bridge(app: FastAPI) -> None:
    """Mount /v1/zapier/* endpoints on the FastAPI app. Fail-open."""

    zcfg = _load_zapier_config()
    inbound_path = zcfg.get("inbound_path", "/v1/zapier/inbound")
    emit_path = zcfg.get("emit_path", "/v1/zapier/emit")

    # â”€â”€ POST inbound â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @app.post(inbound_path)
    async def zapier_inbound(
        body: ZapierInboundBody,
        request: Request,
        x_swarmz_secret: Optional[str] = Header(None),
    ):
        zcfg_live = _load_zapier_config()

        # disabled check
        if not zcfg_live.get("enabled", True):
            return {"ok": False, "error": "zapier integration disabled"}

        # auth
        _check_secret(zcfg_live, x_swarmz_secret)

        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # dedupe
        _prune_dedupe()
        if body.dedupe_key and body.dedupe_key in _DEDUPE:
            _append_log(
                _INBOUND_LOG,
                {
                    "ts": now,
                    "direction": "inbound",
                    "event_id": event_id,
                    "source": body.source,
                    "type": body.type,
                    "payload": body.payload,
                    "ok": True,
                    "error": None,
                    "dedupe": "skipped",
                },
            )
            return {
                "ok": True,
                "event_id": event_id,
                "mission_id": None,
                "dedupe": "skipped",
            }

        if body.dedupe_key:
            _DEDUPE[body.dedupe_key] = time.time()

        # create mission (same schema as /v1/missions/create)
        mission_id = f"mission_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        mission = {
            "mission_id": mission_id,
            "goal": f"[zapier] {body.type}: {json.dumps(body.payload)[:200]}",
            "category": "zapier_inbound",
            "constraints": {},
            "results": {},
            "status": "PENDING",
            "created_at": now,
            "source": body.source,
            "zapier_type": body.type,
        }
        _write_mission(mission)
        _write_audit(
            {
                "event": "zapier_inbound",
                "mission_id": mission_id,
                "timestamp": now,
                "source": body.source,
                "type": body.type,
            }
        )

        _append_log(
            _INBOUND_LOG,
            {
                "ts": now,
                "direction": "inbound",
                "event_id": event_id,
                "source": body.source,
                "type": body.type,
                "payload": body.payload,
                "ok": True,
                "error": None,
            },
        )

        return {"ok": True, "event_id": event_id, "mission_id": mission_id}

    # â”€â”€ POST emit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @app.post(emit_path)
    async def zapier_emit(
        body: ZapierEmitBody,
        request: Request,
        x_swarmz_secret: Optional[str] = Header(None),
    ):
        zcfg_live = _load_zapier_config()

        if not zcfg_live.get("enabled", True):
            return {"ok": False, "error": "zapier integration disabled"}

        _check_secret(zcfg_live, x_swarmz_secret)

        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        hook_url = zcfg_live.get("zapier_catch_hook_url", "")

        if not hook_url:
            _append_log(
                _OUTBOUND_LOG,
                {
                    "ts": now,
                    "direction": "outbound",
                    "event_id": event_id,
                    "source": "swarmz",
                    "type": body.type,
                    "payload": body.payload,
                    "ok": False,
                    "error": "no zapier_catch_hook_url configured",
                },
            )
            return {
                "ok": False,
                "event_id": event_id,
                "delivered": False,
                "error": "no zapier_catch_hook_url configured",
            }

        # POST to Zapier catch hook (stdlib only, fail-open)
        delivered = False
        error_str: Optional[str] = None
        try:
            data = json.dumps(
                {
                    "event_id": event_id,
                    "type": body.type,
                    "payload": body.payload,
                    "ts": now,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                hook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                delivered = resp.status < 400
        except Exception as exc:
            error_str = str(exc)[:300]

        _append_log(
            _OUTBOUND_LOG,
            {
                "ts": now,
                "direction": "outbound",
                "event_id": event_id,
                "source": "swarmz",
                "type": body.type,
                "payload": body.payload,
                "ok": delivered,
                "error": error_str,
            },
        )

        return {
            "ok": delivered,
            "event_id": event_id,
            "delivered": delivered,
            "error": error_str,
        }
