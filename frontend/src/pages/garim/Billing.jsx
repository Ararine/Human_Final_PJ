import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // 이전 화면 이동을 위한 useNavigate 임포트
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import {
  cancelScheduledPlanChange,
  getMyPaymentInfo,
  requestPlanChange,
  resumeSubscription,
} from "../../utils/api";
import { formatKstDateTime } from "../../utils/timezone";
import "../../css/garim-pages/Billing.css";

import GarimPage from "../../components/garim/GarimPage";

function formatDateTime(value) {
  return formatKstDateTime(value);
}

function formatPrice(value) {
  return new Intl.NumberFormat("ko-KR").format(Number(value || 0));
}

function formatPlanName(name, code) {
  const normalizedCode = String(code || "").toLowerCase();
  if (normalizedCode === "free" || name === "Free") return "무료";
  return name || "-";
}

function formatPaymentMethod(value) {
  const normalized = String(value || "").toLowerCase();
  if (!normalized) return "-";
  if (normalized === "billing") return "자동결제";
  if (normalized === "card") return "카드";
  if (normalized === "easy_pay") return "간편결제";
  if (normalized === "free_bypass") return "무료 처리";
  return value;
}

function formatOrderName(value) {
  if (!value) return "-";
  return String(value)
    .replace(/yearly subscription/gi, "연 구독")
    .replace(/monthly subscription/gi, "월 구독")
    .replace(/renewal/gi, "자동결제 갱신")
    .replace(/scheduled downgrade/gi, "예약 다운그레이드")
    .replace(/\bFree\b/g, "무료");
}

// 결제 상태(billing_status)값을 한국어로 변환해주는 유틸리티 함수
function formatBillingStatus(status) {
  if (!status) return "-";
  const statusMap = {
    paid: "결제 완료",
    pending: "결제 대기",
    failed: "결제 실패",
    unpaid: "미결제",
    cancelled: "취소됨",
  };
  return statusMap[status.toLowerCase()] || status;
}

