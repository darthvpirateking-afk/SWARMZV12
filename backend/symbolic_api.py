from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.symbolic_audit import list_audit_events
from backend.symbolic_governance import (
    activate_symbolic_system,
    enforce_operator_protocol,
    list_active_systems,
)
from backend.symbolic_lineage_log import list_lineage_records
from backend.symbolic_registry import (
    SYMBOLIC_FAMILIES,
    discover_families,
    get_entry_manifest,
    get_family_manifest,
    list_family_entries,
)
from backend.symbolic_runtime import dispatch_hook
from backend.symbolic_types import framed_symbolic_response

router = APIRouter()


def _entry_overview(entry: Dict[str, Any]) -> Dict[str, Any]:
    manifest = entry["manifest"]
    return {
        "entry_id": entry["entry_id"],
        "path": entry["path"],
        "id": manifest["id"],
        "name": manifest["name"],
        "origin": manifest["origin"],
        "symbolic_role": manifest["symbolic_role"],
    }


def _resolve_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    family = str(payload.get("family", "")).strip()
    entry_id = str(payload.get("entry_id", "")).strip()
    if not family:
        raise HTTPException(status_code=400, detail="family is required in payload")

    if not entry_id:
        try:
            family_payload = get_family_manifest(family)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "family": family,
            "entry_id": "__family__",
            "path": family_payload["path"],
            "manifest": family_payload["manifest"],
        }

    try:
        return get_entry_manifest(family, entry_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        try:
            family_payload = get_family_manifest(family)
            manifest = family_payload["manifest"]
            if entry_id in {"manifest", manifest.get("id", "")}:
                return {
                    "family": family,
                    "entry_id": "__family__",
                    "path": family_payload["path"],
                    "manifest": manifest,
                }
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _run_symbolic_hook(
    request: Request,
    hook: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    entry = _resolve_entry(payload)
    manifest = entry["manifest"]
    symbolic_id = manifest["id"]
    governance = enforce_operator_protocol(
        request=request,
        payload=payload,
        action=f"symbolic.{hook}",
        target=symbolic_id,
    )
    runtime_output = dispatch_hook(
        hook=hook,
        family=entry["family"],
        manifest=manifest,
        payload=payload,
    )
    return {
        **runtime_output,
        "entry_id": entry["entry_id"],
        "governance": governance,
    }


@router.get("/v1/nexusmon/symbolic/families")
async def symbolic_families():
    families = discover_families()
    return framed_symbolic_response(
        {
            "families": [
                {
                    "family": family,
                    "entry_count": len(list_family_entries(family)),
                }
                for family in families
            ],
            "active_systems": list_active_systems(),
        }
    )


@router.get("/v1/nexusmon/symbolic/families/{family}")
async def symbolic_family(family: str):
    try:
        family_payload = get_family_manifest(family)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown family")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="family manifest not found")
    return framed_symbolic_response(
        {
            "family": family_payload["family"],
            "path": family_payload["path"],
            "manifest": family_payload["manifest"],
            "entry_count": len(list_family_entries(family)),
        }
    )


@router.get("/v1/nexusmon/symbolic/families/{family}/entries")
async def symbolic_family_entries(family: str):
    try:
        entries = list_family_entries(family)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown family")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="family directory not found")
    return framed_symbolic_response(
        {
            "family": family,
            "entries": [_entry_overview(entry) for entry in entries],
        }
    )


@router.post("/v1/nexusmon/symbolic/invoke")
async def symbolic_invoke(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_invoke", payload)


@router.post("/v1/nexusmon/symbolic/consult")
async def symbolic_consult(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_consult", payload)


@router.post("/v1/nexusmon/symbolic/interpret")
async def symbolic_interpret(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_symbolic_interpretation", payload)


@router.post("/v1/nexusmon/symbolic/geometry")
async def symbolic_geometry(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_generate_geometry", payload)


@router.post("/v1/nexusmon/symbolic/anomaly")
async def symbolic_anomaly(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_trigger_anomaly", payload)


@router.post("/v1/nexusmon/symbolic/correspondence")
async def symbolic_correspondence(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_resolve_correspondence", payload)


@router.post("/v1/nexusmon/symbolic/altar")
async def symbolic_altar(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_render_altar_mode", payload)


@router.post("/v1/nexusmon/symbolic/branch")
async def symbolic_branch(request: Request, payload: Dict[str, Any]):
    return await _run_symbolic_hook(request, "on_simulate_branch", payload)


@router.get("/v1/nexusmon/symbolic/lineage")
async def symbolic_lineage():
    return framed_symbolic_response({"lineage": list_lineage_records()})


@router.get("/v1/nexusmon/symbolic/audit")
async def symbolic_audit():
    return framed_symbolic_response({"audit": list_audit_events()})


@router.post("/v1/nexusmon/symbolic/activate/{family_or_id}")
async def symbolic_activate(
    family_or_id: str,
    request: Request,
    payload: Dict[str, Any],
):
    target_id = family_or_id
    if family_or_id in SYMBOLIC_FAMILIES:
        try:
            target_id = get_family_manifest(family_or_id)["manifest"]["id"]
        except Exception:
            target_id = family_or_id
    else:
        for family in discover_families():
            for entry in list_family_entries(family):
                manifest = entry["manifest"]
                if entry["entry_id"] == family_or_id or manifest["id"] == family_or_id:
                    target_id = manifest["id"]
                    break

    governance = enforce_operator_protocol(
        request=request,
        payload=payload,
        action="symbolic.activate",
        target=target_id,
    )
    activate_symbolic_system(target_id)
    return framed_symbolic_response(
        {
            "ok": True,
            "activated": target_id,
            "active_systems": list_active_systems(),
            "governance": governance,
        }
    )
