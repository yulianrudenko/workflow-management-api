import networkx as nx
import rule_engine


def find_path_recursive(G: nx.DiGraph, current_node_id: int, end_node_id: int, previous_message_node_id: int = None):
    """
    Recursively finds a path from current node to target node

    Args:
        G: NetworkX DiGraph
        current_node_id: ID of the current node
        end_node_id: ID of the target node
        visited (optional): Set to keep track of visited nodes (default: None)

    Returns:
        List containing the path or None if no path is found
    """
    if current_node_id == end_node_id:
        return [current_node_id]

    for neighbor_node_id in G.successors(current_node_id):
        node_data = G.nodes[neighbor_node_id]

        if node_data["type"] == "condition":
            rule = rule_engine.Rule(node_data["expression"])
            previous_message_data = G.nodes[previous_message_node_id]
            if rule.matches(previous_message_data):
                neighbor_node_id = node_data["yes_node_id"]
            else:
                neighbor_node_id = node_data["no_node_id"]

        elif node_data["type"] == "message":
            previous_message_node_id = neighbor_node_id

        path = find_path_recursive(G, neighbor_node_id, end_node_id, previous_message_node_id)
        if path:
            return [current_node_id] + path

    return None


def find_path(G: nx.DiGraph, start_node_id: int, end_node_id: int):
    path = []
    previous_message_node_id = None
    current_node_id = start_node_id

    while True:
        path.append(current_node_id)
        if current_node_id == end_node_id:
            break

        successors = G.successors(current_node_id)
        if not successors:
            raise ValueError("No end node at the end of the path.")

        neighbor_node_id = list(successors)[0]
        node_data = G.nodes[neighbor_node_id]

        if node_data["type"] == "condition":
            path.append(neighbor_node_id)
            if previous_message_node_id is None:
                raise ValueError(f"No message found for condition with ID of {neighbor_node_id}")
            rule = rule_engine.Rule(node_data["expression"])
            previous_message_data = G.nodes[previous_message_node_id]
            print(node_data["expression"], previous_message_data)
            if rule.matches(previous_message_data):
                current_node_id = node_data["yes_node_id"]
            else:
                current_node_id = node_data["no_node_id"]
                print("rule does not match,current_node_id:", current_node_id)
            continue

        elif node_data["type"] == "message":
            previous_message_node_id = neighbor_node_id

        current_node_id = neighbor_node_id

    for x in path:
        print(G.nodes[x])
    return path
