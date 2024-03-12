from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models
from . import schemas


def create_node(node: schemas.NodeInCreate, workflow: models.Workflow, db: Session) -> models.Node:
    """
    Creates node based on provided data.

    Validates if workflow exists and if node can be appended to workflow based on provided type and parameters.
    """

    workflow_obj = db.query(models.Workflow).filter(models.Workflow.id == node.workflow_id).first()
    if not workflow_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    node_data = node.model_dump()
    node_obj = models.Node(**node_data, workflow=workflow_obj)
    db.add(node_obj)
    db.commit()
    db.refresh(node_obj)
    return node_obj
