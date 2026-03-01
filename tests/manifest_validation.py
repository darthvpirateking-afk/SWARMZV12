"""Validate every manifest in config/manifests against schemas/agent-manifest.v1.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "agent-manifest.v1.json"
MANIFEST_DIR = REPO_ROOT / "config" / "manifests"


@pytest.fixture(scope="session")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))


@pytest.fixture(scope="session")
def validator(schema: dict) -> jsonschema.Draft7Validator:
    jsonschema.Draft7Validator.check_schema(schema)
    return jsonschema.Draft7Validator(schema)


def _errors(validator: jsonschema.Draft7Validator, payload: dict) -> list[str]:
    return [f"[{err.json_path}] {err.message}" for err in validator.iter_errors(payload)]


def test_all_manifests_validate(validator: jsonschema.Draft7Validator) -> None:
    failures: list[str] = []
    for manifest_path in sorted(MANIFEST_DIR.glob("*.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        errors = _errors(validator, payload)
        if errors:
            failures.append(f"{manifest_path.name}: " + " | ".join(errors))
    assert not failures, "\n".join(failures)


def test_missing_required_field_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    del payload["version"]
    errors = _errors(validator, payload)
    assert errors
    assert "required property" in errors[0]


def test_unknown_top_level_property_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["rogue"] = True
    errors = _errors(validator, payload)
    assert errors
    assert "Additional properties are not allowed" in errors[0]


def test_invalid_semver_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["version"] = "1.0"
    errors = _errors(validator, payload)
    assert errors


def test_invalid_spawn_policy_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["spawn_policy"] = "singleton"
    errors = _errors(validator, payload)
    assert errors


def test_invalid_constraints_shape_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["constraints"] = "invalid"
    errors = _errors(validator, payload)
    assert errors


def test_invalid_error_modes_shape_fails(validator: jsonschema.Draft7Validator) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["error_modes"] = "invalid"
    errors = _errors(validator, payload)
    assert errors


def test_extensions_object_allowed_only_in_extensions_field(
    validator: jsonschema.Draft7Validator,
) -> None:
    payload = json.loads((MANIFEST_DIR / "fetcher@1.0.0.json").read_text(encoding="utf-8-sig"))
    payload["extensions"] = {"custom": {"enabled": True}}
    assert not _errors(validator, payload)
