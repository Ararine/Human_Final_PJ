import { useEffect, useMemo, useState } from "react";
import { getAdminPolicySettings } from "../utils/api";

export const PLAN_KEYS = ["free", "pro", "studio"];

// DB 정책 설정이 우선되므로 하드코딩된 기본 정책 플랜/크레딧 목록 데이터를 빈 객체로 초기화합니다.
export const DEFAULT_POLICY = {
  file_processing: {
    plans: {},
    allowedFormats: ["jpg", "jpeg", "png", "webp", "mp4", "mov"],
  },
  payment: {
    plans: {},
    creditPlans: {},
  },
  retention: {
    plans: {},
  },
};

export const PLAN_META = {
  free: {
    name: "Free",
    badge: "기본",
    badgeClass: "mui-chip--primary",
    featured: true,
    description: "개인 테스트와 가벼운 분석을 위한 무료 플랜입니다.",
    cta: "무료로 시작",
  },
  pro: {
    name: "PRO",
    badge: "추천",
    badgeClass: "mui-chip--soft-warning",
    description: "정기적으로 영상을 분석하는 개인 사용자에게 적합합니다.",
    cta: "결제하기",
  },
  studio: {
    name: "STUDIO",
    badge: "팀/스튜디오",
    badgeClass: "mui-chip--secondary",
    description: "팀 단위 작업과 대량 분석을 위한 플랜입니다.",
    cta: "결제하기",
  },
};

export function formatPrice(value) {
  const price = Number(value || 0);
  return price === 0 ? "0" : price.toLocaleString("ko-KR");
}

export function formatQuota(value, unit = "건") {
  if (value === null || value === undefined || value === "") return "무제한";
  return `${Number(value).toLocaleString("ko-KR")}${unit}`;
}

export function formatFileSize(value) {
  const size = Number(value || 0);
  if (size >= 1024) {
    return `${Number((size / 1024).toFixed(1)).toLocaleString("ko-KR")}GB`;
  }
  return `${size.toLocaleString("ko-KR")}MB`;
}

export function mergePolicy(base, incoming = {}) {
  const incomingFilePlans = incoming.file_processing?.plans;
  const incomingPaymentPlans = incoming.payment?.plans;
  const incomingRetentionPlans = incoming.retention?.plans;
  const incomingCreditPlans = incoming.payment?.creditPlans;

  return {
    file_processing: {
      ...base.file_processing,
      ...(incoming.file_processing || {}),
      plans: incomingFilePlans || base.file_processing.plans,
    },
    payment: {
      ...base.payment,
      ...(incoming.payment || {}),
      plans: incomingPaymentPlans || base.payment.plans,
      creditPlans: incomingCreditPlans || base.payment.creditPlans,
    },
    retention: {
      ...base.retention,
      ...(incoming.retention || {}),
      plans: incomingRetentionPlans || base.retention.plans,
    },
  };
}

export function buildPricingPlans(policy) {
  return Object.entries(policy.payment.plans || {})
    .map(([key, payment]) => {
      const meta = PLAN_META[key] || {
        name: payment.name || key,
        badge: "플랜",
        badgeClass: "mui-chip--primary",
        description: `${payment.name || key} 구독 플랜입니다.`,
        cta: Number(payment.price || 0) === 0 ? "무료로 시작" : "결제하기",
      };
      return {
        key,
        ...meta,
        name: payment.name || meta.name,
        badge: payment.badgeLabel || meta.badge,
        badgeClass: payment.badgeClass || meta.badgeClass,
        description: payment.description || meta.description,
        // 버튼 문구는 price 기준 고정 분기값 (cta_label 제거됨)
        cta: Number(payment.price || 0) === 0 ? "무료로 시작" : "결제하기",
        sortOrder: Number(payment.sortOrder ?? 0),
        planRank: Number(payment.planRank ?? 0),
        status: payment.status || "active",
        file:
          policy.file_processing.plans[key] ||
          DEFAULT_POLICY.file_processing.plans[key] ||
          {},
        payment,
        retention:
          policy.retention.plans[key] ||
          DEFAULT_POLICY.retention.plans[key] ||
          {},
      };
    })
    .filter((plan) => plan.status === "active")
    .sort((a, b) => a.sortOrder - b.sortOrder);
}

export function buildCreditPlans(policy) {
  return Object.entries(policy.payment.creditPlans || {})
    .map(([key, credit]) => ({
      key,
      productType: "credit",
      name: credit.name || `${formatQuota(credit.credits, "개")} 크레딧`,
      sortOrder: Number(credit.sortOrder ?? 0),
      status: credit.status || "active",
      payment: {
        price: credit.price,
        credits: Number(credit.credits || 0) + Number(credit.bonusCredits || 0),
        baseCredits: credit.credits,
        bonusCredits: credit.bonusCredits || 0,
      },
      expiresDays: credit.expiresDays,
      // 개별 크레딧 플랜의 과거 결제 성공 건수 통계를 정수형태로 바인딩합니다.
      popularityCount: Number(credit.popularityCount ?? 0),
    }))
    .filter((plan) => plan.status === "active")
    .sort((a, b) => a.sortOrder - b.sortOrder);
}

export function usePricingPlans() {
  const [policy, setPolicy] = useState(DEFAULT_POLICY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPolicy() {
      try {
        const response = await getAdminPolicySettings();
        if (cancelled) return;
        setPolicy(mergePolicy(DEFAULT_POLICY, response.data || {}));
      } catch (err) {
        console.error("Failed to load pricing policy", err);
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadPolicy();
    return () => {
      cancelled = true;
    };
  }, []);

  const plans = useMemo(() => buildPricingPlans(policy), [policy]);
  const creditPlans = useMemo(() => buildCreditPlans(policy), [policy]);

  return { plans, creditPlans, policy, loading, error };
}
