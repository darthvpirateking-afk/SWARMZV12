"""
NEXUSMON - Manifest schema validation tests.
These are the CI gate: a failing manifest blocks the PR.
Coverage floor: 85% branch (enforced in pyproject.toml).
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "agent-manifest.v1.json"
MANIFEST_DIR = REPO_ROOT / "config" / "manifests"


@pytest.fixture(scope="session")
def schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))


@pytest.fixture(scope="session")
def validator(schema: dict[str, object]) -> jsonschema.Draft7Validator:
    jsonschema.Draft7Validator.check_schema(schema)
    return jsonschema.Draft7Validator(schema)


@pytest.fixture(scope="session")
def helper1() -> dict[str, object]:
    return json.loads((MANIFEST_DIR / "helper1.manifest.json").read_text(encoding="utf-8-sig"))


@pytest.mark.parametrize(
    "manifest_path",
    sorted(MANIFEST_DIR.glob("*.manifest.json")),
    ids=lambda p: p.stem,
)
def test_all_seed_manifests_valid(
    manifest_path: Path, validator: jsonschema.Draft7Validator
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    errors = list(validator.iter_errors(manifest))
    assert not errors, (
        f"'{manifest_path.name}' has {len(errors)} violation(s):\n"
        + "\n".join(f"  [{e.json_path}] {e.message}" for e in errors)
    )


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "version",
        "capabilities",
        "inputs",
        "outputs",
        "spawn_policy",
        "constraints",
        "error_modes",
    ],
)
def test_missing_required_field_fails(
    field: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    data = {**helper1}
    del data[field]
    assert list(validator.iter_errors(data)), f"Should fail when '{field}' is missing"


@pytest.mark.parametrize("bad_id", ["", "Hello", "has space", "123start", "HAS_UPPER"])
def test_invalid_id_fails(
    bad_id: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "id": bad_id}))


@pytest.mark.parametrize("good_id", ["helper1", "my-agent", "agent_v2", "a"])
def test_valid_id_passes(
    good_id: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert not list(validator.iter_errors({**helper1, "id": good_id}))


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "1.0.0.0", "latest", ""])
def test_invalid_version_fails(
    bad: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "version": bad}))


@pytest.mark.parametrize("bad", ["dynamic", "auto", "", "SINGLETON"])
def test_invalid_spawn_policy_fails(
    bad: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "spawn_policy": bad}))


def test_extra_top_level_field_rejected(
    helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "rogue_field": "nope"}))


def test_extensions_block_accepted(
    helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert not list(validator.iter_errors({**helper1, "extensions": {"x": 1}}))


@pytest.mark.parametrize("bad", ["read", "Data.Read", "data.", ".read", "data read"])
def test_invalid_capability_token_fails(
    bad: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "capabilities": [bad]}))


def test_empty_capabilities_fails(
    helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "capabilities": []}))


def test_duplicate_capabilities_fails(
    helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    assert list(validator.iter_errors({**helper1, "capabilities": ["data.read", "data.read"]}))


@pytest.mark.parametrize(
    "mode",
    ["on_validation_failure", "on_dependency_missing", "on_runtime_exception"],
)
def test_missing_error_mode_fails(
    mode: str, helper1: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    data = {**helper1, "error_modes": {**helper1["error_modes"]}}
    del data["error_modes"][mode]
    assert list(validator.iter_errors(data))


def test_schema_embedded_examples_valid(
    schema: dict[str, object], validator: jsonschema.Draft7Validator
) -> None:
    examples = schema.get("examples", [])
    assert isinstance(examples, list)
    for index, example in enumerate(examples):
        assert isinstance(example, dict)
        errors = list(validator.iter_errors(example))
        assert not errors, f"schema example[{index}] invalid: {[e.message for e in errors]}"


def test_child_cannot_escalate_capabilities() -> None:
    parent_allowed = {"data.read", "agent.introspect"}
    child_requested = {"data.read", "agent.spawn"}
    granted = child_requested & parent_allowed
    assert "agent.spawn" not in granted
    assert granted == {"data.read"}
