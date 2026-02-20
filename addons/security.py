# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Security helpers: IDS, JWT/RBAC, and security audit logging.

This module is intentionally self-contained and opt-in:
- IDS/behavioral anomaly detection via middleware (logs only, does not block).
- JWT-based session tokens with role claims.
- Lightweight RBAC dependency that can be used on sensitive routes.

Design goals:
- Never break existing flows by default.
- All strong enforcement is behind explicit config/env toggles.
- Security events go to a dedicated JSONL file under data/.
"""

from __future__ import annotations

import ipaddress
import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from addons.config_ext import get_config


# ---------------------------------------------------------------------------
# Security audit log helpers
# ---------------------------------------------------------------------------


def _security_log_path() -> Path:
    cfg = get_config()
    base = Path(cfg.get("security_audit_file", "data/security_incidents.jsonl"))
    base.parent.mkdir(parents=True, exist_ok=True)
    return base


def append_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Append a structured security/audit event to the JSONL log.

    This is intentionally lightweight and fire-and-forget.
    """

    path = _security_log_path()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
    }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        # Logging must never crash the app; fail silently.
        return


def read_security_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the most recent security events from the JSONL log.

    Intended for status/debug UIs, not for heavy analytics.
    """

    path = _security_log_path()
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = [ln for ln in f.readlines() if ln.strip()]
    except OSError:
        return []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


# ---------------------------------------------------------------------------
# IDS / behavioral anomaly detection middleware
# ---------------------------------------------------------------------------


class IDSMiddleware(BaseHTTPMiddleware):
    """Lightweight IDS-style middleware.

    Responsibilities:
    - Track per-IP error spikes (4xx/5xx) over a rolling time window.
    - Flag obviously suspicious probe paths/payloads.
    - Emit structured events to the security log only (no blocking).

    This is intentionally conservative: it observes and records but does not
    change responses. Operators can inspect data/security_incidents.jsonl or
    ship it to external monitoring.
    """

    def __init__(self, app, *, window_seconds: int = 60, max_errors: int = 20):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.max_errors = max_errors
        # ip -> deque of error timestamps
        self._error_windows: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = self._client_ip(request)
        path = request.url.path
        method = request.method.upper()
        started = time.time()

        suspicious_reason: Optional[str] = None
        if self._looks_like_probe(path):
            suspicious_reason = "suspicious_path_pattern"

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            self._record_error(client_ip)
            append_security_event(
                "uncaught_exception",
                {
                    "ip": client_ip,
                    "path": path,
                    "method": method,
                },
            )
            raise
        else:
            if status_code >= 400:
                self._record_error(client_ip)
        finally:
            duration_ms = int((time.time() - started) * 1000)
            if suspicious_reason:
                append_security_event(
                    "suspicious_request",
                    {
                        "ip": client_ip,
                        "path": path,
                        "method": method,
                        "reason": suspicious_reason,
                        "duration_ms": duration_ms,
                    },
                )

        return response

    def _client_ip(self, request: Request) -> str:
        host = request.client.host if request.client else "127.0.0.1"
        try:
            ip = ipaddress.ip_address(host)
            return str(ip)
        except ValueError:
            return host

    def _record_error(self, ip: str) -> None:
        now = time.time()
        dq = self._error_windows[ip]
        dq.append(now)
        # Evict old entries
        cutoff = now - self.window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self.max_errors:
            append_security_event(
                "error_spike",
                {
                    "ip": ip,
                    "window_seconds": self.window_seconds,
                    "error_count": len(dq),
                },
            )

    def _looks_like_probe(self, path: str) -> bool:
        lowered = path.lower()
        suspicious_fragments = [
            "wp-admin",
            "wp-login",
            ".git/",
            "/.env",
            "phpmyadmin",
            "admin.php",
            "../",
        ]
        return any(fragment in lowered for fragment in suspicious_fragments)


# ---------------------------------------------------------------------------
# JWT + RBAC helpers
# ---------------------------------------------------------------------------


class TokenData(BaseModel):
    sub: str
    roles: List[str] = []
    exp: Optional[int] = None


def _jwt_secret() -> Optional[str]:
    # Prefer config, then env. If missing, JWT auth is effectively disabled.
    cfg = get_config()
    secret = cfg.get("jwt_secret") or os.environ.get("JWT_SECRET")
    return secret or None


def _jwt_algorithm() -> str:
    return os.environ.get("JWT_ALGO", "HS256")


def create_access_token(subject: str, roles: Optional[List[str]] = None, expires_minutes: int = 60) -> str:
    """Create a signed JWT access token with role claims.

    If no JWT secret is configured, this will raise so callers can surface
    a clear configuration error.
    """

    secret = _jwt_secret()
    if not secret:
        raise RuntimeError("JWT secret not configured; set SWARMZ_JWT_SECRET or JWT_SECRET")

    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "roles": roles or [],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm=_jwt_algorithm())
    # pyjwt may return bytes or str depending on version
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def decode_access_token(token: str) -> TokenData:
    secret = _jwt_secret()
    if not secret:
        raise HTTPException(status_code=401, detail="JWT auth not configured")
    try:
        payload = jwt.decode(token, secret, algorithms=[_jwt_algorithm()])
        return TokenData(**payload)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (DecodeError, InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> Optional[TokenData]:
    """Dependency to retrieve the current user from Authorization header.

    Returns None when no token is provided or JWT is not configured.
    """

    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        return decode_access_token(token)
    except HTTPException:
        # For dependency use we re-raise; callers that want optional auth can
        # catch this explicitly if desired.
        raise


class RoleChecker:
    """FastAPI dependency for simple RBAC checks.

    Usage:
        @app.get("/v1/secure")
        async def secure_route(user = Depends(RoleChecker(["admin"]))):
            ...

    Behavior:
    - If JWT secret is not configured, RBAC is effectively disabled and the
      dependency returns a synthetic user with no roles.
    - If required roles are given and no user / missing roles, 403 is raised.
    """

    def __init__(self, required_roles: Optional[List[str]] = None):
        self.required_roles = required_roles or []

    def __call__(self, user: Optional[TokenData] = Depends(get_current_user)) -> TokenData:
        # If JWT secret is not configured, allow through with a dummy user.
        if not _jwt_secret():
            return TokenData(sub="anonymous", roles=[])

        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")

        if self.required_roles:
            if not any(role in user.roles for role in self.required_roles):
                raise HTTPException(status_code=403, detail="Insufficient role")

        return user


# ---------------------------------------------------------------------------
    # Honeypot utilities and status helpers
# ---------------------------------------------------------------------------


def record_honeypot_hit(request: Request, label: str) -> None:
    """Record a honeypot hit for IDS/alerting purposes."""

    client = request.client.host if request.client else "unknown"
    append_security_event(
        "honeypot_hit",
        {
            "ip": client,
            "path": request.url.path,
            "label": label,
            "method": request.method,
        },
    )


async def honeypot_endpoint(request: Request, label: str = "generic") -> Response:
    """Generic honeypot endpoint.

    Always responds as if the resource does not exist while logging the
    interaction as a potential intrusion probe.
    """

    from fastapi.responses import JSONResponse

    record_honeypot_hit(request, label)
    # Deliberately bland 404 to avoid giving hints.
    return JSONResponse(status_code=404, content={"detail": "Not found"})


def security_status_snapshot(limit_events: int = 50) -> Dict[str, Any]:
    """Summarize current security-related configuration + recent incidents.

    This is deliberately small and cheap so it can be used on a status page
    without impacting the main hot path.
    """

    cfg = get_config()
    status: Dict[str, Any] = {
        "lan_auth_enabled": bool(cfg.get("lan_auth_enabled", True)),
        "rate_limit_per_minute": int(cfg.get("rate_limit_per_minute", 120)),
        "jwt_configured": bool(cfg.get("jwt_secret") or os.environ.get("JWT_SECRET")),
        "security_audit_file": str(_security_log_path()),
    }
    events = read_security_events(limit=limit_events)
    return {"config": status, "recent_events": events}

