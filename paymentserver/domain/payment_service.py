from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date, timezone
from bson import ObjectId
import pandas

from paymentserver.models.evidence import Evidence
from paymentserver.models.payment import Payment
from paymentserver.infrastructure.payment_repo import (
    payment_collection,
    evidence_collection,
)


@dataclass
class PaymentService:

    async def get_payments(
        search: Optional[str] = None, page_number: int = 1, page_size: int = 20
    ) -> list[Payment]:
        query = {}
        if search:
            query = {
                "$or": [
                    {"payee_first_name": {"$regex": search, "$options": "i"}},
                    {"payee_last_name": {"$regex": search, "$options": "i"}},
                    {"payee_email": {"$regex": search, "$options": "i"}},
                    {"payee_payment_status": {"$regex": search, "$options": "i"}},
                    {"payee_address_line_1": {"$regex": search, "$options": "i"}},
                    {"payee_address_line_2": {"$regex": search, "$options": "i"}},
                    {"payee_city": {"$regex": search, "$options": "i"}},
                    {"payee_country": {"$regex": search, "$options": "i"}},
                    {"payee_province_or_state": {"$regex": search, "$options": "i"}},
                    {"payee_postal_code": {"$regex": search, "$options": "i"}},
                    {"payee_phone_number": {"$regex": search, "$options": "i"}},
                    {"currency": {"$regex": search, "$options": "i"}},
                ]
            }

        payments = (
            payment_collection.find(query)
            .skip((page_number - 1) * page_size)
            .limit(page_size)
        )
        total = payment_collection.count_documents({})
        data = []
        for payment in payments:
            print(payment)
            payment["payee_payment_status"] = update_payment_status(
                payment, today=date.today()
            )
            payment["id"] = str(payment["_id"])
            payment["payee_due_date"] = payment["payee_due_date"].date()
            data.append(Payment(**payment))

        return data, total

    def create_payment(payment: Payment) -> str:
        payment_dict = payment.model_dump()
        payment_dict["id"] = "0"
        payment_dict["payee_due_date"] = datetime.combine(
            payment_dict["payee_due_date"], datetime.min.time()
        )
        try:
            result = payment_collection.insert_one(payment_dict)
        except Exception as e:
            print("An error occurred while inserting the document:", e)
            raise e
        # Do the logic here
        return str(result.inserted_id)

    async def update_payment(payment_id: str, payment: Payment) -> str:
        found_payment = payment_collection.find_one({"_id": ObjectId(payment_id)})
        if not found_payment:
            raise Exception("Payment not found")

        if payment.payee_payment_status == "completed":
            evidence = evidence_collection.find_one(
                {"payment_id": ObjectId(payment_id)}
            )
            if not evidence:
                raise Exception(
                    "Unable to mark a payment as completed without evidence"
                )
        found_payment["payee_due_date"] = datetime.combine(
            payment.payee_due_date, datetime.min.time()
        )
        found_payment["due_amount"] = payment.due_amount
        found_payment["payee_payment_status"] = payment.payee_payment_status

        result = payment_collection.update_one(
            {"_id": ObjectId(payment_id)}, {"$set": found_payment}
        )

        if result.matched_count == 0:
            raise Exception("Payment not found for id", payment_id)
        return

    def delete_payment(payment_id: str) -> str:
        result = payment_collection.delete_one({"_id": ObjectId(payment_id)})
        if result.deleted_count == 0:
            raise Exception("Payment not found")

    async def create_evidence(payment_id: str, content, file_name: str) -> str:

        payment = payment_collection.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise Exception("Payment not found")

        evidence_data = {
            "payment_id": ObjectId(payment_id),
            "filename": file_name,
            "content": content,
        }

        try:
            evidence_collection.insert_one(evidence_data)
        except Exception as e:
            print("An error occurred while inserting the document:", e)
            raise e
        return

    async def get_evidence(payment_id: str) -> Evidence:
        evidence = evidence_collection.find_one({"payment_id": ObjectId(payment_id)})
        if not evidence:
            raise Exception("Evidence not found")
        return evidence

    def add_data_from_file(file_path: str):
        if payment_collection.count_documents({}) > 0:
            return

        data = pandas.read_csv(file_path)

        required = [
            "payee_address_line_1",
            "payee_city",
            "payee_country",
            "payee_postal_code",
            "payee_phone_number",
            "payee_email",
            "currency",
        ]
        data = data.dropna(subset=required)
        normalized = data.fillna(
            {"discount_percent": 0, "tax_percent": 0, "due_amount": 0, "total_due": 0}
        ).to_dict(orient="records")

        for entry in normalized:
            entry["payee_added_date_utc"] = pandas.to_datetime(
                entry["payee_added_date_utc"], errors="coerce"
            )
            entry["payee_due_date"] = pandas.to_datetime(
                entry["payee_due_date"], errors="coerce"
            )
            entry["discount_percent"] = pandas.to_numeric(
                entry["discount_percent"], errors="coerce"
            )
            entry["tax_percent"] = pandas.to_numeric(
                entry["tax_percent"], errors="coerce"
            )
            entry["due_amount"] = pandas.to_numeric(
                entry["due_amount"], errors="coerce"
            )
            entry["payee_postal_code"] = str(entry["payee_postal_code"])
            entry["payee_phone_number"] = str(entry["payee_phone_number"])

            entry["payee_payment_status"] = update_payment_status(
                entry, today=date.today()
            )

        try:
            payment_collection.insert_many(normalized)
        except Exception as e:
            print("An error occurred while inserting the document:", e)
            raise e


def update_payment_status(payment: Payment, today) -> str:
    due_date = payment["payee_due_date"].date()
    if today == due_date:
        return "due_now"
    elif due_date < today:
        return "overdue"
    return payment["payee_payment_status"]
