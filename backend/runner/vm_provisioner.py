from __future__ import annotations

from enum import Enum
from typing import Any
import uuid


class VMBackend(Enum):
    DOCKER = "docker"
    QEMU = "qemu"
    LIBVIRT = "libvirt"


VM_PROFILES: dict[str, dict[str, Any]] = {
    "windows_server_2019": {
        "backend": VMBackend.QEMU,
        "image": "/data/vm_images/win_server_2019.qcow2",
        "ram_gb": 4,
        "vcpus": 2,
        "network": "isolated_vlan",
    },
    "windows_ad_domain": {
        "backend": VMBackend.LIBVIRT,
        "image": "/data/vm_images/win_ad_domain.qcow2",
        "ram_gb": 8,
        "vcpus": 4,
        "network": "ad_test_vlan",
        "services": ["active_directory", "dns", "kerberos"],
    },
    "linux_legacy_kernel": {
        "backend": VMBackend.QEMU,
        "image": "/data/vm_images/ubuntu_18_legacy.qcow2",
        "ram_gb": 2,
        "vcpus": 2,
        "kernel": "4.15.0",
        "network": "isolated_vlan",
    },
}


def _generate_id() -> str:
    return uuid.uuid4().hex[:10]


def provision_vm(
    profile_name: str, creativity: int, patience: int, protectiveness: int
) -> dict[str, Any]:
    profile = VM_PROFILES.get(profile_name)
    if not profile:
        raise ValueError(f"No VM profile: {profile_name}")

    return {
        "vm_id": f"nexus_vm_{_generate_id()}",
        "profile": profile_name,
        "backend": profile["backend"].value,
        "snapshot_pre": protectiveness >= 50,
        "auto_destroy": True,
        "ready_signal": "vm_boot_complete",
        "boot_timeout_s": int((patience / 100) * 120),
        "network_mode": "isolated",
        "network_isolation_required": True,
        "spec": profile,
    }


def get_vm_config(
    creativity: int, patience: int, protectiveness: int
) -> dict[str, Any]:
    return {
        "enabled": patience >= 60,
        "preferred_for_windows": True,
        "snapshot_support": protectiveness >= 50,
        "auto_teardown": True,
        "max_concurrent_vms": int((creativity / 100) * 3),
        "allow_custom_vm_images": creativity >= 70,
        "network_isolation_required": True,
    }
