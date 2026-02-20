class DynamicNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.state = "stable"
        self.energy = 0
        self.links = []

    def update_state(self, state):
        self.state = state

    def update_energy(self, energy):
        self.energy = energy

    def add_link(self, target_node):
        self.links.append(target_node)

class CosmologyTicker:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node_id):
        if node_id not in self.nodes:
            self.nodes[node_id] = DynamicNode(node_id)

    def update_node(self, node_id, state=None, energy=None):
        if node_id in self.nodes:
            if state:
                self.nodes[node_id].update_state(state)
            if energy:
                self.nodes[node_id].update_energy(energy)

    def tick(self):
        for node in self.nodes.values():
            # Example: Dim energy over time
            node.update_energy(max(0, node.energy - 1))

    def get_node_states(self):
        return {node_id: {"state": node.state, "energy": node.energy} for node_id, node in self.nodes.items()}