"""
Geometry Layer (P1.3 - Contextual Transformation)

Transforms context and perspective before governance decisions.
Applies spatial reasoning and dimensional projections to action/context.

Design:
- Transform coordinates: map actions to appropriate decision spaces
- Project dimensions: reduce/expand context for specific checks
- Apply transformations: normalize, scale, rotate context vectors
- Deterministic transforms only (no randomness)
"""

import json
import time
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_GEOMETRY_CONFIG_FILE = _CONFIG_DIR / "governance" / "geometry.json"

from core.reversible import LayerResult


class TransformType(str, Enum):
    """Types of geometric transformations."""

    NORMALIZE = "normalize"  # Scale to 0-1
    SCALE = "scale"  # Multiply by factor
    CLAMP = "clamp"  # Limit to range
    PROJECT = "project"  # Project onto subspace
    ROTATE = "rotate"  # Rotate in feature space
    TRANSLATE = "translate"  # Shift by offset


@dataclass
class Transform:
    """A single geometric transformation."""

    name: str
    transform_type: TransformType
    target_field: str  # Which field to transform
    parameters: Dict[str, Any]


@dataclass
class GeometryResult:
    """Result of applying geometric transformations."""

    original_context: Dict[str, Any]
    transformed_context: Dict[str, Any]
    transforms_applied: List[str]
    deterministic: bool


