import { useEffect, useMemo, useState } from "react";
import { getAdminPolicySettings } from "../utils/api";

export const PLAN_KEYS = ["free", "pro", "studio"];

export const DEFAULT_POLICY = {
  file_processing: {
    plans: {
      free: {
        fileSizeLimit: 50,
        maxJobs: 3,
        monthlyQuota: 5,
        resultRetention: 3,
      },
      pro: {
        fileSizeLimit: 500,
        maxJobs: 10,
        monthlyQuota: 50,
        resultRetention: 7,
      },
      studio: {
        fileSizeLimit: 2048,
        maxJobs: 30,
        monthlyQuota: null,
        resultRetention: 30,
      },
    },
    allowedFormats: ["jpg", "jpeg", "png", "webp", "mp4", "mov"],
  },
  payment: {
    plans: {
      free: { credits: 5, price: 0 },
      pro: { credits: 50, price: 2900 },
      studio: { credits: 500, price: 19800 },
    },
  },
  retention: {
    plans: {
      free: { autoDeleteOriginalHours: 12, metadataRetentionDays: 90 },
      pro: { autoDeleteOriginalHours: 12, metadataRetentionDays: 90 },
      studio: { autoDeleteOriginalHours: 12, metadataRetentionDays: 90 },
    },
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
  return {
    file_processing: {
      ...base.file_processing,
      ...(incoming.file_processing || {}),
      plans: {
        ...base.file_processing.plans,
        ...(incoming.file_processing?.plans || {}),
      },
    },
    payment: {
      ...base.payment,
      ...(incoming.payment || {}),
      plans: { ...base.payment.plans, ...(incoming.payment?.plans || {}) },
    },
    retention: {
      ...base.retention,
      ...(incoming.retention || {}),
      plans: { ...base.retention.plans, ...(incoming.retention?.plans || {}) },
    },
  };
}

export function buildPricingPlans(policy) {
  return PLAN_KEYS.map((key) => ({
    key,
    ...PLAN_META[key],
    file:
      policy.file_processing.plans[key] ||
      DEFAULT_POLICY.file_processing.plans[key],
    payment: policy.payment.plans[key] || DEFAULT_POLICY.payment.plans[key],
    retention:
      policy.retention.plans[key] || DEFAULT_POLICY.retention.plans[key],
  }));
}

export function usePricingPlans() {
  const [policy, setPolicy] = useState(DEFAULT_POLICY);

  useEffect(() => {
    let cancelled = false;

    async function loadPolicy() {
      try {
        const response = await getAdminPolicySettings();
        if (cancelled) return;
        setPolicy(mergePolicy(DEFAULT_POLICY, response.data || {}));
      } catch (error) {
        console.error("Failed to load pricing policy", error);
      }
    }

    loadPolicy();
    return () => {
      cancelled = true;
    };
  }, []);

  return useMemo(() => buildPricingPlans(policy), [policy]);
}
