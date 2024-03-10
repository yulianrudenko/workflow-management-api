from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .db import get_db

app = FastAPI()


@app.post("/api/workflows")
def create_workflow(db: Session = Depends(get_db)):
    pass
