import enum

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Enum,
    CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import  relationship, mapped_column, Mapped

from .db import Base


class Workflow(Base):
    __tablename__ = "workflow"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=50), nullable=True)

    nodes: Mapped[list["Node"]] = relationship(back_populates="workflow")


class Node(Base):
    __tablename__ = "node"

    class NodeTypeEnum(enum.Enum):
        start = "start"
        message = "message"
        condition = "condition"
        end = "end"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(NodeTypeEnum), nullable=False)

    source_edges: Mapped[list["Edge"]] = relationship(back_populates="source_node")
    target_edges: Mapped[list["Edge"]] = relationship(back_populates="target_node")
    condition: Mapped["Condition"] = relationship(back_populates="node")
    message: Mapped["Message"] = relationship(back_populates="node")


class Edge(Base):
    __tablename__ = "edge"
    __table_args__ = (
        CheckConstraint("source_node_id != target_node_id", name="check_source_node_not_equal_target_node"),
        UniqueConstraint("source_node_id", "target_node_id", name="unq_source_node_target_node"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)

    source_node: Mapped["Node"] = relationship(back_populates="source_edges", foreign_keys=[source_node_id])
    target_node: Mapped["Node"] = relationship(back_populates="target_edges", foreign_keys=[target_node_id])


class Condition(Base):
    __tablename__ = "condition"

    id = Column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)
    expression = Column(String(length=100), nullable=False)

    node: Mapped["Node"] = relationship(back_populates="condition")


class Message(Base):
    __tablename__ = "message"

    class ConditionStatusEnum(enum.Enum):
        pending = "pending"
        sent = "sent"
        opened = "opened"

    id = Column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ConditionStatusEnum), nullable=False)
    text = Column(String(length=100))

    node: Mapped["Node"] = relationship(back_populates="message")
