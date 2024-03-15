from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from . import models


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
        # Message
        status: Optional[models.Message.MessageStatusEnum] = None
        text: Optional[str] = None
        # Condition
        expression: Optional[str] = None
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


class BaseEdge(BaseModel):
    source_node_id: int
    target_node_id: int


class EdgeIn(BaseEdge):
    is_yes_condition: Optional[bool] = None


class EdgeOut(BaseEdge):
    id: int
