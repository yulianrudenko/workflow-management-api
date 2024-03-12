from pydantic import BaseModel, field_validator
from datetime import datetime

from . import models

ALLOWED_MESSAGE_STATUS = ["pending", "sent", "opened"]


class BaseWorkflow(BaseModel):
    name: str


class WorkflowIn(BaseWorkflow):
    pass


class WorkflowOut(BaseWorkflow):
    id: int
    created_at: datetime


class BaseNode(BaseModel):
    class NodeData(BaseModel):
        """
        Represents additional parameters for specific node types (e.g. Condition and Message)
        """
        expression: str | None
        yes_node_id: int | None
        no_node_id: int | None
        status: models.Message.MessageStatusEnum | None
    type: models.Node.NodeTypeEnum


class NodeInCreate(BaseNode):
    workflow_id: int
    data: BaseNode.NodeData | None = None


class NodeInUpdate(BaseNode):
    data: BaseNode.NodeData | None = None


class NodeOut(BaseNode):
    id: int
    workflow_id: int
    data: BaseNode.NodeData | None = None


class MessageNode(BaseModel):
    previous_nodes_id: list[int]
    next_node_id: int
    status: str
    text: str

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str) -> str:
        if v not in ALLOWED_MESSAGE_STATUS:
            raise ValueError("Status is not allowed")
        return v


class ConditionNode(BaseModel):
    condition: str
    yes_node_id: int
    no_node_id: int
    previous_nodes_id: list[int]
    next_nodes_id: list[int]


class EndNode(BaseModel):
    previous_nodes_id: list[int]
