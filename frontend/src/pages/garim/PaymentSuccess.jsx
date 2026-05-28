import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const confirmPayment = async () => {
      try {
        const paymentKey = searchParams.get("paymentKey");

        const orderId = searchParams.get("orderId");

        const amount = Number(searchParams.get("amount"));

        console.log({
          paymentKey,
          orderId,
          amount,
        });

        const response = await fetch(
          "http://localhost:8000/payment/payment/confirm",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              paymentKey,
              orderId,
              amount,
            }),
          },
        );

        const data = await response.json();

        console.log("결제 승인 성공:", data);
      } catch (err) {
        console.error("결제 승인 실패:", err);
      }
    };

    confirmPayment();
  }, [searchParams]);

  return (
    <div style={{ padding: "40px" }}>
      <h1>결제 성공</h1>
      <p>결제가 완료되었습니다.</p>
    </div>
  );
}
