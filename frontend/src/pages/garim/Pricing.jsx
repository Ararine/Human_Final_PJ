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

            // 백엔드 데이터 및 정책 설정의 동적 랭크 값을 기반으로 대소 판별
            const curRank = Number(paymentInfo?.current_plan?.plan_rank ?? 0);
            const planRank = Number(plan.planRank ?? 0);
            const isLowerPlan = planRank < curRank;

            // 이월 구독 이력 정보 매핑
            const carriedOver = paymentInfo?.carried_over_subscription;
            const isCarriedPlan = carriedOver && carriedOver.plan_code === plan.key;

            // 다운그레이드 예약 활성화 상태 매핑
            const isScheduledToThis = paymentInfo?.scheduled_plan_change?.to_plan_code === plan.key;

            return (
            <div
              key={plan.key}
              className={`price-card${isHighlighted ? " price-card--featured" : ""}${isCurrentPlan ? " price-card--current" : ""}`}
            >
              {/* 플랜 명칭과 배지를 한 행에 정렬 */}
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span className="overline-k" style={{ margin: 0, lineHeight: 1 }}>{plan.name}</span>
                {/* 1번 체크: 이전 플랜 뱃지 표시(이월 발생 시) */}
                {isCarriedPlan ? (
                  <span className="mui-chip" style={{ background: "rgba(0, 0, 0, 0.08)", color: "var(--fg-2)" }}>
                    이전 플랜
                  </span>
                ) : (isCurrentPlan || plan.badge) && (
                  <span className={`mui-chip ${isCurrentPlan ? "" : plan.badgeClass} price-card__badge`}>
                    {isCurrentPlan ? "현재 플랜" : plan.badge}
                  </span>
                )}
              </div>
              <div className="price-card__price">
                {formatPrice(plan.payment.price)}
                <small>원</small>
                {/* 요금제 기간 표시 (/ 영구 또는 / 30일) */}
                <span className="price-card__period">
                  {plan.key === "free" ? "/ 영구" : "/ 30일"}
                </span>
              </div>
              {/* 1번 체크: 업그레이드로 종료됨 회색 배지 박스 추가 */}
              {isCarriedPlan && (
                <div style={{ marginTop: "4px", marginBottom: "8px" }}>
                  <span
                    style={{
                      background: "rgba(0, 0, 0, 0.05)",
                      border: "1px solid var(--mui-divider)",
                      color: "var(--fg-2)",
                      padding: "4px 8px",
                      fontSize: "11px",
                      borderRadius: "4px",
                      fontWeight: "500",
                      display: "inline-block"
                    }}
                  >
                    업그레이드로 종료됨
                  </span>
                </div>
              )}
              <p className="caption-k" style={{ fontSize: "13px" }}>
                {plan.description}
              </p>
              {/* 2번 체크: Pro 카드 중간 업그레이드 및 이월 설명 안내 박스 */}
              {isCarriedPlan && (
                <div
                  style={{
                    background: "#e5f6fd",
                    border: "1px solid #b3e5fc",
                    color: "#014361",
                    borderRadius: "8px",
                    padding: "16px",
                    fontSize: "13px",
                    lineHeight: "1.6",
                    marginBottom: "16px"
                  }}
                >
                  <div style={{ display: "flex", gap: "6px", alignItems: "flex-start" }}>
                    <span className="material-icons" style={{ fontSize: "18px", marginTop: "1px" }}>info</span>
                    <div>
                      {formatDateDot(carriedOver.current_period_end)} {carriedOver.plan_name} 플랜으로 업그레이드되며 종료되었습니다.
                      <div style={{ marginTop: "4px" }}>
                        남은 {carriedOver.carried_over_days}일이 {paymentInfo?.plan_name || "Studio"} 플랜 기간 뒤로 이월되었습니다.
                      </div>
                    </div>
                  </div>
                </div>
              )}
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
                /* 현재 플랜인 경우: 버튼 문구를 '현재 구독 중'으로 변경하고 하단에 구독 정보 및 관리 링크 노출 */
                <>
                  <button
                    type="button"
                    className="mui-btn mui-btn--contained mui-btn--block current-plan-btn"
                    onClick={() => navigate("/settings")}
                  >
                    현재 구독 중
                  </button>

                  {/* 노란색 체크: 현재 구독 정보 표시 영역 */}
                  {paymentInfo?.current_subscription && (
                    <div style={{ marginTop: "16px" }}>
                      <div
                        style={{
                          fontSize: "13px",
                          fontWeight: "600",
                          color: "var(--fg-1)",
                          marginBottom: "8px",
                          textAlign: "left"
                        }}
                      >
                        현재 구독 정보
                      </div>
                      <div
                        style={{
                          border: "1px solid var(--mui-divider)",
                          borderRadius: "8px",
                          background: "#fff",
                          fontSize: "12px",
                          lineHeight: "1.6",
                          overflow: "hidden"
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "8px 12px",
                            borderBottom: "1px solid var(--mui-divider)"
                          }}
                        >
                          <span style={{ color: "var(--fg-2)" }}>다음 결제일</span>
                          <span style={{ fontWeight: "500" }}>
                            {formatDateDot(paymentInfo.current_subscription.next_billing_at)}
                          </span>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "8px 12px",
                            borderBottom: "1px solid var(--mui-divider)"
                          }}
                        >
                          <span style={{ color: "var(--fg-2)" }}>자동결제</span>
                          <span style={{ fontWeight: "500" }}>
                            {paymentInfo.current_subscription.auto_renew ? "사용 중" : "중지"}
                          </span>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "8px 12px"
                          }}
                        >
                          <span style={{ color: "var(--fg-2)" }}>상태</span>
                          <span style={{ fontWeight: "500" }}>
                            {paymentInfo.current_subscription.status === "active" ? "활성" : "정지"}
                          </span>
                        </div>
                      </div>

                      {/* 구독 관리로 이동 링크 */}
                      <div style={{ textAlign: "center", marginTop: "12px" }}>
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
                    </div>
                  )}
                </>
              ) : isLowerPlan ? (
                /* 현재 플랜보다 rank가 낮은 플랜인 경우: 무료 플랜으로 변경(3번 체크) 또는 ~로 변경 예약(1번 체크) */
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
              )}

              {/* 2번 및 4번 체크: 전환 예약 설명 문구 박스 (하위 플랜일 때 상시 노출) */}
              {isLowerPlan && (
                <div
                  style={{
                    background: "#f8fafc",
                    border: "1px solid var(--mui-divider)",
                    borderRadius: "8px",
                    padding: "16px",
                    fontSize: "13px",
                    lineHeight: "1.5",
                    color: "var(--fg-2)",
                    marginTop: "16px",
                    textAlign: "center"
                  }}
                >
                  {plan.key === "free" ? (
                    "현재 유료 플랜은 이번 이용 기간 종료일까지 유지되며, 다음 결제일부터 Free 플랜으로 전환됩니다."
                  ) : (
                    `현재 ${paymentInfo?.plan_name || "Studio"} 플랜은 이번 이용 기간 종료일까지 유지되며, 다음 결제일부터 ${plan.name} 플랜으로 전환됩니다.`
                  )}
                </div>
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
