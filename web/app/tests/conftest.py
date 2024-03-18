import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .. import models
from .. import schemas
from ..main import app
from ..db import get_db, Base
from ..config import settings


engine = create_engine(settings.TESTS_DB_URL)
TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="function")
def session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app=app)

@pytest.fixture(scope="function")
def test_workflow(session: Session) -> models.Workflow:
    """
    Workflow fixture
    """
    workflow = models.Workflow(name="Test")
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return workflow


@pytest.fixture(scope="function")
def test_workflow_data(session: Session, test_workflow) -> dict:
    """
    Fixture that creates nodes and edges from workflow example in task
    """
    workflow = test_workflow

    # Create Nodes and related objects
    start_node = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.start)
    msg_node1 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.message)
    condition_node1 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.condition)
    msg_node2 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.message)
    condition_node2 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.condition)
    msg_node3 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.message)
    msg_node4 = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.message)
    end_node = models.Node(workflow=workflow, type=models.Node.NodeTypeEnum.end)

    messages_and_conditions = [
        models.Message(
            node=msg_node1,
            status=models.Message.MessageStatusEnum.opened,
            text="hello"
        ),
        models.Condition(
            node=condition_node1,
            expression='status == "sent"',
        ),
        models.Message(
            node=msg_node2,
            status=models.Message.MessageStatusEnum.pending,
            text="How are you?"
        ),
        models.Condition(
            node=condition_node2,
            expression='status == "opened"',
        ),
        models.Message(
            node=msg_node3,
            status=models.Message.MessageStatusEnum.pending,
            text="How old are you?"
        ),
        models.Message(
            node=msg_node4,
            status=models.Message.MessageStatusEnum.pending,
            text="Do you like pets?"
        ),
    ]

    # Create edges
    edges = [
        models.Edge(
            source_node=start_node,
            target_node=msg_node1
        ),
        models.Edge(
            source_node=msg_node1,
            target_node=condition_node1
        ),
        models.Edge(
            source_node=msg_node2,
            target_node=end_node
        ),
        models.Edge(
            source_node=msg_node3,
            target_node=end_node
        ),
        models.Edge(
            source_node=msg_node4,
            target_node=end_node
        ),
    ]
    yes_edge1 = models.Edge(source_node=condition_node1, target_node=msg_node2)
    no_edge1 = models.Edge(source_node=condition_node1, target_node=condition_node2)
    yes_edge2 = models.Edge(source_node=condition_node2, target_node=msg_node3)
    no_edge2 = models.Edge(source_node=condition_node2, target_node=msg_node4)
    edges += [yes_edge1, yes_edge2, no_edge1, no_edge2]

    condition_node1.condition.yes_edge = yes_edge1
    condition_node1.condition.no_edge = no_edge1
    condition_node2.condition.yes_edge = yes_edge2
    condition_node2.condition.no_edge = no_edge2

    session.add_all([
        start_node,
        msg_node1,
        condition_node1,
        msg_node2,
        condition_node2,
        msg_node3,
        msg_node4,
        end_node,
    ])
    session.add_all(messages_and_conditions)
    session.add_all(edges)
    session.commit()
    session.refresh(workflow)
    return {
        "workflow_id": workflow.id,
        "start_node": start_node.id,
        "msg_node1": msg_node1.id,
        "condition_node1": condition_node1.id,
        "msg_node2": msg_node2.id,
        "condition_node2": condition_node2.id,
        "msg_node3": msg_node3.id,
        "msg_node4": msg_node4.id,
        "end_node": end_node.id
    }
