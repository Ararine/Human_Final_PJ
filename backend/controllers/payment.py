from fastapi import HTTPException
from sqlalchemy.orm import Session
from schemas.payment import (
    PaymentConfirmRequest,
    TempOrderRequest
)

from services import payment


async def create_temp_order(
    body: TempOrderRequest,
    current_user: dict,
    db: Session
):
    try:
        result = await payment.create_temp_order(
            db=db,
            user_id=current_user["id"],
            plan_code=body.plan_code,
            amount=body.amount
        )
        return {
            "orderId": result["payment_id"],
            "amount": result["amount"],
            "orderName": result["plan_name"],
            "planCode": result["plan_code"]
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




async def confirm_payment(
    body: PaymentConfirmRequest,
    db: Session
):
    try:
        result = await payment.confirm_payment(
            db=db,
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

def get_my_payment_info(current_user: dict, db: Session):
    try:
        # services/payment.py의 함수 호출
        return payment.get_my_payment_info(
            db=db,
            user_id=current_user["id"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
