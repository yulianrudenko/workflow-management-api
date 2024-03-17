from fastapi import (
    FastAPI,
    Depends,
    status
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from . import schemas
from . import services
from . import selectors
from .db import get_db

app = FastAPI()


@app.post("/api/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(workflow: schemas.WorkflowIn, db: Session = Depends(get_db)) -> schemas.WorkflowOut:
    """
    Create Workflow
    """
    workflow_obj = models.Workflow(**workflow.model_dump())
    db.add(workflow_obj)
    db.commit()
    db.refresh(workflow_obj)
    return workflow_obj


@app.get("/api/workflows/{workflow_id}", status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)) -> schemas.WorkflowOut:
    """
    Retrieve Workflow data and its nodes
    """
    workflow_obj = selectors.get_object_or_404(models.Workflow, object_id=workflow_id, db=db)
    workflow_obj.nodes = db.query(models.Node).filter(models.Node.workflow_id == workflow_id).all()
    nodes_ids = [node.id for node in workflow_obj.nodes]
    workflow_obj.edges = db.query(models.Edge)   \
        .filter(or_(
            (models.Edge.source_node_id.in_(nodes_ids)),
            (models.Edge.target_node_id.in_(nodes_ids)),
        ))
    return workflow_obj


@app.delete("/api/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete Workflow
    """
    db.query(models.Workflow).filter(models.Workflow.id == workflow_id).delete()
    db.commit()


@app.get("/api/workflows/{workflow_id}/run", status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def run_workflow(workflow_id: int, db: Session = Depends(get_db)) -> schemas.Graph:
    """
    Run specific Workflow and return full DiGraph path with Nodes data
    """
    workflow_obj = selectors.get_object_or_404(models.Workflow, object_id=workflow_id, db=db)
    workflow_nodes_path = services.run_workflow(workflow_obj=workflow_obj, db=db)
    return {
        "workflow_id": workflow_id,
        "nodes": workflow_nodes_path
    }


@app.post("/api/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: schemas.NodeInCreate, db: Session = Depends(get_db)) -> schemas.NodeOut:
    """
    Create Node within provided Workflow
    """
    node_obj = services.create_node(node=node, db=db)
    return node_obj


@app.patch("/api/nodes/{node_id}", status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def update_node(node_id: int, node: schemas.NodeInUpdate, db: Session = Depends(get_db)) -> schemas.NodeOut:
    """
    Update given Node.

    Notes:
    Node type cannot be changed, only the additional parameters.
    For condition only the expression can be changed, as well as status and text for Message Node.
    To update Condition "yes" and "no" edges endpoints for egdes creation/deletion must be used.
    """
    node_obj = services.update_node(node_id=node_id, node_data=node, db=db)
    return node_obj


@app.delete("/api/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete given Node
    """
    db.query(models.Node).filter(models.Node.id == node_id).delete()
    db.commit()


@app.post("/api/edges", status_code=status.HTTP_201_CREATED)
def create_edge(edge: schemas.EdgeIn, db: Session = Depends(get_db)) -> schemas.EdgeOut:
    """
    Create Edge that links 2 Nodes
    """
    edge_obj = services.create_edge(edge=edge, db=db)
    return edge_obj


@app.delete("/api/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(edge_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete Edge
    """
    db.query(models.Edge).filter(models.Edge.id == edge_id).delete()
    db.commit()
