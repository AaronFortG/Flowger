import datetime

from pydantic import BaseModel


class BankSession(BaseModel):
    """Represents an authorized bank session obtained after user OAuth flow."""

    session_id: str
    bank_name: str
    country: str
    created_at: datetime.datetime
