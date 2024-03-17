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
    # Parameters for specific node types (e.g. Message and Condition)
    # Message
    status: Optional[models.Message.MessageStatusEnum] = None
    text: Optional[str] = None
    # Condition
    expression: Optional[str] = None


class NodeInCreate(BaseNode):
    workflow_id: int
    type: models.Node.NodeTypeEnum


class NodeInUpdate(BaseNode):
    pass


class NodeOut(BaseNode):
    id: int
    type: models.Node.NodeTypeEnum


class Graph(BaseModel):
    workflow_id: int
    nodes: list[NodeOut]


class BaseEdge(BaseModel):
    source_node_id: int
    target_node_id: int


class EdgeIn(BaseEdge):
    is_yes_condition: Optional[bool] = None


class EdgeOut(BaseEdge):
    id: int


class WorkflowRunOut(WorkflowOut):
    nodes: list[NodeOut]
