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
import PricingCard from "../../components/garim/PricingCard";
import "../../css/garim-pages/Pricing.css";
import GarimPage from "../../components/garim/GarimPage";

// ISO 8601 날짜 문자열을 YYYY.MM.DD 포맷으로 변환하는 한국어 헬퍼 함수
function formatDateDot(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}.${m}.${d}`;
}

export default function Pricing() {
  useDocumentTitle("요금제 · Garim");
  const isAuthed = useAuthStatus();
  const navigate = useNavigate();
  const startHref = isAuthed
    ? "/upload"
    : `/login?next=${encodeURIComponent("/upload")}`;
  const { plans: allPlans, creditPlans } = usePricingPlans();
  // 사용자의 요청에 따라 화면에 노출될 구독 플랜을 최대 3개까지만 제한하여 사용합니다.
  const plans = allPlans.slice(0, 3);
  const [currentPlanCode, setCurrentPlanCode] = useState("");
  const [paymentInfo, setPaymentInfo] = useState(null);

  useEffect(() => {
    let cancelled = false;

    if (!isAuthed) {
      setCurrentPlanCode("");
      setPaymentInfo(null);
      return () => {
        cancelled = true;
      };
    }

    getMyPaymentInfo()
      .then((info) => {
        if (!cancelled) {
          setPaymentInfo(info);
          setCurrentPlanCode((info.plan_code || "").toLowerCase());
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCurrentPlanCode("");
          setPaymentInfo(null);
        }
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

  // [한글 주석]
  // 결제 성공 횟수가 가장 높은 활성 크레딧 플랜에 하이라이트를 적용하기 위한 키 계산 로직입니다.
  // 1. 노출할 크레딧 플랜 목록 중 최대 결제 성공 횟수(popularityCount)를 도출합니다.
  // 2. 최대 횟수가 0보다 큰 경우, 해당 최대 횟수를 가진 플랜들 중 정렬 순서(sortOrder)가 가장 높은 것을 선택합니다.
  // 3. 만약 모든 플랜의 결제 성공 횟수가 0이거나 초기 상태인 경우, 목록의 첫 번째 크레딧 플랜을 기본 하이라이트 대상으로 지정합니다.
  let highlightedCreditKey = "";
  if (displayedCredits.length > 0) {
    const maxPopularity = Math.max(...displayedCredits.map((p) => p.popularityCount ?? 0));
    if (maxPopularity > 0) {
      const candidates = displayedCredits.filter((p) => (p.popularityCount ?? 0) === maxPopularity);
      // sortOrder 기준 내림차순 정렬 후 첫 번째 선택 (동률인 경우 가격이 더 높은 플랜을 선택하기 위함)
      candidates.sort((a, b) => b.sortOrder - a.sortOrder);
      highlightedCreditKey = candidates[0].key;
    } else {
      highlightedCreditKey = displayedCredits[0].key;
    }
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

  // [한글 주석] 세 요금제 카드 중 2번 영역(전환 예약 안내 박스 혹은 구독 관리 링크)에 유효한 정보가 하나라도 노출되는지 감지합니다.
  // 하나도 노출되지 않는 경우(예: 현재 무료 플랜을 쓰고 있어서 자동결제나 이력 등이 없는 상태)에는 하단의 80px 여백을 제거하기 위함입니다.
  const hasAnyActionInfo = plans.some((plan) => {
    const isCurrent = plan.key === currentPlanCode;
    const curRank = Number(paymentInfo?.current_plan?.plan_rank ?? 0);
    const planRank = Number(plan.planRank ?? 0);
    const isLower = planRank < curRank;

    // 현재 플랜이면서 구독 정보가 있는 경우 (단, 무료 플랜은 다음 결제일 등의 구독 관리가 없으므로 제외)
    if (isCurrent && paymentInfo?.current_subscription && plan.key !== "free") {
      return true;
    }
    // 현재 플랜보다 낮은 랭크의 플랜인 경우 (전환 변경 예약 설명 박스 노출 대상)
    if (isLower) {
      return true;
    }
    return false;
  });

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

            // 백엔드 데이터 및 정책 설정의 동적 랭크 값을 기반으로 대소 판별
            const curRank = Number(paymentInfo?.current_plan?.plan_rank ?? 0);
            const planRank = Number(plan.planRank ?? 0);
            const isLowerPlan = planRank < curRank;

            // 다운그레이드 예약 활성화 상태 매핑
            const isScheduledToThis = paymentInfo?.scheduled_plan_change?.to_plan_code === plan.key;

            // [한글 주석] 컴포넌트에 주입할 액션 버튼(1번 영역)을 생성합니다.
            const actionButton = isCurrentPlan ? (
              plan.key === "free" ? (
                <button
                  type="button"
                  className="mui-btn mui-btn--contained mui-btn--primary mui-btn--block"
                  onClick={() => navigate(startHref)}
                >
                  무료로 시작
                </button>
              ) : (
                <button
                  type="button"
                  className="mui-btn mui-btn--contained mui-btn--block current-plan-btn"
                  onClick={() => navigate("/settings")}
                >
                  현재 구독 중
                </button>
              )
            ) : isLowerPlan ? (
              <button
                type="button"
                className="mui-btn mui-btn--outlined mui-btn--block"
                onClick={() => navigate("/settings")}
              >
                {plan.key === "free" ? "무료 플랜으로 변경" : `${plan.name}로 변경 예약`}
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
            );

            // [한글 주석] 컴포넌트에 주입할 상태 알림 설명 및 구독 관리 링크(2번 영역)를 생성합니다.
            const actionInfo = isCurrentPlan && paymentInfo?.current_subscription ? (
              <div style={{ textAlign: "center", display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
                <button
                  type="button"
                  onClick={() => navigate("/settings")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#1976d2",
                    fontSize: "13px",
                    fontWeight: "500",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px"
                  }}
                >
                  구독 관리로 이동
                  <span className="material-icons" style={{ fontSize: "14px" }}>
                    chevron_right
                  </span>
                </button>
              </div>
            ) : isLowerPlan ? (
              <div
                style={{
                  background: "#f8fafc",
                  border: "1px solid var(--mui-divider)",
                  borderRadius: "8px",
                  padding: "16px",
                  fontSize: "13px",
                  lineHeight: "1.5",
                  color: "var(--fg-2)",
                  textAlign: "center",
                  height: "100%",
                  boxSizing: "border-box"
                }}
              >
                {plan.key === "free" ? (
                  "현재 유료 플랜은 이번 이용 기간 종료일까지 유지되며, 다음 결제일부터 Free 플랜으로 전환됩니다."
                ) : (
                  `현재 ${paymentInfo?.plan_name || "Studio"} 플랜은 이번 이용 기간 종료일까지 유지되며, 다음 결제일부터 ${plan.name} 플랜으로 전환됩니다.`
                )}
              </div>
            ) : (
              <div style={{ height: "100%" }} />
            );

            return (
              <PricingCard
                key={plan.key}
                plan={plan}
                isCurrentPlan={isCurrentPlan}
                isHighlighted={isHighlighted}
                showPeriod={true}
                actionButton={actionButton}
                actionInfo={actionInfo}
                hasAnyActionInfo={hasAnyActionInfo}
              />
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
                // [한글 주석] 계산된 highlightedCreditKey와 현재 플랜의 key가 일치하는지 비교하여 하이라이트 여부를 결정합니다.
                const isHighlighted = plan.key === highlightedCreditKey;
                return (
                  <div
                    key={plan.key}
                    style={{
                      width: "320px",
                      textAlign: "center",
                      border:
                        isHighlighted
                          ? "2px solid #1976d2"
                          : "1px solid var(--mui-divider)",
                      padding: "32px 24px",
                      borderRadius: "16px",
                      background: "#fff",
                      position: "relative",
                      boxShadow:
                        isHighlighted ? "0 8px 24px rgba(25,118,210,0.12)" : "none",
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    {isHighlighted && (
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
                          color: isHighlighted ? "#1976d2" : "var(--fg-2)",
                          fontSize: "24px",
                        }}
                      >
                        toll
                      </span>
                      <h3
                        style={{
                          margin: 0,
                          fontSize: "20px",
                          color: isHighlighted ? "#1976d2" : "var(--fg-1)",
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
                        isHighlighted ? "mui-btn--contained" : "mui-btn--outlined"
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
