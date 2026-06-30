import { useEffect, useMemo, useState } from "react";
import { getAdminPolicySettings } from "../utils/api";

export const PLAN_KEYS = ["free", "pro", "studio"];

const EMPTY_POLICY = {
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
    name: "무료",
    badge: "기본",
    badgeClass: "mui-chip--primary",
    description: "개인 진단과 가벼운 체험을 위한 무료 플랜.",
    cta: "무료로 시작",
  },
  pro: {
    name: "Pro",
    badge: "인기",
    badgeClass: "mui-chip--soft-warning",
    featured: true,
    description: "정기적으로 영상을 다루는 크리에이터를 위한 플랜.",
    cta: "Pro 시작하기",
  },
  studio: {
    name: "Studio",
    badge: "팀",
    badgeClass: "mui-chip--secondary",
    description: "팀 단위 작업과 대량 분석을 위한 최상위 플랜.",
    cta: "Studio 시작하기",
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

export function normalizePolicy(incoming = {}) {
  return {
    file_processing: {
      ...EMPTY_POLICY.file_processing,
      ...(incoming.file_processing || {}),
      plans: incoming.file_processing?.plans || {},
    },
    payment: {
      ...EMPTY_POLICY.payment,
      ...(incoming.payment || {}),
      plans: incoming.payment?.plans || {},
      creditPlans: incoming.payment?.creditPlans || {},
    },
    retention: {
      ...EMPTY_POLICY.retention,
      ...(incoming.retention || {}),
      plans: incoming.retention?.plans || {},
    },
  };
}

export function buildPricingPlans(policy) {
  return Object.entries(policy?.payment?.plans || {})
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
        cta: meta.cta || (Number(payment.price || 0) === 0 ? "무료로 시작" : "결제하기"),
        sortOrder: Number(payment.sortOrder ?? 0),
        planRank: Number(payment.planRank ?? 0),
        status: payment.status || "active",
        file: policy?.file_processing?.plans?.[key] || {},
        payment,
        retention: policy?.retention?.plans?.[key] || {},
      };
    })
    .filter((plan) => plan.status === "active")
    .sort((a, b) => a.sortOrder - b.sortOrder);
}

export function buildCreditPlans(policy) {
  return Object.entries(policy?.payment?.creditPlans || {})
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
      popularityCount: Number(credit.popularityCount ?? 0),
    }))
    .filter((plan) => plan.status === "active")
    .sort((a, b) => a.sortOrder - b.sortOrder);
}

export function usePricingPlans() {
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPolicy() {
      try {
        const response = await getAdminPolicySettings();
        if (cancelled) return;
        setPolicy(normalizePolicy(response.data || {}));
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

  const normalizedPolicy = policy || EMPTY_POLICY;
  const plans = useMemo(() => buildPricingPlans(normalizedPolicy), [normalizedPolicy]);
  const creditPlans = useMemo(() => buildCreditPlans(normalizedPolicy), [normalizedPolicy]);

  return { plans, creditPlans, policy: normalizedPolicy, loading, error };
}
