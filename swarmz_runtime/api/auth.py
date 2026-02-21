# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Authentication endpoints — JWT login and user info."""

import os

from fastapi import APIRouter, HTTPException, Request

from swarmz_runtime.api.models import LoginRequest

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login")
async def auth_login(payload: LoginRequest, request: Request):
    """Issue a JWT for operator usage when correctly authenticated."""
    from addons.security import (
        append_security_event,
        create_access_token,
    )

    expected_key = os.environ.get("OPERATOR_KEY") or ""
    if (
        payload.username != "operator"
        or not expected_key
        or payload.password != expected_key
    ):
        append_security_event(
            "login_failed",
            {
                "ip": request.client.host if request.client else "unknown",
                "username": payload.username,
            },
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        token = create_access_token(subject="operator", roles=["admin"])
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    append_security_event(
        "login_success",
        {
            "ip": request.client.host if request.client else "unknown",
            "username": payload.username,
            "roles": ["admin"],
        },
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/operator/auth/status", tags=["operator-auth"])
async def operator_auth_status(request: Request):
    """Operator auth status — used by OperatorAuthPage cockpit."""
    import os
    has_key = bool(os.environ.get("OPERATOR_KEY"))
    # Check for bearer token
    auth_header = request.headers.get("Authorization", "")
    authenticated = False
    if auth_header.startswith("Bearer "):
        try:
            from addons.security import get_current_user
            user = await get_current_user(request)
            authenticated = user is not None
        except Exception:
            pass
    return {
        "ok": True,
        "configured": has_key,
        "authenticated": authenticated,
        "method": "operator_key" if has_key else "none",
    }


@router.post("/operator/auth/verify", tags=["operator-auth"])
async def operator_auth_verify(request: Request):
    """Verify an operator key — used by OperatorAuthPage cockpit."""
    import os
    try:
        body = await request.json()
    except Exception:
        body = {}
    provided_key = body.get("operator_key", "").strip()
    expected_key = os.environ.get("OPERATOR_KEY", "")
    if not expected_key:
        return {"ok": True, "valid": True, "message": "No key configured — open access"}
    valid = provided_key == expected_key
    return {"ok": True, "valid": valid, "message": "Verified" if valid else "Invalid key"}


@router.get("/me")
async def auth_me(request: Request):
    """Return current user information if a valid JWT is provided."""
    from addons.security import get_current_user

    user = await get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"sub": user.sub, "roles": user.roles}
