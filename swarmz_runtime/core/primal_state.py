from pathlib import Path
import json

_SLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "primal_state_slate.json"
)


def load_primal_state_slate() -> dict:
    with _SLATE_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload["PRIMAL_STATE_SLATE"]
