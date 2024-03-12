import networkx as nx
import matplotlib.pyplot as plt

from utils import find_path

G = nx.DiGraph()

start_node = {"id": 1, "type": "start", "label": "Start"}
message_node = {"id": 2, "type": "message", "label": "Message", "message_text": "Hello, world!", "status": "open"}
message_node2 = {"id": 3, "type": "message", "label": "Message", "message_text": "Hello, world!", "status": "open"}
condition_node = {"id": 4, "type": "condition", "label": "Condition", "expression": 'status == "open"', "yes_node_id": 5, "no_node_id": 6}
message_node3 = {"id": 5, "type": "message", "label": "Message", "message_text": "Hello, world!", "status": "sent"}
message_node4 = {"id": 6, "type": "message", "label": "Message", "message_text": "Hello, world!", "status": "open"}
end_node = {"id": 7, "type": "end", "label": "End"}

G.add_node(start_node["id"], **start_node)
G.add_node(message_node["id"], **message_node)
G.add_node(message_node2["id"], **message_node2)
G.add_node(message_node3["id"], **message_node3)
G.add_node(message_node4["id"], **message_node4)
G.add_node(condition_node["id"], **condition_node)
G.add_node(end_node["id"], **end_node)

G.add_edge(start_node["id"], message_node["id"])
G.add_edge(start_node["id"], message_node2["id"])
G.add_edge(message_node["id"], condition_node["id"])
G.add_edge(condition_node["id"], message_node3["id"])
G.add_edge(condition_node["id"], message_node4["id"])
G.add_edge(message_node3["id"], end_node["id"])
G.add_edge(message_node4["id"], end_node["id"])


nx.draw(G, with_labels=True)
plt.show()

print(find_path(G, start_node["id"], end_node["id"]))