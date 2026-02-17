# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
FastAPI surface for the SWARMZ Shell Registry.

Call register_shell_api(app) from server.py to mount:
- GET /v1/shell/modules
- POST /v1/shell/self_check

All endpoints are read-only and operate over the registry.
"""

from fastapi import FastAPI
from core.shell_registry import list_modules, self_check


def register_shell_api(app: FastAPI) -> None:
    """Mount /v1/shell/* endpoints on the given FastAPI app."""

    @app.get("/v1/shell/modules")
    async def shell_modules() -> dict:
        try:
            modules = list_modules()
            return {"ok": True, "modules": modules}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @app.post("/v1/shell/self_check")
    async def shell_self_check() -> dict:
        try:
            result = self_check()
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
