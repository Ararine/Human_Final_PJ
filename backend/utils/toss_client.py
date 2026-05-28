import base64
import os
import requests

TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY")


def confirm_payment(payment_key, order_id, amount):
    secret_key = f"{TOSS_SECRET_KEY}:"

    encoded_key = base64.b64encode(
        secret_key.encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": amount,
    }

    response = requests.post(
        "https://api.tosspayments.com/v1/payments/confirm",
        json=payload,
        headers=headers,
    )

    return response.json()