from fastapi import APIRouter
from controllers import payment
from schemas.payment import (
    PaymentConfirmRequest
)

router = APIRouter(
    prefix="/payment",
    tags=["payment"]
)


@router.post("/confirm")
async def confirm_payment(
    body: PaymentConfirmRequest
):
    return await payment.confirm_payment(
        body
    )