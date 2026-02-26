"""
Tests for Geometry Layer (P1.3)

Validates geometric transformations and context projection.
"""

import pytest
from core.geometry import GeometryLayer, Transform, TransformType, GeometryResult


def test_normalize_transform():
    """Normalize should scale to 0-1 range."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="normalize_test",
        transform_type=TransformType.NORMALIZE,
        target_field="value",
        parameters={"min": 0.0, "max": 100.0},
    ))
    
    result = geometry.apply_transforms({"value": 50.0})
    
    assert result.transformed_context["value"] == 0.5
    assert "normalize_test" in result.transforms_applied


def test_normalize_clamps_bounds():
    """Normalize should clamp values outside range."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="normalize_bounded",
        transform_type=TransformType.NORMALIZE,
        target_field="value",
        parameters={"min": 0.0, "max": 100.0},
    ))
    
    # Value above max
    result1 = geometry.apply_transforms({"value": 150.0})
    assert result1.transformed_context["value"] == 1.0
    
    # Value below min
    result2 = geometry.apply_transforms({"value": -50.0})
    assert result2.transformed_context["value"] == 0.0


def test_scale_fixed_factor():
    """Scale with fixed factor should multiply value."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="scale_fixed",
        transform_type=TransformType.SCALE,
        target_field="value",
        parameters={"factor": 2.5},
    ))
    
    result = geometry.apply_transforms({"value": 10.0})
    
    assert result.transformed_context["value"] == 25.0


def test_scale_dynamic_field():
    """Scale should use another field for dynamic scaling."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="scale_dynamic",
        transform_type=TransformType.SCALE,
        target_field="complexity",
        parameters={"scale_field": "mission_rank", "base_scale": 1.0},
    ))
    
    result = geometry.apply_transforms({
        "complexity": 5.0,
        "mission_rank": 3.0,
    })
    
    assert result.transformed_context["complexity"] == 15.0  # 5 * 3 * 1.0


def test_clamp_transform():
    """Clamp should limit values to range."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="clamp_test",
        transform_type=TransformType.CLAMP,
        target_field="value",
        parameters={"min": 10.0, "max": 90.0},
    ))
    
    # Within range
    result1 = geometry.apply_transforms({"value": 50.0})
    assert result1.transformed_context["value"] == 50.0
    
    # Above max
    result2 = geometry.apply_transforms({"value": 150.0})
    assert result2.transformed_context["value"] == 90.0
    
    # Below min
    result3 = geometry.apply_transforms({"value": 5.0})
    assert result3.transformed_context["value"] == 10.0


def test_translate_transform():
    """Translate should shift value by offset."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="translate_test",
        transform_type=TransformType.TRANSLATE,
        target_field="value",
        parameters={"offset": 100.0},
    ))
    
    result = geometry.apply_transforms({"value": 50.0})
    
    assert result.transformed_context["value"] == 150.0


def test_project_magnitude():
    """Project with magnitude mode should compute vector length."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="project_magnitude",
        transform_type=TransformType.PROJECT,
        target_field="risk_vector",
        parameters={"mode": "magnitude"},
    ))
    
    result = geometry.apply_transforms({
        "risk_vector": {"x": 3.0, "y": 4.0}  # 3-4-5 triangle
    })
    
    assert result.transformed_context["risk_vector"] == 5.0


def test_project_max():
    """Project with max mode should extract maximum component."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="project_max",
        transform_type=TransformType.PROJECT,
        target_field="scores",
        parameters={"mode": "max"},
    ))
    
    result = geometry.apply_transforms({
        "scores": {"risk": 30, "cost": 80, "complexity": 50}
    })
    
    assert result.transformed_context["scores"] == 80


def test_rotate_phase_shift():
    """Rotate should apply phase shift for cyclic features."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="rotate_time",
        transform_type=TransformType.ROTATE,
        target_field="hour",
        parameters={"angle": 90.0, "period": 360.0},
    ))
    
    result = geometry.apply_transforms({"hour": 0.0})
    
    # 0 + 90 degree shift
    assert abs(result.transformed_context["hour"] - 90.0) < 0.01


def test_missing_field_skipped():
    """Transforms should skip missing fields without error."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="normalize_nonexistent",
        transform_type=TransformType.NORMALIZE,
        target_field="nonexistent_field",
        parameters={"min": 0.0, "max": 100.0},
    ))
    
    result = geometry.apply_transforms({"other_field": 123})
    
    # Should not error, just skip
    assert "normalize_nonexistent" not in result.transforms_applied
    assert result.original_context == result.transformed_context


def test_evaluate_returns_both_contexts():
    """Evaluate should return both original and transformed contexts."""
    geometry = GeometryLayer()
    geometry.transforms.clear()
    
    geometry.add_transform(Transform(
        name="scale_test",
        transform_type=TransformType.SCALE,
        target_field="value",
        parameters={"factor": 2.0},
    ))
    
    result = geometry.evaluate({}, {"value": 10.0})
    
    assert result.passed is True
    assert result.metadata["original_context"]["value"] == 10.0
    assert result.metadata["transformed_context"]["value"] == 20.0
    assert "scale_test" in result.metadata["transforms_applied"]


def test_deterministic_flag():
    """GeometryResult should always report as deterministic."""
    geometry = GeometryLayer()
    
    result = geometry.apply_transforms({"value": 123})
    
    assert result.deterministic is True
