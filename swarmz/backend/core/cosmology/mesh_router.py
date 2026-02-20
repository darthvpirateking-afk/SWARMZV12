# Mesh Router module for SWARMZ cosmology

class MeshRouter:
    """
    Routes missions and swarm units across the mesh.
    """
    def __init__(self, nodes, links):
        self.nodes = nodes
        self.links = links

    def route_mission(self, mission):
        return self.links[0] if self.links else None

    def route_unit(self, unit):
        return self.links[0] if self.links else None