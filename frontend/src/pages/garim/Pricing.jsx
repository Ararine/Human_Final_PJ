import { useNavigate } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useAuthStatus } from "../../hooks/useAuthStatus";
import {
  formatFileSize,
  formatPrice,
  formatQuota,
  usePricingPlans,
} from "../../hooks/usePricingPlans";
import "../../css/garim-pages/Pricing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Pricing() {
  useDocumentTitle("요금제 · Garim");
  const isAuthed = useAuthStatus();
  const navigate = useNavigate();
  const startHref = isAuthed
    ? "/upload"
    : `/login?next=${encodeURIComponent("/upload")}`;
  const { plans } = usePricingPlans();

  function handlePayClick(plan) {
    const isCredit = plan.productType === "credit";
    const params = new URLSearchParams({
      productType: isCredit ? "credit" : "subscription",
      productCode: plan.key,
      price: String(plan.payment.price ?? ""),
      credits: String(plan.payment.credits ?? ""),
    });
    const paymentPath = `/payment?${params.toString()}`;
    if (!isAuthed) {
      navigate(`/login?next=${encodeURIComponent(paymentPath)}`);
      return;
    }
    navigate(paymentPath);
  }

  return (
    <GarimPage bodyClass="page-public" screenLabel="02 Pricing">
      <section className="page-head">
        <h1>필요한 만큼 선택하는 요금제</h1>
        <p>
          관리자 정책에서 설정한 크레딧, 금액, 파일 처리 한도, 데이터 보존
          기간을 기준으로 플랜 정보를 표시합니다.
        </p>
        <div className="billing-toggle">
          <button className="active">월 결제</button>
          <button>
            연 결제
            <span className="save">준비 중</span>
          </button>
        </div>
      </section>

      <section style={{ padding: "24px 32px 64px" }}>
        <div className="pricing-grid">
          {plans.map((plan) => (
            <div
              key={plan.key}
              className={`price-card${plan.featured ? " price-card--featured" : ""}`}
            >
              <span className={`mui-chip ${plan.badgeClass} price-card__badge`}>
                {plan.badge}
              </span>
              <span className="overline-k">{plan.name}</span>
              <div className="price-card__price">
                {formatPrice(plan.payment.price)}
                <small>원</small>
              </div>
              <p className="caption-k" style={{ fontSize: "13px" }}>
                {plan.description}
              </p>
              <ul className="price-card__feats">
                <li>
                  <span className="material-icons">check</span>크레딧{" "}
                  {formatQuota(plan.payment.credits, "개")}
                </li>
                <li>
                  <span className="material-icons">check</span>월 처리 한도{" "}
                  {formatQuota(plan.file.monthlyQuota)}
                </li>
                <li>
                  <span className="material-icons">check</span>최대 파일 크기{" "}
                  {formatFileSize(plan.file.fileSizeLimit)}
                </li>
                <li>
                  <span className="material-icons">check</span>동시 처리 최대{" "}
                  {formatQuota(plan.file.maxJobs)}
                </li>
                <li>
                  <span className="material-icons">check</span>결과 파일{" "}
                  {formatQuota(plan.file.resultRetention, "일")} 보관
                </li>
                <li>
                  <span className="material-icons">check</span>원본 파일{" "}
                  {formatQuota(plan.retention.autoDeleteOriginalHours, "시간")}{" "}
                  후 삭제
                </li>
                <li>
                  <span className="material-icons">check</span>메타데이터{" "}
                  {formatQuota(plan.retention.metadataRetentionDays, "일")} 보존
                </li>
              </ul>
              {plan.key === "free" ? (
                <a
                  href={startHref}
                  className="mui-btn mui-btn--contained mui-btn--block"
                >
                  {plan.cta}
                </a>
              ) : (
                <button
                  type="button"
                  className="mui-btn mui-btn--outlined mui-btn--block"
                  onClick={() => handlePayClick(plan)}
                >
                  {plan.cta}
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 크레딧 추가 구매 섹션 */}
      <section className="credit-section" style={{ padding: "0 32px 64px" }}>
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <h2 style={{ fontSize: "28px", fontWeight: "600" }}>크레딧 충전</h2>
          <p style={{ color: "var(--fg-2)", marginTop: "8px" }}>
            플랜 변경 없이 부족한 크레딧만 필요한 만큼 충전하세요.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "24px",
            flexWrap: "wrap",
          }}
        >
          {/* 100 크레딧 */}
          <div
            style={{
              width: "320px",
              textAlign: "center",
              border: "2px solid #1976d2",
              padding: "32px 24px",
              borderRadius: "16px",
              background: "#fff",
              position: "relative",
              boxShadow: "0 8px 24px rgba(25,118,210,0.12)",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "-14px",
                left: "50%",
                transform: "translateX(-50%)",
                background: "#1976d2",
                color: "#fff",
                padding: "6px 16px",
                borderRadius: "20px",
                fontSize: "12px",
                fontWeight: "bold",
                letterSpacing: "0.5px",
              }}
            >
              가장 인기
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "6px",
                marginBottom: "8px",
              }}
            >
              <span
                className="material-icons"
                style={{ color: "#1976d2", fontSize: "24px" }}
              >
                toll
              </span>
              <h3
                style={{
                  margin: 0,
                  fontSize: "20px",
                  color: "#1976d2",
                  fontWeight: "600",
                }}
              >
                100 크레딧
              </h3>
            </div>
            <div
              style={{ fontSize: "32px", fontWeight: "bold", margin: "16px 0" }}
            >
              5,000
              <span
                style={{
                  fontSize: "16px",
                  color: "var(--fg-2)",
                  fontWeight: "normal",
                }}
              >
                원
              </span>
            </div>
            <p
              style={{
                color: "var(--fg-2)",
                fontSize: "13px",
                marginBottom: "24px",
                flex: "1",
              }}
            >
              가벼운 단건 처리 및 테스트에 적합한 기본 크레딧 패키지입니다.
            </p>
            <button
              onClick={() =>
                handlePayClick({
                  key: "credit_100",
                  productType: "credit",
                  payment: { price: 5000, credits: 100 },
                })
              }
              className="mui-btn mui-btn--contained mui-btn--block"
              style={{ padding: "12px" }}
            >
              충전하기
            </button>
          </div>

          {/* 500 크레딧 */}
          <div
            style={{
              width: "320px",
              textAlign: "center",
              border: "1px solid var(--mui-divider)",
              padding: "32px 24px",
              borderRadius: "16px",
              background: "#fff",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "6px",
                marginBottom: "8px",
              }}
            >
              <span
                className="material-icons"
                style={{ color: "var(--fg-2)", fontSize: "24px" }}
              >
                toll
              </span>
              <h3
                style={{
                  margin: 0,
                  fontSize: "20px",
                  color: "var(--fg-1)",
                  fontWeight: "600",
                }}
              >
                500 크레딧
              </h3>
            </div>
            <div
              style={{ fontSize: "32px", fontWeight: "bold", margin: "16px 0" }}
            >
              20,000
              <span
                style={{
                  fontSize: "16px",
                  color: "var(--fg-2)",
                  fontWeight: "normal",
                }}
              >
                원
              </span>
            </div>
            <p
              style={{
                color: "var(--fg-2)",
                fontSize: "13px",
                marginBottom: "24px",
                flex: "1",
              }}
            >
              대량 처리를 위한 넉넉한 크레딧 팩입니다. <br />
              (20% 할인 효과)
            </p>
            <button
              onClick={() =>
                handlePayClick({
                  key: "credit_500",
                  productType: "credit",
                  payment: { price: 20000, credits: 500 },
                })
              }
              className="mui-btn mui-btn--outlined mui-btn--block"
              style={{ padding: "12px" }}
            >
              충전하기
            </button>
          </div>
        </div>
      </section>

      <section className="compare-section" style={{ background: "#fafafa" }}>
        <h2
          style={{
            textAlign: "center",
            font: "500 32px var(--font-sans)",
            margin: "0 0 32px",
          }}
        >
          플랜 비교
        </h2>
        <table className="compare">
          <thead>
            <tr>
              <th></th>
              {plans.map((plan) => (
                <th key={plan.key}>{plan.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="row-head">
              <td colSpan="4">결제 정책</td>
            </tr>
            <tr>
              <td>제공 크레딧</td>
              {plans.map((plan) => (
                <td key={plan.key}>
                  {formatQuota(plan.payment.credits, "개")}
                </td>
              ))}
            </tr>
            <tr>
              <td>금액</td>
              {plans.map((plan) => (
                <td key={plan.key}>{formatPrice(plan.payment.price)}원</td>
              ))}
            </tr>
            <tr className="row-head">
              <td colSpan="4">파일 처리 정책</td>
            </tr>
            <tr>
              <td>월 처리 한도</td>
              {plans.map((plan) => (
                <td key={plan.key}>{formatQuota(plan.file.monthlyQuota)}</td>
              ))}
            </tr>
            <tr>
              <td>동시 처리 최대 건수</td>
              {plans.map((plan) => (
                <td key={plan.key}>{formatQuota(plan.file.maxJobs)}</td>
              ))}
            </tr>
            <tr>
              <td>최대 파일 크기</td>
              {plans.map((plan) => (
                <td key={plan.key}>
                  {formatFileSize(plan.file.fileSizeLimit)}
                </td>
              ))}
            </tr>
            <tr>
              <td>결과 파일 보관 기간</td>
              {plans.map((plan) => (
                <td key={plan.key}>
                  {formatQuota(plan.file.resultRetention, "일")}
                </td>
              ))}
            </tr>
            <tr className="row-head">
              <td colSpan="4">데이터 보존 정책</td>
            </tr>
            <tr>
              <td>원본 파일 자동 삭제</td>
              {plans.map((plan) => (
                <td key={plan.key}>
                  처리 후{" "}
                  {formatQuota(plan.retention.autoDeleteOriginalHours, "시간")}
                </td>
              ))}
            </tr>
            <tr>
              <td>처리 메타데이터 보존</td>
              {plans.map((plan) => (
                <td key={plan.key}>
                  {formatQuota(plan.retention.metadataRetentionDays, "일")}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </section>
    </GarimPage>
  );
}
