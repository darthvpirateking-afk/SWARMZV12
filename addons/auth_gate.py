# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
LAN Write-Auth Hardening middleware for FastAPI.

Any mutating request (POST/PUT/PATCH/DELETE) from a non-localhost IP
must carry a valid ``X-Operator-Key`` header (or ``operator_key`` query param)
matching the configured PIN/key.

Localhost requests (127.0.0.1, ::1) are always allowed.
"""

import ipaddress
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from addons.config_ext import get_config

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

_LOCALHOST_ADDRS = {
    ipaddress.ip_address("127.0.0.1"),
    ipaddress.ip_address("::1"),
}


def _client_ip(request: Request) -> Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    host = request.client.host if request.client else "127.0.0.1"
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _is_localhost(request: Request) -> bool:
    addr = _client_ip(request)
    return addr in _LOCALHOST_ADDRS if addr else False


def _append_audit(event: str, details: dict) -> None:
    cfg = get_config()
    audit_path = Path(cfg.get("audit_file", "data/audit.jsonl"))
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "details": details,
    }
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


class LANAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cfg = get_config()
        if not cfg.get("lan_auth_enabled", True):
            return await call_next(request)

        pin = cfg.get("operator_pin", "")
        if not pin:
            # No PIN configured â†’ allow all (operator chose not to enable)
            return await call_next(request)

        if request.method in _SAFE_METHODS:
            return await call_next(request)

        if _is_localhost(request):
            return await call_next(request)

        # Non-localhost write â†’ require key
        provided = (
            request.headers.get("X-Operator-Key")
            or request.query_params.get("operator_key")
        )
        if provided != pin:
            _append_audit("lan_auth_denied", {
                "ip": str(_client_ip(request)),
                "path": request.url.path,
                "method": request.method,
            })
            raise HTTPException(status_code=403, detail="Operator key required for LAN writes")

        return await call_next(request)

