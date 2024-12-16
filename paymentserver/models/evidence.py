from typing import Any, Optional
from pydantic import BaseModel


class Evidence(BaseModel):
    _id: Optional[str]
    payment_id: str
    filename: str
    content: Any
