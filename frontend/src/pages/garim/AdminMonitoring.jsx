import { useState } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminMonitoring.css";

import GarimPage from "../../components/garim/GarimPage";

const MOCK_USERS = [
  {
    id: "u-0023",
    email: "kim.jungwoo@example.com",
    plan: "Pro",
    planColor: "warn",
    status: "processing",
    jobFile: "family_trip_2026.mp4",
    jobType: "video",
    progress: 64,
    elapsed: "1:24",
    lastSeen: "방금 전",
    ip: "211.123.***.***",
    ua: "Chrome 124 / macOS",
    joined: "2026.02.14",
    todayJobs: 3,
    totalJobs: 47,
    sessionStart: "14:30:12",
  },
  {
    id: "u-0041",
    email: "park.soojin@example.com",
    plan: "Free",
    planColor: "",
    status: "queued",
    jobFile: "portrait_edit.jpg",
    jobType: "image",
    progress: 0,
    elapsed: "0:08",
    lastSeen: "1분 전",
    ip: "110.45.***.***",
    ua: "Safari / iOS 17",
    joined: "2026.04.01",
    todayJobs: 1,
    totalJobs: 12,
    sessionStart: "14:38:44",
  },
  {
    id: "u-0087",
    email: "lee.minjae@example.com",
    plan: "Pro",
    planColor: "warn",
    status: "done",
    jobFile: "wedding_video.mp4",
    jobType: "video",
    progress: 100,
    elapsed: "4:52",
    lastSeen: "3분 전",
    ip: "175.118.***.***",
    ua: "Chrome 124 / Windows",
    joined: "2026.01.19",
    todayJobs: 5,
    totalJobs: 103,
    sessionStart: "13:55:08",
  },
  {
    id: "u-0102",
    email: "choi.yena@example.com",
    plan: "Free",
    planColor: "",
    status: "error",
    jobFile: "concert_clip.mp4",
    jobType: "video",
    progress: 22,
    elapsed: "0:45",
    lastSeen: "5분 전",
    ip: "203.227.***.***",
    ua: "Firefox / Windows",
    joined: "2026.03.22",
    todayJobs: 2,
    totalJobs: 8,
    sessionStart: "14:32:19",
  },
  {
    id: "u-0118",
    email: "jung.hyunwoo@example.com",
    plan: "Pro",
    planColor: "warn",
    status: "processing",
    jobFile: "vlog_ep12.mp4",
    jobType: "video",
    progress: 81,
    elapsed: "3:10",
    lastSeen: "방금 전",
    ip: "59.10.***.***",
    ua: "Chrome 124 / macOS",
    joined: "2026.02.28",
    todayJobs: 4,
    totalJobs: 76,
    sessionStart: "14:12:33",
  },
  {
    id: "u-0134",
    email: "shin.dayeon@example.com",
    plan: "Free",
    planColor: "",
    status: "idle",
    jobFile: "—",
    jobType: "",
    progress: 0,
    elapsed: "—",
    lastSeen: "12분 전",
    ip: "121.190.***.***",
    ua: "Safari / macOS",
    joined: "2026.05.01",
    todayJobs: 0,
    totalJobs: 5,
    sessionStart: "14:05:50",
  },
];

const STATUS_META = {
  processing: { label: "처리 중", dot: "#1976d2", chip: "mui-chip--soft-primary" },
  queued:     { label: "대기 중", dot: "#ed6c02", chip: "mui-chip--soft-warning" },
  done:       { label: "완료",   dot: "#2e7d32", chip: "mui-chip--soft-success" },
  error:      { label: "오류",   dot: "#d32f2f", chip: "mui-chip--soft-error" },
  idle:       { label: "유휴",   dot: "#bdbdbd", chip: "" },
};

