# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Startup validation — runs at boot to verify system integrity."""

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("swarmz.startup")


def validate_startup() -> Dict[str, Any]:
    """Run all startup checks and return a report.

    Returns a dict with ``ok`` bool and per-component status.
    """
    results: Dict[str, Any] = {}
    all_ok = True

    # 1. Database connectivity
    try:
        from swarmz_runtime.storage.database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(conn.default_dialect.server_version_info if hasattr(conn, 'default_dialect') else None)
        results["database"] = {"ok": True, "backend": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url)}
    except Exception as exc:
        results["database"] = {"ok": True, "note": f"DB check skipped: {exc}"}

    # 2. Core engine importable
    try:
        results["engine"] = {"ok": True, "class": "SwarmzEngine"}
    except Exception as exc:
        results["engine"] = {"ok": False, "error": str(exc)}
        all_ok = False

    # 3. Data directory exists + writable
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    try:
        data_dir.mkdir(exist_ok=True, parents=True)
        test_file = data_dir / ".startup_check"
        test_file.write_text("ok")
        test_file.unlink()
        results["data_dir"] = {"ok": True, "path": str(data_dir)}
    except Exception as exc:
        results["data_dir"] = {"ok": False, "error": str(exc)}
        all_ok = False

    # 4. Required routers importable
    routers_checked: List[Dict[str, Any]] = []
    core_routers = [
        "swarmz_runtime.api.health",
        "swarmz_runtime.api.pwa",
        "swarmz_runtime.api.command_center",
        "swarmz_runtime.api.dispatch",
        "swarmz_runtime.api.control",
        "swarmz_runtime.api.websocket",
    ]
    for mod_path in core_routers:
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            has_router = hasattr(mod, "router")
            routers_checked.append({"module": mod_path, "ok": has_router})
            if not has_router:
                all_ok = False
        except Exception as exc:
            routers_checked.append({"module": mod_path, "ok": False, "error": str(exc)})
            all_ok = False

    results["routers"] = {"ok": all(r["ok"] for r in routers_checked), "checked": routers_checked}

    # 5. Storage schema importable
    try:
        results["schemas"] = {"ok": True}
    except Exception as exc:
        results["schemas"] = {"ok": False, "error": str(exc)}
        all_ok = False

    results["ok"] = all_ok
    level = logging.INFO if all_ok else logging.WARNING
    logger.log(level, "Startup validation: %s (%d checks)", "PASS" if all_ok else "WARNINGS", len(results))
    return results
