import networkx as nx
import matplotlib.pyplot as plt

from utils import find_path

G = nx.DiGraph()

start_node = {"id": 1, "type": "start"}
message_node2 = {"id": 2, "type": "message", "status": "open", "text": "Hello"}
condition_node3 = {"id": 3, "type": "condition", "expression": 'status == "sent"', "yes_node_id": 4, "no_node_id": 5}
message_node4 = {"id": 4, "type": "message", "status": "pending", "text": "How are you?"}
condition_node5 = {"id": 5, "type": "condition", "expression": 'status == "open"', "yes_node_id": 6, "no_node_id": 7}
message_node6 = {"id": 6, "type": "message", "status": "pending", "text": "How old are you?"}
message_node7 = {"id": 7, "type": "message", "status": "pending", "text": "Do you like pets?"}
end_node = {"id": 8, "type": "end"}

G.add_node(start_node["id"], **start_node)
G.add_node(condition_node3["id"], **condition_node3)
G.add_node(condition_node5["id"], **condition_node5)
G.add_node(message_node2["id"], **message_node2)
G.add_node(message_node4["id"], **message_node4)
G.add_node(message_node6["id"], **message_node6)
G.add_node(message_node7["id"], **message_node7)
G.add_node(end_node["id"], **end_node)

G.add_edge(start_node["id"], message_node2["id"])
G.add_edge(message_node2["id"], condition_node3["id"])
G.add_edge(condition_node3["id"], message_node4["id"])
G.add_edge(message_node4["id"], end_node["id"])
G.add_edge(condition_node3["id"], condition_node5["id"])
G.add_edge(condition_node5["id"], message_node6["id"])
G.add_edge(condition_node5["id"], message_node7["id"])
G.add_edge(message_node6["id"], end_node["id"])
G.add_edge(message_node7["id"], end_node["id"])


nx.draw(G, with_labels=True)
plt.show()

print(find_path(G, start_node["id"], end_node["id"]))