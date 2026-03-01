"""
Boundaries Layer (P1.4 - Domain Control)

Enforces isolation and interaction boundaries between system domains.
Ensures clean separation of concerns and controlled cross-domain interactions.

Design:
- Define domain boundaries (data, control, observation, execution)
- Enforce boundary crossing rules
- Track cross-domain interactions for audit
- Validate boundary contracts (interfaces)
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_BOUNDARIES_CONFIG_FILE = _CONFIG_DIR / "governance" / "boundaries.json"

from core.reversible import LayerResult


class DomainType(str, Enum):
    """System domain types."""

    DATA = "data"  # Data storage and retrieval
    CONTROL = "control"  # Control plane decisions
    OBSERVATION = "observation"  # Monitoring and telemetry
    EXECUTION = "execution"  # Action execution
    SECURITY = "security"  # Security checks
    EXTERNAL = "external"  # External system interactions


@dataclass
class BoundaryRule:
    """A boundary crossing rule."""

    name: str
    from_domain: DomainType
    to_domain: DomainType
    allowed: bool
    requires_interface: bool  # Must use defined interface
    audit: bool  # Log all crossings


@dataclass
class BoundaryCrossing:
    """Records a domain boundary crossing."""

    timestamp: float
    from_domain: DomainType
    to_domain: DomainType
    action: str
    allowed: bool
    interface_used: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BoundariesLayer:
    """
    Domain boundary enforcement engine.

    Ensures proper isolation between system domains and controlled
    cross-domain interactions.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.rules: List[BoundaryRule] = []
        self.crossing_log: List[BoundaryCrossing] = []
        self._config_path = config_path or _BOUNDARIES_CONFIG_FILE
        self._load_default_rules()
        self._apply_config_rules()

    def _apply_config_rules(self) -> None:
        """Merge additional rules from config/governance/boundaries.json if it exists."""
        if not self._config_path.exists():
            return
        try:
            with open(self._config_path, "r") as f:
                cfg = json.load(f)
            for rdesc in cfg.get("rules", []):
                name = rdesc.get("name", "")
                from_d = rdesc.get("from_domain", "")
                to_d = rdesc.get("to_domain", "")
                # Skip wildcard rules (handled in defaults) and existing rules
                if from_d == "*" or to_d == "*":
                    continue
                if any(r.name == name for r in self.rules):
                    # Update existing rule in place
                    for r in self.rules:
                        if r.name == name:
                            r.allowed = rdesc.get("allowed", r.allowed)
                            r.requires_interface = rdesc.get(
                                "requires_interface", r.requires_interface
                            )
                            r.audit = rdesc.get("audit", r.audit)
                            break
                else:
                    try:
                        self.add_rule(
                            BoundaryRule(
                                name=name,
                                from_domain=DomainType(from_d),
                                to_domain=DomainType(to_d),
                                allowed=rdesc.get("allowed", True),
                                requires_interface=rdesc.get(
                                    "requires_interface", False
                                ),
                                audit=rdesc.get("audit", True),
                            )
                        )
                    except (ValueError, KeyError):
                        pass  # Skip rules referencing unknown domain values
        except Exception:
            pass  # Config errors are non-fatal; defaults remain active

    def _load_default_rules(self):
        """Initialize with baseline boundary rules."""
        # All domains can observe (read-only)
        for domain_from in DomainType:
            self.add_rule(
                BoundaryRule(
                    name=f"{domain_from.value}_to_observation",
                    from_domain=domain_from,
                    to_domain=DomainType.OBSERVATION,
                    allowed=True,
                    requires_interface=False,
                    audit=True,
                )
            )

        # Control -> Execution allowed with interface
        self.add_rule(
            BoundaryRule(
                name="control_to_execution",
                from_domain=DomainType.CONTROL,
                to_domain=DomainType.EXECUTION,
                allowed=True,
                requires_interface=True,
                audit=True,
            )
        )

        # Execution -> Data allowed (for results)
        self.add_rule(
            BoundaryRule(
                name="execution_to_data",
                from_domain=DomainType.EXECUTION,
                to_domain=DomainType.DATA,
                allowed=True,
                requires_interface=True,
                audit=True,
            )
        )

        # Security can inspect all domains
        for domain_to in DomainType:
            if domain_to != DomainType.SECURITY:
                self.add_rule(
                    BoundaryRule(
                        name=f"security_inspect_{domain_to.value}",
                        from_domain=DomainType.SECURITY,
                        to_domain=domain_to,
                        allowed=True,
                        requires_interface=False,
                        audit=True,
                    )
                )

        # BLOCK: Execution -> Control (no reverse flow)
        self.add_rule(
            BoundaryRule(
                name="block_execution_to_control",
                from_domain=DomainType.EXECUTION,
                to_domain=DomainType.CONTROL,
                allowed=False,
                requires_interface=False,
                audit=True,
            )
        )

        # BLOCK: External -> Control (requires security checks)
        self.add_rule(
            BoundaryRule(
                name="block_external_to_control_direct",
                from_domain=DomainType.EXTERNAL,
                to_domain=DomainType.CONTROL,
                allowed=False,
                requires_interface=True,
                audit=True,
            )
        )

    def add_rule(self, rule: BoundaryRule):
        """Add a boundary rule."""
        self.rules.append(rule)

    def _find_rule(
        self, from_domain: DomainType, to_domain: DomainType
    ) -> Optional[BoundaryRule]:
        """Find applicable boundary rule."""
        # Look for exact match first
        for rule in self.rules:
            if rule.from_domain == from_domain and rule.to_domain == to_domain:
                return rule

        # Default: deny unlisted crossings
        return None

    def check_boundary_crossing(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
    ) -> LayerResult:
        """
        Check if a boundary crossing is allowed.

        Expects context to contain:
        - from_domain: source domain
        - to_domain: target domain
        - interface: (optional) interface name being used
        """
        from_domain_str = context.get("from_domain")
        to_domain_str = context.get("to_domain")
        interface = context.get("interface")

        # Convert to enum
        try:
            from_domain = DomainType(from_domain_str)
            to_domain = DomainType(to_domain_str)
        except (ValueError, TypeError):
            return LayerResult(
                layer="boundaries",
                passed=False,
                reason=f"Invalid domain types: {from_domain_str} -> {to_domain_str}",
                metadata={},
                timestamp=time.time(),
            )

        # Same domain = always allowed
        if from_domain == to_domain:
            return LayerResult(
                layer="boundaries",
                passed=True,
                reason="Same domain interaction",
                metadata={
                    "from_domain": from_domain.value,
                    "to_domain": to_domain.value,
                },
                timestamp=time.time(),
            )

        # Find applicable rule
        rule = self._find_rule(from_domain, to_domain)

        if rule is None:
            # No rule = deny by default
            crossing = BoundaryCrossing(
                timestamp=time.time(),
                from_domain=from_domain,
                to_domain=to_domain,
                action=action.get("action_type", "unknown"),
                allowed=False,
                metadata={"reason": "No boundary rule defined"},
            )
            self.crossing_log.append(crossing)

            return LayerResult(
                layer="boundaries",
                passed=False,
                reason=f"No boundary rule for {from_domain.value} -> {to_domain.value}",
                metadata={"crossing": crossing.__dict__},
                timestamp=time.time(),
            )

        # Check if allowed
        if not rule.allowed:
            crossing = BoundaryCrossing(
                timestamp=time.time(),
                from_domain=from_domain,
                to_domain=to_domain,
                action=action.get("action_type", "unknown"),
                allowed=False,
                interface_used=interface,
                metadata={"rule": rule.name},
            )
            self.crossing_log.append(crossing)

            return LayerResult(
                layer="boundaries",
                passed=False,
                reason=f"Boundary crossing blocked by rule: {rule.name}",
                metadata={"crossing": crossing.__dict__},
                timestamp=time.time(),
            )

        # Check interface requirement
        if rule.requires_interface and not interface:
            crossing = BoundaryCrossing(
                timestamp=time.time(),
                from_domain=from_domain,
                to_domain=to_domain,
                action=action.get("action_type", "unknown"),
                allowed=False,
                interface_used=interface,
                metadata={"rule": rule.name, "reason": "Missing required interface"},
            )
            self.crossing_log.append(crossing)

            return LayerResult(
                layer="boundaries",
                passed=False,
                reason=f"Boundary crossing requires interface: {rule.name}",
                metadata={"crossing": crossing.__dict__},
                timestamp=time.time(),
            )

        # Allowed - log if auditing enabled
        if rule.audit:
            crossing = BoundaryCrossing(
                timestamp=time.time(),
                from_domain=from_domain,
                to_domain=to_domain,
                action=action.get("action_type", "unknown"),
                allowed=True,
                interface_used=interface,
                metadata={"rule": rule.name},
            )
            self.crossing_log.append(crossing)

        return LayerResult(
            layer="boundaries",
            passed=True,
            reason=f"Boundary crossing allowed: {rule.name}",
            metadata={
                "from_domain": from_domain.value,
                "to_domain": to_domain.value,
                "interface": interface,
                "rule": rule.name,
            },
            timestamp=time.time(),
        )

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Checks boundary crossings if domain info is present.
        """
        if "from_domain" in context and "to_domain" in context:
            return self.check_boundary_crossing(action, context)

        # No boundary info = pass through
        return LayerResult(
            layer="boundaries",
            passed=True,
            reason="No boundary check required",
            metadata={},
            timestamp=time.time(),
        )

    def get_crossing_log(
        self,
        from_domain: Optional[DomainType] = None,
        to_domain: Optional[DomainType] = None,
        allowed: Optional[bool] = None,
        limit: int = 100,
    ) -> List[BoundaryCrossing]:
        """Query boundary crossing log."""
        results = self.crossing_log[-limit * 2 :]

        if from_domain is not None:
            results = [c for c in results if c.from_domain == from_domain]

        if to_domain is not None:
            results = [c for c in results if c.to_domain == to_domain]

        if allowed is not None:
            results = [c for c in results if c.allowed == allowed]

        return results[-limit:]

    def clear_crossing_log(self):
        """Clear crossing log (for testing)."""
        self.crossing_log.clear()


# Module-level instance
_boundaries = BoundariesLayer()


def add_rule(rule: BoundaryRule):
    """Add boundary rule to global instance."""
    _boundaries.add_rule(rule)


def check_boundary_crossing(
    action: Dict[str, Any], context: Dict[str, Any]
) -> LayerResult:
    """Check boundary crossing using global instance."""
    return _boundaries.check_boundary_crossing(action, context)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _boundaries.evaluate(action, context)


def get_crossing_log(
    from_domain: Optional[DomainType] = None,
    to_domain: Optional[DomainType] = None,
    allowed: Optional[bool] = None,
    limit: int = 100,
) -> List[BoundaryCrossing]:
    """Get crossing log."""
    return _boundaries.get_crossing_log(from_domain, to_domain, allowed, limit)
