# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Brain Mapping - Optimal model routing for cognitive stability.

Maps specific task types to specific AI models to maintain stable cognitive
identity. Auto mode is explicitly disabled to preserve personality continuity
and learning weights.

Architecture:
    Commander Brain  (thinking, companion, reasoning)    â†’ Claude Opus 4.6
    Builder Brain    (coding, refactoring, writing files) â†’ GPT-5.3-Codex
    Utility Brain    (small tasks, classification, routing) â†’ Claude Sonnet 4.5
    Safety Brain     (diff inspection, bug spotting, verification) â†’ GPT-5.1-Codex-Max
"""

from enum import Enum
from typing import Dict, Any, Optional


class BrainRole(str, Enum):
    COMMANDER = "commander"
    BUILDER = "builder"
    UTILITY = "utility"
    SAFETY = "safety"


# Default brain-to-model assignments
DEFAULT_BRAINS: Dict[str, Dict[str, str]] = {
    BrainRole.COMMANDER: {
        "model": "claude-opus-4.6",
        "provider": "anthropic",
        "purpose": "thinking, companion, reasoning, planning",
        "description": "Largest context stability + coherent long reasoning",
    },
    BrainRole.BUILDER: {
        "model": "gpt-5.3-codex",
        "provider": "openai",
        "purpose": "coding, refactoring, writing files",
        "description": "Strongest structured code generation + patch accuracy",
    },
    BrainRole.UTILITY: {
        "model": "claude-sonnet-4.5",
        "provider": "anthropic",
        "purpose": "small tasks, classification, routing, intent detection",
        "description": "Cheap + fast + reliable classification",
    },
    BrainRole.SAFETY: {
        "model": "gpt-5.1-codex-max",
        "provider": "openai",
        "purpose": "diff inspection, bug spotting, edge-case checking, verification",
        "description": "Best at diff inspection and edge-case checking",
    },
}

# Deterministic task-type â†’ brain-role routing table
DEFAULT_TASK_ROUTING: Dict[str, BrainRole] = {
    # Commander
    "thinking": BrainRole.COMMANDER,
    "companion": BrainRole.COMMANDER,
    "reasoning": BrainRole.COMMANDER,
    "planning": BrainRole.COMMANDER,
    "conversation": BrainRole.COMMANDER,
    # Builder
    "coding": BrainRole.BUILDER,
    "refactoring": BrainRole.BUILDER,
    "writing_files": BrainRole.BUILDER,
    "code_generation": BrainRole.BUILDER,
    "patching": BrainRole.BUILDER,
    # Utility
    "classification": BrainRole.UTILITY,
    "routing": BrainRole.UTILITY,
    "intent_detection": BrainRole.UTILITY,
    "quick_decision": BrainRole.UTILITY,
    # Safety
    "verification": BrainRole.SAFETY,
    "diff_inspection": BrainRole.SAFETY,
    "bug_check": BrainRole.SAFETY,
    "pre_commit": BrainRole.SAFETY,
    "edge_case_check": BrainRole.SAFETY,
}


class BrainMapping:
    """Deterministic brain-to-model mapping.

    Each task type routes to a specific model â€” no auto-routing.
    This preserves personality continuity and learning weights.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._brains: Dict[BrainRole, Dict[str, str]] = {
            BrainRole(k) if isinstance(k, str) else k: dict(v)
            for k, v in DEFAULT_BRAINS.items()
        }
        self._task_routing: Dict[str, BrainRole] = dict(DEFAULT_TASK_ROUTING)

        if config:
            self._apply_config(config)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply operator-provided overrides to the brain mapping."""
        if config.get("auto_mode"):
            raise ValueError(
                "Auto mode is explicitly disabled. "
                "Auto destroys personality continuity and learning weights "
                "because routing changes every call."
            )

        for role_str, brain_cfg in config.get("brains", {}).items():
            role = BrainRole(role_str)
            self._brains[role].update(brain_cfg)

        for task_type, role_str in config.get("task_routing", {}).items():
            self._task_routing[task_type] = BrainRole(role_str)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route(self, task_type: str) -> Dict[str, Any]:
        """Route a task type to its assigned brain.

        Deterministic: the same task type always resolves to the same model.
        Unknown task types fall back to the utility brain for fast triage.
        """
        role = self._task_routing.get(task_type, BrainRole.UTILITY)
        brain = self._brains[role]
        return {
            "role": role.value,
            "model": brain["model"],
            "provider": brain["provider"],
            "purpose": brain["purpose"],
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_brain(self, role: BrainRole) -> Dict[str, str]:
        """Return the configuration dict for a single brain role."""
        return dict(self._brains[role])

    def get_all_brains(self) -> Dict[str, Dict[str, str]]:
        """Return every brain role and its configuration."""
        return {role.value: dict(cfg) for role, cfg in self._brains.items()}

    def get_routing_table(self) -> Dict[str, str]:
        """Return the full task-type â†’ role routing table."""
        return {task: role.value for task, role in self._task_routing.items()}

    @property
    def auto_mode(self) -> bool:
        """Auto mode is always disabled for cognitive stability."""
        return False

