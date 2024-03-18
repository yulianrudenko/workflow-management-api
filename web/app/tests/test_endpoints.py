import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .conftest import TestClient
from .. import models
from .. import schemas
from ..main import app


class TestGetAllWorkflows:
    def test_success(self, client: TestClient, session: Session, test_workflow_data):
        # Prepare workflow data to compare
        workflow_obj = session.query(models.Workflow).first()
        workflow_data = workflow_obj.__dict__
        nodes_data = [schemas.NodeOut(**node.__dict__).model_dump() for node in workflow_obj.nodes]
        nodes_ids = [node.id for node in workflow_obj.nodes]
        workflow_obj.edges = session.query(models.Edge) \
            .filter(or_(
                (models.Edge.source_node_id.in_(nodes_ids)),
                (models.Edge.target_node_id.in_(nodes_ids)),
            )).all()
        edges_data = [schemas.EdgeOut(**edge.__dict__).model_dump() for edge in workflow_obj.edges]

        response = client.get(app.url_path_for("get_all_workflows"))
        assert response.status_code == 200
        del workflow_data["nodes"]
        del workflow_data["edges"]
        assert response.json() == \
            [json.loads(schemas.WorkflowOut(**workflow_data, nodes=nodes_data, edges=edges_data).model_dump_json(exclude_none=True))]


class TestCreateWorkflow:
    def test_success(self, client: TestClient, session: Session):
        response = client.post(app.url_path_for("create_workflow"), json={"name": "test"})
        assert response.status_code == 201
        workflow = session.query(models.Workflow).first()
        json = response.json()
        assert type(json.pop("created_at")) is str
        assert json == {"id": workflow.id, "name": "test", "nodes": [], "edges": []}


class TestGetWorkflow:
    def test_success(self, client: TestClient, session: Session, test_workflow_data):
        # Prepare workflow data to compare
        workflow_obj = session.query(models.Workflow).first()
        workflow_data = workflow_obj.__dict__ 
        nodes_data = [schemas.NodeOut(**node.__dict__).model_dump() for node in workflow_obj.nodes]
        nodes_ids = [node.id for node in workflow_obj.nodes]
        workflow_obj.edges = session.query(models.Edge) \
            .filter(or_(
                (models.Edge.source_node_id.in_(nodes_ids)),
                (models.Edge.target_node_id.in_(nodes_ids)),
            )).all()
        edges_data = [schemas.EdgeOut(**edge.__dict__).model_dump() for edge in workflow_obj.edges]

        response = client.get(app.url_path_for("get_workflow", workflow_id=test_workflow_data["workflow_id"]))
        assert response.status_code == 200
        del workflow_data["nodes"]
        del workflow_data["edges"]
        assert response.json() == \
            json.loads(schemas.WorkflowOut(**workflow_data, nodes=nodes_data, edges=edges_data).model_dump_json(exclude_none=True))


class TestDeleteWorkflow:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        assert session.query(models.Workflow).count() == 1
        response = client.delete(app.url_path_for("delete_workflow", workflow_id=test_workflow.id))
        assert response.status_code == 204
        assert session.query(models.Workflow).count() == 0


class TestRunWorkflow:
    def test_success(self, client: TestClient, session: Session, test_workflow_data):
        response = client.get(app.url_path_for("run_workflow", workflow_id=test_workflow_data["workflow_id"]))
        assert response.status_code == 200
        json = response.json()
        assert json == {
            'workflow_id': test_workflow_data["workflow_id"],
            'nodes': [
                {'id': test_workflow_data["start_node"], 'type': 'start'},
                {'status': 'opened', 'text': 'hello', 'id': test_workflow_data["msg_node1"], 'type': 'message'},
                {'expression': 'status == "sent"', 'id': test_workflow_data["condition_node1"], 'type': 'condition'},
                {'expression': 'status == "opened"', 'id': test_workflow_data["condition_node2"], 'type': 'condition'},
                {'status': 'pending', 'text': 'How old are you?', 'id': test_workflow_data["msg_node3"], 'type': 'message'},
                {'id': test_workflow_data["end_node"], 'type': 'end'}
            ]
        }


class TestCreateNode:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        response = client.post(app.url_path_for("create_node"), json={"workflow_id": test_workflow.id, "type": "start"})
        node = session.query(models.Node).first()
        assert response.status_code == 201
        assert response.json() == {"id": node.id, "type": "start"}


class TestUpdateNode:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        node_obj = models.Node(workflow_id=test_workflow.id, type="message")
        msg_obj = models.Message(node=node_obj, status=models.Message.MessageStatusEnum.opened, text="test")
        session.add(node_obj)
        session.add(msg_obj)
        session.commit()
        session.refresh(node_obj)

        response = client.patch(
            app.url_path_for("update_node", node_id=node_obj.id),
            json={"status": models.Message.MessageStatusEnum.pending.name, "text": "new"}
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": node_obj.id,
            "type": "message",
            "status": models.Message.MessageStatusEnum.pending.name,
            "text": "new"
        }


class TestDeleteNode:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        node_obj = models.Node(workflow_id=test_workflow.id, type="message")
        session.add(node_obj)
        session.commit()

        response = client.delete(app.url_path_for("delete_node", node_id=node_obj.id))
        assert response.status_code == 204
        assert session.query(models.Node).count() == 0


class TestCreateEdge:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        start_node = models.Node(workflow_id=test_workflow.id, type="start")
        end_node = models.Node(workflow_id=test_workflow.id, type="end")
        session.add_all([start_node, end_node])
        session.commit()

        response = client.post(app.url_path_for("create_edge"), json={
            "source_node_id": start_node.id,
            "target_node_id": end_node.id,
        })
        assert response.status_code == 201
        edge = session.query(models.Edge).first()
        assert response.json() == {"id": edge.id, "source_node_id": start_node.id, "target_node_id": end_node.id}


class TestDeleteEdge:
    def test_success(self, client: TestClient, session: Session, test_workflow):
        start_node = models.Node(workflow_id=test_workflow.id, type="start")
        end_node = models.Node(workflow_id=test_workflow.id, type="end")
        edge = models.Edge(source_node=start_node, target_node=end_node)
        session.add_all([start_node, end_node, edge])
        session.commit()

        response = client.delete(app.url_path_for("delete_edge", edge_id=edge.id))
        assert response.status_code == 204
        assert session.query(models.Edge).count() == 0
