import time
from pathlib import Path
import json

PATCHPACK_DIR = Path("patchpacks")

class PatchpackEngine:
    def __init__(self):
        PATCHPACK_DIR.mkdir(exist_ok=True)

    def create(self, payload: dict):
        ts = int(time.time())
        file = PATCHPACK_DIR / f"patch_{ts}.json"
        with open(file, "w") as f:
            json.dump(payload, f, indent=2)
        return {"created": file.name, "timestamp": ts}

    def list(self):
        return sorted([f.name for f in PATCHPACK_DIR.iterdir()])

    def load(self, name: str):
        file = PATCHPACK_DIR / name
        if not file.exists():
            return {"error": "not_found"}
        return json.loads(file.read_text())