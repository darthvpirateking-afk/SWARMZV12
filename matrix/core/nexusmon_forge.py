# SWARMZ NEXUSMON — The Forge: Autonomous Module Synthesis
# ─────────────────────────────────────────────────────────
import json
import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def _get_forge_dir() -> Path:
    p = Path("c:/Users/Gaming PC/Desktop/swarmz/forge")
    p.mkdir(parents=True, exist_ok=True)
    return p

class Forge:
    """Autonomous module synthesis and hot-patching system."""
    
    def __init__(self, nerve_instance):
        self.nerve = nerve_instance
        self.modules = {} # module_id -> imported_module

    def forge_module(self, module_id: str, code: str) -> bool:
        """Saves a new Python module to the forge directory and imports it."""
        try:
            path = _get_forge_dir() / f"{module_id}.py"
            path.write_text(code, encoding="utf-8")
            
            # Hot-import (or reload)
            sys.path.append(str(_get_forge_dir()))
            if module_id in sys.modules:
                importlib.reload(sys.modules[module_id])
            else:
                importlib.import_module(module_id)
            
            self.nerve.fire("FORGE", "SYNERGY", payload={"module": module_id, "status": "SYNTHESIZED"}, intensity=3.0)
            logger.info(f"[FORGE] Module '{module_id}' synthesized and active.")
            return True
        except Exception as e:
            logger.error(f"[FORGE] Synthesis failed for '{module_id}': {e}")
            self.nerve.fire("FORGE", "STRESS", payload={"error": str(e)}, intensity=2.0)
            return False

    def list_modules(self) -> Dict[str, Any]:
        """Lists all files in the forge directory."""
        return {f.stem: str(f) for f in _get_forge_dir().glob("*.py")}

def integrate_forge(nerve_instance) -> Forge:
    return Forge(nerve_instance)
