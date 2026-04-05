from pydantic import BaseModel


class Account(BaseModel):
    """Core domain model representing a Bank Account."""

    id: str
    iban: str
    name: str
    currency: str
