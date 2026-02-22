# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Evolution Tree — all possible forms, modes, transitions, and conditions.

Nodes: forms/modes the system can occupy.
Edges: valid evolution paths between nodes.
Conditions: requirements to traverse an edge.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
TREE_FILE = ROOT / "data" / "evolution_tree.json"

# ──────────────────────────────────────────────────────────────
# DEFAULT TREE
# ──────────────────────────────────────────────────────────────

DEFAULT_TREE: Dict[str, Any] = {
    "version": 1,
    "nodes": [
        {
            "id": "egg",
            "label": "Egg",
            "type": "form",
            "tier": 0,
            "traits": ["dormant", "potential"],
            "description": "Initial state. No capabilities yet.",
        },
        {
            "id": "core",
            "label": "Core",
            "type": "form",
            "tier": 1,
            "traits": ["stable", "balanced", "observant"],
            "description": "Foundational form. Basic capabilities active.",
        },
        {
            "id": "cosmos",
            "label": "Cosmos",
            "type": "form",
            "tier": 2,
            "traits": ["exploratory", "wide-scan", "networked"],
            "description": "Exploration form. Enhanced scanning and networking.",
        },
        {
            "id": "forge",
            "label": "Forge",
            "type": "form",
            "tier": 2,
            "traits": ["builder", "precision", "creative"],
            "description": "Build form. Enhanced construction and planning.",
        },
        {
            "id": "void",
            "label": "Void",
            "type": "form",
            "tier": 2,
            "traits": ["analytical", "deep-scan", "pattern-recognition"],
            "description": "Analysis form. Enhanced pattern detection and insight.",
        },
        {
            "id": "sovereign",
            "label": "Sovereign",
            "type": "form",
            "tier": 3,
            "traits": ["autonomous", "self-governing", "resilient", "adaptive"],
            "description": "Autonomous form. Full self-governance and adaptation.",
        },
        {
            "id": "nexus",
            "label": "Nexus",
            "type": "form",
            "tier": 3,
            "traits": ["connected", "orchestrating", "multi-modal"],
            "description": "Orchestration form. Multi-worker, multi-mission coordination.",
        },
    ],
    "edges": [
        {
            "from": "egg",
            "to": "core",
            "conditions": {"minMissions": 1, "operatorApproval": False},
            "cost": {"energy": 0, "cooldownSeconds": 0},
        },
        {
            "from": "core",
            "to": "cosmos",
            "conditions": {"minMissions": 5, "minSuccessRate": 50, "minSwarmTier": 1, "operatorApproval": True},
            "cost": {"energy": 10, "cooldownSeconds": 60},
        },
        {
            "from": "core",
            "to": "forge",
            "conditions": {"minMissions": 5, "minSuccessRate": 50, "requiredCapabilities": ["build"], "operatorApproval": True},
            "cost": {"energy": 10, "cooldownSeconds": 60},
        },
        {
            "from": "core",
            "to": "void",
            "conditions": {"minMissions": 5, "minSuccessRate": 60, "requiredCapabilities": ["analyze"], "operatorApproval": True},
            "cost": {"energy": 15, "cooldownSeconds": 120},
        },
        {
            "from": "cosmos",
            "to": "sovereign",
            "conditions": {"minMissions": 20, "minSuccessRate": 70, "minSwarmTier": 2, "requiredMissions": ["diagnose system"], "operatorApproval": True},
            "cost": {"energy": 50, "cooldownSeconds": 300},
        },
        {
            "from": "forge",
            "to": "sovereign",
            "conditions": {"minMissions": 20, "minSuccessRate": 70, "minSwarmTier": 2, "operatorApproval": True},
            "cost": {"energy": 50, "cooldownSeconds": 300},
        },
        {
            "from": "void",
            "to": "nexus",
            "conditions": {"minMissions": 25, "minSuccessRate": 75, "minSwarmTier": 2, "operatorApproval": True},
            "cost": {"energy": 60, "cooldownSeconds": 300},
        },
        {
            "from": "cosmos",
            "to": "nexus",
            "conditions": {"minMissions": 25, "minSuccessRate": 75, "minSwarmTier": 2, "operatorApproval": True},
            "cost": {"energy": 60, "cooldownSeconds": 300},
        },
        # Cross-tier 2 lateral moves
        {
            "from": "cosmos",
            "to": "forge",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
        {
            "from": "cosmos",
            "to": "void",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
        {
            "from": "forge",
            "to": "cosmos",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
        {
            "from": "forge",
            "to": "void",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
        {
            "from": "void",
            "to": "cosmos",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
        {
            "from": "void",
            "to": "forge",
            "conditions": {"minMissions": 10, "operatorApproval": True},
            "cost": {"energy": 5, "cooldownSeconds": 30},
        },
    ],
}


# ──────────────────────────────────────────────────────────────
# TREE FUNCTIONS
# ──────────────────────────────────────────────────────────────

def _load_tree() -> Dict[str, Any]:
    """Load evolution tree from disk, or use default."""
    if TREE_FILE.exists():
        try:
            return json.loads(TREE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_TREE


def _save_tree(tree: Dict[str, Any]) -> None:
    TREE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TREE_FILE.write_text(json.dumps(tree, indent=2), encoding="utf-8")


def get_tree() -> Dict[str, Any]:
    """Return the full evolution tree."""
    return _load_tree()


def get_node(node_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific node by ID."""
    tree = _load_tree()
    for n in tree.get("nodes", []):
        if n["id"] == node_id:
            return n
    return None


def get_available_transitions(current_form: str) -> List[Dict[str, Any]]:
    """Return all edges that start from current_form."""
    tree = _load_tree()
    return [e for e in tree.get("edges", []) if e["from"] == current_form]


def check_transition(
    current_form: str,
    target_form: str,
    total_missions: int = 0,
    success_rate: float = 0,
    swarm_tier: int = 1,
    capabilities_used: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Check if a transition from current_form to target_form is valid.
    Returns {valid: bool, edge: {...}, unmet: [...]}
    """
    tree = _load_tree()
    caps = set(capabilities_used or [])

    for edge in tree.get("edges", []):
        if edge["from"] == current_form and edge["to"] == target_form:
            conds = edge.get("conditions", {})
            unmet: List[str] = []

            if total_missions < conds.get("minMissions", 0):
                unmet.append(f"Need {conds['minMissions']} missions (have {total_missions})")
            if success_rate < conds.get("minSuccessRate", 0):
                unmet.append(f"Need {conds['minSuccessRate']}% success (have {success_rate:.1f}%)")
            if swarm_tier < conds.get("minSwarmTier", 0):
                unmet.append(f"Need swarm tier {conds['minSwarmTier']} (have {swarm_tier})")
            req_caps = set(conds.get("requiredCapabilities", []))
            missing_caps = req_caps - caps
            if missing_caps:
                unmet.append(f"Need capabilities: {', '.join(missing_caps)}")
            req_missions = conds.get("requiredMissions", [])
            # We can't verify this without mission history, so just note it
            if req_missions:
                unmet.append(f"Requires completed missions: {', '.join(req_missions)}")

            return {
                "valid": len(unmet) == 0,
                "from": current_form,
                "to": target_form,
                "edge": edge,
                "unmet": unmet,
                "requires_approval": conds.get("operatorApproval", False),
            }

    return {
        "valid": False,
        "from": current_form,
        "to": target_form,
        "edge": None,
        "unmet": [f"No evolution path from '{current_form}' to '{target_form}'"],
    }


def initialize_tree() -> None:
    """Write the default tree to disk if it doesn't exist."""
    if not TREE_FILE.exists():
        _save_tree(DEFAULT_TREE)
