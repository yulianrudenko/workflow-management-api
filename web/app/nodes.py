from abc import ABC, abstractmethod
from enum import Enum

import networkx as nx
nx.DiGraph


class BaseNode(ABC):
    pass


class StartNode:
    next_node: BaseNode


class MessageNode:
    class ALLOWED_TYPES(Enum):
        PENDING = "pending"
        SENT = "sent"
        OPENED = "opened"

    type_: str
    text: str
    previous_nodes: list[BaseNode]
    next_node: BaseNode


class ConditionNode:
    previous_nodes: list[MessageNode | "ConditionNode"]
    yes_node: BaseNode
    no_node: BaseNode

    def get_condition(self) -> bool:
        last_message_node = None
        for node in self.previous_nodes[::-1]:
            if type(node) is MessageNode:
                last_message_node = node

        if last_message_node is not None:
            if last_message_node.status == MessageNode.ALLOWED_TYPES.SENT:
                return True

        return False


class EndNode:
    previous_nodes: list[BaseNode]
