from __future__ import annotations

from typing import Any

from backend.runner.container_manager import get_container_image, get_isolation_level
from backend.runner.vm_provisioner import get_vm_config, provision_vm


def provision_environment(
    backend: str,
    mission_type: str,
    profile_name: str,
    creativity: int,
    autonomy: int,
    patience: int,
    protectiveness: int,
    mood: str | None = "calm",
) -> dict[str, Any]:
    normalized = (backend or "docker").strip().lower()

    if normalized in {"qemu", "libvirt", "vm"}:
        vm = provision_vm(profile_name, creativity=creativity, patience=patience, protectiveness=protectiveness)
        return {
            "backend": "vm",
            "config": get_vm_config(creativity=creativity, patience=patience, protectiveness=protectiveness),
            "environment": vm,
        }

    image = get_container_image(
        mission_type=mission_type,
        creativity=creativity,
        autonomy=autonomy,
        mood=mood,
    )
    return {
        "backend": "docker",
        "environment": {
            "image": image,
            "isolation": get_isolation_level(protectiveness=protectiveness, mood=mood),
        },
    }
