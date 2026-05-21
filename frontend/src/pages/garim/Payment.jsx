import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Payment.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Payment() {
  useDocumentTitle("결제 · Garim [v1 정식]");

  return (
    <GarimPage bodyClass="page-app" screenLabel="14 Payment (MVP1 disabled)">
      <div className="pay-page">
        <div className="pay-shell">
          <div className="pay-head">
            <h1>
              결제
            </h1>
          </div>
          <div className="summary">
            <div className="row">
              <span>
                1회권 (영상 1편 처리)
              </span>
              <span className="v">
                2,900원
              </span>
            </div>
            <div className="row">
              <span className="caption-k" style={{ fontSize: "13px" }}>
                신규 가입 할인
              </span>
              <span className="v" style={{ color: "#2e7d32" }}>
                -500원
              </span>
            </div>
            <div className="row total">
              <span>
                합계
              </span>
              <span className="v">
                2,400원
              </span>
            </div>
          </div>
          <div className="pay-disabled">
            <span className="material-icons">
              credit_card_off
            </span>
            <h2>
              MVP1 단계에서는 결제가 비활성화되어 있어요
            </h2>
            <p>
              결제 시스템은 v1 정식 출시 시점에 도입됩니다. 현재는 모든 기능을 무료로 이용하세요.
            </p>
            <a href="/replace-options" className="mui-btn mui-btn--contained mui-btn--lg">
              바로 무료 처리하기 →
            </a>
          </div>
          <div className="pg-mock">
            <h3>
              참고 · v1 정식 출시 후 PG사 결제 UI
            </h3>
            <div className="pg-method">
              <button className="active">
                <span className="material-icons">
                  credit_card
                </span>
                신용/체크카드
              </button>
              <button>
                <span className="material-icons">
                  account_balance
                </span>
                계좌이체
              </button>
              <button>
                <span className="material-icons">
                  payment
                </span>
                간편결제
              </button>
            </div>
            <input className="pg-input" placeholder="카드 번호 (PG사 보안 입력)" disabled value="**** **** **** ****" />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              <input className="pg-input" placeholder="MM/YY" disabled value="--/--" />
              <input className="pg-input" placeholder="CVC" disabled value="***" />
            </div>
            <div className="caption-k" style={{ fontSize: "12px", marginTop: "8px" }}>
              카드 정보는 PG사(토스페이먼츠)로 직접 전송됩니다. Garim 서버는 카드번호·CVC를 받지 않습니다 (B-1).
            </div>
          </div>
          <div className="trust-strip">
            <span className="trust">
              <span className="material-icons">
                lock
              </span>
              SSL 256bit
            </span>
            <span className="trust">
              <span className="material-icons">
                verified
              </span>
              PCI DSS Level 1
            </span>
            <span className="trust">
              <span className="material-icons">
                timer
              </span>
              처리 후 즉시 영수증 발급
            </span>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
