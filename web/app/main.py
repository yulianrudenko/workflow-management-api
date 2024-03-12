from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from . import models
from . import schemas
from .db import get_db
from .services import create_node

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


@app.delete("/api/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete Workflow
    """
    db.query(models.Workflow).filter(models.Workflow.id == workflow_id).delete()
    db.commit()


@app.post("/api/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: schemas.NodeInCreate, db: Session = Depends(get_db)) -> schemas.NodeOut:
    """
    Create Node within provided Workflow
    """
    node_obj = create_node(node=node, db=db)
    return node_obj


@app.patch("/api/nodes/{node_id}", status_code=status.HTTP_200_OK)
def update_node(node_id: int, node: schemas.NodeInUpdate, db: Session = Depends(get_db)) -> schemas.NodeOut:
    """
    Update given Node
    """
    node_data = node.model_dump(exclude_unset=True)
    node_additional_data = node_data.pop("data", {})
    # node_obj = create_node(workflow=workflow_obj, type=node.type, data=node.node_additional_data, db=db)
    node_obj = models.Node(**node_data)
    db.add(node_obj)
    db.commit()
    db.refresh(node_obj)
    return node_obj


@app.delete("/api/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete given Node
    """
    db.query(models.Node).filter(models.Node.id == node_id).delete()
    db.commit()
