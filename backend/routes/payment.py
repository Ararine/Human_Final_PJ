from fastapi import APIRouter, Depends, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.database import get_db
from services import auth
from controllers import payment
from schemas.payment import PaymentConfirmRequest, TempOrderRequest, TempOrderResponse

router = APIRouter(tags=["payment"])

@router.get("/me")
async def get_my_payment_info(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    current_user = auth.authenticate_access_token(access_token)
    user_id = current_user["id"]
    
    # 1. 플랜 정보 및 구독 날짜 확인
    sub_row = db.execute(
        text("""
            SELECT pl.plan_name, pl.plan_code, s.created_at 
            FROM subscriptions s
            JOIN plans pl ON s.plan_id = pl.plan_id
            WHERE s.user_id = :user_id AND s.status = 'active'
        """),
        {"user_id": user_id}
    ).fetchone()

    plan_name = "무료 플랜"
    plan_date = None
    is_premium = False
    
    if sub_row:
        p_code = sub_row._mapping["plan_code"].lower()
        if p_code != 'free':
            is_premium = True
            plan_name = sub_row._mapping["plan_name"]
            plan_date = sub_row._mapping["created_at"]

    # 2. 결제 내역 전체 조회 (플랜 및 크레딧 모두 포함)
    pay_rows = db.execute(
        text("""
            SELECT 
                payment_id, order_name, pg_provider, amount, created_at
            FROM payments
            WHERE user_id = :user_id AND status IN ('DONE', 'success')
            ORDER BY created_at DESC
        """),
        {"user_id": user_id}
    ).fetchall()

    history = []
    for r in pay_rows:
        p = r._mapping
        history.append({
            "orderId": str(p["payment_id"]),
            "orderName": p["order_name"],
            "method": p.get("pg_provider") or "간편결제",
            "amount": p["amount"],
            "approvedAt": p["created_at"].isoformat() if p["created_at"] else None
        })

    return {
        "is_premium": is_premium,
        "plan_name": plan_name,
        "plan_date": plan_date.isoformat() if plan_date else None,
        "payment_history": history
    }


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
