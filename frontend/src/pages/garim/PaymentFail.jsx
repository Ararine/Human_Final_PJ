/*
코드 설명:
결제 취소·실패 시 표시되는 안내 페이지.
PaymentSuccess와 동일한 레이아웃으로 꾸며지며,
이전 버튼 클릭 시 요금제 페이지(/pricing)로 이동한다.
오류 상세 내용은 사용자에게 노출하지 않고 고정 안내 문구만 표시한다.
*/
import { useNavigate } from "react-router-dom";

import GarimPage from "../../components/garim/GarimPage";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/PaymentFail.css";

export default function PaymentFail() {
  useDocumentTitle("결제 실패 · Garim");
  const navigate = useNavigate();

  /* 이전 버튼: 요금제 페이지로 이동 */
  const handleGoBack = () => {
    navigate("/pricing");
  };

  return (
    <GarimPage bodyClass="page-app page-payment-fail" screenLabel="Payment Fail">
      <main className="payment-fail-main">
        <div className="payment-fail-content">

          {/* 결과 카드 */}
          <div className="pay-shell">
            {/* 헤더 */}
            <div className="pay-head">
              <h1>결제 실패</h1>
            </div>

            {/* 아이콘 및 안내 문구 영역 */}
            <div className="pay-disabled">
              <div className="pay-fail-visual">
                {/* 붉은 원 배경 위 취소 아이콘 */}
                <span className="material-icons pay-fail-icon">cancel</span>
              </div>
              <h2>결제를 완료하지 못했어요</h2>
              <p>
                결제가 취소되었거나 처리 중 문제가 발생했습니다.<br />
                잠시 후 다시 시도해 주세요.
              </p>
            </div>
          </div>

          {/* 하단 버튼 */}
          <div className="payment-fail-actions">
            <button
              type="button"
              className="mui-btn mui-btn--contained payment-fail-back-btn"
              onClick={handleGoBack}
              aria-label="요금제 페이지로 이동"
            >
              <span className="material-icons">arrow_back</span>
              요금제로 돌아가기
            </button>
          </div>

        </div>
      </main>
    </GarimPage>
  );
}
