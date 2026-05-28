from fastapi import HTTPException
from schemas.payment import (
    PaymentConfirmRequest
)

from services import payment


async def confirm_payment(
    body: PaymentConfirmRequest
):
    try:
        result = await payment.confirm_payment(
            payment_key=body.paymentKey,
            order_id=body.orderId,
            amount=body.amount
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )