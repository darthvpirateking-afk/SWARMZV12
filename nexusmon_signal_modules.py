# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
NEXUSMON Signal Modules
───────────────────────
Scaffold registry and dial controls for advanced capability lanes:
- all-language interaction
- computational vision / feature extraction
- real-time visual pattern interpretation
- augmented reality overlays
- shape-shift expression modes
- animal-voice sound layer
- instant LLM steering dials
- bio aura dial telemetry
- particle simulation + strange attractors
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field


_STATE_FILE = "signal_modules_state.json"


router = APIRouter(prefix="/v1/nexusmon/signal", tags=["signal-modules"])


class DialPatch(BaseModel):
    llm_steer: Optional[float] = Field(None, ge=0.0, le=1.0)
    bio_aura: Optional[float] = Field(None, ge=0.0, le=1.0)
    particle_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    strange_attractor_gain: Optional[float] = Field(None, ge=0.0, le=1.0)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _data_dir() -> Path:
    db = os.environ.get("DATABASE_URL", "data/nexusmon.db")
    directory = Path(db).parent
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _state_path() -> Path:
    return _data_dir() / _STATE_FILE


def _default_modules() -> Dict[str, Dict[str, Any]]:
    return {
        "all_language": {
            "title": "All-Language Interaction",
            "description": "Multilingual mission input/output and cross-lingual operator context.",
            "capabilities": ["translate", "cross_lingual_memory", "multilingual_io"],
            "status": "scaffolded",
        },
        "computational_vision": {
            "title": "Computational Vision",
            "description": "Visual analysis, feature extraction, and frame-level interpretation.",
            "capabilities": ["feature_extraction", "scene_parse", "visual_embeddings"],
            "status": "scaffolded",
        },
        "realtime_pattern_interpreter": {
            "title": "Realtime Visual Pattern Interpreter",
            "description": "Live stream pattern tracking and anomaly highlighting.",
            "capabilities": ["stream_inference", "pattern_tracking", "anomaly_flags"],
            "status": "scaffolded",
        },
        "augmented_reality": {
            "title": "Augmented Reality Overlays",
            "description": "Operator overlays for mission context and visual guidance.",
            "capabilities": ["ar_overlay", "hud_annotations", "spatial_labels"],
            "status": "scaffolded",
        },
        "shape_shift_modes": {
            "title": "Shape-Shift Expression Modes",
            "description": "Adaptive presentation modes for persona and visual shell behavior.",
            "capabilities": ["adaptive_persona_shell", "mode_morph", "avatar_shift"],
            "status": "scaffolded",
        },
        "animal_voice": {
            "title": "Animal-Voice Sound Layer",
            "description": "Synthetic expressive sound layer mapped to state and event intent.",
            "capabilities": ["voice_profile_map", "state_to_sound", "event_audio_cues"],
            "status": "scaffolded",
        },
        "instant_llm_dials": {
            "title": "Instant LLM Dials",
            "description": "Live steering controls for response style, aggression, and reasoning depth.",
            "capabilities": ["live_model_steer", "response_style_dial", "reasoning_depth_dial"],
            "status": "scaffolded",
        },
        "bio_aura_dial": {
            "title": "Bio Aura Dial",
            "description": "State telemetry dial for bio-inspired signal presentation and fusion displays.",
            "capabilities": ["aura_telemetry", "state_projection", "fusion_signal"],
            "status": "scaffolded",
        },
        "particle_attractors": {
            "title": "Particle + Strange Attractors",
            "description": "Particle-field simulation and attractor mapping for dynamic behavior surfaces.",
            "capabilities": ["particle_sim", "attractor_map", "chaotic_field_render"],
            "status": "scaffolded",
        },
    }


def _default_dials() -> Dict[str, float]:
    return {
        "llm_steer": 0.5,
        "bio_aura": 0.5,
        "particle_intensity": 0.5,
        "strange_attractor_gain": 0.5,
    }


def _load_state() -> Dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return {
            "modules": _default_modules(),
            "dials": _default_dials(),
            "updated_at": _utc(),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        modules = payload.get("modules") or _default_modules()
        dials = payload.get("dials") or _default_dials()
        return {
            "modules": modules,
            "dials": dials,
            "updated_at": payload.get("updated_at") or _utc(),
        }
    except Exception:
        return {
            "modules": _default_modules(),
            "dials": _default_dials(),
            "updated_at": _utc(),
        }


def _save_state(state: Dict[str, Any]) -> None:
    state["updated_at"] = _utc()
    _state_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def _with_flags(modules: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for module_id, entry in modules.items():
        env_key = f"NEXUSMON_SIGNAL_{module_id.upper()}_ENABLED"
        enabled_raw = os.environ.get(env_key, "1").strip().lower()
        enabled = enabled_raw in {"1", "true", "yes", "on"}
        out[module_id] = {
            **entry,
            "module_id": module_id,
            "enabled": enabled,
            "flag_env": env_key,
        }
    return out


@router.get("/modules")
def list_signal_modules() -> Dict[str, Any]:
    state = _load_state()
    modules = _with_flags(state.get("modules", {}))
    return {
        "ok": True,
        "count": len(modules),
        "modules": modules,
        "dials": state.get("dials", {}),
        "updated_at": state.get("updated_at"),
    }


@router.get("/modules/{module_id}")
def get_signal_module(module_id: str) -> Dict[str, Any]:
    state = _load_state()
    modules = _with_flags(state.get("modules", {}))
    module = modules.get(module_id)
    if not module:
        raise HTTPException(status_code=404, detail=f"Unknown signal module: {module_id}")
    return {
        "ok": True,
        "module": module,
        "dials": state.get("dials", {}),
        "updated_at": state.get("updated_at"),
    }


@router.post("/dials")
def patch_signal_dials(payload: DialPatch) -> Dict[str, Any]:
    state = _load_state()
    dials = state.get("dials", _default_dials())
    patch = payload.model_dump(exclude_none=True)
    dials.update(patch)
    state["dials"] = dials
    _save_state(state)
    return {
        "ok": True,
        "dials": dials,
        "updated_at": state.get("updated_at"),
    }


@router.get("/status")
def signal_status() -> Dict[str, Any]:
    state = _load_state()
    modules = _with_flags(state.get("modules", {}))
    enabled_count = sum(1 for m in modules.values() if m.get("enabled"))
    return {
        "ok": True,
        "status": "online",
        "total_modules": len(modules),
        "enabled_modules": enabled_count,
        "dials": state.get("dials", {}),
        "updated_at": state.get("updated_at"),
    }


def fuse_signal_modules(app: FastAPI) -> None:
    app.include_router(router)
