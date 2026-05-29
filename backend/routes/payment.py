from fastapi import APIRouter, Depends, Cookie
from sqlalchemy.orm import Session
from utils.database import get_db
from services import auth
from controllers import payment
from schemas.payment import (
    PaymentConfirmRequest,
    TempOrderRequest,
    TempOrderResponse
)

router = APIRouter(
    tags=["payment"]
)


@router.post("/temp-order", response_model=TempOrderResponse)
async def create_temp_order(
    body: TempOrderRequest,
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    current_user = auth.authenticate_access_token(access_token)
    return await payment.create_temp_order(
        body=body,
        current_user=current_user,
        db=db
    )


@router.post("/confirm")
async def confirm_payment(
    body: PaymentConfirmRequest,
    db: Session = Depends(get_db)
):
    return await payment.confirm_payment(
        body,
        db
    )
