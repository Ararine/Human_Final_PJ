import { useSearchParams, useNavigate } from "react-router-dom";
import GarimPage from "../../components/garim/GarimPage";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";

// [한글 주석] 결제 혹은 빌링키 승인 실패 시의 안내 화면 컴포넌트
export default function PaymentFail() {
  useDocumentTitle("결제 실패 · Garim");
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // URL 쿼리 스트링에서 전달받은 상세 에러 메시지를 우선 출력하며, 없을 시 기본값을 지정합니다.
  const message = searchParams.get("message") || "결제가 취소되었거나 실패했습니다.";
  const code = searchParams.get("code") || "";

  return (
    <GarimPage bodyClass="page-app page-payment-fail" screenLabel="Payment Fail">
      <main style={{ padding: "80px 24px", display: "flex", justifyContent: "center" }}>
        <div className="pay-shell" style={{ maxWidth: "600px", width: "100%", textAlign: "center", padding: "48px 32px" }}>
          <div style={{ marginBottom: "24px" }}>
            <span className="material-icons" style={{ fontSize: "64px", color: "var(--color-error, #f44336)" }}>
              error_outline
            </span>
          </div>
          
          <h1 style={{ fontSize: "28px", fontWeight: "700", marginBottom: "16px", color: "var(--color-text-primary, #333)" }}>
            결제 및 구독 승인 실패
          </h1>
          
          <p style={{ fontSize: "16px", color: "var(--color-text-secondary, #666)", marginBottom: "32px", wordBreak: "break-all" }}>
            {message} {code && `(에러 코드: ${code})`}
          </p>

          <div style={{ display: "flex", justifyContent: "center", gap: "12px" }}>
            <button
              type="button"
              className="mui-btn mui-btn--contained"
              onClick={() => navigate("/pricing")}
              style={{ minWidth: "140px" }}
            >
              요금제 페이지로
            </button>
          </div>
        </div>
      </main>
    </GarimPage>
  );
}
