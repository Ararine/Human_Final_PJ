from typing import Literal

from pydantic import BaseModel


class PaymentConfirmRequest(BaseModel):
    paymentKey: str
    orderId: str
    amount: int


class TempOrderRequest(BaseModel):
    product_type: Literal["subscription", "credit"]
    product_code: str
    amount: int


class TempOrderResponse(BaseModel):
    orderId: str
    amount: int
    orderName: str
    productType: Literal["subscription", "credit"]
    productCode: str
