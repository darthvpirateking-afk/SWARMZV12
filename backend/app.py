"""
Canonical backend app wrapper for NEXUSMON v0.1.

This module provides a stable import target for ASGI runners:
- `create_app()` for factory-based startup
- `app` for direct ASGI startup

Canonical runtime surface: `swarmz_server.py`
"""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    from swarmz_server import app as canonical_app

    return canonical_app


app = create_app()
