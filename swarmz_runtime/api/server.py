# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Unified SWARMZ API server — single create_app() entry point.

All routes are organised into dedicated router modules. This file is
responsible only for:
  1. Creating the FastAPI application
  2. Configuring middleware (CORS, security)
  3. Registering all routers
  4. Initialising the engine + orchestrator via lifespan
"""

import logging
import os
import json
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("swarmz.server")

# ---- directory constants (no heavy init at import time) ----
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data"
UI_DIR = ROOT_DIR / "web_ui"
DATA_DIR.mkdir(exist_ok=True, parents=True)
START_TIME = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Runtime config helpers
# ---------------------------------------------------------------------------
def _load_runtime_config() -> Dict[str, Any]:
    cfg_path = ROOT_DIR / "config" / "runtime.json"
    if not cfg_path.exists():
        return {}
    try:
        raw = json.loads(cfg_path.read_text())
    except Exception:
        return {}
    cfg: Dict[str, Any] = {}
    if isinstance(raw, dict):
        cfg.update(raw)
        api_base = (
            raw.get("apiBaseUrl") or raw.get("api_base") or raw.get("api_base_url")
        )
        ui_base = raw.get("uiBaseUrl") or raw.get("ui_base") or raw.get("ui_base_url")
        if api_base:
            cfg["apiBaseUrl"] = api_base
        if ui_base:
            cfg["uiBaseUrl"] = ui_base
        if "bind" not in cfg and raw.get("host"):
            cfg["bind"] = raw.get("host")
        if "port" not in cfg and raw.get("api_port"):
            cfg["port"] = raw.get("api_port")
        if "offlineMode" not in cfg and "offline_mode" in raw:
            cfg["offlineMode"] = raw.get("offline_mode")
    return cfg


def _resolve_offline_mode(cfg: Dict[str, Any]) -> bool:
    env_val = os.getenv("OFFLINE_MODE")
    if env_val is not None and env_val not in {"", "0", "false", "False"}:
        return True
    if env_val is not None and env_val in {"0", "false", "False"}:
        return False
    return bool(cfg.get("offlineMode"))


def _load_operator_pin() -> Dict[str, Any]:
    """Resolve operator PIN (env → config → file → generate)."""
    pin_source = "env"
    pin = os.getenv("SWARMZ_OPERATOR_PIN")
    config_path = DATA_DIR / "config.json"
    pin_file = DATA_DIR / "operator_pin.txt"

    if not pin and config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            if cfg.get("operator_pin"):
                pin = str(cfg["operator_pin"]).strip()
                pin_source = "config"
        except Exception:
            pin = None

    if not pin and pin_file.exists():
        try:
            pin = pin_file.read_text().strip()
            pin_source = "file"
        except Exception:
            pin = None

    generated = False
    if not pin:
        pin = "".join(secrets.choice("0123456789") for _ in range(6))
        pin_source = "generated"
        generated = True
        pin_file.write_text(pin)
        logger.info("Generated operator PIN; saved to %s", pin_file)

    return {"pin": pin, "source": pin_source, "file": str(pin_file), "generated": generated}


# ---------------------------------------------------------------------------
# Lifespan: engine + orchestrator init
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # startup ---------------------------------------------------------------
    from swarmz_runtime.core.engine import SwarmzEngine
    from swarmz_runtime.core.system_primitives import SystemPrimitivesRuntime

    runtime_cfg = _load_runtime_config()
    offline_mode = _resolve_offline_mode(runtime_cfg)
    pin_info = _load_operator_pin()

    engine = SwarmzEngine(data_dir=str(DATA_DIR))
    engine.offline_mode = offline_mode
    engine.operator_key = pin_info["pin"]
    primitives = SystemPrimitivesRuntime(ROOT_DIR)

    app.state.engine = engine
    app.state.primitives = primitives
    app.state.operator_pin_source = pin_info
    app.state.runtime_cfg = runtime_cfg
    app.state.offline_mode = offline_mode

    # Wire engine into sub-modules that need it
    try:
        from swarmz_runtime.api import system, admin, ecosystem
        from swarmz_runtime.api import arena as arena_api

        system.get_engine = lambda: engine
        admin.get_engine = lambda: engine
        ecosystem.set_engine_provider(lambda: engine)
        arena_api.get_engine = lambda: engine
    except Exception as exc:
        logger.warning("Engine wiring skipped: %s", exc)

    # Build orchestrator
    try:
        from kernel_runtime.orchestrator import SwarmzOrchestrator

        app.state.orchestrator = SwarmzOrchestrator()
    except Exception as exc:
        logger.warning("Orchestrator not loaded: %s", exc)
        app.state.orchestrator = None

    logger.info(
        "SWARMZ started — offline=%s, pin_source=%s",
        offline_mode,
        pin_info["source"],
    )

    yield  # ---- application running ----

    # shutdown (optional cleanup) -------------------------------------------


# ---------------------------------------------------------------------------
# Router collection (with safe imports)
# ---------------------------------------------------------------------------
def _safe_import_router(module_path: str, attr: str = "router"):
    """Import a router, returning None on failure so the app still boots."""
    try:
        import importlib

        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    except Exception as exc:
        logger.warning("Router %s not loaded: %s", module_path, exc)
        return None


def create_app() -> FastAPI:
    """Create and return the unified FastAPI application."""

    cors_env = os.environ.get("CORS_ALLOW_ORIGINS", "")
    cors_origins = (
        [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env else ["*"]
    )

    app = FastAPI(
        title="SWARMZ",
        description="Operator-Sovereign Mission Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middlewares (optional — safe-import)
    try:
        from addons.rate_limiter import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)
    except Exception as exc:
        logger.warning("RateLimitMiddleware not loaded: %s", exc)
    try:
        from addons.auth_gate import LANAuthMiddleware
        app.add_middleware(LANAuthMiddleware)
    except Exception as exc:
        logger.warning("LANAuthMiddleware not loaded: %s", exc)

    # ------------------------------------------------------------------
    # CORE routers (extracted modules — always available)
    # ------------------------------------------------------------------
    from swarmz_runtime.api.health import router as health_router
    from swarmz_runtime.api.pwa import router as pwa_router
    from swarmz_runtime.api.command_center import router as command_center_router
    from swarmz_runtime.api.dispatch import router as dispatch_router
    from swarmz_runtime.api.control import router as control_router
    from swarmz_runtime.api.websocket import router as ws_router

    app.include_router(health_router)
    app.include_router(pwa_router)
    app.include_router(command_center_router)
    app.include_router(dispatch_router)
    app.include_router(control_router)
    app.include_router(ws_router)

    # Auth (depends on addons.security — optional)
    auth_router = _safe_import_router("swarmz_runtime.api.auth")
    if auth_router:
        app.include_router(auth_router)

    # Galileo harness (optional)
    galileo_router = _safe_import_router("swarmz_runtime.api.galileo")
    if galileo_router:
        app.include_router(galileo_router)

    # ------------------------------------------------------------------
    # RUNTIME routers (swarmz_runtime.api.*)
    # ------------------------------------------------------------------
    _runtime_routers = [
        ("swarmz_runtime.api.missions", "/v1/missions", "missions"),
        ("swarmz_runtime.api.system", "/v1/system", "system"),
        ("swarmz_runtime.api.admin", "/v1/admin", "admin"),
        ("swarmz_runtime.api.arena", "/v1/arena", "arena"),
        ("swarmz_runtime.api.factory_routes", "/v1/factory", "factory"),
        ("swarmz_runtime.api.meta_routes", "/v1/meta", "meta"),
        ("swarmz_runtime.api.operational_routes", "/v1", "operational"),
        ("swarmz_runtime.api.operator_ecosystem_routes", "/v1", "operator-os"),
        ("swarmz_runtime.api.federation_routes", "/v1", "federation"),
        ("swarmz_runtime.api.charter_routes", "/v1", "charter"),
        ("swarmz_runtime.api.fusion_routes", "/v1", "fusion"),
        ("swarmz_runtime.api.primal_routes", "/v1", "primal"),
        ("swarmz_runtime.api.template_sync_routes", "/v1", "template-sync"),
        ("swarmz_runtime.api.system_primitives_routes", "/v1", "system-primitives"),
        ("swarmz_runtime.api.system_control", "/v1/system", "system-control"),
        ("swarmz_runtime.api.mission_lifecycle", "/v1/missions", "mission-lifecycle"),
    ]
    for mod_path, prefix, tag in _runtime_routers:
        r = _safe_import_router(mod_path)
        if r:
            app.include_router(r, prefix=prefix, tags=[tag])

    # ------------------------------------------------------------------
    # ADDON routers (from swarmz_server.py + server.py try/except blocks)
    # ------------------------------------------------------------------
    _addon_routers = [
        ("addons.api.addons_router", "/v1/addons", "addons"),
        ("addons.api.guardrails_router", "/v1/guardrails", "guardrails"),
        ("core.nexusmon_router", "/v1/nexusmon", "nexusmon"),
        # addons.api.operator_auth_router — file does not exist, skip
    ]
    for mod_path, prefix, tag in _addon_routers:
        r = _safe_import_router(mod_path)
        if r:
            app.include_router(r, prefix=prefix, tags=[tag])

    # ------------------------------------------------------------------
    # FEATURE routers (may not exist yet — safe import)
    # ------------------------------------------------------------------
    _feature_routers = [
        ("swarmz_runtime.api.bootstrap_routes", "/v1/bootstrap", "bootstrap"),
        ("swarmz_runtime.api.foundation_routes", "/v1/api", "foundation"),
        ("swarmz_runtime.api.database_routes", "/v1/db", "database"),
        # companion routes handled by control.py — companion_state.py has no router
        ("swarmz_runtime.api.build_milestones_routes", "/v1/build/milestones", "build-milestones"),
    ]
    for mod_path, prefix, tag in _feature_routers:
        r = _safe_import_router(mod_path)
        if r:
            app.include_router(r, prefix=prefix, tags=[tag])

    # ------------------------------------------------------------------
    # Optional module registrations (trials, hologram, etc.)
    # ------------------------------------------------------------------
    _optional_modules = [
        "core.trials",
        "core.hologram",
        "core.awareness_model",
        "core.forensics",
        "core.shell_registry",
        "core.market_lab",
        "core.zapier_bridge",
    ]
    for mod_path in _optional_modules:
        try:
            import importlib

            mod = importlib.import_module(mod_path)
            if hasattr(mod, "register_api"):
                mod.register_api(app)
            elif hasattr(mod, "router"):
                app.include_router(mod.router)
        except Exception:
            pass  # Optional modules may not exist

    # ------------------------------------------------------------------
    # Static file mounts
    # ------------------------------------------------------------------
    # Frontend build output (Vite dist)
    frontend_dist = ROOT_DIR / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/app", StaticFiles(directory=str(frontend_dist), html=True), name="cockpit")

    # Legacy web_ui
    if UI_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    return app


# Create the default app instance (used by `uvicorn server:app`)
app = create_app()
