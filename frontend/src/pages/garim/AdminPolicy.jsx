import { useState } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminPolicy.css";

import GarimPage from "../../components/garim/GarimPage";

const PLANS = [
  { key: "free",   label: "Free",   color: "" },
  { key: "pro",    label: "Pro",    color: "#ed6c02" },
  { key: "studio", label: "Studio", color: "#1976d2" },
];

const SECTIONS = [
  { key: "file",      icon: "storage",              label: "파일 처리 정책" },
  { key: "retention", icon: "auto_delete",           label: "데이터 보존 정책" },
  { key: "notify",    icon: "notifications_active",  label: "운영자 알림 설정" },
];

export default function AdminPolicy() {
  useDocumentTitle("정책 설정 · Garim Admin");

  const [activeSection, setActiveSection] = useState("file");

  const [planPolicies, setPlanPolicies] = useState({
    free:   { fileSizeLimit: "50",   maxJobs: "3",  monthlyQuota: "5",  resultRetention: "3"  },
    pro:    { fileSizeLimit: "500",  maxJobs: "10", monthlyQuota: "50", resultRetention: "7"  },
    studio: { fileSizeLimit: "2048", maxJobs: "30", monthlyQuota: "",   resultRetention: "30" },
  });
  const [allowedFormats,     setAllowedFormats]     = useState("jpg,jpeg,png,webp,mp4,mov");
  const [autoDeleteOriginal, setAutoDeleteOriginal] = useState("12");
  const [metaRetention,      setMetaRetention]      = useState("90");
  const [notifyAbuse,        setNotifyAbuse]        = useState(true);
  const [queueDelay,         setQueueDelay]         = useState("30");
  const [autoReport,         setAutoReport]         = useState(true);

  function updatePlan(planKey, field, value) {
    setPlanPolicies((prev) => ({
      ...prev,
      [planKey]: { ...prev[planKey], [field]: value },
    }));
  }

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
                          {plan.key === "studio" ? (
                            <span className="pol-unlimited">무제한</span>
                          ) : (
                            <>
                              <input type="number" className="pol-input"
                                value={planPolicies[plan.key].monthlyQuota}
                                onChange={(e) => updatePlan(plan.key, "monthlyQuota", e.target.value)}
                                min="1" />
                              <span className="pol-unit">건/월</span>
                            </>
                          )}
                        </span>
                      ))}
                    </div>
                    <div className="pol-plan-row" style={{ borderBottom: "none" }}>
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
                  <button className="mui-btn mui-btn--contained">저장</button>
                </div>
              </section>

              {/* 데이터 보존 정책 */}
              <section className="pol-section" id="retention">
                <h1>데이터 보존 정책</h1>

                <div className="pol-card">
                  <div className="pol-card-head">
                    <h3>자동 삭제 설정</h3>
                  </div>
                  <div className="pol-card-body">
                    <div className="pol-field">
                      <label>원본 파일 자동 삭제 (처리 후)</label>
                      <div className="pol-input-row">
                        <input type="number" className="pol-input"
                          value={autoDeleteOriginal}
                          onChange={(e) => setAutoDeleteOriginal(e.target.value)} min="1" />
                        <span className="pol-unit">시간</span>
                      </div>
                    </div>
                    <div className="pol-field">
                      <label>처리 메타데이터 보존 기간</label>
                      <div className="pol-input-row">
                        <input type="number" className="pol-input"
                          value={metaRetention}
                          onChange={(e) => setMetaRetention(e.target.value)} min="1" />
                        <span className="pol-unit">일</span>
                      </div>
                      <p className="pol-hint">워터마크 역추적용 · 법적 의무 준수</p>
                    </div>
                  </div>
                </div>

                <div className="pol-save-bar">
                  <button className="mui-btn mui-btn--outlined">초기화</button>
                  <button className="mui-btn mui-btn--contained">저장</button>
                </div>
              </section>

              {/* 운영자 알림 설정 */}
              <section className="pol-section" id="notify">
                <h1>운영자 알림 설정</h1>

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
                  <button className="mui-btn mui-btn--contained">저장</button>
                </div>
              </section>

          </div>
        </main>
      </div>
    </GarimPage>
  );
}
