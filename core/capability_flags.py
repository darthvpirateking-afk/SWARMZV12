from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class CapabilityStatus(Enum):
    """Defines the possible states of a system capability."""
    AVAILABLE = "AVAILABLE"
    EXPERIMENTAL = "EXPERIMENTAL"
    DISABLED = "DISABLED"


@dataclass
class Capability:
    """Represents a specific NEXUSMON system capability."""
    id: str
    name: str
    status: CapabilityStatus
    version_required: str
    governance_lock: bool = False


class CapabilityRegistry:
    """
    Maintains a registry of NEXUSMON capabilities and manages their operational status.
    """

    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initializes the registry with default NEXUSMON capabilities."""
        defaults = [
            Capability(
                id="kernel_base",
                name="Kernel Base",
                status=CapabilityStatus.AVAILABLE,
                version_required="1.0.0",
                governance_lock=True
            ),
            Capability(
                id="rollback_system",
                name="Rollback System",
                status=CapabilityStatus.AVAILABLE,
                version_required="1.0.0",
                governance_lock=True
            ),
            Capability(
                id="bio_lab_api",
                name="Bio Lab API",
                status=CapabilityStatus.EXPERIMENTAL,
                version_required="0.5.0",
                governance_lock=False
            ),
            Capability(
                id="space_mission_control",
                name="Space Mission Control",
                status=CapabilityStatus.DISABLED,
                version_required="0.8.0",
                governance_lock=False
            ),
            Capability(
                id="sovereign_classifier",
                name="Sovereign Classifier",
                status=CapabilityStatus.AVAILABLE,
                version_required="1.0.0",
                governance_lock=True
            ),
        ]
        for cap in defaults:
            self.register(cap)

    def register(self, capability: Capability):
        """Registers a new capability within the system."""
        self._capabilities[capability.id] = capability

    def check(self, capability_id: str) -> bool:
        """
        Returns True if the capability exists and is NOT DISABLED.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            return False
        return cap.status != CapabilityStatus.DISABLED

    def get_status(self, capability_id: str) -> Optional[CapabilityStatus]:
        """Returns the current status of a capability."""
        cap = self._capabilities.get(capability_id)
        return cap.status if cap else None

    def set_status(self, capability_id: str, new_status: CapabilityStatus) -> bool:
        """
        Updates the status of a capability if it is not governance locked.
        Returns True if successful, False if locked or not found.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            return False
        
        if cap.governance_lock:
            # Cannot change status of governance-locked capabilities at runtime
            return False
            
        cap.status = new_status
        return True


# Global registry instance for NEXUSMON
registry = CapabilityRegistry()