class GeometryLayer:
    """
    Context transformation engine for governance.

    Applies geometric transformations to normalize/project/scale
    context before it reaches decision layers.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.transforms: List[Transform] = []
        self._config_path = config_path or _GEOMETRY_CONFIG_FILE
        self._load_default_transforms()
        self._apply_config_overrides()

    def _apply_config_overrides(self) -> None:
        """Override transform parameters from config/governance/geometry.json if it exists."""
        if not self._config_path.exists():
            return
        try:
            with open(self._config_path, "r") as f:
                cfg = json.load(f)
            for tdesc in cfg.get("transforms", []):
                name = tdesc.get("name")
                params = tdesc.get("parameters", {})
                for t in self.transforms:
                    if t.name == name:
                        t.parameters.update(
                            {k: v for k, v in params.items() if not k.startswith("_")}
                        )
                        break
        except Exception:
            pass  # Config errors are non-fatal; defaults remain active

    def _load_default_transforms(self):
        """Initialize with standard transformations."""
        # Normalize budget to 0-1 range
        self.add_transform(
            Transform(
                name="normalize_budget",
                transform_type=TransformType.NORMALIZE,
                target_field="budget_remaining",
                parameters={"min": -1000.0, "max": 10000.0},
            )
        )

        # Clamp risk scores to 0-100
        self.add_transform(
            Transform(
                name="clamp_risk",
                transform_type=TransformType.CLAMP,
                target_field="risk_score",
                parameters={"min": 0.0, "max": 100.0},
            )
        )

        # Scale complexity by mission rank
        self.add_transform(
            Transform(
                name="scale_complexity_by_rank",
                transform_type=TransformType.SCALE,
                target_field="complexity",
                parameters={"scale_field": "mission_rank", "base_scale": 1.0},
            )
        )

    def add_transform(self, transform: Transform):
        """Add a geometric transformation."""
        self.transforms.append(transform)

    def _apply_normalize(self, value: float, params: Dict[str, Any]) -> float:
        """Normalize value to 0-1 range."""
        min_val = params.get("min", 0.0)
        max_val = params.get("max", 1.0)

        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))

    def _apply_scale(
        self, value: float, params: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Scale value by a factor."""
        if "scale_field" in params:
            # Dynamic scaling based on another field
            scale_factor = context.get(params["scale_field"], 1.0)
            base_scale = params.get("base_scale", 1.0)
            return value * scale_factor * base_scale
        else:
            # Fixed scaling
            factor = params.get("factor", 1.0)
            return value * factor

    def _apply_clamp(self, value: float, params: Dict[str, Any]) -> float:
        """Clamp value to range."""
        min_val = params.get("min", float("-inf"))
        max_val = params.get("max", float("inf"))
        return max(min_val, min(max_val, value))

    def _apply_translate(self, value: float, params: Dict[str, Any]) -> float:
        """Translate (shift) value by offset."""
        offset = params.get("offset", 0.0)
        return value + offset

    def _apply_project(
        self, value: Any, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """
        Project onto subspace (dimension reduction).

        Example: Project multi-dimensional risk vector onto single scalar.
        """
        projection_mode = params.get("mode", "identity")

        if projection_mode == "identity":
            return value

        elif projection_mode == "magnitude":
            # If value is dict, compute magnitude
            if isinstance(value, dict):
                return math.sqrt(
                    sum(v**2 for v in value.values() if isinstance(v, (int, float)))
                )
            return abs(value)

        elif projection_mode == "max":
            # Project to maximum component
            if isinstance(value, dict):
                return max(value.values())
            elif isinstance(value, list):
                return max(value)
            return value

        return value

    def _apply_rotate(self, value: float, params: Dict[str, Any]) -> float:
        """
        Rotate in feature space.

        For 1D: applies phase shift (useful for cyclic features like time of day).
        """
        angle = params.get("angle", 0.0)
        period = params.get("period", 360.0)

        # Apply rotation (phase shift) in the same units as period
        rotated = (value + angle) % period
        return rotated

    def apply_transforms(
        self,
        context: Dict[str, Any],
    ) -> GeometryResult:
        """
        Apply all configured transforms to context.

        Returns both original and transformed context.
        """
        transformed = context.copy()
        applied = []

        for transform in self.transforms:
            field = transform.target_field

            # Skip if field not present
            if field not in transformed:
                continue

            value = transformed[field]

            # Apply transformation based on type
            try:
                if transform.transform_type == TransformType.NORMALIZE:
                    if isinstance(value, (int, float)):
                        transformed[field] = self._apply_normalize(
                            value, transform.parameters
                        )

                elif transform.transform_type == TransformType.SCALE:
                    if isinstance(value, (int, float)):
                        transformed[field] = self._apply_scale(
                            value, transform.parameters, context
                        )

                elif transform.transform_type == TransformType.CLAMP:
                    if isinstance(value, (int, float)):
                        transformed[field] = self._apply_clamp(
                            value, transform.parameters
                        )

                elif transform.transform_type == TransformType.TRANSLATE:
                    if isinstance(value, (int, float)):
                        transformed[field] = self._apply_translate(
                            value, transform.parameters
                        )

                elif transform.transform_type == TransformType.PROJECT:
                    transformed[field] = self._apply_project(
                        value, transform.parameters, context
                    )

                elif transform.transform_type == TransformType.ROTATE:
                    if isinstance(value, (int, float)):
                        transformed[field] = self._apply_rotate(
                            value, transform.parameters
                        )

                applied.append(transform.name)

            except Exception as e:
                # Log but don't fail on transform errors
                import logging

                logging.warning(f"Transform {transform.name} failed: {e}")
                continue

        return GeometryResult(
            original_context=context,
            transformed_context=transformed,
            transforms_applied=applied,
            deterministic=True,
        )

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Applies transformations and returns transformed context in metadata.
        """
        geometry_result = self.apply_transforms(context)

        return LayerResult(
            layer="geometry",
            passed=True,  # Geometry doesn't block, it transforms
            reason=f"Applied {len(geometry_result.transforms_applied)} transformations",
            metadata={
                "original_context": geometry_result.original_context,
                "transformed_context": geometry_result.transformed_context,
                "transforms_applied": geometry_result.transforms_applied,
            },
            timestamp=time.time(),
        )


# Module-level instance
_geometry = GeometryLayer()


def add_transform(transform: Transform):
    """Add a transform to global instance."""
    _geometry.add_transform(transform)


def apply_transforms(context: Dict[str, Any]) -> GeometryResult:
    """Apply transforms using global instance."""
    return _geometry.apply_transforms(context)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _geometry.evaluate(action, context)
