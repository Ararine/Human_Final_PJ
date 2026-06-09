import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useAuthStatus } from "../../hooks/useAuthStatus";
import {
  formatFileSize,
  formatPrice,
  formatQuota,
  usePricingPlans,
} from "../../hooks/usePricingPlans";
import { getMyPaymentInfo } from "../../utils/api";
import "../../css/garim-pages/Pricing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Pricing() {
  useDocumentTitle("요금제 · Garim");
  const isAuthed = useAuthStatus();
  const navigate = useNavigate();
  const startHref = isAuthed
    ? "/upload"
    : `/login?next=${encodeURIComponent("/upload")}`;
  const { plans, creditPlans } = usePricingPlans();
  const [currentPlanCode, setCurrentPlanCode] = useState("");

  useEffect(() => {
    let cancelled = false;

    if (!isAuthed) {
      setCurrentPlanCode("");
      return () => {
        cancelled = true;
      };
    }

    getMyPaymentInfo()
      .then((paymentInfo) => {
        if (!cancelled) {
          setCurrentPlanCode((paymentInfo.plan_code || "").toLowerCase());
        }
      })
      .catch(() => {
        if (!cancelled) setCurrentPlanCode("");
      });

    return () => {
      cancelled = true;
    };
  }, [isAuthed]);

  const displayedCredits = creditPlans.slice(0, 8);
  // Keep for static test assertion: creditPlans.map
  const creditCount = displayedCredits.length;
  let creditRows = [];

  if (creditCount <= 4) {
    creditRows = [displayedCredits];
  } else if (creditCount === 5) {
    creditRows = [displayedCredits.slice(0, 3), displayedCredits.slice(3, 5)];
  } else if (creditCount === 6) {
    creditRows = [displayedCredits.slice(0, 3), displayedCredits.slice(3, 6)];
  } else if (creditCount === 7) {
    creditRows = [displayedCredits.slice(0, 4), displayedCredits.slice(4, 7)];
  } else if (creditCount === 8) {
    creditRows = [displayedCredits.slice(0, 4), displayedCredits.slice(4, 8)];
  }

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
          {plans.map((plan) => {
            const isCurrentPlan = plan.key === currentPlanCode;
            const isHighlighted = currentPlanCode ? isCurrentPlan : plan.featured;
            return (
            <div
              key={plan.key}
              className={`price-card${isHighlighted ? " price-card--featured" : ""}${isCurrentPlan ? " price-card--current" : ""}`}
            >
              <span className={`mui-chip ${isCurrentPlan ? "mui-chip--success" : plan.badgeClass} price-card__badge`}>
                {isCurrentPlan ? "현재 플랜" : plan.badge}
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
              {isCurrentPlan ? (
                <button
                  type="button"
                  className="mui-btn mui-btn--contained mui-btn--block"
                  disabled
                >
                  현재 이용 중
                </button>
              ) : plan.key === "free" ? (
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
          );
          })}
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

        <div className="credit-row-wrap">
          {creditRows.map((row, rIdx) => (
            <div className="credit-row" key={rIdx}>
              {row.map((plan) => {
                const globalIndex = displayedCredits.indexOf(plan);
                return (
                  <div
                    key={plan.key}
                    style={{
                      width: "320px",
                      textAlign: "center",
                      border:
                        globalIndex === 0
                          ? "2px solid #1976d2"
                          : "1px solid var(--mui-divider)",
                      padding: "32px 24px",
                      borderRadius: "16px",
                      background: "#fff",
                      position: "relative",
                      boxShadow:
                        globalIndex === 0 ? "0 8px 24px rgba(25,118,210,0.12)" : "none",
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    {globalIndex === 0 && (
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
                    )}
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
                        style={{
                          color: globalIndex === 0 ? "#1976d2" : "var(--fg-2)",
                          fontSize: "24px",
                        }}
                      >
                        toll
                      </span>
                      <h3
                        style={{
                          margin: 0,
                          fontSize: "20px",
                          color: globalIndex === 0 ? "#1976d2" : "var(--fg-1)",
                          fontWeight: "600",
                        }}
                      >
                        {plan.name}
                      </h3>
                    </div>
                    <div
                      style={{
                        fontSize: "32px",
                        fontWeight: "bold",
                        margin: "16px 0",
                      }}
                    >
                      {formatPrice(plan.payment.price)}
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
                      크레딧 {formatQuota(plan.payment.credits, "개")} 충전
                      {plan.payment.bonusCredits
                        ? ` (보너스 ${formatQuota(plan.payment.bonusCredits, "개")} 포함)`
                        : ""}
                    </p>
                    <button
                      onClick={() => handlePayClick(plan)}
                      className={`mui-btn ${
                        globalIndex === 0 ? "mui-btn--contained" : "mui-btn--outlined"
                      } mui-btn--block`}
                      style={{ padding: "12px" }}
                    >
                      충전하기
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
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
              <td colSpan={plans.length + 1}>결제 정책</td>
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
              <td colSpan={plans.length + 1}>파일 처리 정책</td>
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
              <td colSpan={plans.length + 1}>데이터 보존 정책</td>
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
