from typing import Optional

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from paymentserver.models.payment import Payment
from paymentserver.domain.payment_service import PaymentService

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Payment API is up and running"}


@router.get("/payments")
async def get_payments(
    search: Optional[str] = None, page_number: int = 1, page_size: int = 20
):
    if page_number < 0:
        raise HTTPException(
            status_code=400,
            detail="page number must be greater than 0",
        )

    if page_size < 0:
        raise HTTPException(
            status_code=400,
            detail="page size must be greater than 0",
        )

    payments, total = await PaymentService.get_payments(search, page_number, page_size)
    return {"payments": payments, "total": total}


@router.post("/payment/")
async def create_payment(payment: Payment):
    if payment.payee_payment_status != "pending":
        raise HTTPException(
            status_code=400,
            detail="payment status can only be pending when creating a payment",
        )

    try:
        id = PaymentService.create_payment(payment)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return id


@router.put("/payment/{payment_id}")
async def update_payment(payment_id: str, payment: Payment):
    payment_statuses = ["pending", "due_now", "completed", "overdue"]

    if payment.payee_payment_status not in payment_statuses:
        raise HTTPException(
            status_code=400,
            detail="payment status must be one of: pending, due_now, completed, overdue",
        )
    try:
        await PaymentService.update_payment(payment_id, payment)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    return {"status": "success"}


@router.delete("/payment/{payment_id}")
async def delete_payment(payment_id: str):
    try:
        PaymentService.delete_payment(payment_id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    return {"status": "success"}


@router.post("/payment/{payment_id}/evidence")
async def upload_evidence(payment_id: str, file: UploadFile):
    content = await file.read()
    file_name = file.filename

    if not file.content_type in ["application/pdf", "image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        await PaymentService.create_evidence(payment_id, content, file_name)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    return {"status": "success"}


@router.get("/payment/{payment_id}/evidence")
async def download_evidence(payment_id: str):
    try:
        evidence = await PaymentService.get_evidence(payment_id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return StreamingResponse(
        BytesIO(evidence["content"]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=${evidence['filename']}"
        },
    )
