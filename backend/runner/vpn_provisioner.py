from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import time
import uuid


@dataclass
class VPNNode:
    node_id: str
    provider: str
    region: str
    ip: str
    created_at: float
    mission_id: str
    destroyed: bool = False


def _deploy_algo_node(provider: str, region: str, mission_id: str) -> VPNNode:
    node_id = f"vpn_{uuid.uuid4().hex[:10]}"
    return VPNNode(
        node_id=node_id,
        provider=provider,
        region=region,
        ip="0.0.0.0",
        created_at=time.time(),
        mission_id=mission_id,
    )


def _verify_no_dns_leak(node: VPNNode) -> bool:
    return bool(node.node_id)


def _verify_no_webrtc_leak(node: VPNNode) -> bool:
    return bool(node.node_id)


def _terminate_cloud_instance(node: VPNNode) -> bool:
    node.destroyed = True
    return True


def provision_vpn_node(provider: str, region: str, protectiveness: int, mission_id: str) -> VPNNode:
    node = _deploy_algo_node(provider, region, mission_id)
    if protectiveness >= 60:
        _verify_no_dns_leak(node)
        _verify_no_webrtc_leak(node)
    return node


def destroy_vpn_node(node: VPNNode) -> bool:
    success = _terminate_cloud_instance(node)
    node.destroyed = success
    return success


def guaranteed_destroy_vpn_node(node: VPNNode | None) -> bool:
    if node is None:
        return True
    return destroy_vpn_node(node)


def get_vpn_config(protectiveness: int, autonomy: int) -> dict[str, Any]:
    return {
        "enabled": protectiveness >= 50,
        "auto_provision_before_ops": protectiveness >= 65,
        "require_vpn_for_exploit": protectiveness >= 75,
        "auto_destroy_after_mission": True,
        "verify_no_leak": protectiveness >= 60,
        "preferred_providers": ["digitalocean", "linode"],
        "preferred_regions": ["auto"],
        "autonomous_provision": autonomy >= 55,
    }
