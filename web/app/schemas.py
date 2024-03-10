from pydantic import BaseModel, field_validator

ALLOWED_MESSAGE_STATUS = ["pending", "sent", "opened"]


class StartNode(BaseModel):
    next_node_id: int


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
