from pydantic import BaseModel


class PaymentConfirmRequest(BaseModel):
    paymentKey: str
    orderId: str
    amount: int


class TempOrderRequest(BaseModel):
    plan_code: str
    amount: int


class TempOrderResponse(BaseModel):
    orderId: str
    amount: int
    orderName: str
    planCode: str