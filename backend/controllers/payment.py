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
            product_type=body.product_type,
            product_code=body.product_code,
            amount=body.amount
        )
        return {
            "orderId": result["payment_id"],
            "amount": result["amount"],
            "orderName": result["order_name"],
            "productType": result["product_type"],
            "productCode": result["product_code"]
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


def get_my_credit_balance(current_user: dict, db: Session):
    try:
        return payment.get_my_credit_balance(
            db=db,
            user_id=current_user["id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
