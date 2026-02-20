# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Core infrastructure domain models for SWARMZ infra orchestrator.

These models describe data center resources (racks, servers, storage,
networks, power, cooling, VMs, containers, tenants, etc.).  They are
pure data structures; all behavior lives in higher-level engines and
plugins.

This module is intentionally conservative and is not imported anywhere
by default. It becomes active only when infra_orchestrator_enabled is
true and higher layers opt in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# --- Physical topology ------------------------------------------------------


@dataclass
class DataCenter:
    id: str
    name: str
    location: str
    racks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Rack:
    id: str
    datacenter_id: str
    name: str
    units: int = 42
    power_feeds: List[str] = field(default_factory=list)
    cooling_zones: List[str] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerNode:
    id: str
    rack_id: str
    hostname: str
    cpu_cores: int
    memory_gb: float
    storage_tb: float
    gpu_ids: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GPUNode:
    id: str
    server_id: str
    model: str
    memory_gb: float
    compute_capability: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageArray:
    id: str
    datacenter_id: str
    name: str
    capacity_tb: float
    raid_level: Optional[str] = None
    encrypted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkSegment:
    id: str
    datacenter_id: str
    cidr: str
    vlan: Optional[int] = None
    purpose: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PowerFeed:
    id: str
    datacenter_id: str
    capacity_kw: float
    redundant_with: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoolingZone:
    id: str
    datacenter_id: str
    capacity_kw: float
    racks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Virtual resources ------------------------------------------------------


@dataclass
class VMInstance:
    id: str
    tenant_id: str
    server_id: Optional[str]
    vcpus: int
    memory_gb: float
    disk_gb: float
    status: str = "stopped"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerInstance:
    id: str
    tenant_id: str
    cluster_id: str
    cpu_shares: float
    memory_gb: float
    status: str = "stopped"
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Tenants, allocations, and billing -------------------------------------


@dataclass
class Tenant:
    id: str
    name: str
    contact: Optional[str] = None
    sla_tier: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ColoAllocation:
    id: str
    tenant_id: str
    datacenter_id: str
    rack_ids: List[str] = field(default_factory=list)
    power_kw: float = 0.0
    cooling_kw: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CloudSubscription:
    id: str
    tenant_id: str
    max_vms: int
    max_storage_tb: float
    max_bandwidth_tb: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Backup and disaster recovery -----------------------------------------


@dataclass
class BackupJob:
    id: str
    target_resource_id: str
    schedule: str  # cron-like string or simple interval descriptor
    retention_days: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DRPlan:
    id: str
    primary_datacenter_id: str
    secondary_datacenter_id: str
    rpo_minutes: int
    rto_minutes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- GPU / blockchain hosting ---------------------------------------------


@dataclass
class GPUCluster:
    id: str
    name: str
    gpu_node_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MiningJob:
    id: str
    tenant_id: str
    gpu_cluster_id: str
    algorithm: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockchainNode:
    id: str
    tenant_id: str
    network: str  # e.g., "ethereum", "bitcoin", "custom"
    server_id: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# The actual orchestration engines, metrics ingest, and mission wiring live
# in other modules. This file is intentionally limited to data structures so
# importing it cannot change behavior on its own.
