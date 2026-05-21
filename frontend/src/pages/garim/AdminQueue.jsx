import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminQueue.css";

import GarimPage from "../../components/garim/GarimPage";

export default function AdminQueue() {
  useDocumentTitle("처리 큐 관리 · Garim Admin");

  return (
    <GarimPage bodyClass="" screenLabel="26 Admin queue">
      <div className="adm-shell">
        <aside className="adm-side">
          <div className="sec">
            운영
          </div>
          <a href="/admin/abuse">
            <span className="material-icons">
              shield
            </span>
            어뷰징 모니터링
          </a>
          <a href="/admin/queue" className="active">
            <span className="material-icons">
              queue
            </span>
            처리 큐
          </a>
          <a href="/admin/compliance">
            <span className="material-icons">
              verified_user
            </span>
            컴플라이언스
          </a>
          <div className="sec">
            시스템
          </div>
          <a href="#">
            <span className="material-icons">
              people
            </span>
            사용자
          </a>
          <a href="#">
            <span className="material-icons">
              analytics
            </span>
            분석
          </a>
          <a href="#">
            <span className="material-icons">
              tune
            </span>
            정책 설정
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>
              처리 큐 관리
            </h1>
            <span className="live-indicator">
              LIVE
            </span>
            <span className="caption-k">
              WebSocket 연결됨 · 1초 간격
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <button className="mui-btn mui-btn--outlined mui-btn--sm" style={{ color: "#ed6c02", borderColor: "rgba(237,108,2,0.5)" }}>
                <span className="material-icons" style={{ fontSize: "16px" }}>
                  pause
                </span>
                큐 일시 정지
              </button>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>
                  add
                </span>
                워커 추가
              </button>
            </div>
          </div>
          <div className="metric-row">
            <div className="metric">
              <div className="lbl">
                현재 큐
              </div>
              <div className="num">
                47
              </div>
              <div className="delta">
                대기 12 · 처리 35
              </div>
            </div>
            <div className="metric warn">
              <div className="lbl">
                평균 대기
              </div>
              <div className="num">
                38
                <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                  초
                </small>
              </div>
              <div className="delta">
                SLA 60초 이내
              </div>
            </div>
            <div className="metric">
              <div className="lbl">
                GPU 평균
              </div>
              <div className="num">
                72
                <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                  %
                </small>
              </div>
              <div className="delta">
                12개 워커 활성
              </div>
            </div>
            <div className="metric ok">
              <div className="lbl">
                시간당 완료
              </div>
              <div className="num">
                412
              </div>
              <div className="delta">
                +8% (24h 대비)
              </div>
            </div>
            <div className="metric err">
              <div className="lbl">
                실패율
              </div>
              <div className="num">
                2.4
                <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                  %
                </small>
              </div>
              <div className="delta">
                정상 (목표 &amp;lt;3%)
              </div>
            </div>
            <div className="metric">
              <div className="lbl">
                활성 워커
              </div>
              <div className="num">
                12
                <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                  /16
                </small>
              </div>
              <div className="delta">
                4 idle
              </div>
            </div>
          </div>
          <div className="charts">
            <div className="chart-card">
              <h3>
                시간별 처리량 (24h)
                <span className="spacer">
                </span>
                <span className="caption-k" style={{ fontSize: "11px" }}>
                  완료 8,427건
                </span>
              </h3>
              <div className="chart-area">
                <svg viewBox="0 0 600 160" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                  <defs>
                    <lineargradient id="ch1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="rgba(25,118,210,0.3)" />
                      <stop offset="100%" stopColor="rgba(25,118,210,0)" />
                    </lineargradient>
                  </defs>
                  <g stroke="#e0e0e0" strokeWidth="1">
                    <line x1="0" y1="40" x2="600" y2="40" />
                    <line x1="0" y1="80" x2="600" y2="80" />
                    <line x1="0" y1="120" x2="600" y2="120" />
                  </g>
                  <path d="M0,130 L25,128 L50,120 L75,115 L100,100 L125,85 L150,72 L175,68 L200,75 L225,82 L250,88 L275,72 L300,60 L325,55 L350,50 L375,42 L400,38 L425,45 L450,55 L475,65 L500,52 L525,48 L550,42 L575,35 L600,30 L600,160 L0,160 Z" fill="url(#ch1)" />
                  <path d="M0,130 L25,128 L50,120 L75,115 L100,100 L125,85 L150,72 L175,68 L200,75 L225,82 L250,88 L275,72 L300,60 L325,55 L350,50 L375,42 L400,38 L425,45 L450,55 L475,65 L500,52 L525,48 L550,42 L575,35 L600,30" fill="none" stroke="#1976d2" strokeWidth="2" />
                  <g fontFamily="Pretendard" fontSize="10" fill="#9e9e9e">
                    <text x="0" y="155">
                      00:00
                    </text>
                    <text x="200" y="155">
                      08:00
                    </text>
                    <text x="400" y="155">
                      16:00
                    </text>
                    <text x="572" y="155">
                      now
                    </text>
                  </g>
                </svg>
              </div>
            </div>
            <div className="chart-card">
              <h3>
                큐 길이 추이
              </h3>
              <div className="chart-area">
                <svg viewBox="0 0 300 160" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                  <g stroke="#e0e0e0" strokeWidth="1">
                    <line x1="0" y1="40" x2="300" y2="40" />
                    <line x1="0" y1="80" x2="300" y2="80" />
                    <line x1="0" y1="120" x2="300" y2="120" />
                  </g>
                  <path d="M0,110 L20,105 L40,98 L60,85 L80,90 L100,75 L120,68 L140,72 L160,60 L180,55 L200,62 L220,72 L240,68 L260,55 L280,52 L300,60" fill="none" stroke="#9747ff" strokeWidth="2" />
                  <line x1="0" y1="45" x2="300" y2="45" stroke="#d32f2f" strokeWidth="1" strokeDasharray="4 4" />
                  <text x="305" y="48" fontFamily="Pretendard" fontSize="9" fill="#d32f2f">
                    알림 임계 100
                  </text>
                </svg>
              </div>
            </div>
          </div>
          <div className="lower">
            <div className="adm-card">
              <div className="head">
                <h3>
                  현재 처리 중 작업 — 35건
                </h3>
                <span className="mui-chip mui-chip--soft-info">
                  Free 24
                </span>
                <span className="mui-chip mui-chip--soft-warning">
                  Pro 9
                </span>
                <span className="mui-chip mui-chip--secondary">
                  Studio 2
                </span>
              </div>
              <div className="job-row head">
                <span>
                  작업 ID
                </span>
                <span>
                  파일
                </span>
                <span>
                  플랜
                </span>
                <span>
                  진행률
                </span>
                <span>
                  경과
                </span>
                <span>
                </span>
              </div>
              <div className="job-row">
                <span className="jid">
                  j_8e4f...a23
                </span>
                <div className="file">
                  family_picnic_2026.mp4
                  <small>
                    2분 14초 · 17건 처리
                  </small>
                </div>
                <span>
                  <span className="mui-chip mui-chip--md">
                    Free
                  </span>
                </span>
                <div>
                  <div className="progress-mini">
                    <div style={{ width: "64%" }}>
                    </div>
                  </div>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    64%
                  </span>
                </div>
                <span className="caption-k">
                  0:52
                </span>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  ⋯
                </button>
              </div>
              <div className="job-row">
                <span className="jid">
                  j_2c1a...b87
                </span>
                <div className="file">
                  vlog_episode_12.mp4
                  <small>
                    8분 04초 · 41건 처리
                  </small>
                </div>
                <span>
                  <span className="mui-chip mui-chip--soft-warning mui-chip--md">
                    Pro
                  </span>
                </span>
                <div>
                  <div className="progress-mini">
                    <div style={{ width: "82%", background: "#9747ff" }}>
                    </div>
                  </div>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    82% · 우선
                  </span>
                </div>
                <span className="caption-k">
                  2:14
                </span>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  ⋯
                </button>
              </div>
              <div className="job-row">
                <span className="jid">
                  j_5f9b...c44
                </span>
                <div className="file">
                  interview_recording.mp3
                  <small>
                    5분 22초 · 8건
                  </small>
                </div>
                <span>
                  <span className="mui-chip mui-chip--md">
                    Free
                  </span>
                </span>
                <div>
                  <div className="progress-mini">
                    <div style={{ width: "32%" }}>
                    </div>
                  </div>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    32%
                  </span>
                </div>
                <span className="caption-k">
                  0:28
                </span>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  ⋯
                </button>
              </div>
              <div className="job-row">
                <span className="jid">
                  j_9a3e...f72
                </span>
                <div className="file">
                  2026_summer_album/ · 32 photos
                  <small>
                    일괄 처리 (Studio)
                  </small>
                </div>
                <span>
                  <span className="mui-chip mui-chip--secondary mui-chip--md">
                    Studio
                  </span>
                </span>
                <div>
                  <div className="progress-mini">
                    <div style={{ width: "47%", background: "#9747ff" }}>
                    </div>
                  </div>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    47% · 우선
                  </span>
                </div>
                <span className="caption-k">
                  3:42
                </span>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  ⋯
                </button>
              </div>
              <div className="job-row">
                <span className="jid">
                  j_4d7c...e91
                </span>
                <div className="file">
                  cafe_video.mp4
                  <small>
                    1분 02초 · 4건
                  </small>
                </div>
                <span>
                  <span className="mui-chip mui-chip--md">
                    Free
                  </span>
                </span>
                <div>
                  <div className="progress-mini">
                    <div style={{ width: "8%" }}>
                    </div>
                  </div>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    8%
                  </span>
                </div>
                <span className="caption-k">
                  0:04
                </span>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  ⋯
                </button>
              </div>
              <div style={{ padding: "10px 16px", textAlign: "center", color: "var(--fg-2)", font: "400 12px var(--font-sans)" }}>
                … 30건 더 보기
              </div>
            </div>
            <div className="adm-card">
              <div className="head">
                <h3>
                  GPU 워커 상태
                </h3>
                <span className="caption-k" style={{ fontSize: "11px" }}>
                  12 / 16 활성
                </span>
              </div>
              <div className="gpu-grid">
                <div className="gpu-card">
                  <h4>
                    <span className="material-icons" style={{ fontSize: "14px", color: "#2e7d32" }}>
                      memory
                    </span>
                    worker-01 · A100
                  </h4>
                  <div className="util">
                    68
                    <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                      %
                    </small>
                  </div>
                  <div className="util-bar">
                    <div style={{ width: "68%" }}>
                    </div>
                  </div>
                  <div className="stat-row" style={{ marginTop: "6px" }}>
                    <span>
                      32 GB / 40
                    </span>
                    <span>
                      72°C
                    </span>
                  </div>
                </div>
                <div className="gpu-card">
                  <h4>
                    <span className="material-icons" style={{ fontSize: "14px", color: "#2e7d32" }}>
                      memory
                    </span>
                    worker-02 · A100
                  </h4>
                  <div className="util">
                    71
                    <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                      %
                    </small>
                  </div>
                  <div className="util-bar">
                    <div style={{ width: "71%" }}>
                    </div>
                  </div>
                  <div className="stat-row" style={{ marginTop: "6px" }}>
                    <span>
                      34 GB / 40
                    </span>
                    <span>
                      74°C
                    </span>
                  </div>
                </div>
                <div className="gpu-card alert">
                  <h4>
                    <span className="material-icons" style={{ fontSize: "14px", color: "#d32f2f" }}>
                      warning
                    </span>
                    worker-03 · A100
                  </h4>
                  <div className="util err">
                    96
                    <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                      %
                    </small>
                  </div>
                  <div className="util-bar">
                    <div style={{ width: "96%" }}>
                    </div>
                  </div>
                  <div className="stat-row" style={{ marginTop: "6px" }}>
                    <span style={{ color: "#d32f2f" }}>
                      38 GB / 40
                    </span>
                    <span style={{ color: "#d32f2f" }}>
                      86°C
                    </span>
                  </div>
                </div>
                <div className="gpu-card">
                  <h4>
                    <span className="material-icons" style={{ fontSize: "14px", color: "#2e7d32" }}>
                      memory
                    </span>
                    worker-04 · A100
                  </h4>
                  <div className="util warn">
                    85
                    <small style={{ fontSize: "12px", color: "var(--fg-2)" }}>
                      %
                    </small>
                  </div>
                  <div className="util-bar">
                    <div style={{ width: "85%" }}>
                    </div>
                  </div>
                  <div className="stat-row" style={{ marginTop: "6px" }}>
                    <span>
                      36 GB / 40
                    </span>
                    <span>
                      78°C
                    </span>
                  </div>
                </div>
              </div>
              <div style={{ padding: "8px 16px", textAlign: "center", color: "var(--fg-2)", font: "400 11px var(--font-sans)" }}>
                … 8개 워커 더 · 4개 idle
              </div>
            </div>
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
