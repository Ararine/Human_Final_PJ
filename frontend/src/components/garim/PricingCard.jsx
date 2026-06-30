import React from "react";
import {
  formatFileSize,
  formatPrice,
  formatQuota,
} from "../../hooks/usePricingPlans";

// [한글 주석]
// 구독 요금제 정보를 렌더링하기 위한 공통 카드 컴포넌트입니다.
// 플랜 명칭, 가격, 설명 및 주요 혜택들을 표시합니다.
// 하단 버튼 및 상황별 추가 설명 영역은 Landing 페이지와 Pricing 페이지의 요구사항이 다르므로 Props로 받아 렌더링합니다.
export default function PricingCard({
  plan,
  isCurrentPlan = false,
  isHighlighted = false,
  showPeriod = false,
  actionButton,
  actionInfo,
  hasAnyActionInfo = false,
}) {
  return (
    <div
      className={`price-card${isHighlighted ? " price-card--featured" : ""}${isCurrentPlan ? " price-card--current" : ""}`}
    >
      {/* [한글 주석] 플랜 명칭과 배지를 상단 영역에 한 행으로 정렬합니다. */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <span className="overline-k" style={{ margin: 0, lineHeight: 1 }}>{plan.name}</span>
        {(isCurrentPlan || plan.badge) && (
          <span className={`mui-chip ${isCurrentPlan ? "" : plan.badgeClass} price-card__badge`}>
            {isCurrentPlan ? "현재 플랜" : plan.badge}
          </span>
        )}
      </div>

      {/* [한글 주석] 요금 금액 및 주기(월/영구)를 표시합니다. */}
      <div className="price-card__price">
        {formatPrice(plan.payment.price)}
        <small>원</small>
        {showPeriod && (
          <span className="price-card__period">
            {plan.key === "free" ? "/ 영구" : "/ 30일"}
          </span>
        )}
      </div>

      {/* [한글 주석] 플랜에 대한 간단한 설명을 표시합니다. */}
      <p className="caption-k" style={{ fontSize: "13px" }}>
        {plan.description}
      </p>

      {/* [한글 주석] 플랜이 제공하는 크레딧, 처리 한도 등의 상세 혜택 리스트입니다. */}
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

      {/* [한글 주석] 하단 1번 버튼 영역 및 2번 예약 정보 알림 영역입니다. */}
      {(actionButton || actionInfo) && (
        <div className="price-card__actions">
          {actionButton && (
            <div className="price-card__action-btn">
              {actionButton}
            </div>
          )}
          {hasAnyActionInfo && (
            <div className="price-card__action-info">
              {actionInfo}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
