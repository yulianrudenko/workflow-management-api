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
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP

from .db import Base


class Workflow(Base):
    __tablename__ = "workflow"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

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

    workflow: Mapped[Workflow] = relationship(back_populates="nodes")
    source_edges: Mapped[list["Edge"]] = relationship(back_populates="source_node", foreign_keys="Edge.source_node_id")
    target_edges: Mapped[list["Edge"]] = relationship(back_populates="target_node", foreign_keys="Edge.target_node_id")
    condition: Mapped["Condition"] = relationship(back_populates="node", foreign_keys="Condition.node_id")
    message: Mapped["Message"] = relationship(back_populates="node")


class Edge(Base):
    __tablename__ = "edge"
    __table_args__ = (
        CheckConstraint("source_node_id != target_node_id", name="check_source_node_not_equal_target_node"),
        UniqueConstraint("source_node_id", "target_node_id", name="unq_source_node_target_node"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"))
    target_node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    source_node: Mapped["Node"] = relationship(back_populates="source_edges", foreign_keys=[source_node_id])
    target_node: Mapped["Node"] = relationship(back_populates="target_edges", foreign_keys=[target_node_id])
    yes_condition: Mapped["Condition"] = relationship(back_populates="yes_edge", foreign_keys="Condition.yes_edge_id")
    no_condition: Mapped["Condition"] = relationship(back_populates="no_edge", foreign_keys="Condition.no_edge_id")


class Message(Base):
    __tablename__ = "message"

    class MessageStatusEnum(enum.Enum):
        pending = "pending"
        sent = "sent"
        opened = "opened"

    node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    status = Column(Enum(MessageStatusEnum), nullable=False)
    text = Column(String(length=100))

    node: Mapped["Node"] = relationship(back_populates="message")


class Condition(Base):
    __tablename__ = "condition"

    node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    expression = Column(String(length=100), nullable=False)
    yes_edge_id: Mapped[int] = mapped_column(ForeignKey("edge.id", ondelete="SET NULL"), nullable=True)
    no_edge_id: Mapped[int] = mapped_column(ForeignKey("edge.id", ondelete="SET NULL"), nullable=True)

    node: Mapped["Node"] = relationship(back_populates="condition", foreign_keys=[node_id])
    yes_edge: Mapped["Edge"] = relationship(back_populates="yes_condition", foreign_keys=[yes_edge_id])
    no_edge: Mapped["Edge"] = relationship(back_populates="no_condition", foreign_keys=[no_edge_id])
