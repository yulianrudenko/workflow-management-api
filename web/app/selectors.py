from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models


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
