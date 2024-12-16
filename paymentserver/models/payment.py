from pydantic import BaseModel, EmailStr, computed_field
from typing import Optional
from datetime import date, datetime


class Payment(BaseModel):
    _id: Optional[str]
    id: Optional[str]
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: str
    payee_added_date_utc: datetime
    payee_due_date: date
    payee_address_line_1: str
    payee_address_line_2: Optional[str]
    payee_city: str
    payee_country: str
    payee_province_or_state: Optional[str]
    payee_postal_code: str
    payee_phone_number: str
    payee_email: EmailStr
    currency: str
    discount_percent: Optional[float]
    tax_percent: Optional[float]
    due_amount: float

    @computed_field
    def total_due(self) -> float:
        discount = self.due_amount * self.discount_percent / 100
        tax = self.due_amount * self.tax_percent / 100
        return self.due_amount - discount + tax
