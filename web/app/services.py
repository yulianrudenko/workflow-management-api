import networkx as nx

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from . import schemas
from . import utils
from .selectors import get_object_or_404



def run_workflow(workflow_obj: models.Workflow, db: Session) -> None:
    """
    Converts data from DB into DiGraph and try finding path from start to end Node
    """
    G = nx.DiGraph()

    nodes = db.query(models.Node).filter(models.Node.workflow_id == workflow_obj.id)
    start_node: models.Node = nodes.filter(models.Node.type == models.Node.NodeTypeEnum.start).first()
    if start_node is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow has no Start Node")

    end_node: models.Node = nodes.filter(models.Node.type == models.Node.NodeTypeEnum.end).first()
    if end_node is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow has no End Node")

    # Fetch edges
    nodes_ids = [node.id for node in nodes]
    edges = db.query(models.Edge).filter(
        or_(
            models.Edge.source_node_id.in_(nodes_ids),
            models.Edge.target_node_id.in_(nodes_ids)
        )
    ).order_by(models.Edge.created_at)

    # Add Nodes to graph with additional data
    for node in nodes:
        node_data = {}
        node_data["id"] = node.id
        node_type = node.type
        node_data["type"] = node_type
        if node_type == models.Node.NodeTypeEnum.message:
            node_data["status"] = node.message.status
            node_data["text"] = node.message.text
        if node_type == models.Node.NodeTypeEnum.condition:
            node_data["expression"] = node.condition.expression
            node_data["yes_node_id"] = getattr(node.condition.yes_edge, "target_node_id", None)
            node_data["no_node_id"] = getattr(node.condition.no_edge, "target_node_id", None)
        G.add_node(node.id, **node_data)

    # Add Edges to graph
    for edge in edges:
        G.add_edge(edge.source_node_id, edge.target_node_id)

    try:
        nodes_path = utils.find_path(G, start_node_id=start_node.id, end_node_id=end_node.id)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return nodes_path


def create_node(node: schemas.NodeInCreate, db: Session) -> models.Node:
    """
    Creates node based on provided data.

    Validates if workflow exists and if node can be appended to workflow based on provided type and parameters.
    """

    # Check if workflow exists
    get_object_or_404(models.Workflow, object_id=node.workflow_id, db=db)

    # Create Node
    node_obj = models.Node(workflow_id=node.workflow_id, type=node.type)
    db.add(node_obj)

    # Additional logic depending on provided Node type
    if node.type in [models.Node.NodeTypeEnum.start, models.Node.NodeTypeEnum.end]:
        if db.query(models.Node).filter(models.Node.type == node.type).first():
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only one {node.type.name.title()} Node allowed in single workflow."
                )
    if node.type == models.Node.NodeTypeEnum.message:
        if not node.status or not node.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status and text required for Message Node"
            )
        message_obj = models.Message(node=node_obj, status=node.status, text=node.text)
        db.add(message_obj)
        node_obj.text = message_obj.text
        node_obj.status =  message_obj.status
    elif node.type == models.Node.NodeTypeEnum.condition:
        if not node.expression:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expression required for Condition Node"
            )
        condition_obj = models.Condition(node=node_obj, expression=node.expression)
        db.add(condition_obj)
        node_obj.expression = condition_obj.expression

    db.commit()
    db.refresh(node_obj)
    return node_obj


def update_node(node_id: int, node_data: schemas.NodeInUpdate, db: Session) -> models.Node:
    """
    Updates node based on provided data.

    Validates if node exists and updates data if possible.
    """

    # Check if Node exists
    node_obj: models.Node = get_object_or_404(models.Node, object_id=node_id, db=db)

    # Perform update
    if node_obj.type == models.Node.NodeTypeEnum.condition:
        if node_data.expression:
            node_obj.condition.expression = node_data.expression
        node_obj.expression = node_obj.condition.expression
    elif node_obj.type == models.Node.NodeTypeEnum.message:
        if node_data.status:
            node_obj.message.status = node_data.status
        if node_data.text:
            node_obj.message.text = node_data.text
        node_obj.status = node_obj.message.status
        node_obj.text = node_obj.message.text

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field 'is_yes_condition' required for this Edge"
            )

    db.commit()
    db.refresh(edge_obj)
    return edge_obj