export default function AdminMonitoring() {
  useDocumentTitle("사용자 모니터링 · Garim Admin");
  const [selectedId, setSelectedId] = useState("u-0023");
  const selected = MOCK_USERS.find((u) => u.id === selectedId);

  return (
    <GarimPage bodyClass="" screenLabel="25 Admin monitor">
      <div className="adm-shell">
        <aside className="adm-side">
          <div className="sec">운영</div>
          <a href="/admin/monitoring" className="active">
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
          <a href="/admin/policy">
            <span className="material-icons">tune</span>
            정책 및 상품 관리
          </a>
          <a href="/admin/payments">
            <span className="material-icons">payments</span>
            사용자 결제 확인
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>사용자 모니터링</h1>
            <span className="live-badge">
              <span className="live-dot" />
              LIVE
            </span>
            <span className="meta">실시간 활동 중인 사용자 · 10초 갱신</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>refresh</span>
                새로고침
              </button>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>filter_list</span>
                필터
              </button>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <div className="lbl">현재 접속자</div>
              <div className="num">127</div>
              <div className="delta">↑ 23 (1시간 전 대비)</div>
            </div>
            <div className="metric">
              <div className="lbl">처리 중</div>
              <div className="num">35</div>
              <div className="delta">Free 24 · Pro 9 · Studio 2</div>
            </div>
            <div className="metric warn">
              <div className="lbl">대기 중</div>
              <div className="num">12</div>
              <div className="delta">평균 대기 38초</div>
            </div>
            <div className="metric">
              <div className="lbl">금일 완료</div>
              <div className="num">412</div>
              <div className="delta">오류 9건 (2.2%)</div>
            </div>
          </div>

          <div className="adm-grid">
            <div className="adm-card">
              <div className="head">
                <h3>실시간 사용자 활동</h3>
                <span className="mui-chip mui-chip--soft-primary">처리 중 2</span>
                <span className="mui-chip mui-chip--soft-warning">대기 1</span>
                <span className="mui-chip mui-chip--soft-error">오류 1</span>
              </div>
              <div className="mon-row tbl-head">
                <span />
                <span>사용자</span>
                <span>플랜</span>
                <span>현재 작업</span>
                <span>진행률</span>
                <span>경과</span>
                <span>마지막 활동</span>
                <span />
              </div>
              {MOCK_USERS.map((u) => {
                const sm = STATUS_META[u.status];
                return (
                  <div
                    key={u.id}
                    className={`mon-row${selectedId === u.id ? " selected" : ""}`}
                  >
                    <span
                      className="status-dot"
                      style={{ background: sm.dot }}
                      title={sm.label}
                    />
                    <span>
                      <div className="mon-email">{u.email}</div>
                      <div className="mon-uid">{u.id}</div>
                    </span>
                    <span>
                      <span className={`mui-chip ${u.planColor === "warn" ? "mui-chip--soft-warning" : ""}`}>
                        {u.plan}
                      </span>
                    </span>
                    <span>
                      {u.jobFile !== "—" ? (
                        <>
                          <div className="mon-filename">{u.jobFile}</div>
                          <div className="mon-type">{u.jobType}</div>
                        </>
                      ) : (
                        <span style={{ color: "var(--fg-3)", fontSize: "12px" }}>—</span>
                      )}
                    </span>
                    <span>
                      {u.status !== "idle" && u.jobFile !== "—" ? (
                        <div className="mon-progress-wrap">
                          <div className="mon-progress-bar">
                            <div
                              style={{
                                width: `${u.progress}%`,
                                background: u.status === "error" ? "#d32f2f" : u.status === "done" ? "#2e7d32" : "#1976d2",
                              }}
                            />
                          </div>
                          <span className="mon-pct">{u.progress}%</span>
                        </div>
                      ) : (
                        <span style={{ color: "var(--fg-3)", fontSize: "12px" }}>—</span>
                      )}
                    </span>
                    <span className="mon-elapsed">{u.elapsed}</span>
                    <span>
                      <span className={`mui-chip ${sm.chip}`} style={{ fontSize: "11px", height: "20px" }}>
                        {sm.label}
                      </span>
                      <div className="mon-lastseen">{u.lastSeen}</div>
                    </span>
                    <span>
                      <button
                        className={`mon-view-btn${selectedId === u.id ? " active" : ""}`}
                        onClick={() => setSelectedId(u.id)}
                      >
                        확인
                      </button>
                    </span>
                  </div>
                );
              })}
              <div style={{ padding: "10px 16px", textAlign: "center", color: "var(--fg-2)", font: "400 12px var(--font-sans)" }}>
                … 121명 더 보기
              </div>
            </div>

            {selected && (
              <aside className="adm-card">
                <div className="head">
                  <h3>{selected.email}</h3>
                  <span className={`mui-chip ${STATUS_META[selected.status].chip}`} style={{ fontSize: "11px" }}>
                    {STATUS_META[selected.status].label}
                  </span>
                </div>
                <div className="detail-body">
                  <section className="detail-section">
                    <h4>사용자 정보</h4>
                    <div className="detail-row"><span>UID</span><span className="mono">{selected.id}</span></div>
                    <div className="detail-row"><span>플랜</span><span>{selected.plan}</span></div>
                    <div className="detail-row"><span>가입일</span><span className="mono">{selected.joined}</span></div>
                    <div className="detail-row"><span>IP</span><span className="mono">{selected.ip}</span></div>
                    <div className="detail-row"><span>브라우저</span><span>{selected.ua}</span></div>
                    <div className="detail-row"><span>세션 시작</span><span className="mono">{selected.sessionStart}</span></div>
                  </section>

                  <section className="detail-section">
                    <h4>작업 현황</h4>
                    {selected.jobFile !== "—" ? (
                      <>
                        <div className="detail-row"><span>파일</span><span className="mono" style={{ wordBreak: "break-all" }}>{selected.jobFile}</span></div>
                        <div className="detail-row"><span>유형</span><span>{selected.jobType}</span></div>
                        <div className="detail-row"><span>진행률</span>
                          <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <div className="detail-progress">
                              <div style={{
                                width: `${selected.progress}%`,
                                background: selected.status === "error" ? "#d32f2f" : selected.status === "done" ? "#2e7d32" : "#1976d2",
                              }} />
                            </div>
                            {selected.progress}%
                          </span>
                        </div>
                        <div className="detail-row"><span>경과 시간</span><span className="mono">{selected.elapsed}</span></div>
                      </>
                    ) : (
                      <div style={{ color: "var(--fg-3)", font: "400 12px var(--font-sans)", padding: "4px 0" }}>현재 처리 중인 작업 없음</div>
                    )}
                    <div className="detail-row"><span>오늘 처리</span><span>{selected.todayJobs}건</span></div>
                    <div className="detail-row"><span>누적 처리</span><span>{selected.totalJobs}건</span></div>
                  </section>

                  <section className="detail-section">
                    <h4>최근 활동</h4>
                    <div className="activity-log">
                      <div><span className="ts">{selected.sessionStart}</span> 세션 시작</div>
                      {selected.todayJobs > 0 && (
                        <>
                          <div><span className="ts">14:31:05</span> 파일 업로드 ({selected.jobType})</div>
                          <div><span className="ts">14:31:08</span> 처리 시작 → 큐 진입</div>
                          {selected.status === "done" && <div><span className="ts">14:36:00</span> <span style={{ color: "#2e7d32" }}>처리 완료 → 다운로드</span></div>}
                          {selected.status === "error" && <div><span className="ts">14:33:04</span> <span style={{ color: "#d32f2f" }}>오류 발생 (파일 손상)</span></div>}
                          {selected.status === "processing" && <div><span className="ts">14:32:00</span> GPU 워커 배정 → 처리 중</div>}
                        </>
                      )}
                    </div>
                  </section>

                  <section className="detail-section">
                    <h4>관리 액션</h4>
                    <div className="detail-actions">
                      <button className="mui-btn mui-btn--outlined mui-btn--sm" style={{ flex: 1 }}>
                        <span className="material-icons" style={{ fontSize: "15px" }}>cancel</span>
                        작업 취소
                      </button>
                      <button className="mui-btn mui-btn--outlined mui-btn--sm" style={{ flex: 1, color: "#d32f2f", borderColor: "rgba(211,47,47,0.5)" }}>
                        <span className="material-icons" style={{ fontSize: "15px" }}>logout</span>
                        세션 종료
                      </button>
                    </div>
                  </section>
                </div>
              </aside>
            )}
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
