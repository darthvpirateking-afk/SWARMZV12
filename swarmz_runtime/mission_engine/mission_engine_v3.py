class GraphBuilder:
    def __init__(self):
        self.graph = {}

    def add_node(self, node_id, dependencies=None):
        self.graph[node_id] = {
            "dependencies": dependencies or [],
            "state": "pending",
        }

    def build_graph(self):
        return self.graph

class GraphExecutor:
    def __init__(self, graph):
        self.graph = graph

    def execute_node(self, node_id):
        node = self.graph.get(node_id)
        if node and all(self.graph[dep]["state"] == "completed" for dep in node["dependencies"]):
            node["state"] = "completed"
            return f"Node {node_id} executed"
        return f"Node {node_id} cannot be executed"

class GraphMonitor:
    def __init__(self, graph):
        self.graph = graph

    def get_active_nodes(self):
        return [node_id for node_id, data in self.graph.items() if data["state"] == "pending"]

class GraphReporter:
    def __init__(self, graph):
        self.graph = graph

    def visualize_graph(self):
        return {
            node_id: {
                "state": data["state"],
                "dependencies": data["dependencies"],
            }
            for node_id, data in self.graph.items()
        }