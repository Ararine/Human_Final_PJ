import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useAuthStatus } from "../../hooks/useAuthStatus";
import { getMyPaymentInfo, requestPlanChange } from "../../utils/api";
import {
  formatFileSize,
  formatPrice,
  formatQuota,
  usePricingPlans,
} from "../../hooks/usePricingPlans";
import "../../css/garim-pages/Pricing.css";

import GarimPage from "../../components/garim/GarimPage";

function goBackOrHome(navigate) {
  if (window.history.length > 1) {
    navigate(-1);
  } else {
    navigate("/");
  }
}

export default function Pricing() {
  useDocumentTitle("요금제 · Garim");
  const isAuthed = useAuthStatus();
  const navigate = useNavigate();
  const startHref = isAuthed
    ? "/upload"
    : `/login?next=${encodeURIComponent("/upload")}`;
  const { plans, creditPlans, loading, error } = usePricingPlans();
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [currentPlanCode, setCurrentPlanCode] = useState(null);
  const [currentPlanRank, setCurrentPlanRank] = useState(null);
  const [planActionLoading, setPlanActionLoading] = useState("");

  const getYearlyPrice = (plan) => {
    const yearly = Number(plan.payment.yearlyPrice || 0);
    if (yearly > 0) return yearly;
    return Number(plan.payment.price || 0) * 10;
  };

  const getYearlyCredits = (plan) => {
    const yearly = Number(plan.payment.yearlyCredits || 0);
    if (yearly > 0) return yearly;
    return Number(plan.payment.credits || 0) * 12;
  };

  const getDisplayPrice = (plan) => {
    const monthly = Number(plan.payment.price || 0);
    if (monthly === 0) return { main: 0, unit: "원", sub: null };
    if (billingCycle === "yearly") {
      const yearly = getYearlyPrice(plan);
      const perMonth = Math.round(yearly / 12);
      return { main: yearly, unit: "원 / 년", sub: `월 ${perMonth.toLocaleString("ko-KR")}원 상당` };
    }
    return { main: monthly, unit: "원 / 월", sub: null };
  };

  const getDisplayCredits = (plan) => {
    const monthlyCredits = Number(plan.payment.credits || 0);
    const isFreePlan = plan.key === "free";
    if (billingCycle === "yearly" && Number(plan.payment.price || 0) > 0 && !isFreePlan) {
      const yearlyCredits = getYearlyCredits(plan);
      return {
        text: `크레딧 ${yearlyCredits.toLocaleString("ko-KR")}개 / 년`,
        note: `월 ${monthlyCredits.toLocaleString("ko-KR")}개씩 제공`,
      };
    }
    return { text: `크레딧 ${monthlyCredits.toLocaleString("ko-KR")}개`, note: null };
  };

  const getVideoFeature = (plan) => {
    const monthlyCredits = Number(plan.payment.credits || 0);
    if (billingCycle === "yearly" && Number(plan.payment.price || 0) > 0) {
      const perYear = Math.floor(getYearlyCredits(plan) / 3);
      return `영상 약 ${perYear.toLocaleString("ko-KR")}편 / 년`;
    }
    return `영상 약 ${Math.floor(monthlyCredits / 3).toLocaleString("ko-KR")}편 / 월`;
  };

  useEffect(() => {
    if (!error) return;

    alert("요금제 정보를 불러오지 못했습니다. 이전 페이지로 이동합니다.");
    goBackOrHome(navigate);
  }, [error, navigate]);

  useEffect(() => {
    let cancelled = false;

    async function loadCurrentPlan() {
      if (!isAuthed) {
        if (!cancelled) {
          setCurrentPlanCode(null);
          setCurrentPlanRank(null);
        }
        return;
      }

      try {
        const result = await getMyPaymentInfo();
        if (cancelled) return;
        const planCode = result?.current_plan?.plan_code || result?.plan_code || null;
        const planRank = result?.current_plan?.plan_rank;
        setCurrentPlanCode(planCode ? String(planCode).toLowerCase() : null);
        setCurrentPlanRank(planRank === null || planRank === undefined ? null : Number(planRank));
      } catch (err) {
        console.error("Failed to load current plan", err);
        if (!cancelled) {
          setCurrentPlanCode(null);
          setCurrentPlanRank(null);
        }
      }
    }

    loadCurrentPlan();

    return () => {
      cancelled = true;
    };
  }, [isAuthed]);

  const displayedCredits = creditPlans.slice(0, 8);
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

  function isLowerThanCurrent(plan) {
    return currentPlanRank !== null && Number(plan.planRank ?? 0) < currentPlanRank;
  }

  function isHigherThanCurrent(plan) {
    return currentPlanRank !== null && Number(plan.planRank ?? 0) > currentPlanRank;
  }

  function getPlanButtonLabel(plan, isCurrentPlan) {
    if (isCurrentPlan) return "구독중";
    if (isLowerThanCurrent(plan)) return `${plan.name}로 변경`;
    if (isHigherThanCurrent(plan)) return `${plan.name} 시작하기`;
    return plan.cta;
  }

  async function handlePayClick(plan) {
    if (currentPlanCode && currentPlanCode === plan.key) {
      navigate("/settings");
      return;
    }

    const isCredit = plan.productType === "credit";
    if (!isCredit && isLowerThanCurrent(plan)) {
      if (!isAuthed) {
        navigate(`/login?next=${encodeURIComponent("/pricing")}`);
        return;
      }

      setPlanActionLoading(plan.key);
      try {
        await requestPlanChange({ to_plan_id: plan.key });
        alert(`${plan.name} 플랜으로 변경 예약이 등록되었습니다. 현재 구독은 이번 이용 기간 종료일까지 유지됩니다.`);
        navigate("/settings");
      } catch (err) {
        alert(err.message || "플랜 변경 예약에 실패했습니다.");
      } finally {
        setPlanActionLoading("");
      }
      return;
    }

    const payPrice =
      !isCredit && billingCycle === "yearly"
        ? getYearlyPrice(plan)
        : plan.payment.price;
    const payCredits =
      !isCredit && billingCycle === "yearly"
        ? getYearlyCredits(plan)
        : plan.payment.credits;
    const params = new URLSearchParams({
      productType: isCredit ? "credit" : "subscription",
      productCode: plan.key,
      price: String(payPrice ?? ""),
      credits: String(payCredits ?? ""),
      ...(!isCredit ? { billingCycle } : {}),
    });
    const paymentPath = `/payment?${params.toString()}`;
    if (!isAuthed) {
      navigate(`/login?next=${encodeURIComponent(paymentPath)}`);
      return;
    }
    navigate(paymentPath);
  }

  if (loading) {
    return (
      <GarimPage bodyClass="page-public pricing-page" screenLabel="02 Pricing">
        <section className="page-head">
          <div className="pricing-eyebrow">GARIM MEMBERSHIP</div>
          <h1>요금제를 불러오는 중입니다</h1>
        </section>
      </GarimPage>
    );
  }

  if (error) {
    return (
      <GarimPage bodyClass="page-public pricing-page" screenLabel="02 Pricing">
        <section className="page-head">
          <div className="pricing-eyebrow">GARIM MEMBERSHIP</div>
          <h1>요금제 정보를 불러오지 못했습니다</h1>
        </section>
      </GarimPage>
    );
  }

  return (
    <GarimPage bodyClass="page-public pricing-page" screenLabel="02 Pricing">
      <section className="page-head">
        <div className="pricing-eyebrow">GARIM MEMBERSHIP</div>
        <h1>가치 있는 만큼의 선택</h1>
        <p>
          영상미를 해치지 않고 개인정보만 자연스럽게. 필요한 만큼만 선택하세요.
        </p>
        <div
          className={`billing-toggle ${billingCycle === "yearly" ? "billing-toggle--yearly" : ""}`}
          onClick={() =>
            setBillingCycle((prev) => (prev === "monthly" ? "yearly" : "monthly"))
          }
        >
          <div className="billing-toggle__slider" />
          <button
            type="button"
            className={billingCycle === "monthly" ? "active" : ""}
          >
            월 결제
          </button>
          <button
            type="button"
            className={billingCycle === "yearly" ? "active" : ""}
          >
            <span>연 결제</span>
            <span className="save">2개월 무료</span>
          </button>
        </div>
      </section>

      <section className="pricing-plans-section">
        <div className="pricing-grid">
          {plans.map((plan) => {
            const isCurrentPlan = currentPlanCode === String(plan.key).toLowerCase();
            return (
              <div
                key={plan.key}
                className={`price-card${!isCurrentPlan && plan.featured ? " price-card--featured" : ""}${isCurrentPlan ? " price-card--current" : ""}`}
              >
              <span className={`mui-chip ${plan.badgeClass} price-card__badge`}>
                {isCurrentPlan ? "구독중" : plan.badge}
              </span>
              <span className="overline-k price-card__name">{plan.name}</span>
              {(() => {
                const disp = getDisplayPrice(plan);
                return (
                  <>
                    <div className="price-card__price">
                      {formatPrice(disp.main)}
                      <small>{disp.unit}</small>
                    </div>
                    {disp.sub && <div className="price-card__permonth">{disp.sub}</div>}
                  </>
                );
              })()}
              <p className="caption-k price-card__desc">{plan.description}</p>
              {(() => {
                const credit = getDisplayCredits(plan);
                return (
                  <div className="price-card__credit-line">
                    {credit.text}
                    {credit.note && (
                      <span className="price-card__credit-note">{credit.note}</span>
                    )}
                  </div>
                );
              })()}
              <ul className="price-card__feats">
                <li>
                  <span className="material-icons">check</span>월 처리{" "}
                  {formatQuota(plan.file.monthlyQuota)}
                </li>
                <li>
                  <span className="material-icons">check</span>최대{" "}
                  {formatFileSize(plan.file.fileSizeLimit)}
                </li>
                <li>
                  <span className="material-icons">check</span>
                  {plan.file.resultRetention
                    ? `결과 ${plan.file.resultRetention}일 보관`
                    : "결과 보관 없음"}
                </li>
                <li>
                  <span className="material-icons">check</span>
                  {plan.key === "free" ? "워터마크 미리보기" : getVideoFeature(plan)}
                </li>
              </ul>
              {isCurrentPlan ? (
                <button
                  type="button"
                  className="mui-btn mui-btn--block price-card__cta price-card__cta--current"
                  onClick={() => navigate("/settings")}
                >
                  {getPlanButtonLabel(plan, isCurrentPlan)}
                </button>
              ) : plan.key === "free" ? (
                isLowerThanCurrent(plan) ? (
                  <button
                    type="button"
                    className="mui-btn mui-btn--block price-card__cta"
                    onClick={() => handlePayClick(plan)}
                    disabled={planActionLoading === plan.key}
                  >
                    {planActionLoading === plan.key ? "처리 중" : getPlanButtonLabel(plan, isCurrentPlan)}
                  </button>
                ) : (
                  <a href={startHref} className="mui-btn mui-btn--block price-card__cta">
                    {getPlanButtonLabel(plan, isCurrentPlan)}
                  </a>
                )
              ) : (
                <button
                  type="button"
                  className="mui-btn mui-btn--block price-card__cta"
                  onClick={() => handlePayClick(plan)}
                  disabled={planActionLoading === plan.key}
                >
                  {planActionLoading === plan.key ? "처리 중" : getPlanButtonLabel(plan, isCurrentPlan)}
                </button>
              )}
            </div>
            );
          })}
        </div>
      </section>

      <section className="credit-section">
        <div className="credit-section__head">
          <h2 className="credit-section__title">크레딧 충전</h2>
          <p className="credit-section__desc">
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
                    className={`credit-card${globalIndex === 0 ? " credit-card--hot" : ""}`}
                  >
                    {globalIndex === 0 && (
                      <div className="credit-card__tag">가장 인기</div>
                    )}
                    <div className="credit-card__head">
                      <span className="material-icons credit-card__icon">toll</span>
                      <h3 className="credit-card__name">{plan.name}</h3>
                    </div>
                    <div className="credit-card__price">
                      {formatPrice(plan.payment.price)}
                      <span className="credit-card__won">원</span>
                    </div>
                    <p className="credit-card__desc">
                      크레딧 {formatQuota(plan.payment.credits, "개")} 충전
                      {plan.payment.bonusCredits
                        ? ` (보너스 ${formatQuota(plan.payment.bonusCredits, "개")} 포함)`
                        : ""}
                    </p>
                    <button
                      type="button"
                      onClick={() => handlePayClick(plan)}
                      className="mui-btn mui-btn--contained mui-btn--block credit-card__btn"
                    >
                      충전
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        <p className="pricing-note">
          개인정보 탐지 확인 — 무료 / 마스킹 작업시 크레딧 차감 — 이미지 2 크레딧 · 영상 3 크레딧
        </p>
      </section>
    </GarimPage>
  );
}
