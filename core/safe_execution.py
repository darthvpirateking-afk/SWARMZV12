# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/safe_execution.py â€” PREPAREâ€‘ONLY execution wrapper for SWARMZ.

All AIâ€‘generated actions are written as proposals to prepared_actions/.
NOTHING is executed automatically.  The operator reviews and runs manually.

Functions:
  prepare_action(category, mission_id, action_data) â†’ path to proposal dir
  list_pending(category)  â†’ list of pending proposals
  mark_executed(path)     â†’ stamp a proposal as executed by operator
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.time_source import now
from core.atomic import atomic_write_json

ROOT = Path(__file__).resolve().parent.parent
PREPARED_DIR = ROOT / "prepared_actions"

# Valid categories â€” each maps to a subdirectory
CATEGORIES = {"messages", "schedules", "commands", "purchases", "preemptive"}


def _ensure_dirs() -> None:
    for cat in CATEGORIES:
        (PREPARED_DIR / cat).mkdir(parents=True, exist_ok=True)


def prepare_action(
    category: str,
    mission_id: str,
    action_data: Dict[str, Any],
    *,
    reason: str = "",
    expected_effect: Optional[Dict[str, Any]] = None,
    risk_level: str = "low",
) -> str:
    """Write a prepared action proposal.  Returns path to the proposal directory.

    Creates:
      prepared_actions/<category>/<mission_id>/proposal.json
      prepared_actions/<category>/<mission_id>/reason.txt
      prepared_actions/<category>/<mission_id>/expected_effect.json
    """
    if category not in CATEGORIES:
        category = "commands"  # safe default, don't crash

    _ensure_dirs()
    out_dir = PREPARED_DIR / category / mission_id
    out_dir.mkdir(parents=True, exist_ok=True)

    proposal = {
        "mission_id": mission_id,
        "category": category,
        "action": action_data,
        "risk_level": risk_level,
        "prepared_at": now(),
        "executed": False,
    }
    atomic_write_json(out_dir / "proposal.json", proposal)

    if reason:
        (out_dir / "reason.txt").write_text(reason, encoding="utf-8")

    if expected_effect:
        atomic_write_json(out_dir / "expected_effect.json", expected_effect)

    return str(out_dir)


def list_pending(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List pending (not yet executed) proposals.

    If *category* is None, lists across all categories.
    """
    _ensure_dirs()
    results: List[Dict[str, Any]] = []
    cats = [category] if category and category in CATEGORIES else list(CATEGORIES)

    for cat in cats:
        cat_dir = PREPARED_DIR / cat
        if not cat_dir.exists():
            continue
        for d in sorted(cat_dir.iterdir()):
            if not d.is_dir():
                continue
            proposal_file = d / "proposal.json"
            if not proposal_file.exists():
                continue
            try:
                data = json.loads(proposal_file.read_text(encoding="utf-8"))
                if not data.get("executed", False):
                    results.append(data)
            except Exception:
                pass
    return results


def mark_executed(proposal_dir: str) -> bool:
    """Stamp a prepared action as executed by the operator.

    Returns True if successfully stamped, False otherwise.
    """
    p = Path(proposal_dir) / "proposal.json"
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["executed"] = True
        data["executed_at"] = now()
        atomic_write_json(p, data)
        return True
    except Exception:
        return False


def count_pending() -> Dict[str, int]:
    """Count pending proposals per category."""
    _ensure_dirs()
    counts: Dict[str, int] = {}
    for cat in CATEGORIES:
        pending = list_pending(cat)
        counts[cat] = len(pending)
    return counts

