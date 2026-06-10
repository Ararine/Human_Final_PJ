import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom"; // useNavigate 임포트 추가

import GarimPage from "../../components/garim/GarimPage";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { confirmPayment } from "../../utils/api";

function getProcessedOrders() {
  try {
    return JSON.parse(sessionStorage.getItem("processedPaymentOrders") || "[]");
  } catch {
    return [];
  }
}

function addProcessedOrder(orderId) {
  const orders = getProcessedOrders();
  if (orders.includes(orderId)) return;
  sessionStorage.setItem("processedPaymentOrders", JSON.stringify([...orders, orderId]));
}

function getStoredPaymentResult(orderId) {
  try {
    const stored = sessionStorage.getItem(`paymentResult:${orderId}`);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function storePaymentResult(orderId, data) {
  try {
    sessionStorage.setItem(`paymentResult:${orderId}`, JSON.stringify(data));
  } catch {
    // Backend idempotency is the source of truth, so storage failure is non-fatal.
  }
}

export default function PaymentSuccess() {
  useDocumentTitle("결제 성공 · Garim");
  const navigate = useNavigate(); // useNavigate 훅 초기화

  // 이전 페이지 이동 핸들러 (히스토리가 없으면 설정 페이지로 fallback)
  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate("/settings");
    }
  };

  // 결제 내역 확인(설정 페이지) 이동 핸들러
  const handleGoSettings = () => {
    navigate("/settings");
  };

  const [searchParams] = useSearchParams();
  const didConfirmRef = useRef(false);
  const [status, setStatus] = useState("confirming");
  const [message, setMessage] = useState("결제 승인 처리 중입니다.");
  const [result, setResult] = useState(null);

  const paymentKey = searchParams.get("paymentKey") || "";
  const orderId = searchParams.get("orderId") || "";
  const requestedAmount = Number(searchParams.get("amount") || 0);
  const displayAmount = Number(result?.amount || requestedAmount || 0);

  useEffect(() => {
    async function runConfirm() {
      if (didConfirmRef.current) return;
      didConfirmRef.current = true;

      if (!paymentKey || !orderId || !requestedAmount) {
        setStatus("error");
        setMessage("결제 승인에 필요한 파라미터가 부족합니다.");
        return;
      }

      const processedOrders = getProcessedOrders();
      if (processedOrders.includes(orderId)) {
        setResult(getStoredPaymentResult(orderId));
        setStatus("success");
        setMessage("이미 처리된 결제입니다.");
        return;
      }

      try {
        const data = await confirmPayment({
          paymentKey,
          orderId,
          amount: requestedAmount,
        });
        addProcessedOrder(orderId);
        storePaymentResult(orderId, data);
        setResult(data);
        setStatus("success");
        setMessage(data.idempotent ? "이미 승인 완료된 결제입니다." : "결제 승인이 완료되었습니다.");
      } catch (error) {
        console.error("Failed to confirm payment", error);
        setStatus("error");
        setMessage(error.message || "결제 승인 처리에 실패했습니다.");
      }
    }

    runConfirm();
  }, [orderId, paymentKey, requestedAmount]);

  return (
    <GarimPage bodyClass="page-app page-payment-success" screenLabel="Payment Success">
      <main className="payment-success-main">
        <div className="payment-success-content">
          <div
            className={`mui-alert ${status === "error" ? "mui-alert--error" : "mui-alert--success"}`}
            style={{ marginBottom: "16px" }}
          >
            {message}
          </div>

          <div className="pay-shell" style={{ maxWidth: "720px" }}>
            <div className="pay-head">
              <h1>결제 성공</h1>
            </div>

            <div className="summary">
              <div className="row">
                <span>주문명</span>
                <span className="v">{result?.orderName || "Garim 결제"}</span>
              </div>
              <div className="row">
                <span>주문번호</span>
                <span className="v" style={{ fontSize: "13px", wordBreak: "break-all" }}>
                  {orderId || "-"}
                </span>
              </div>
              {result?.method && (
                <div className="row">
                  <span>결제 수단</span>
                  <span className="v">{result.method}</span>
                </div>
              )}
              <div className="row total">
                <span>결제 금액</span>
                <span className="v">{displayAmount ? `${displayAmount.toLocaleString("ko-KR")}원` : "-"}</span>
              </div>
            </div>
          </div>

          {/* 결제 확인창 아래 중앙 버튼 영역 (flexWrap: "wrap" 추가로 좁은 화면 줄바꿈 대응) */}
          <div
            className="payment-success-actions"
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: "12px",
              marginTop: "24px",
              flexWrap: "wrap",
            }}
          >
            <button
              type="button"
              className="mui-btn mui-btn--outlined"
              onClick={handleGoBack}
              aria-label="이전 페이지로 이동"
              style={{ minWidth: "120px" }}
            >
              이전 페이지로
            </button>

            <button
              type="button"
              className="mui-btn mui-btn--contained"
              onClick={handleGoSettings}
              aria-label="결제 내역 확인 페이지로 이동"
              style={{ minWidth: "140px" }}
            >
              결제 내역 확인
            </button>
          </div>

        </div>
      </main>
    </GarimPage>
  );
}
