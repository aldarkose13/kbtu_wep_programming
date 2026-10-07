from pydantic import BaseModel, Field, model_validator


class RegistrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    attending: bool
    amount_of_people: int = Field(default=0, ge=0, le=10)

    @model_validator(mode="after")
    def check_guests(self):
        if self.attending and self.amount_of_people < 1:
            raise ValueError("amount_of_people must be at least 1 when attending")
        if not self.attending:
            self.amount_of_people = 0
        return self