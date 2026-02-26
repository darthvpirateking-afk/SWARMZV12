# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/integrity.py — Architectural Restraint Layer (P0.2)

Structural constraints — what cannot be built.
Enforces: no cyclic deps, no cross-domain writes without interface, no stub exposure.

Pattern:
    result = integrity.enforce_constraint(action, boundaries)
    if not result.passed:
        deny(result.reason)

Architecture Role: Integrity Layer
Doctrine: Architectural restraint = What can't be built can't be broken
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_CONSTRAINTS_FILE = _CONFIG_DIR / "constraints.json"


@dataclass
class LayerResult:
    """Deterministic state object returned by all layers."""
    layer: str
    passed: bool
    reason: str
    metadata: dict
    timestamp: float


# Domain boundaries (from codebase analysis)
DOMAINS = {
    "nexusmon": ["nexusmon", "nexusmon_*"],
    "core": ["core"],
    "galileo": ["galileo"],
    "swarmz_runtime": ["swarmz_runtime"],
    "api": ["api", "addons/api"],
    "control_plane": ["control_plane"],
    "kernel_runtime": ["kernel_runtime"],
}


class IntegrityLayer:
    """Architectural restraint layer enforcing structural integrity."""

    def __init__(self, constraints_path: Optional[Path] = None):
        self.constraints_path = constraints_path or _CONSTRAINTS_FILE
        self.constraints = self._load_constraints()

    def _load_constraints(self) -> Dict[str, Any]:
        """Load constraint rules from config."""
        if not self.constraints_path.exists():
            # Default constraints if config missing
            return {
                "allow_cyclic_dependencies": False,
                "allow_cross_domain_mutation": False,
                "allow_stub_exposure": False,
                "max_dependency_depth": 10,
                "forbidden_patterns": [
                    "pass  # TODO",
                    "NotImplementedError",
                    "stub implementation",
                ],
            }
        
        with open(self.constraints_path, "r") as f:
            return json.load(f)

    def check_cyclic_dependency(self, action: Dict[str, Any]) -> LayerResult:
        """Detect if action would create cyclic dependency."""
        # Extract dependency information from action
        dependencies = action.get("dependencies", [])
        action_id = action.get("id", "")
        
        if not dependencies:
            return LayerResult(
                layer="integrity",
                passed=True,
                reason="No dependencies to check",
                metadata={"check": "cyclic_dependency"},
                timestamp=time.time(),
            )
        
        # Check if action_id appears in its own dependency chain
        if action_id in dependencies:
            return LayerResult(
                layer="integrity",
                passed=False,
                reason=f"Self-dependency detected: {action_id}",
                metadata={
                    "check": "cyclic_dependency",
                    "violation": "self_reference",
                    "action_id": action_id,
                },
                timestamp=time.time(),
            )
        
        # For now, basic check (full cycle detection in nexusmon_mission_engine)
        return LayerResult(
            layer="integrity",
            passed=True,
            reason="Basic cycle check passed",
            metadata={"check": "cyclic_dependency"},
            timestamp=time.time(),
        )

    def check_cross_domain_mutation(self, action: Dict[str, Any]) -> LayerResult:
        """Block cross-domain writes without interface."""
        source_domain = action.get("source_domain", "unknown")
        target_domain = action.get("target_domain", "unknown")
        mutation_type = action.get("type", "")
        
        if source_domain == target_domain:
            return LayerResult(
                layer="integrity",
                passed=True,
                reason="Same-domain operation allowed",
                metadata={"check": "cross_domain_mutation"},
                timestamp=time.time(),
            )
        
        if not self.constraints.get("allow_cross_domain_mutation", False):
            # Check if there's an interface contract
            has_interface = action.get("has_interface_contract", False)
            if not has_interface and mutation_type in ["write", "mutate", "delete"]:
                return LayerResult(
                    layer="integrity",
                    passed=False,
                    reason=f"Cross-domain mutation {source_domain}→{target_domain} without interface",
                    metadata={
                        "check": "cross_domain_mutation",
                        "violation": "no_interface_contract",
                        "source": source_domain,
                        "target": target_domain,
                    },
                    timestamp=time.time(),
                )
        
        return LayerResult(
            layer="integrity",
            passed=True,
            reason="Cross-domain check passed",
            metadata={"check": "cross_domain_mutation"},
            timestamp=time.time(),
        )

    def check_stub_exposure(self, action: Dict[str, Any]) -> LayerResult:
        """Prevent stub implementations from being exposed as real features."""
        code = action.get("code", "")
        description = action.get("description", "")
        is_public_api = action.get("is_public_api", False)
        
        if not is_public_api:
            return LayerResult(
                layer="integrity",
                passed=True,
                reason="Internal action, stub check skipped",
                metadata={"check": "stub_exposure"},
                timestamp=time.time(),
            )
        
        # Check for forbidden stub patterns
        for pattern in self.constraints.get("forbidden_patterns", []):
            if pattern.lower() in code.lower() or pattern.lower() in description.lower():
                return LayerResult(
                    layer="integrity",
                    passed=False,
                    reason=f"Stub pattern '{pattern}' detected in public API",
                    metadata={
                        "check": "stub_exposure",
                        "violation": "stub_in_public_api",
                        "pattern": pattern,
                    },
                    timestamp=time.time(),
                )
        
        return LayerResult(
            layer="integrity",
            passed=True,
            reason="No stub patterns detected",
            metadata={"check": "stub_exposure"},
            timestamp=time.time(),
        )

    def enforce_constraint(
        self,
        action: Dict[str, Any],
        boundaries: Optional[Dict[str, Any]] = None,
    ) -> LayerResult:
        """
        Run all integrity checks on an action.
        
        Returns first failure or overall pass.
        """
        checks = [
            self.check_cyclic_dependency(action),
            self.check_cross_domain_mutation(action),
            self.check_stub_exposure(action),
        ]
        
        violations = [c for c in checks if not c.passed]
        
        if violations:
            # Return first violation
            violation = violations[0]
            return LayerResult(
                layer="integrity",
                passed=False,
                reason=violation.reason,
                metadata={
                    "total_checks": len(checks),
                    "violations": len(violations),
                    "first_violation": violation.metadata,
                },
                timestamp=time.time(),
            )
        
        return LayerResult(
            layer="integrity",
            passed=True,
            reason="All integrity checks passed",
            metadata={
                "total_checks": len(checks),
                "checks_passed": ["cyclic_dep", "cross_domain", "stub_exposure"],
            },
            timestamp=time.time(),
        )

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """Entry point for pipeline composition."""
        return self.enforce_constraint(action, context.get("boundaries"))


# Singleton instance
_integrity = IntegrityLayer()


def enforce_constraint(
    action: Dict[str, Any],
    boundaries: Optional[Dict[str, Any]] = None,
) -> LayerResult:
    """Module-level convenience function."""
    return _integrity.enforce_constraint(action, boundaries)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Module-level convenience function."""
    return _integrity.evaluate(action, context)
