import json
from pathlib import Path

from swarmz_runtime.verify import patchpacks


def _configure_patchpack_root(monkeypatch, tmp_path):
    pack_root = tmp_path / "patchpacks"
    pack_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(patchpacks, "PACK_ROOT", pack_root)
    monkeypatch.setattr(
        patchpacks.provenance,
        "append_audit",
        lambda *args, **kwargs: {"event": args[0] if args else "audit"},
    )
    return pack_root


def test_apply_requires_operator_approval(monkeypatch, tmp_path):
    _configure_patchpack_root(monkeypatch, tmp_path)
    monkeypatch.delenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", raising=False)

    generated = patchpacks.generate_patchpack("test")
    result = patchpacks.apply_patchpack(generated["id"])

    assert result["ok"] is False
    assert "approval" in result["error"]


def test_apply_succeeds_with_operator_approval(monkeypatch, tmp_path):
    _configure_patchpack_root(monkeypatch, tmp_path)
    monkeypatch.delenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", raising=False)

    generated = patchpacks.generate_patchpack("test")
    pack_dir = Path(generated["path"])
    (pack_dir / patchpacks.APPROVAL_NAME).write_text(
        json.dumps(
            {
                "approved": True,
                "approved_by": "operator",
                "approved_at": "2026-02-27T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    result = patchpacks.apply_patchpack(generated["id"])

    assert result["ok"] is True
    assert result["approval"]["approved_by"] == "operator"


def test_apply_blocks_forbidden_manifest_paths(monkeypatch, tmp_path):
    _configure_patchpack_root(monkeypatch, tmp_path)
    monkeypatch.delenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", raising=False)

    generated = patchpacks.generate_patchpack("test")
    pack_dir = Path(generated["path"])
    manifest = json.loads((pack_dir / patchpacks.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["files"] = [{"path": "core/unsafe.py"}]
    (pack_dir / patchpacks.MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (pack_dir / patchpacks.APPROVAL_NAME).write_text(
        json.dumps({"approved": True, "approved_by": "operator"}),
        encoding="utf-8",
    )

    result = patchpacks.apply_patchpack(generated["id"])

    assert result["ok"] is False
    assert "forbidden" in result["error"]


def test_apply_blocks_non_plugin_paths(monkeypatch, tmp_path):
    _configure_patchpack_root(monkeypatch, tmp_path)
    monkeypatch.delenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", raising=False)

    generated = patchpacks.generate_patchpack("test")
    pack_dir = Path(generated["path"])
    manifest = json.loads((pack_dir / patchpacks.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["files"] = [{"path": "nexusmon/runtime/loader.py"}]
    (pack_dir / patchpacks.MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (pack_dir / patchpacks.APPROVAL_NAME).write_text(
        json.dumps({"approved": True, "approved_by": "operator"}),
        encoding="utf-8",
    )

    result = patchpacks.apply_patchpack(generated["id"])

    assert result["ok"] is False
    assert "plugins" in result["error"]


def test_env_override_allows_apply_without_file_approval(monkeypatch, tmp_path):
    _configure_patchpack_root(monkeypatch, tmp_path)
    monkeypatch.setenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", "1")

    generated = patchpacks.generate_patchpack("test")
    result = patchpacks.apply_patchpack(generated["id"])

    assert result["ok"] is True
    assert result["approval"]["source"] == "env_override"
