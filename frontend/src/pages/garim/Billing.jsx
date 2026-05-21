import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Billing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Billing() {
  useDocumentTitle("결제·구독 관리 · Garim [v1 정식]");

  return (
    <GarimPage bodyClass="page-app" screenLabel="21 Billing (MVP1 disabled)">
      <div className="billing-page">
        <h1>
          결제·구독 관리
        </h1>
        <div className="empty-state">
          <span className="material-icons">
            payments
          </span>
          <h2>
            MVP1 단계에서는 결제 관리가 아직 활성화되지 않았어요
          </h2>
          <p>
            결제 시스템은 v1 정식 출시 시점에 도입됩니다. 현재는 모든 기능을 무료로 이용하실 수 있어요.
          </p>
          <a href="/dashboard" className="mui-btn mui-btn--contained">
            대시보드로 돌아가기
          </a>
        </div>
        <div className="preview-area">
          <div className="caption-k">
            참고 · v1 정식 출시 후 노출될 결제·구독 관리 UI
          </div>
          <div className="plan-card">
            <span className="mui-chip mui-chip--primary mui-chip--md">
              현재 플랜
            </span>
            <div className="info">
              <h3>
                Pro 월간
              </h3>
              <p>
                다음 결제일 2026.06.14 · 잔여 27/50회
              </p>
            </div>
            <div className="price">
              19,800
              <small style={{ fontSize: "13px", color: "var(--fg-2)" }}>
                원/월
              </small>
            </div>
          </div>
          <div className="table-card">
            <h3>
              결제 내역
            </h3>
            <table className="bills">
              <thead>
                <tr>
                  <th>
                    날짜
                  </th>
                  <th>
                    상품
                  </th>
                  <th>
                    금액
                  </th>
                  <th>
                    영수증
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    2026.05.14
                  </td>
                  <td>
                    Pro 월간
                  </td>
                  <td>
                    19,800원
                  </td>
                  <td>
                    <a style={{ color: "#1976d2" }}>
                      PDF
                    </a>
                  </td>
                </tr>
                <tr>
                  <td>
                    2026.04.14
                  </td>
                  <td>
                    Pro 월간
                  </td>
                  <td>
                    19,800원
                  </td>
                  <td>
                    <a style={{ color: "#1976d2" }}>
                      PDF
                    </a>
                  </td>
                </tr>
                <tr>
                  <td>
                    2026.03.14
                  </td>
                  <td>
                    Pro 월간
                  </td>
                  <td>
                    19,800원
                  </td>
                  <td>
                    <a style={{ color: "#1976d2" }}>
                      PDF
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
