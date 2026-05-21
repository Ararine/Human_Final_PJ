import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/PaymentGate.css";

import GarimPage from "../../components/garim/GarimPage";

export default function PaymentGate() {
  useDocumentTitle("플랜 선택 · Garim [v1 정식]");

  return (
    <GarimPage bodyClass="page-app" screenLabel="13 Payment gate (MVP1 disabled)">
      <div className="gate-page">
        <a href="/analysis-report" className="gh__icon close-btn" style={{ background: "rgba(0,0,0,0.04)" }}>
          <span className="material-icons">
            close
          </span>
        </a>
        <div className="gate-shell">
          <div className="gate-head">
            <h1>
              결제 게이트 · 플랜 선택
            </h1>
            <div className="sub">
              처리할 파일을 확인하고 플랜을 선택해주세요.
            </div>
          </div>
          <div className="target-file">
            <div className="thumb">
              <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=300&amp;q=60" alt="" />
            </div>
            <div style={{ flex: "1" }}>
              <h3>
                family_picnic_2026.mp4
              </h3>
              <div className="meta">
                17건 검출됨 · 위험도 8.2/10 · 2분 14초 · 847MB
              </div>
            </div>
            <span className="mui-chip mui-chip--soft-info mui-chip--md">
              처리 대상
            </span>
          </div>
          <div className="gate-body">
            <div className="gate-disabled">
              <span className="material-icons">
                payments
              </span>
              <h2>
                MVP1 단계에서는 결제 없이 이용하실 수 있어요
              </h2>
              <p>
                현재 모든 치환 기능이 무료입니다. 결제 시스템은 v1 정식 출시 시점에 도입됩니다. 지금 바로 처리하러 이동하시겠어요?
              </p>
              <div className="actions-row">
                <a href="/analysis-report" className="mui-btn mui-btn--outlined">
                  ← 리포트로 돌아가기
                </a>
                <a href="/replace-options" className="mui-btn mui-btn--contained mui-btn--lg">
                  <span className="material-icons" style={{ fontSize: "20px" }}>
                    arrow_forward
                  </span>
                  바로 무료 처리하기
                </a>
              </div>
            </div>
            <div style={{ marginTop: "48px", paddingTop: "32px", borderTop: "1px dashed var(--mui-divider)" }}>
              <div className="caption-k" style={{ textAlign: "center", marginBottom: "16px" }}>
                참고 · v1 정식 출시 후 노출될 플랜 옵션
              </div>
              <div className="preview-grid">
                <div className="preview-card">
                  <span className="overline-k">
                    1회권
                  </span>
                  <div className="price">
                    2,900
                    <small style={{ fontSize: "14px" }}>
                      원
                    </small>
                  </div>
                  <p className="caption-k" style={{ fontSize: "13px" }}>
                    이번 영상 1편만 처리
                  </p>
                </div>
                <div className="preview-card" style={{ borderColor: "#1976d2" }}>
                  <span className="mui-chip mui-chip--primary" style={{ marginBottom: "8px" }}>
                    추천
                  </span>
                  <h4>
                    Pro
                  </h4>
                  <div className="price">
                    19,800
                    <small style={{ fontSize: "14px" }}>
                      원/월
                    </small>
                  </div>
                  <p className="caption-k" style={{ fontSize: "13px" }}>
                    월 50회 · 우선 처리
                  </p>
                </div>
                <div className="preview-card">
                  <span className="overline-k">
                    Studio
                  </span>
                  <div className="price">
                    99,000
                    <small style={{ fontSize: "14px" }}>
                      원/월
                    </small>
                  </div>
                  <p className="caption-k" style={{ fontSize: "13px" }}>
                    팀 5인 · 월 500회
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
