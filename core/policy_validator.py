"""
MIT License
Copyright (c) 2026 NEXUSMON

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of policy validation."""

    def __init__(
        self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(warning)

    def __bool__(self) -> bool:
        return self.is_valid


class PolicyValidator:
    """
    PolicyValidator provides comprehensive validation for governance policies.

    Features:
    - Syntax and logic validation
    - Impact assessment before applying
    - Rollback on validation failures
    - Policy compatibility checking
    """

    def __init__(self):
        """Initialize the PolicyValidator."""
        self._schema = self._build_schema()
        self._custom_validators = [
            self._validate_policy_structure,
            self._validate_policy_logic,
            self._validate_policy_impact,
            self._validate_policy_compatibility,
        ]

    def _build_schema(self) -> Dict[str, Any]:
        """Build the JSON schema for policy validation."""
        return {
            "type": "object",
            "properties": {
                "policy_id": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^[a-zA-Z0-9_-]+$",
                },
                "version": {"type": "string", "pattern": "^v\\d+\\.\\d+\\.\\d+$"},
                "description": {"type": "string", "minLength": 1},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "enabled": {"type": "boolean"},
                "priority": {"type": "integer", "minimum": 0, "maximum": 100},
                "rules": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string"},
                            "condition": {"type": "object"},
                            "action": {"type": "string"},
                            "enabled": {"type": "boolean"},
                            "priority": {"type": "integer"},
                        },
                        "required": ["rule_id", "condition", "action"],
                    },
                },
                "metadata": {"type": "object"},
            },
            "required": ["policy_id", "version", "description", "rules"],
            "additionalProperties": False,
        }

    def validate(self, policy_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a policy against schema and custom rules.

        Args:
            policy_data: Policy configuration data

        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(True)

        try:
            # Basic schema validation
            validate(instance=policy_data, schema=self._schema)

            # Custom validation rules
            for validator in self._custom_validators:
                try:
                    validator(policy_data, result)
                except Exception as e:
                    logger.error(f"Custom validation error: {e}")
                    result.add_error(f"Custom validation failed: {str(e)}")

            # Log validation result
            if result.is_valid:
                logger.info(
                    f"Policy {policy_data.get('policy_id', 'unknown')} validation passed"
                )
            else:
                logger.warning(
                    f"Policy {policy_data.get('policy_id', 'unknown')} validation failed: {result.errors}"
                )

        except ValidationError as e:
            result.add_error(f"Schema validation failed: {e.message}")
        except Exception as e:
            result.add_error(f"Validation error: {str(e)}")

        return result

    def _validate_policy_structure(
        self, policy_data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate policy structure and required fields."""
        policy_id = policy_data.get("policy_id")

        # Check for required fields
        required_fields = ["policy_id", "version", "description", "rules"]
        for field in required_fields:
            if field not in policy_data:
                result.add_error(f"Missing required field: {field}")

        # Validate policy ID format
        if policy_id and not re.match(r"^[a-zA-Z0-9_-]+$", policy_id):
            result.add_error(
                "Policy ID must contain only alphanumeric characters, underscores, or hyphens"
            )

        # Validate version format
        version = policy_data.get("version", "")
        if version and not re.match(r"^v\d+\.\d+\.\d+$", version):
            result.add_error(
                "Version must follow semantic versioning format (e.g., v1.0.0)"
            )

        # Validate rules structure
        rules = policy_data.get("rules", [])
        if not rules:
            result.add_error("Policy must contain at least one rule")

        rule_ids = set()
        for i, rule in enumerate(rules):
            if "rule_id" not in rule:
                result.add_error(f"Rule {i} missing rule_id")
                continue

            rule_id = rule["rule_id"]
            if rule_id in rule_ids:
                result.add_error(f"Duplicate rule ID: {rule_id}")
            rule_ids.add(rule_id)

            if "condition" not in rule:
                result.add_error(f"Rule {rule_id} missing condition")

            if "action" not in rule:
                result.add_error(f"Rule {rule_id} missing action")

    def _validate_policy_logic(
        self, policy_data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate policy logic and consistency."""
        rules = policy_data.get("rules", [])

        # Check for conflicting rules
        rule_conditions = {}
        for rule in rules:
            rule_id = rule.get("rule_id")
            condition = rule.get("condition", {})

            # Simple conflict detection based on identical conditions
            condition_str = json.dumps(condition, sort_keys=True)
            if condition_str in rule_conditions:
                result.add_warning(
                    f"Potential conflict: Rule {rule_id} has same condition as rule {rule_conditions[condition_str]}"
                )

            rule_conditions[condition_str] = rule_id

        # Validate action types
        valid_actions = {
            "allow",
            "deny",
            "audit",
            "log",
            "notify",
            "throttle",
            "rate_limit",
            "timeout",
            "retry",
        }

        for rule in rules:
            action = rule.get("action", "").lower()
            if action not in valid_actions:
                result.add_warning(
                    f"Unknown action type: {action} in rule {rule.get('rule_id')}"
                )

    def _validate_policy_impact(
        self, policy_data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate potential impact of policy changes."""
        policy_id = policy_data.get("policy_id", "unknown")
        rules = policy_data.get("rules", [])

        # Check for overly broad deny rules
        deny_rules = [r for r in rules if r.get("action", "").lower() == "deny"]
        if len(deny_rules) > len(rules) * 0.8:  # More than 80% deny rules
            result.add_warning(
                f"Policy {policy_id} has high percentage of deny rules - may be too restrictive"
            )

        # Check for missing priority settings
        missing_priority = [r for r in rules if "priority" not in r]
        if missing_priority:
            result.add_warning(
                f"Policy {policy_id} has {len(missing_priority)} rules without priority settings"
            )

        # Validate priority ranges
        for rule in rules:
            priority = rule.get("priority")
            if priority is not None and (priority < 0 or priority > 100):
                result.add_error(
                    f"Rule {rule.get('rule_id')} has invalid priority: {priority}"
                )

    def _validate_policy_compatibility(
        self, policy_data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate policy compatibility with system constraints."""
        policy_id = policy_data.get("policy_id", "unknown")

        # Check policy size
        policy_size = len(json.dumps(policy_data).encode("utf-8"))
        max_size = 1024 * 1024  # 1MB limit

        if policy_size > max_size:
            result.add_error(
                f"Policy {policy_id} too large: {policy_size} bytes (max: {max_size})"
            )

        # Validate metadata structure
        metadata = policy_data.get("metadata", {})
        if not isinstance(metadata, dict):
            result.add_error("Metadata must be a dictionary")

        # Check for reserved metadata keys
        reserved_keys = {"system", "internal", "private"}
        for key in metadata.keys():
            if key in reserved_keys:
                result.add_warning(
                    f"Policy {policy_id} uses reserved metadata key: {key}"
                )

    def validate_policy_update(
        self, old_policy: Dict[str, Any], new_policy: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a policy update for breaking changes.

        Args:
            old_policy: Current policy data
            new_policy: New policy data

        Returns:
            ValidationResult with update validation status
        """
        result = ValidationResult(True)

        old_id = old_policy.get("policy_id")
        new_id = new_policy.get("policy_id")

        # Check policy ID consistency
        if old_id != new_id:
            result.add_error(f"Policy ID cannot be changed: {old_id} -> {new_id}")

        # Validate version increment
        old_version = old_policy.get("version", "v0.0.0")
        new_version = new_policy.get("version", "v0.0.0")

        if not self._is_version_increment(old_version, new_version):
            result.add_warning(
                f"Version should be incremented: {old_version} -> {new_version}"
            )

        # Validate backward compatibility
        self._validate_backward_compatibility(old_policy, new_policy, result)

        return result

    def _is_version_increment(self, old_version: str, new_version: str) -> bool:
        """Check if new version is a valid increment."""
        try:
            old_parts = [int(x) for x in old_version[1:].split(".")]
            new_parts = [int(x) for x in new_version[1:].split(".")]

            if len(old_parts) != 3 or len(new_parts) != 3:
                return False

            # Major version increment always valid
            if new_parts[0] > old_parts[0]:
                return True

            # Minor version increment valid if major is same
            if new_parts[0] == old_parts[0] and new_parts[1] > old_parts[1]:
                return True

            # Patch version increment valid if major and minor are same
            if (
                new_parts[0] == old_parts[0]
                and new_parts[1] == old_parts[1]
                and new_parts[2] > old_parts[2]
            ):
                return True

            return False
        except (ValueError, IndexError):
            return False

    def _validate_backward_compatibility(
        self,
        old_policy: Dict[str, Any],
        new_policy: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate that policy update maintains backward compatibility."""
        old_rules = {r["rule_id"]: r for r in old_policy.get("rules", [])}
        new_rules = {r["rule_id"]: r for r in new_policy.get("rules", [])}

        # Check for removed rules
        removed_rules = set(old_rules.keys()) - set(new_rules.keys())
        if removed_rules:
            result.add_warning(
                f"Policy update removes rules: {', '.join(removed_rules)}"
            )

        # Check for changed rule actions
        for rule_id, old_rule in old_rules.items():
            if rule_id in new_rules:
                new_rule = new_rules[rule_id]
                if old_rule.get("action") != new_rule.get("action"):
                    result.add_warning(
                        f"Rule {rule_id} action changed: {old_rule.get('action')} -> {new_rule.get('action')}"
                    )

    def validate_policy_syntax(self, policy_json: str) -> ValidationResult:
        """
        Validate policy JSON syntax.

        Args:
            policy_json: Policy as JSON string

        Returns:
            ValidationResult with syntax validation status
        """
        result = ValidationResult(True)

        try:
            policy_data = json.loads(policy_json)
            result = self.validate(policy_data)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON syntax: {e.msg} at position {e.pos}")
        except Exception as e:
            result.add_error(f"Syntax validation error: {str(e)}")

        return result

    def get_policy_summary(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of policy characteristics.

        Args:
            policy_data: Policy configuration data

        Returns:
            Summary of policy characteristics
        """
        rules = policy_data.get("rules", [])

        summary = {
            "policy_id": policy_data.get("policy_id"),
            "version": policy_data.get("version"),
            "description": policy_data.get("description"),
            "total_rules": len(rules),
            "enabled_rules": len([r for r in rules if r.get("enabled", True)]),
            "disabled_rules": len([r for r in rules if not r.get("enabled", True)]),
            "action_types": list(set(r.get("action", "").lower() for r in rules)),
            "priority_range": self._get_priority_range(rules),
            "size_bytes": len(json.dumps(policy_data).encode("utf-8")),
        }

        return summary

    def _get_priority_range(
        self, rules: List[Dict[str, Any]]
    ) -> Dict[str, Optional[int]]:
        """Get the priority range of rules."""
        priorities = [r.get("priority") for r in rules if r.get("priority") is not None]

        if not priorities:
            return {"min": None, "max": None}

        return {"min": min(priorities), "max": max(priorities)}

    def validate_policy_compliance(
        self, policy_data: Dict[str, Any], compliance_rules: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate policy against compliance requirements.

        Args:
            policy_data: Policy configuration data
            compliance_rules: List of compliance requirements

        Returns:
            ValidationResult with compliance validation status
        """
        result = ValidationResult(True)

        for compliance_rule in compliance_rules:
            try:
                self._check_compliance_rule(policy_data, compliance_rule, result)
            except Exception as e:
                result.add_error(f"Compliance check error: {str(e)}")

        return result

    def _check_compliance_rule(
        self,
        policy_data: Dict[str, Any],
        compliance_rule: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check a single compliance rule."""
        rule_type = compliance_rule.get("type")
        rule_config = compliance_rule.get("config", {})

        if rule_type == "required_actions":
            self._check_required_actions(policy_data, rule_config, result)
        elif rule_type == "forbidden_actions":
            self._check_forbidden_actions(policy_data, rule_config, result)
        elif rule_type == "min_rules":
            self._check_min_rules(policy_data, rule_config, result)
        elif rule_type == "max_rules":
            self._check_max_rules(policy_data, rule_config, result)

    def _check_required_actions(
        self,
        policy_data: Dict[str, Any],
        config: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check that required actions are present."""
        required_actions = config.get("actions", [])
        rules = policy_data.get("rules", [])
        available_actions = {r.get("action", "").lower() for r in rules}

        missing_actions = set(required_actions) - available_actions
        if missing_actions:
            result.add_error(f"Missing required actions: {', '.join(missing_actions)}")

    def _check_forbidden_actions(
        self,
        policy_data: Dict[str, Any],
        config: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check that forbidden actions are not present."""
        forbidden_actions = config.get("actions", [])
        rules = policy_data.get("rules", [])
        available_actions = {r.get("action", "").lower() for r in rules}

        forbidden_found = set(forbidden_actions) & available_actions
        if forbidden_found:
            result.add_error(f"Forbidden actions found: {', '.join(forbidden_found)}")

    def _check_min_rules(
        self,
        policy_data: Dict[str, Any],
        config: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check minimum number of rules."""
        min_rules = config.get("count", 0)
        rules = policy_data.get("rules", [])

        if len(rules) < min_rules:
            result.add_error(
                f"Policy has {len(rules)} rules, minimum required: {min_rules}"
            )

    def _check_max_rules(
        self,
        policy_data: Dict[str, Any],
        config: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check maximum number of rules."""
        max_rules = config.get("count", float("inf"))
        rules = policy_data.get("rules", [])

        if len(rules) > max_rules:
            result.add_error(
                f"Policy has {len(rules)} rules, maximum allowed: {max_rules}"
            )
