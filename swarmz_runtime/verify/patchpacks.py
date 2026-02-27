# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import os
import time
from pathlib import Path
from typing import Dict, Any

from swarmz_runtime.verify import provenance

PACK_ROOT = Path(__file__).resolve().parents[2] / "packs" / "patchpacks"
PACK_ROOT.mkdir(parents=True, exist_ok=True)
MANIFEST_NAME = "manifest.json"
APPROVAL_NAME = "operator_approval.json"
FORBIDDEN_PREFIXES = ("core/", "governance/", "protocol/")
REQUIRED_PREFIX = "plugins/"


def _load_manifest(base: Path) -> tuple[dict[str, Any] | None, str | None]:
    manifest_path = base / MANIFEST_NAME
    if not manifest_path.exists():
        return None, f"missing {MANIFEST_NAME}"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None, f"invalid {MANIFEST_NAME}"
    if not isinstance(manifest, dict):
        return None, f"invalid {MANIFEST_NAME}"
    return manifest, None


def _entry_path(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return str(entry.get("path", ""))
    return ""


def _validate_manifest_paths(manifest: Dict[str, Any]) -> tuple[bool, str | None]:
    files = manifest.get("files", [])
    if not isinstance(files, list):
        return False, "manifest files must be a list"
    for entry in files:
        raw_path = _entry_path(entry).strip()
        if not raw_path:
            continue
        normalized = raw_path.replace("\\", "/").lstrip("./")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            return False, f"unsafe patch path: {raw_path}"
        for prefix in FORBIDDEN_PREFIXES:
            if normalized.startswith(prefix):
                return False, f"path touches forbidden area: {raw_path}"
        if not normalized.startswith(REQUIRED_PREFIX):
            return False, f"path must stay under plugins/: {raw_path}"
    return True, None


def _approval_status(base: Path) -> Dict[str, Any]:
    if os.getenv("SWARMZ_PATCHPACK_ALLOW_UNAPPROVED", "").strip() == "1":
        return {"approved": True, "source": "env_override", "approved_by": "override"}
    approval_path = base / APPROVAL_NAME
    if not approval_path.exists():
        return {"approved": False, "reason": "operator approval required"}
    try:
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    except Exception:
        return {"approved": False, "reason": "invalid operator approval file"}
    if not isinstance(approval, dict):
        return {"approved": False, "reason": "invalid operator approval file"}
    if not approval.get("approved"):
        return {"approved": False, "reason": "operator approval not granted"}
    approved_by = str(approval.get("approved_by", "")).strip()
    if not approved_by:
        return {"approved": False, "reason": "operator approval missing approved_by"}
    return {
        "approved": True,
        "source": "file",
        "approved_by": approved_by,
        "approved_at": approval.get("approved_at"),
    }


def generate_patchpack(note: str = "auto") -> Dict[str, Any]:
    ts = int(time.time() * 1000)
    pack_id = f"patch-{ts}"
    base = PACK_ROOT / pack_id
    base.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": pack_id,
        "created": ts,
        "note": note,
        "files": [],
    }
    (base / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (base / APPROVAL_NAME).write_text(
        json.dumps(
            {
                "approved": False,
                "approved_by": "",
                "approved_at": "",
                "note": "Set approved=true and approved_by before apply.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (base / "plan.md").write_text(f"# Patchpack {pack_id}\n\n- note: {note}\n")
    (base / "diff.patch").write_text("(no diff captured)\n")
    for name, body in {
        "apply.ps1": "Write-Host 'apply stub'",
        "rollback.ps1": "Write-Host 'rollback stub'",
        "verify.ps1": "Write-Host 'verify stub'",
        "apply.cmd": "@echo apply stub",
        "rollback.cmd": "@echo rollback stub",
        "verify.cmd": "@echo verify stub",
    }.items():
        (base / name).write_text(body)
    provenance.append_audit("patchpack_generated", {"id": pack_id})
    return {"ok": True, "id": pack_id, "path": str(base)}


def apply_patchpack(pack_id: str) -> Dict[str, Any]:
    base = PACK_ROOT / pack_id
    if not base.exists():
        return {"ok": False, "error": "missing pack"}
    manifest, manifest_error = _load_manifest(base)
    if manifest_error:
        return {"ok": False, "error": manifest_error}
    manifest_ok, manifest_path_error = _validate_manifest_paths(manifest or {})
    if not manifest_ok:
        provenance.append_audit(
            "patchpack_apply_blocked",
            {"id": pack_id, "reason": manifest_path_error},
        )
        return {"ok": False, "error": manifest_path_error}

    approval = _approval_status(base)
    if not approval.get("approved"):
        provenance.append_audit(
            "patchpack_apply_blocked",
            {"id": pack_id, "reason": approval.get("reason")},
        )
        return {"ok": False, "error": approval.get("reason")}

    provenance.append_audit(
        "patchpack_apply",
        {
            "id": pack_id,
            "approved_by": approval.get("approved_by", ""),
            "approval_source": approval.get("source", ""),
        },
    )
    file_count = len((manifest or {}).get("files", []))
    return {
        "ok": True,
        "message": "apply stub",
        "validated_files": file_count,
        "approval": approval,
    }


def rollback_patchpack(pack_id: str) -> Dict[str, Any]:
    base = PACK_ROOT / pack_id
    if not base.exists():
        return {"ok": False, "error": "missing pack"}
    provenance.append_audit("patchpack_rollback", {"id": pack_id})
    return {"ok": True, "message": "rollback stub"}
