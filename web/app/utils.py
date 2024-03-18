import networkx as nx
import rule_engine

from . import models


def find_path(G: nx.DiGraph, start_node_id: int, end_node_id: int) -> list[dict[any, any]]:
    """
    Go through the graph and find the path to end node
    """
    path = []
    previous_message_node_id = None
    current_node_id = start_node_id

    while True:
        path.append(current_node_id)
        if current_node_id == end_node_id:
            break  # End of graph

        successors = list(G.successors(current_node_id))
        if not successors:
            raise ValueError(f"No end node at the end of the path or edge missing. Node id: {current_node_id}")

        neighbor_node_id = successors[0]
        node_data = G.nodes[neighbor_node_id]

        if node_data["type"] == models.Node.NodeTypeEnum.condition:
            path.append(neighbor_node_id)
            # Handle Condition logic
            if previous_message_node_id is None:
                raise ValueError(f"No message found for condition with ID of {neighbor_node_id}")
            rule = rule_engine.Rule(node_data["expression"])
            previous_message_data = G.nodes[previous_message_node_id]
            try:
                rule_match = rule.matches(previous_message_data)
            except:
                raise ValueError(f"Condition with ID of {current_node_id} is invalid, please update the expression.")
            if rule_match:
                current_node_id = node_data["yes_node_id"]
            else:
                current_node_id = node_data["no_node_id"]
            continue

        elif node_data["type"] == models.Node.NodeTypeEnum.message:
            # Save message for future Conditions
            previous_message_node_id = neighbor_node_id

        current_node_id = neighbor_node_id

    result = []
    for node_id in path:
        result.append(G.nodes[node_id])
    return result
