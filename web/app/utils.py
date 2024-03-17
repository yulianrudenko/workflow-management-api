import networkx as nx
import rule_engine

from . import models


def find_path(G: nx.DiGraph, start_node_id: int, end_node_id: int) -> list[dict]:
    path = []
    previous_message_node_id = None
    current_node_id = start_node_id

    while True:
        path.append(current_node_id)
        if current_node_id == end_node_id:
            break

        successors = list(G.successors(current_node_id))
        if not successors:
            raise ValueError(f"No end node at the end of the path or edge missing. Node id: {current_node_id}")

        neighbor_node_id = successors[0]
        node_data = G.nodes[neighbor_node_id]

        if node_data["type"] == models.Node.NodeTypeEnum.condition:
            path.append(neighbor_node_id)
            if previous_message_node_id is None:
                raise ValueError(f"No message found for condition with ID of {neighbor_node_id}")
            rule = rule_engine.Rule(node_data["expression"])
            previous_message_data = G.nodes[previous_message_node_id]
            # print(node_data["expression"], previous_message_data, rule.matches(previous_message_data))
            if rule.matches(previous_message_data):
                current_node_id = node_data["yes_node_id"]
            else:
                current_node_id = node_data["no_node_id"]
                # print("rule does not match,current_node_id:", current_node_id)
            continue

        elif node_data["type"] == models.Node.NodeTypeEnum.message:
            previous_message_node_id = neighbor_node_id

        current_node_id = neighbor_node_id

    result = []
    for x in path:
        result.append(G.nodes[x])
    return result
