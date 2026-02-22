# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/config_loader.py â€” Load config/runtime.json with envâ€‘var overrides.

Single source of truth for all runtime configuration.
Never crashes â€” returns safe defaults if files are missing/corrupt.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "runtime.json"

_cache: Optional[Dict[str, Any]] = None
_cache_mtime: float = 0.0


def _invalidate() -> None:
    """Force next load() to reâ€‘read from disk (for tests)."""
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = 0.0


def load(*, force: bool = False) -> Dict[str, Any]:
    """Return merged config (file + env overrides).  Cached by mtime."""
    global _cache, _cache_mtime

    if not force and _cache is not None:
        try:
            mtime = CONFIG_FILE.stat().st_mtime if CONFIG_FILE.exists() else 0.0
            if mtime == _cache_mtime:
                return dict(_cache)
        except Exception:
            pass

    raw: Dict[str, Any] = {}
    if CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw = {}

    try:
        _cache_mtime = CONFIG_FILE.stat().st_mtime if CONFIG_FILE.exists() else 0.0
    except Exception:
        _cache_mtime = 0.0

    # â”€â”€ env overrides â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if os.environ.get("PORT"):
        try:
            raw["port"] = int(os.environ["PORT"])
        except ValueError:
            pass
    if os.environ.get("HOST"):
        raw["bind"] = os.environ["HOST"]
    if os.environ.get("OFFLINE_MODE", "").strip().lower() in ("1", "true", "yes"):
        raw["offlineMode"] = True
    if os.environ.get("MODEL_PROVIDER"):
        raw.setdefault("models", {})["provider"] = os.environ["MODEL_PROVIDER"]

    _cache = dict(raw)
    return dict(raw)


def get(key: str, default: Any = None) -> Any:
    """Shorthand: ``config_loader.get("port", 8012)``."""
    return load().get(key, default)


def models() -> Dict[str, Any]:
    """Return the ``models`` section."""
    return dict(load().get("models", {}))


def companion() -> Dict[str, Any]:
    """Return the ``companion`` section."""
    return dict(load().get("companion", {}))


def is_offline() -> bool:
    """True when OFFLINE_MODE is active (env or config)."""
    env = os.environ.get("OFFLINE_MODE", "").strip().lower()
    if env in ("1", "true", "yes"):
        return True
    return bool(load().get("offlineMode", False))
