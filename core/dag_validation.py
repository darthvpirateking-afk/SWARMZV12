"""
DAG Validation (P0.3)

Provides a utility to verify that a given graph structure, such as a mission plan,
is a Directed Acyclic Graph. This is critical for ensuring that mission steps
can be executed in a valid topological order without circular dependencies.
"""

from typing import List, Dict, Any


def is_dag(nodes: List[Dict[str, Any]]) -> bool:
    """
    Checks if the provided graph structure is a Directed Acyclic Graph (DAG).

    Args:
        nodes: A list of nodes, where each node is a dictionary with at least
               an 'id' and a 'dependencies' list of IDs.

    Returns:
        True if the graph is a DAG, False otherwise.
    """
    if not nodes:
        return True

    # Create an adjacency list and an in-degree count for each node
    adj = {node["id"]: [] for node in nodes}
    in_degree = {node["id"]: 0 for node in nodes}
    node_map = {node["id"]: node for node in nodes}

    # Build the graph
    for node in nodes:
        node_id = node["id"]
        for dep_id in node.get("dependencies", []):
            # Check for dependencies that don't exist in the provided node list
            if dep_id not in node_map:
                return False  # Invalid dependency points to a non-existent node

            # Add edge to adjacency list
            adj[dep_id].append(node_id)
            # Increment in-degree of the dependent node
            in_degree[node_id] += 1

    # Initialize a queue with all nodes that have an in-degree of 0
    # (i.e., nodes with no dependencies)
    queue = [node_id for node_id in in_degree if in_degree[node_id] == 0]

    # Count of visited nodes
    count = 0

    # Process nodes in the queue (Kahn's algorithm for topological sort)
    while queue:
        u = queue.pop(0)
        count += 1

        # For each neighbor of the current node, decrement its in-degree
        for v in adj.get(u, []):
            in_degree[v] -= 1
            # If a neighbor's in-degree becomes 0, add it to the queue
            if in_degree[v] == 0:
                queue.append(v)

    # If the count of visited nodes is equal to the total number of nodes,
    # then the graph is a DAG. Otherwise, it contains a cycle.
    return count == len(nodes)
