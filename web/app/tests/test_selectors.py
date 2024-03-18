from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from ..selectors import get_object_or_404
from .. import models


def test_get_object_or_404(session: Session, test_workflow):
    # Object found
    assert \
        get_object_or_404(models.Workflow, object_id=test_workflow.id, db=session).id == \
        test_workflow.id

    # Object not found
    import pytest
    with pytest.raises(HTTPException) as exception:
        get_object_or_404(models.Workflow, object_id=test_workflow.id+10000, db=session).id
    assert exception.value.status_code == 404
    assert exception.value.detail == "Workflow not found"
