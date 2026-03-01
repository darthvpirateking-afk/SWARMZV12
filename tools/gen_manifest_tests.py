"""Generate per-manifest schema tests."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def sanitize_manifest_id(manifest_id: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", manifest_id).strip("_").lower()
    return value or "manifest"


def render_test(manifest_file_name: str) -> str:
    return f'''"""Auto-generated manifest validation test for {manifest_file_name}."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def test_manifest_{sanitize_manifest_id(Path(manifest_file_name).stem)}() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    schema = json.loads((repo_root / "schemas" / "agent-manifest.v1.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((repo_root / "config" / "manifests" / "{manifest_file_name}").read_text(encoding="utf-8-sig"))

    jsonschema.validate(instance=manifest, schema=schema)

    assert isinstance(manifest.get("inputs"), dict)
    assert isinstance(manifest.get("outputs"), dict)
    assert manifest.get("inputs")
    assert manifest.get("outputs")
'''


def generate(manifest_dir: Path, output_dir: Path) -> dict[str, str]:
    generated: dict[str, str] = {}
    for manifest_path in sorted(manifest_dir.glob("*.json")):
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        manifest_id = str(manifest_payload.get("id", manifest_path.stem))
        output_name = f"test_manifest_{sanitize_manifest_id(manifest_id)}.py"
        generated[output_name] = render_test(manifest_path.name)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate manifest tests")
    parser.add_argument("--manifest-dir", default="config/manifests", help="Manifest directory")
    parser.add_argument("--output-dir", default="tests", help="Output test directory")
    parser.add_argument("--check", action="store_true", help="Check files are up to date")
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = generate(manifest_dir, output_dir)
    mismatches: list[str] = []

    for file_name, content in generated.items():
        target = output_dir / file_name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                mismatches.append(file_name)
        else:
            target.write_text(content, encoding="utf-8")

    if args.check:
        expected = set(generated.keys())
        for existing in sorted(output_dir.glob("test_manifest_*.py")):
            if existing.name not in expected:
                mismatches.append(existing.name)

    if args.check and mismatches:
        print("Generated tests out of date:")
        for mismatch in mismatches:
            print(f" - {mismatch}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
