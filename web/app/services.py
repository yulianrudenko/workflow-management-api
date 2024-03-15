from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from . import schemas


def get_object_or_404(Model: models.Base, object_id: int, db: Session) -> models.Base:
    """
    Gets an object by ID or raises a 404 if not found.

    Args:
        model: Type of object that needs to be retrieved from database.
        object_id: ID of the object to retrieve.
        db: Database session.

    Returns:
        The retrieved object if found, otherwise raises a 404 exception.
    """
    obj = db.query(Model).filter(Model.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{Model.__name__} not found")
    return obj


def create_node(node: schemas.NodeInCreate, db: Session) -> models.Node:
    """
    Creates node based on provided data.

    Validates if workflow exists and if node can be appended to workflow based on provided type and parameters.
    """

    # Check if workflow exists
    get_object_or_404(models.Workflow, object_id=node.workflow_id, db=db)

    # Create Node
    node_data = node.model_dump()
    node_data.pop("data", {})  # Clear unnecessary data
    node_obj = models.Node(**node_data)
    db.add(node_obj)

    # Additional database logic depending on provided Node type
    if node.type == models.Node.NodeTypeEnum.message:
        if not node.data.status or not node.data.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status and text required for Message Node"
            )
        message_obj = models.Message(node=node_obj, status=node.data.status, text=node.data.text)
        db.add(message_obj)
    elif node.type == models.Node.NodeTypeEnum.condition:
        if not node.data.expression:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expression required for Condition Node"
            )
        condition_obj = models.Condition(node=node_obj, expression=node.data.expression)
        db.add(condition_obj)

    db.commit()
    db.refresh(node_obj)
    return node_obj


def create_edge(edge: schemas.EdgeIn, db: Session) -> models.Edge:
    """
    Creates edge based on provided data.

    Validates if workflow exists and if edge can link given nodes based on nodes parameters.
    """
    if edge.source_node_id == edge.target_node_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nodes must be 2 different values")

    # Check if Edge already exists
    if db.query(models.Edge)   \
        .filter(or_(
            (models.Edge.source_node_id == edge.source_node_id) &
            (models.Edge.target_node_id == edge.target_node_id),
            (models.Edge.source_node_id == edge.target_node_id) &
            (models.Edge.target_node_id == edge.source_node_id)
        )).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Edge with these nodes already exists")

    # Validate if objects exsit in DB
    target_node: models.Node = get_object_or_404(models.Node, object_id=edge.target_node_id, db=db)
    source_node: models.Node = get_object_or_404(models.Node, object_id=edge.source_node_id, db=db)

    # Validation related to Node types
    if target_node.workflow_id != source_node.workflow_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot link nodes from different workflows")

    if target_node.type == models.Node.NodeTypeEnum.start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start Node cannot have source node")

    if source_node.type == models.Node.NodeTypeEnum.start:
        if db.query(models.Edge).filter(models.Edge.source_node_id == edge.source_node_id).first() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start Node cannot have more than one target node"
            )

    if source_node.type == models.Node.NodeTypeEnum.message:
        if db.query(models.Edge).filter(models.Edge.source_node_id == edge.source_node_id).first() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message Node cannot have more than one target node"
            )

    if source_node.type == models.Node.NodeTypeEnum.condition:
        if db.query(models.Edge).filter(models.Edge.source_node_id == edge.source_node_id).count() >= 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Condition Node cannot have more than two target nodes"
            )

    if target_node.type == models.Node.NodeTypeEnum.condition and \
        source_node.type not in [models.Node.NodeTypeEnum.message, models.Node.NodeTypeEnum.condition]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Condition Node can only have Message or Condition as source Nodes"
        )

    if source_node.type == models.Node.NodeTypeEnum.end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End Node cannot have target nodes")

    # Create Edge
    edge_obj = models.Edge(source_node_id=edge.source_node_id, target_node_id=edge.target_node_id)
    db.add(edge_obj)

    # Additional logic for Condition, link Condition with created Edge
    if source_node.type == models.Node.NodeTypeEnum.condition:
        if edge.is_yes_condition is False:
            source_node.condition.no_edge = edge_obj
        elif edge.is_yes_condition is True:
            source_node.condition.yes_edge = edge_obj
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Field 'is_yes_condition' required for this Edge")

    db.commit()
    db.refresh(edge_obj)
    return edge_obj
