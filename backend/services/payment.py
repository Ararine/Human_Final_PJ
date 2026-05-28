import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

TOSS_SECRET_KEY = os.getenv(
    "TOSS_SECRET_KEY"
)


async def confirm_payment(
    payment_key: str,
    order_id: str,
    amount: int
):
    if not TOSS_SECRET_KEY:
        raise Exception(
            "TOSS_SECRET_KEY가 .env에서 로드되지 않았습니다."
        )

    secret_key = (
        f"{TOSS_SECRET_KEY}:"
    )

    encoded_key = base64.b64encode(
        secret_key.encode()
    ).decode()

    headers = {
        "Authorization":
            f"Basic {encoded_key}",

        "Content-Type":
            "application/json",
    }

    payload = {
        "paymentKey":
            payment_key,

        "orderId":
            order_id,

        "amount":
            amount,
    }

    response = requests.post(
        "https://api.tosspayments.com/v1/payments/confirm",
        json=payload,
        headers=headers,
    )

    return response.json()