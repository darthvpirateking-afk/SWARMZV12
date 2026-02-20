"""
arena/config.py – Arena configuration with self-check.

Provides load/validate/defaults for arena config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from .schema import ArenaConfig

_DATA_DIR = Path("data")
_CONFIG_PATH = _DATA_DIR / "arena_config.json"

_DEFAULT_CONFIG = ArenaConfig()


def load_config() -> ArenaConfig:
    """Load arena config from disk, or return defaults."""
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH) as f:
                raw = json.load(f)
            return ArenaConfig(**raw)
        except Exception:
            return _DEFAULT_CONFIG
    return _DEFAULT_CONFIG


def save_config(config: ArenaConfig) -> None:
    """Persist arena config to disk."""
    _DATA_DIR.mkdir(exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(config.model_dump(mode="json"), f, indent=2)


def self_check() -> Tuple[bool, List[str]]:
    """Validate arena config and storage files.

    Returns (ok, issues).
    """
    issues: List[str] = []

    # Check config
    try:
        cfg = load_config()
        if cfg.max_candidates < 1 or cfg.max_candidates > 8:
            issues.append(f"max_candidates out of range: {cfg.max_candidates}")
        if cfg.default_num_candidates > cfg.max_candidates:
            issues.append("default_num_candidates exceeds max_candidates")
    except Exception as e:
        issues.append(f"Config load error: {e}")

    # Check storage files exist (or can be created)
    for name in ["arena_runs.jsonl", "arena_candidates.jsonl"]:
        p = _DATA_DIR / name
        if p.exists():
            try:
                with open(p) as f:
                    for line in f:
                        if line.strip():
                            json.loads(line)
            except json.JSONDecodeError:
                issues.append(f"{name} has malformed entries")
            except OSError as e:
                issues.append(f"{name} read error: {e}")

    return (len(issues) == 0, issues)
