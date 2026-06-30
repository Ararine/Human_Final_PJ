/*
코드 설명:
Toss 결제 성공 리다이렉트를 받아 백엔드 승인(confirm)을 1회 처리하고, 중복 승인을 방지하며 결제 결과를 보여주는 페이지.
*/
import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom"; // useNavigate 임포트 추가

import GarimPage from "../../components/garim/GarimPage";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { confirmPayment, confirmBillingPayment } from "../../utils/api";
import "../../css/garim-pages/PaymentSuccess.css";

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

function formatOrderName(value) {
  if (!value) return "Garim 결제";
  return String(value)
    .replace(/yearly subscription/gi, "연 구독")
    .replace(/monthly subscription/gi, "월 구독")
    .replace(/renewal/gi, "자동결제 갱신")
    .replace(/scheduled downgrade/gi, "예약 다운그레이드")
    .replace(/\bFree\b/g, "무료");
}

function formatPaymentMethod(value) {
  const normalized = String(value || "").toLowerCase();
  if (!normalized) return "-";
  if (normalized === "billing") return "자동결제";
  if (normalized === "card") return "카드";
  if (normalized === "easy_pay") return "간편결제";
  if (normalized === "free_bypass") return "무료 처리";
  return value;
}

export default function PaymentSuccess() {
  useDocumentTitle("결제 성공 · Garim");
  const navigate = useNavigate(); // useNavigate 훅 초기화

  // [한글 주석] 이전 페이지 이동 핸들러: 결제 성공 이후 백버튼 동작 시, 이전 결제 대기 페이지 진입을 차단하기 위해 요금제 페이지(/pricing)로 직접 라우팅시킵니다.
  const handleGoBack = () => {
    navigate("/pricing");
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

      const isBilling = window.location.pathname.includes("billing-success");

      if (isBilling) {
        /* [한글 주석] 정기 결제 빌링 인증 성공 시의 승인 처리 흐름입니다. */
        const authKey = searchParams.get("authKey") || "";
        const customerKey = searchParams.get("customerKey") || "";
        const planCode = searchParams.get("planCode") || "";
        const billingCycle = searchParams.get("billingCycle") === "yearly" ? "yearly" : "monthly";

        if (!authKey || !customerKey || !planCode) {
          setStatus("error");
          setMessage("정기 결제 승인에 필요한 파라미터가 부족합니다.");
          return;
        }

        try {
          const data = await confirmBillingPayment({
            authKey,
            customerKey,
            planCode,
            billingCycle,
          });
          setResult(data);
          setStatus("success");
          setMessage(data.idempotent ? "이미 승인 완료된 정기 결제입니다." : "정기 구독 승인이 완료되었습니다.");
        } catch (error) {
          /* [한글 주석] 정기 결제 승인 처리가 실패했을 때, 상세 에러 메시지와 함께 정기결제 실패 페이지(/payment/billing-fail)로 리다이렉트시킵니다. */
          console.error("Failed to confirm billing payment", error);
          navigate(`/payment/billing-fail?message=${encodeURIComponent(error.message || "정기 결제 승인 처리에 실패했습니다.")}`);
        }
      } else {
        /* [한글 주석] 기존 크레딧 일회성 결제 성공 시의 승인 처리 흐름입니다. */
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
    }

    runConfirm();
  }, [navigate, orderId, paymentKey, requestedAmount, searchParams]);

  return (
    <GarimPage bodyClass="page-app page-payment-success" screenLabel="Payment Success">
      <main className="payment-success-main">
        <div className="payment-success-content">
          <div
            className={`mui-alert payment-success-alert ${status === "error" ? "mui-alert--error" : "mui-alert--success"}`}
          >
            {message}
          </div>

          <div className="pay-shell">
            <div className="pay-head">
              <h1>결제 성공</h1>
            </div>

            <div className="summary">
              <div className="row">
                <span>주문명</span>
                <span className="v">{formatOrderName(result?.orderName)}</span>
              </div>
              <div className="row">
                <span>주문번호</span>
                <span className="v payment-success-orderid">
                  {orderId || "-"}
                </span>
              </div>
              {result?.method && (
                <div className="row">
                  <span>결제 수단</span>
                  <span className="v">{formatPaymentMethod(result.method)}</span>
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
