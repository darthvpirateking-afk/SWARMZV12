"""
SWARMZ Orchestrator: Centralized activation logic for all subsystems.
Additive-only. Does not modify or overwrite any existing files.
"""

import logging
import time
from typing import Optional, Dict, Any

from core.telemetry import telemetry
from core.capability_flags import registry
from core.sovereign import classify, SovereignOutcome
from core.reversible import LayerResult

_log = logging.getLogger("swarmz.orchestrator")


class SwarmzOrchestrator:
    """Central orchestrator for SWARMZ activation sequence."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or self.load_config()
        self.mesh: Optional[Any] = None
        self.governor: Optional[Any] = None
        self.patchpack: Optional[Any] = None
        self.session: Optional[Any] = None
        self.mission_engine: Optional[Any] = None
        self.swarm_engine: Optional[Any] = None
        self.avatar: Optional[Any] = None
        self.api: Optional[Any] = None
        self.cockpit: Optional[Any] = None

    def _safe_activate(self, component_id: str, start_func) -> Any:
        """Gates component activation with Sovereign classification and Registry checks."""
        # 1. Check Registry
        if not registry.check(component_id):
            telemetry.log_action(
                "WARNING",
                "orchestrator",
                f"Capability '{component_id}' is DISABLED. Skipping.",
            )
            return object()

        # 2. Sovereign Classification
        # Create a mock LayerResult for the activation action
        activation_result = LayerResult(
            layer="orchestrator",
            passed=True,
            reason=f"Attempting to activate {component_id}",
            metadata={},
            timestamp=time.time(),
        )

        # Meta-policy classification
        decision = classify(
            activation_result,
            {"action_type": "subsystem_start", "component": component_id},
        )

        if decision.outcome == SovereignOutcome.DENY:
            telemetry.log_action(
                "ERROR",
                "orchestrator",
                f"Sovereign DENY for {component_id}: {decision.reason}",
            )
            return object()

        if decision.outcome == SovereignOutcome.ESCALATE:
            telemetry.log_escalation(
                "orchestrator",
                decision.rule_name or "unknown",
                decision.reason,
                component=component_id,
            )
            # In a real system, we'd wait for approval. Here we'll skip for safety.
            return object()

        if decision.outcome == SovereignOutcome.QUARANTINE:
            telemetry.log_action(
                "WARNING",
                "orchestrator",
                f"Subsystem {component_id} QUARANTINED during startup.",
            )
            return object()

        # 3. Proceed if PASS
        return start_func()

    def activate(self) -> None:
        telemetry.log_action(
            "INFO", "orchestrator", "NEXUSMON Hardened Activation Sequence Initiated..."
        )

        if not registry.check("kernel_base"):
            telemetry.log_action(
                "CRITICAL", "orchestrator", "KERNEL_BASE DISABLED. Halting deployment."
            )
            return

        self.mesh = self._safe_activate("kernel_base", self.load_mesh)
        self.governor = self._safe_activate("kernel_base", self.start_governor)
        self.patchpack = self._safe_activate("kernel_base", self.start_patchpack)
        self.session = self._safe_activate("kernel_base", self.start_session)
        self.mission_engine = self._safe_activate(
            "kernel_base", self.start_mission_engine
        )
        self.swarm_engine = self._safe_activate("kernel_base", self.start_swarm_engine)
        self.avatar = self._safe_activate("kernel_base", self.start_avatar)
        self.api = self.start_api()  # API start logic is managed externally
        self.cockpit = self._safe_activate("kernel_base", self.launch_cockpit)

        telemetry.log_action(
            "INFO", "orchestrator", "Kernel activation sequence complete."
        )

    def load_config(self) -> Dict[str, Any]:
        return {}

    def load_mesh(self) -> Any:
        try:
            from backend.core.cosmology.mesh_router import MeshRouter

            return MeshRouter()
        except ImportError:
            return object()

    def start_governor(self) -> Any:
        try:
            from core.governor import Governor

            return Governor()
        except ImportError:
            return object()

    def start_patchpack(self) -> Any:
        try:
            from backend.patchpack import Patchpack

            return Patchpack()
        except ImportError:
            return object()

    def start_session(self) -> Any:
        try:
            from swarmz_runtime.session import operator_session

            return operator_session
        except ImportError:
            return object()

    def start_mission_engine(self) -> Any:
        try:
            from swarmz_runtime.mission_engine import mission_engine

            return mission_engine
        except ImportError:
            return object()

    def start_swarm_engine(self) -> Any:
        try:
            from swarmz_runtime.swarm_engine import behaviors

            return behaviors
        except ImportError:
            return object()

    def start_avatar(self) -> Any:
        try:
            from swarmz_runtime.avatar import avatar_omega

            return avatar_omega
        except ImportError:
            return object()

    def start_api(self) -> Optional[Any]:
        return None

    def launch_cockpit(self) -> Any:
        try:
            from swarmz_runtime.ui import cockpit

            return cockpit
        except ImportError:
            return object()
