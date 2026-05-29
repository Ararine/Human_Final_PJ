import { useEffect, useState } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminPolicy.css";

import GarimPage from "../../components/garim/GarimPage";
import { getAdminPolicySettings, updateAdminPolicySettings } from "../../utils/api";

const PLANS = [
  { key: "free",   label: "Free",   color: "" },
  { key: "pro",    label: "Pro",    color: "#ed6c02" },
  { key: "studio", label: "Studio", color: "#1976d2" },
];

// eslint-disable-next-line no-unused-vars
const SECTIONS = [
  { key: "file",      icon: "storage",              label: "파일 처리 정책" },
  { key: "retention", icon: "auto_delete",           label: "데이터 보존 정책" },
  { key: "notify",    icon: "notifications_active",  label: "운영 알림 설정" },
];

export default function AdminPolicy() {
  useDocumentTitle("정책 설정 · Garim Admin");

  // eslint-disable-next-line no-unused-vars
  const [activeSection, setActiveSection] = useState("file");

  const [planPolicies, setPlanPolicies] = useState({
    free:   { fileSizeLimit: "50",   maxJobs: "3",  monthlyQuota: "5",  resultRetention: "3",  watermarkRequired: true },
    pro:    { fileSizeLimit: "500",  maxJobs: "10", monthlyQuota: "50", resultRetention: "7",  watermarkRequired: false },
    studio: { fileSizeLimit: "2048", maxJobs: "30", monthlyQuota: "",   resultRetention: "30", watermarkRequired: false },
  });
  const [paymentPolicies, setPaymentPolicies] = useState({
    free:   { credits: "5",   price: "0"     },
    pro:    { credits: "50",  price: "2900"  },
    studio: { credits: "500", price: "19800" },
  });
  const [retentionPolicies, setRetentionPolicies] = useState({
    free:   { autoDeleteOriginalHours: "12", metadataRetentionDays: "90" },
    pro:    { autoDeleteOriginalHours: "12", metadataRetentionDays: "90" },
    studio: { autoDeleteOriginalHours: "12", metadataRetentionDays: "90" },
  });
  const [allowedFormats,     setAllowedFormats]     = useState("jpg,jpeg,png,webp,mp4,mov");
  const [notifyAbuse,        setNotifyAbuse]        = useState(true);
  const [queueDelay,         setQueueDelay]         = useState("30");
  const [autoReport,         setAutoReport]         = useState(true);
  const [saveMessage,        setSaveMessage]        = useState("");

  function updatePlan(planKey, field, value) {
    setPlanPolicies((prev) => ({
      ...prev,
      [planKey]: { ...prev[planKey], [field]: value },
    }));
  }

  function updatePaymentPolicy(planKey, field, value) {
    setPaymentPolicies((prev) => ({
      ...prev,
      [planKey]: { ...prev[planKey], [field]: value },
    }));
  }

  function updateRetentionPolicy(planKey, field, value) {
    setRetentionPolicies((prev) => ({
      ...prev,
      [planKey]: { ...prev[planKey], [field]: value },
    }));
  }

  useEffect(() => {
    let cancelled = false;

    async function loadPolicies() {
      try {
        const response = await getAdminPolicySettings();
        if (cancelled) return;

        const policies = response.data || {};
        const filePolicy = policies.file_processing || {};
        const paymentPolicy = policies.payment || {};
        const retentionPolicy = policies.retention || {};
        const notificationPolicy = policies.notification || {};

        if (filePolicy.plans) {
          setPlanPolicies((prev) => mergePlanPolicy(prev, filePolicy.plans));
        }
        if (Array.isArray(filePolicy.allowedFormats)) {
          setAllowedFormats(filePolicy.allowedFormats.join(","));
        }
        if (paymentPolicy.plans) {
          setPaymentPolicies((prev) => mergePlanPolicy(prev, paymentPolicy.plans));
        }
        if (retentionPolicy.plans) {
          setRetentionPolicies((prev) => mergePlanPolicy(prev, retentionPolicy.plans));
        } else if (
          retentionPolicy.autoDeleteOriginalHours !== undefined ||
          retentionPolicy.metadataRetentionDays !== undefined
        ) {
          setRetentionPolicies((prev) => mergePlanPolicy(prev, {
            free: retentionPolicy,
            pro: retentionPolicy,
            studio: retentionPolicy,
          }));
        }
        if (notificationPolicy.notifyAbuse !== undefined) {
          setNotifyAbuse(Boolean(notificationPolicy.notifyAbuse));
        }
        if (notificationPolicy.queueDelayMinutes !== undefined) {
          setQueueDelay(String(notificationPolicy.queueDelayMinutes));
        }
        if (notificationPolicy.autoReport !== undefined) {
          setAutoReport(Boolean(notificationPolicy.autoReport));
        }
      } catch (error) {
        console.error("Failed to load admin policy settings", error);
        setSaveMessage("정책 설정을 불러오지 못했습니다.");
      }
    }

    loadPolicies();
    return () => {
      cancelled = true;
    };
  }, []);

  function mergePlanPolicy(current, incoming) {
    const next = { ...current };
    for (const plan of PLANS) {
      if (!incoming[plan.key]) continue;
      next[plan.key] = {};
      for (const [key, value] of Object.entries(current[plan.key])) {
        if (typeof value === "boolean") {
          next[plan.key][key] = incoming[plan.key][key] === null || incoming[plan.key][key] === undefined
            ? false
            : Boolean(incoming[plan.key][key]);
        } else {
          next[plan.key][key] = incoming[plan.key][key] === null || incoming[plan.key][key] === undefined
            ? ""
            : String(incoming[plan.key][key]);
        }
      }
    }
    return next;
  }

  function numberOrNull(value) {
    if (value === "") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function buildPolicyPayload() {
    return {
      file_processing: {
        plans: {
          free: {
            fileSizeLimit: numberOrNull(planPolicies.free.fileSizeLimit),
            maxJobs: numberOrNull(planPolicies.free.maxJobs),
            monthlyQuota: numberOrNull(planPolicies.free.monthlyQuota),
            resultRetention: numberOrNull(planPolicies.free.resultRetention),
            watermarkRequired: Boolean(planPolicies.free.watermarkRequired),
          },
          pro: {
            fileSizeLimit: numberOrNull(planPolicies.pro.fileSizeLimit),
            maxJobs: numberOrNull(planPolicies.pro.maxJobs),
            monthlyQuota: numberOrNull(planPolicies.pro.monthlyQuota),
            resultRetention: numberOrNull(planPolicies.pro.resultRetention),
            watermarkRequired: Boolean(planPolicies.pro.watermarkRequired),
          },
          studio: {
            fileSizeLimit: numberOrNull(planPolicies.studio.fileSizeLimit),
            maxJobs: numberOrNull(planPolicies.studio.maxJobs),
            monthlyQuota: numberOrNull(planPolicies.studio.monthlyQuota),
            resultRetention: numberOrNull(planPolicies.studio.resultRetention),
            watermarkRequired: Boolean(planPolicies.studio.watermarkRequired),
          },
        },
        allowedFormats: allowedFormats
          .split(",")
          .map((format) => format.trim())
          .filter(Boolean),
      },
      payment: {
        plans: {
          free: {
            credits: numberOrNull(paymentPolicies.free.credits),
            price: numberOrNull(paymentPolicies.free.price),
          },
          pro: {
            credits: numberOrNull(paymentPolicies.pro.credits),
            price: numberOrNull(paymentPolicies.pro.price),
          },
          studio: {
            credits: numberOrNull(paymentPolicies.studio.credits),
            price: numberOrNull(paymentPolicies.studio.price),
          },
        },
      },
      retention: {
        plans: {
          free: {
            autoDeleteOriginalHours: numberOrNull(retentionPolicies.free.autoDeleteOriginalHours),
            metadataRetentionDays: numberOrNull(retentionPolicies.free.metadataRetentionDays),
          },
          pro: {
            autoDeleteOriginalHours: numberOrNull(retentionPolicies.pro.autoDeleteOriginalHours),
            metadataRetentionDays: numberOrNull(retentionPolicies.pro.metadataRetentionDays),
          },
          studio: {
            autoDeleteOriginalHours: numberOrNull(retentionPolicies.studio.autoDeleteOriginalHours),
            metadataRetentionDays: numberOrNull(retentionPolicies.studio.metadataRetentionDays),
          },
        },
      },
      notification: {
        notifyAbuse,
        queueDelayMinutes: numberOrNull(queueDelay),
        autoReport,
      },
    };
  }

  async function handleSavePolicies() {
    try {
      setSaveMessage("");
      await updateAdminPolicySettings(buildPolicyPayload());
      setSaveMessage("정책 설정을 저장했습니다.");
    } catch (error) {
      console.error("Failed to save admin policy settings", error);
      setSaveMessage("정책 설정 저장에 실패했습니다.");
    }
  }

  // eslint-disable-next-line no-unused-vars
  const handleNavClick = (e, key) => {
    e.preventDefault();
    setActiveSection(key);
    document.getElementById(key)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <GarimPage bodyClass="" screenLabel="30 Admin policy">
      <div className="adm-shell">
        <aside className="adm-side">
          <div className="sec">운영</div>
          <a href="/admin/monitoring">
            <span className="material-icons">monitor_heart</span>
            사용자 모니터링
          </a>
          <a href="/admin/queue">
            <span className="material-icons">queue</span>
            처리 큐
          </a>
          <a href="/admin/compliance">
            <span className="material-icons">verified_user</span>
            컴플라이언스
          </a>
          <div className="sec">시스템</div>
          <a href="/admin/users">
            <span className="material-icons">people</span>
            사용자
          </a>
          <a href="/admin/analytics">
            <span className="material-icons">analytics</span>
            분석
          </a>
          <a href="/admin/policy" className="active">
            <span className="material-icons">tune</span>
            정책 설정
          </a>
        </aside>

        <main className="adm-main pol-adm-main">
          <div className="pol-content">

              {/* 파일 처리 정책 */}
              {saveMessage && (
                <div className="mui-alert mui-alert--info" style={{ marginBottom: "16px" }}>
                  {saveMessage}
                </div>
              )}

              <section className="pol-section" id="file">
                <h1>파일 처리 정책</h1>

                <div className="pol-card">
                  <div className="pol-card-head">
                    <h3>플랜별 처리 한도</h3>
                  </div>
                  <div className="pol-plan-table">
                    <div className="pol-plan-row pol-plan-head">
                      <span>항목</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} style={{ color: plan.color || "inherit" }}>
                          {plan.label}
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">최대 파일 크기</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={planPolicies[plan.key].fileSizeLimit}
                            onChange={(e) => updatePlan(plan.key, "fileSizeLimit", e.target.value)}
                            min="1" />
                          <span className="pol-unit">MB</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">동시 처리 최대 건수</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={planPolicies[plan.key].maxJobs}
                            onChange={(e) => updatePlan(plan.key, "maxJobs", e.target.value)}
                            min="1" />
                          <span className="pol-unit">건</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">월 처리 한도</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={planPolicies[plan.key].monthlyQuota}
                            onChange={(e) => updatePlan(plan.key, "monthlyQuota", e.target.value)}
                            min="1"
                            placeholder={plan.key === "studio" ? "무제한" : ""} />
                          <span className="pol-unit">건/월</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">결과 파일 보관 기간</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={planPolicies[plan.key].resultRetention}
                            onChange={(e) => updatePlan(plan.key, "resultRetention", e.target.value)}
                            min="1" />
                          <span className="pol-unit">일</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row" style={{ borderBottom: "none" }}>
                      <span className="pol-plan-label">워터마크 필수 여부</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <label className="pol-switch-wrap">
                            <input type="checkbox"
                              checked={planPolicies[plan.key].watermarkRequired}
                              onChange={(e) => updatePlan(plan.key, "watermarkRequired", e.target.checked)} />
                            <span className="pol-toggle-label">{planPolicies[plan.key].watermarkRequired ? "필수" : "선택"}</span>
                          </label>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="pol-common">
                    <span className="pol-common-label">공통 허용 파일 형식</span>
                    <input type="text" className="pol-input pol-input--wide"
                      value={allowedFormats}
                      onChange={(e) => setAllowedFormats(e.target.value)} />
                    <span className="pol-hint">쉼표로 구분 · 모든 플랜에 동일 적용</span>
                  </div>
                </div>

                <div className="pol-save-bar">
                  <button className="mui-btn mui-btn--outlined">초기화</button>
                  <button className="mui-btn mui-btn--contained" onClick={handleSavePolicies}>저장</button>
                </div>
              </section>

              {/* 데이터 보존 정책 */}
              <section className="pol-section" id="payment">
                <h1>결제 정책</h1>

                <div className="pol-card">
                  <div className="pol-card-head">
                    <h3>플랜별 크레딧 및 금액</h3>
                  </div>
                  <div className="pol-plan-table">
                    <div className="pol-plan-row pol-plan-head">
                      <span>항목</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} style={{ color: plan.color || "inherit" }}>
                          {plan.label}
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">제공 크레딧</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={paymentPolicies[plan.key].credits}
                            onChange={(e) => updatePaymentPolicy(plan.key, "credits", e.target.value)}
                            min="0" />
                          <span className="pol-unit">개</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row" style={{ borderBottom: "none" }}>
                      <span className="pol-plan-label">금액</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={paymentPolicies[plan.key].price}
                            onChange={(e) => updatePaymentPolicy(plan.key, "price", e.target.value)}
                            min="0" step="100" />
                          <span className="pol-unit">원</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pol-save-bar">
                  <button className="mui-btn mui-btn--outlined">초기화</button>
                  <button className="mui-btn mui-btn--contained" onClick={handleSavePolicies}>저장</button>
                </div>
              </section>

              <section className="pol-section" id="retention">
                <h1>데이터 보존 정책</h1>

                <div className="pol-card">
                  <div className="pol-card-head">
                    <h3>플랜별 자동 삭제 및 보존 기간</h3>
                  </div>
                  <div className="pol-plan-table">
                    <div className="pol-plan-row pol-plan-head">
                      <span>항목</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} style={{ color: plan.color || "inherit" }}>
                          {plan.label}
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row">
                      <span className="pol-plan-label">원본 파일 자동 삭제</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={retentionPolicies[plan.key].autoDeleteOriginalHours}
                            onChange={(e) => updateRetentionPolicy(plan.key, "autoDeleteOriginalHours", e.target.value)}
                            min="1" />
                          <span className="pol-unit">시간</span>
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row" style={{ borderBottom: "none" }}>
                      <span className="pol-plan-label">처리 메타데이터 보존</span>
                      {PLANS.map((plan) => (
                        <span key={plan.key} className="pol-plan-cell">
                          <input type="number" className="pol-input"
                            value={retentionPolicies[plan.key].metadataRetentionDays}
                            onChange={(e) => updateRetentionPolicy(plan.key, "metadataRetentionDays", e.target.value)}
                            min="1" />
                          <span className="pol-unit">일</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pol-save-bar">
                  <button className="mui-btn mui-btn--outlined">초기화</button>
                  <button className="mui-btn mui-btn--contained" onClick={handleSavePolicies}>저장</button>
                </div>
              </section>
              {/* 운영 알림 설정 */}
              <section className="pol-section" id="notify">
                <h1>운영 알림 설정</h1>

                <div className="pol-card">
                  <div className="pol-card-head">
                    <h3>알림 수신 설정</h3>
                  </div>
                  <div className="pol-card-body">
                    <div className="pol-toggle-row">
                      <div className="pol-toggle-text">
                        <div className="pol-toggle-title">이상 탐지 이메일 수신</div>
                        <div className="pol-toggle-sub">admin@garim.kr 수신</div>
                      </div>
                      <label className="pol-switch-wrap">
                        <input type="checkbox" checked={notifyAbuse}
                          onChange={(e) => setNotifyAbuse(e.target.checked)} />
                        <span className="pol-toggle-label">{notifyAbuse ? "활성" : "비활성"}</span>
                      </label>
                    </div>
                    <div className="pol-field" style={{ marginTop: "16px" }}>
                      <label>큐 지연 알림 임계값</label>
                      <div className="pol-input-row">
                        <input type="number" className="pol-input"
                          value={queueDelay}
                          onChange={(e) => setQueueDelay(e.target.value)} min="1" />
                        <span className="pol-unit">분</span>
                      </div>
                      <p className="pol-hint">처리 대기 시간이 이를 초과하면 알림 발송</p>
                    </div>
                    <div className="pol-toggle-row" style={{ marginTop: "16px" }}>
                      <div className="pol-toggle-text">
                        <div className="pol-toggle-title">컴플라이언스 자동 보고서</div>
                        <div className="pol-toggle-sub">월 1회 자동 생성·이메일 발송</div>
                      </div>
                      <label className="pol-switch-wrap">
                        <input type="checkbox" checked={autoReport}
                          onChange={(e) => setAutoReport(e.target.checked)} />
                        <span className="pol-toggle-label">{autoReport ? "활성" : "비활성"}</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="pol-save-bar">
                  <button className="mui-btn mui-btn--outlined">초기화</button>
                  <button className="mui-btn mui-btn--contained" onClick={handleSavePolicies}>저장</button>
                </div>
              </section>

          </div>
        </main>
      </div>
    </GarimPage>
  );
}
