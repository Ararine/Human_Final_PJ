def test_confirm_payment(client):

    response = client.post(
        "/payment/confirm",
        json={
            "user_id":
            "uuid",
            "paymentKey":
            "test_key",

            "orderId":
            "order_1",

            "amount":
            100,
        },
    )

    assert response.status_code == 200