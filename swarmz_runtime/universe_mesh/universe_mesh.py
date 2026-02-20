class WorldNode:
    def __init__(self, world_id, kernels=None, missions=None, swarm_clusters=None):
        self.world_id = world_id
        self.kernels = kernels or []
        self.missions = missions or []
        self.swarm_clusters = swarm_clusters or []

class MeshLink:
    def __init__(self, source, target, bidirectional=False):
        self.source = source
        self.target = target
        self.bidirectional = bidirectional
        self.validated = False

    def validate(self, governor):
        self.validated = governor.validate_link(self)
        return self.validated

class MeshRouter:
    def __init__(self):
        self.worlds = {}
        self.links = []

    def add_world(self, world):
        self.worlds[world.world_id] = world

    def add_link(self, link):
        self.links.append(link)

    def route_mission(self, source_world, target_world, mission):
        if self._is_route_valid(source_world, target_world):
            return f"Mission {mission} routed from {source_world} to {target_world}"
        return f"Route from {source_world} to {target_world} is invalid"

    def _is_route_valid(self, source, target):
        for link in self.links:
            if link.source == source and link.target == target and link.validated:
                return True
        return False