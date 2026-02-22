# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# SWARMZ Knowledge Graph
# Purpose: Represent relationships between macros, sequences, files, tasks, predictions, bypasses, and operator actions.


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, type, id, metadata):
        try:
            self.nodes[id] = {"type": type, "metadata": metadata}
        except Exception:
            pass  # Fail-open: Skip silently on write failure

    def add_edge(self, from_id, to_id, relation):
        try:
            self.edges.append({"from": from_id, "to": to_id, "relation": relation})
        except Exception:
            pass  # Fail-open: Skip silently on write failure

    def query_graph(self, criteria):
        # Example: Return nodes matching criteria
        return [
            node
            for node in self.nodes.values()
            if all(criteria.get(k) == v for k, v in node.items())
        ]

    def export_graph(self):
        try:
            return {"nodes": self.nodes, "edges": self.edges}
        except Exception:
            return {}  # Fail-open: Return empty graph on error
