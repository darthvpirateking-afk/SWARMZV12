# SWARMZ Universe-Mesh v2
# Multi-Cosmology Routing

from typing import Dict, Any, List


class CosmologyNode:
    def __init__(self, name: str, worlds: List[str], entropy_model: Dict[str, Any]):
        self.name = name
        self.worlds = worlds
        self.entropy_model = entropy_model


class InterCosmicLink:
    def __init__(self, source: CosmologyNode, target: CosmologyNode):
        self.source = source
        self.target = target
        self.validated = False

    def validate(self, governor: Any, shadow_ledger: Any):
        """Validate the link using the governor and shadow ledger."""
        self.validated = governor.approve_link(self) and shadow_ledger.log_link(self)
        return self.validated


class CosmicRouter:
    def __init__(self):
        self.links = []

    def add_link(self, link: InterCosmicLink):
        if link.validate():
            self.links.append(link)

    def route_mission(
        self, mission: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route a mission across cosmologies.

        Selects valid inter-cosmic links that satisfy the supplied constraints
        and returns a routing plan with an ordered hop list.

        Args:
            mission: Dict with at least ``source`` (cosmology name) and
                     ``target`` (cosmology name) keys, plus optional metadata.
            constraints: Filtering rules, e.g. ``{"require_validated": True,
                         "max_hops": 3}``.

        Returns:
            Dict with keys:
              - ``ok`` (bool): True if at least one path was found.
              - ``hops``: List of link descriptors (source→target names).
              - ``total_links``: Number of candidate links considered.
              - ``reason``: Human-readable status string.
        """
        source = mission.get("source", "")
        target = mission.get("target", "")
        require_validated = constraints.get("require_validated", False)
        max_hops = int(constraints.get("max_hops", 10))

        candidates = [
            link for link in self.links if (not require_validated or link.validated)
        ]

        # Build hop path: any link whose source cosmology name matches source
        # OR whose target cosmology name matches target (direct path first).
        hops: List[Dict[str, str]] = []
        for link in candidates[:max_hops]:
            hop = {
                "from": link.source.name,
                "to": link.target.name,
                "validated": link.validated,
            }
            hops.append(hop)

        # Check whether the path actually connects source → target
        connected = (
            any(h["from"] == source or h["to"] == target for h in hops)
            if hops
            else (source == target)
        )

        return {
            "ok": connected,
            "hops": hops,
            "total_links": len(self.links),
            "reason": (
                "path found" if connected else f"no route from {source!r} to {target!r}"
            ),
        }


class CosmicMap:
    def __init__(self):
        self.visualization_data = {}

    def update_map(self, cosmologies: List[CosmologyNode]):
        """Update the cockpit visualization."""
        self.visualization_data = {cosmo.name: cosmo.worlds for cosmo in cosmologies}
