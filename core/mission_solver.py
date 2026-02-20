# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Mission Solver â€” AI-powered mission planning via model_router.

Produces PLAN + PREPARED_ACTIONS + EVIDENCE for a mission.
Writes outputs to prepared_actions/<mission_id>/.
Falls back gracefully when offline or no API key.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
PREPARED_DIR = ROOT / "prepared_actions"
PROMPT_DIR = Path(__file__).resolve().parent / "prompt_templates"

from core.model_router import call as model_call, is_offline, record_call
from core.companion import load_memory, _build_context_block, _audit_model_call

# lazy write_jsonl
try:
    import sys
    sys.path.insert(0, str(ROOT))
    from jsonl_utils import write_jsonl
except ImportError:
    def write_jsonl(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")

AUDIT_FILE = ROOT / "data" / "audit.jsonl"


def _load_solver_prompt() -> str:
    p = PROMPT_DIR / "mission_solver.txt"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "You are the SWARMZ mission solver. Produce PLAN, PREPARED_ACTIONS, EVIDENCE."


def solve(mission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solve a mission via AI (or stub when offline).

    Returns:
        {
            "ok": True/False,
            "plan": str,
            "prepared_actions_dir": str,
            "source": "ai"|"offline_stub"|"rule_stub",
            "provider"?: str,
            "model"?: str,
            "latencyMs"?: int,
            "error"?: str
        }
    """
    mission_id = mission.get("mission_id", "unknown")
    intent = mission.get("intent", mission.get("goal", "unknown"))
    spec = mission.get("spec", {})
    now = datetime.now(timezone.utc).isoformat()

    # Ensure output dir
    action_dir = PREPARED_DIR / mission_id
    action_dir.mkdir(parents=True, exist_ok=True)

    # â”€â”€ Offline stub â”€â”€
    if is_offline():
        plan = _offline_stub(intent, spec)
        _write_plan(action_dir, plan, "offline_stub")
        return {"ok": True, "plan": plan, "prepared_actions_dir": str(action_dir), "source": "offline_stub"}

    # â”€â”€ Check API key â”€â”€
    from core.model_router import get_model_config, _get_api_key
    cfg = get_model_config()
    prov = cfg.get("provider", "anthropic")
    prov_cfg = cfg.get(prov, {})
    has_key = bool(_get_api_key(prov_cfg))

    if not has_key:
        plan = _offline_stub(intent, spec)
        _write_plan(action_dir, plan, "rule_stub")
        return {"ok": True, "plan": plan, "prepared_actions_dir": str(action_dir), "source": "rule_stub"}

    # â”€â”€ AI call â”€â”€
    system = _load_solver_prompt()
    mem = load_memory()
    context = _build_context_block(mem)

    user_msg = (
        f"MISSION ID: {mission_id}\n"
        f"INTENT: {intent}\n"
        f"SPEC: {json.dumps(spec)}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"Produce PLAN, PREPARED_ACTIONS, and EVIDENCE."
    )

    result = model_call([{"role": "user", "content": user_msg}], system=system)
    record_call(now, result.get("error"))
    _audit_model_call(now, result)

    if result.get("ok"):
        plan_text = result.get("text", "")
        _write_plan(action_dir, plan_text, "ai")
        return {
            "ok": True,
            "plan": plan_text,
            "prepared_actions_dir": str(action_dir),
            "source": "ai",
            "provider": result.get("provider"),
            "model": result.get("model"),
            "latencyMs": result.get("latencyMs"),
        }
    else:
        # AI failed â€” fall back to stub
        plan = _offline_stub(intent, spec) + f"\n[AI error: {result.get('error', '?')[:100]}]"
        _write_plan(action_dir, plan, "rule_stub_fallback")
        return {
            "ok": True,
            "plan": plan,
            "prepared_actions_dir": str(action_dir),
            "source": "rule_stub_fallback",
            "error": result.get("error"),
        }


def _offline_stub(intent: str, spec: Dict[str, Any]) -> str:
    """Deterministic stub plan when AI is not available."""
    return (
        f"## PLAN (offline stub)\n"
        f"1. Received intent: {intent}\n"
        f"2. Spec: {json.dumps(spec)}\n"
        f"3. No AI model available â€” stub plan generated.\n\n"
        f"## PREPARED_ACTIONS\n"
        f'[{{"step": 1, "action": "review intent manually", "type": "analysis", "reversible": true}}]\n\n'
        f"## EVIDENCE\n"
        f"- Offline mode or no API key configured.\n"
    )


def _write_plan(action_dir: Path, plan_text: str, source: str) -> None:
    """Write plan.md and metadata.json to the prepared_actions dir."""
    (action_dir / "plan.md").write_text(plan_text, encoding="utf-8")
    meta = {
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (action_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

