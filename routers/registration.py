from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Annotated
from orm.database import get_db
from orm.models import Registration
from pydantic_models.request.registration_request import RegistrationRequest
from pydantic_models.response.registration_out import RegistrationOut

router = APIRouter(
    prefix="/registration",
    tags=["registration"],
)

DbSession = Annotated[Session, Depends(get_db)]

@router.post("/register", status_code=201, response_model=RegistrationOut)
def register(request: RegistrationRequest, db: DbSession):
    row = Registration(**request.model_dump())
    db.add(row)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not save registration {e}")
    db.refresh(row)
    return row

@router.get("/{registration_id}", response_model=RegistrationOut)
def get_registration(registration_id: int, db: DbSession):
    row = db.get(Registration, registration_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Registration with id {registration_id} not found")
    return row