export default function Billing() {
  useDocumentTitle("결제·구독 관리 · Garim");
  const navigate = useNavigate(); // useNavigate 훅 초기화

  // 이전 화면 이동 핸들러 (히스토리 없으면 설정 화면으로 fallback)
  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate("/settings");
    }
  };

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionLoading, setActionLoading] = useState("");

  async function loadBillingInfo() {
    setLoading(true);
    setError("");
    try {
      const result = await getMyPaymentInfo();
      setData(result);
    } catch (err) {
      setError(err.message || "구독 정보를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBillingInfo();
  }, []);

  async function handleCancelToFree() {
    if (!data?.current_plan?.plan_code || data.current_plan.plan_code === "free") return;
    setActionLoading("cancel");
    setActionMessage("");
    try {
      await requestPlanChange({ to_plan_id: "free" });
      await loadBillingInfo();
      setActionMessage("구독 취소 예약이 등록되었습니다.");
    } catch (err) {
      setActionMessage(err.message || "구독 취소 예약에 실패했습니다.");
    } finally {
      setActionLoading("");
    }
  }

  async function handleResume() {
    const subscriptionId = data?.current_subscription?.subscription_id;
    if (!subscriptionId) return;
    setActionLoading("resume");
    setActionMessage("");
    try {
      await resumeSubscription(subscriptionId);
      await loadBillingInfo();
      setActionMessage("구독 취소 예약이 철회되었습니다.");
    } catch (err) {
      setActionMessage(err.message || "구독 취소 철회에 실패했습니다.");
    } finally {
      setActionLoading("");
    }
  }

  async function handleCancelPlanChange() {
    const planChangeId = data?.scheduled_plan_change?.plan_change_id;
    if (!planChangeId) return;
    setActionLoading("plan-change");
    setActionMessage("");
    try {
      await cancelScheduledPlanChange(planChangeId);
      await loadBillingInfo();
      setActionMessage("다운그레이드 예약이 취소되었습니다.");
    } catch (err) {
      setActionMessage(err.message || "다운그레이드 예약 취소에 실패했습니다.");
    } finally {
      setActionLoading("");
    }
  }

  const currentPlan = data?.current_plan;
  const currentSubscription = data?.current_subscription;
  const scheduledPlanChange = data?.scheduled_plan_change;
  // [한글 주석] 기존 carryover 이월 정보를 제거하고 최신 업그레이드 정산 내역을 바인딩합니다.
  const latestUpgradeProration = data?.latest_upgrade_proration;
  const isCancelScheduled = scheduledPlanChange?.change_type === "cancel_to_free";
  const isDowngradeScheduled = scheduledPlanChange?.change_type === "downgrade";

  return (
    <GarimPage bodyClass="page-app" screenLabel="21 Billing">
      <div className="billing-page">
        <div className="billing-page__header">
          <div>
            <h1>결제·구독 관리</h1>
            <p>현재 플랜, 다음 결제일, 예약된 변경 상태를 한 화면에서 확인합니다.</p>
          </div>
          {/* 헤더 버튼 영역: 이전 버튼 및 새로고침 버튼을 가로로 정렬 */}
          <div className="billing-header-actions" style={{ display: "flex", gap: "8px" }}>
            <button
              type="button"
              className="mui-btn mui-btn--outlined"
              onClick={handleGoBack}
              aria-label="이전 페이지로 이동"
              style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}
            >
              <span className="material-icons" style={{ fontSize: "18px" }}>arrow_back</span>
              이전
            </button>
            <button
              type="button"
              className="mui-btn mui-btn--outlined"
              onClick={loadBillingInfo}
              disabled={loading}
              style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}
            >
              <span className="material-icons" style={{ fontSize: "18px" }}>refresh</span>
              새로고침
            </button>
          </div>
        </div>

        {error ? <div className="billing-banner billing-banner--error">{error}</div> : null}
        {actionMessage ? <div className="billing-banner billing-banner--info">{actionMessage}</div> : null}

        {loading ? (
          <div className="billing-surface billing-surface--empty">구독 정보를 불러오는 중입니다.</div>
        ) : (
          <>
            <section className="billing-grid">
              <div className="billing-surface billing-hero">
                <div className="billing-hero__meta">
                  <span className="mui-chip mui-chip--primary mui-chip--md">현재 플랜</span>
                  <h2>{formatPlanName(currentPlan?.plan_name, currentPlan?.plan_code)}</h2>
                  <p>{currentPlan?.plan_code === "free" ? "무료" : currentPlan?.plan_code?.toUpperCase() || "무료"}</p>
                </div>
                <div className="billing-hero__price">
                  {formatPrice(currentPlan?.price_amount)}
                  <small>원</small>
                </div>
              </div>

              <div className="billing-surface billing-facts">
                <div className="billing-fact">
                  <span>현재 플랜 만료</span>
                  <strong>{formatDateTime(currentSubscription?.current_period_end)}</strong>
                </div>
                <div className="billing-fact">
                  <span>다음 결제일</span>
                  <strong>{formatDateTime(currentSubscription?.next_billing_at)}</strong>
                </div>
                <div className="billing-fact">
                  <span>자동결제</span>
                  <strong>{currentSubscription?.auto_renew ? "사용" : "중지"}</strong>
                </div>
                <div className="billing-fact">
                  <span>취소 예약</span>
                  <strong>{currentSubscription?.cancel_at_period_end ? "예약됨" : "없음"}</strong>
                </div>
              </div>
            </section>

            {/* [한글 주석] 기존 이월 하위 플랜 UI 대신 업그레이드 차감 정산 결과를 노출하는 안내 박스를 표시합니다. */}
            {latestUpgradeProration ? (
              <section className="billing-surface billing-message">
                <h3>구독 업그레이드 정산 내역</h3>
                <p>
                  기존 {formatPlanName(latestUpgradeProration.from_plan_name, latestUpgradeProration.from_plan_code)} 플랜의 남은 이용분{" "}
                  {formatPrice(latestUpgradeProration.discount_amount)}원이{" "}
                  {formatPlanName(latestUpgradeProration.to_plan_name, latestUpgradeProration.to_plan_code)} 결제 금액에서 차감되었습니다. (실제 결제 금액:{" "}
                  {formatPrice(latestUpgradeProration.charged_amount)}원)
                </p>
              </section>
            ) : null}

            {isDowngradeScheduled ? (
              <section className="billing-surface billing-message">
                <h3>다운그레이드 예약</h3>
                <p>
                  {formatPlanName(currentPlan?.plan_name, currentPlan?.plan_code)}는 {formatDateTime(currentSubscription?.current_period_end)}까지 유지되고,
                  이후 {formatPlanName(scheduledPlanChange?.to_plan_name, scheduledPlanChange?.to_plan_code)} 플랜으로 변경됩니다.
                </p>
                <div className="billing-actions">
                  <button
                    type="button"
                    className="mui-btn mui-btn--outlined"
                    onClick={handleCancelPlanChange}
                    disabled={actionLoading === "plan-change"}
                  >
                    다운그레이드 예약 취소
                  </button>
                </div>
              </section>
            ) : null}

            {isCancelScheduled ? (
              <section className="billing-surface billing-message">
                <h3>구독 취소 예약</h3>
                <p>
                  {formatDateTime(currentSubscription?.current_period_end)}까지 {formatPlanName(currentPlan?.plan_name, currentPlan?.plan_code)} 플랜을 사용할
                  수 있습니다. 이후 유효한 다른 구독이 없으면 무료 플랜으로 전환됩니다.
                </p>
                <div className="billing-actions">
                  <button
                    type="button"
                    className="mui-btn mui-btn--contained"
                    onClick={handleResume}
                    disabled={actionLoading === "resume"}
                  >
                    취소 철회
                  </button>
                </div>
              </section>
            ) : null}

            <section className="billing-surface">
              <div className="billing-section__header">
                <div>
                  <h3>구독 상태</h3>
                  <p>현재 적용 중인 구독의 핵심 상태값입니다.</p>
                </div>
                {!isCancelScheduled && currentPlan?.plan_code !== "free" ? (
                  <button
                    type="button"
                    className="mui-btn mui-btn--outlined"
                    onClick={handleCancelToFree}
                    disabled={actionLoading === "cancel"}
                  >
                    구독 취소
                  </button>
                ) : null}
              </div>
              <dl className="billing-definition">
                <div>
                  <dt>구독 시작일</dt>
                  <dd>{formatDateTime(currentSubscription?.current_period_start)}</dd>
                </div>
                <div>
                  <dt>구독 만료일</dt>
                  <dd>{formatDateTime(currentSubscription?.current_period_end)}</dd>
                </div>
                <div>
                  <dt>다음 결제 예정일</dt>
                  <dd>{formatDateTime(currentSubscription?.next_billing_at)}</dd>
                </div>
                <div>
                  <dt>결제 상태</dt>
                  <dd>{formatBillingStatus(currentSubscription?.billing_status)}</dd>
                </div>
              </dl>
            </section>

            <section className="billing-surface">
              <div className="billing-section__header">
                <div>
                  <h3>결제 이력</h3>
                  <p>최근 승인된 결제와 전체 이력을 확인합니다.</p>
                </div>
              </div>
              {data?.payment_history?.length ? (
                <div className="billing-history">
                  {data.payment_history.map((item) => (
                    <div key={item.orderId} className="billing-history__row">
                      <div>
                        <strong>{formatOrderName(item.orderName)}</strong>
                        <span>{formatDateTime(item.approvedAt)}</span>
                      </div>
                      <div>
                        <strong>{formatPrice(item.amount)}원</strong>
                        <span>{formatPaymentMethod(item.method)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="billing-surface--empty">표시할 결제 이력이 없습니다.</div>
              )}
            </section>

            {/* 하단 이전 페이지 이동 버튼 영역 */}
            <div className="billing-bottom-actions" style={{ marginTop: "24px", display: "flex", justifyContent: "flex-start" }}>
              <button
                type="button"
                className="mui-btn mui-btn--outlined"
                onClick={handleGoBack}
                aria-label="이전 페이지로 이동"
                style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <span className="material-icons" style={{ fontSize: "18px" }}>arrow_back</span>
                이전 페이지로
              </button>
            </div>
          </>
        )}
      </div>
    </GarimPage>
  );
}
