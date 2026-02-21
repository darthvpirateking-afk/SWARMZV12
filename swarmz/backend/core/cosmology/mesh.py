# mesh.py
# Implements the MeshRouter, Node, and Link classes.


class Node:
    def __init__(self, node_id, node_type, status):
        self.node_id = node_id
        self.node_type = node_type
        self.status = status


class Link:
    def __init__(self, source, target, link_type):
        self.source = source
        self.target = target
        self.link_type = link_type


class MeshRouter:
    def __init__(self):
        self.nodes = []
        self.links = []

    def load_nodes(self, nodes):
        """Load nodes into the mesh."""
        self.nodes = [Node(**node) for node in nodes]

    def load_links(self, links):
        """Load links into the mesh."""
        self.links = [Link(**link) for link in links]


# Example usage
if __name__ == "__main__":
    nodes = [
        {"node_id": "node1", "node_type": "compute", "status": "active"},
        {"node_id": "node2", "node_type": "storage", "status": "active"},
    ]
    links = [{"source": "node1", "target": "node2", "link_type": "data"}]

    router = MeshRouter()
    router.load_nodes(nodes)
    router.load_links(links)
    print("Nodes:", router.nodes)
    print("Links:", router.links)
