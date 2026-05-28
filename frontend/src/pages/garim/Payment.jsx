import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Payment.css";

import { loadTossPayments } from "@tosspayments/payment-sdk";
import GarimPage from "../../components/garim/GarimPage";

const clientKey = import.meta.env.VITE_TOSS_CLIENT_KEY;

export default function Payment() {
  useDocumentTitle("결제 · Garim [v1 정식]");

  const handlePayment = async () => {
    try {
      const tossPayments = await loadTossPayments(clientKey);

      await tossPayments.requestPayment("CARD", {
        amount: 100,

        orderId: "order-" + Date.now(),

        orderName: "Garim PRO 테스트",

        customerName: "테스트유저",

        successUrl: "http://localhost:3000/payment/success",

        failUrl: "http://localhost:3000/payment/fail",
      });
    } catch (err) {
      console.error(err);
      alert("결제창 실행 실패");
    }
  };

  return (
    <GarimPage bodyClass="page-app" screenLabel="14 Payment">
      <div className="pay-page">
        <div className="pay-shell">
          <div className="pay-head">
            <h1>결제</h1>
          </div>

          <div className="summary">
            <div className="row">
              <span>1회권 (영상 1편 처리)</span>
              <span className="v">100원</span>
            </div>

            <div className="row total">
              <span>합계</span>
              <span className="v">100원</span>
            </div>
          </div>

          <div className="pay-disabled">
            <span className="material-icons">payments</span>

            <h2>테스트 결제</h2>

            <p>토스페이먼츠 결제창 테스트입니다.</p>

            <button
              onClick={handlePayment}
              className="mui-btn mui-btn--contained mui-btn--lg"
            >
              결제하기 →
            </button>
          </div>

          <div className="trust-strip">
            <span className="trust">
              <span className="material-icons">lock</span>
              SSL 256bit
            </span>

            <span className="trust">
              <span className="material-icons">verified</span>
              PCI DSS Level 1
            </span>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
