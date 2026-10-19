import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from orm.database import get_db
from orm.models import Registration
from pydantic_models.request.registration_request import RegistrationRequest
from pydantic_models.response.registration_out import RegistrationOut

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/registration",
    tags=["registration"],
)

DbSession = Annotated[Session, Depends(get_db)]


def get_or_404(db: Session, registration_id: int) -> Registration:
    row = db.get(Registration, registration_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Registration with id {registration_id} not found")
    return row


def commit_or_500(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database commit failed")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/", response_model=list[RegistrationOut])
def list_registrations(db: DbSession):
    return db.scalars(select(Registration).order_by(Registration.id)).all()


@router.get("/{registration_id}", response_model=RegistrationOut)
def get_registration(registration_id: int, db: DbSession):
    return get_or_404(db, registration_id)


@router.post("/", status_code=201, response_model=RegistrationOut)
def create_registration(request: RegistrationRequest, db: DbSession):
    row = Registration(**request.model_dump())
    db.add(row)
    commit_or_500(db)
    db.refresh(row)
    return row


@router.put("/{registration_id}", response_model=RegistrationOut)
def update_registration(registration_id: int, request: RegistrationRequest, db: DbSession):
    row = get_or_404(db, registration_id)
    for field, value in request.model_dump().items():
        setattr(row, field, value)
    commit_or_500(db)
    db.refresh(row)
    return row


@router.delete("/{registration_id}", status_code=204)
def delete_registration(registration_id: int, db: DbSession):
    row = get_or_404(db, registration_id)
    db.delete(row)
    commit_or_500(db)
    return Response(status_code=204)
