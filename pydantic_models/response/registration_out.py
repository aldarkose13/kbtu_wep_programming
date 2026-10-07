from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    surname: str
    attending: bool
    amount_of_people: int
    created_at: datetime