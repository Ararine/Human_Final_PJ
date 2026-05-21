import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminAbuse.css";

import GarimPage from "../../components/garim/GarimPage";

export default function AdminAbuse() {
  useDocumentTitle("어뷰징 모니터링 · Garim Admin");

  return (
    <GarimPage bodyClass="" screenLabel="25 Admin abuse">
      <div className="adm-shell">
        <aside className="adm-side">
          <div className="sec">
            운영
          </div>
          <a href="/admin/abuse" className="active">
            <span className="material-icons">
              shield
            </span>
            어뷰징 모니터링
          </a>
          <a href="/admin/queue">
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
              어뷰징 모니터링
            </h1>
            <span className="meta">
              admin.garim.kr · 실시간 · 마지막 갱신 방금 전
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>
                  refresh
                </span>
                새로고침
              </button>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>
                  tune
                </span>
                임계값 설정
              </button>
            </div>
          </div>
          <div className="metric-row">
            <div className="metric danger">
              <div className="lbl">
                자동 차단 (24h)
              </div>
              <div className="num">
                128
              </div>
              <div className="delta">
                +34 (전일 대비 +36%)
              </div>
            </div>
            <div className="metric warn">
              <div className="lbl">
                수동 검토 대기
              </div>
              <div className="num">
                7
              </div>
              <div className="delta">
                평균 응답 12분
              </div>
            </div>
            <div className="metric">
              <div className="lbl">
                차단 해제 (7d)
              </div>
              <div className="num">
                42
              </div>
              <div className="delta">
                오탐률 24%
              </div>
            </div>
            <div className="metric">
              <div className="lbl">
                평균 트리거 점수
              </div>
              <div className="num">
                6.4
                <small style={{ fontSize: "14px", color: "var(--fg-2)" }}>
                  /10
                </small>
              </div>
              <div className="delta">
                정상 범위
              </div>
            </div>
          </div>
          <div className="adm-grid">
            <div className="adm-card">
              <div className="head">
                <h3>
                  의심 활동 — 최근 50건
                </h3>
                <span className="mui-chip mui-chip--soft-error">
                  자동 차단 12
                </span>
                <span className="mui-chip mui-chip--soft-warning">
                  검토 대기 7
                </span>
                <span className="mui-chip mui-chip--soft-info">
                  정상화 31
                </span>
                <div style={{ flex: "1" }}>
                </div>
                <button className="mui-btn mui-btn--text mui-btn--sm">
                  필터 ▾
                </button>
              </div>
              <div className="susp-row head">
                <span>
                </span>
                <span>
                  사용자 (해시)
                </span>
                <span>
                  IP
                </span>
                <span>
                  트리거
                </span>
                <span>
                  점수·시간
                </span>
                <span>
                  조치
                </span>
                <span>
                </span>
              </div>
              <div className="susp-row selected">
                <span className="severity-dot" style={{ background: "#d32f2f" }}>
                </span>
                <span className="uid">
                  u_3f4a8b21...
                </span>
                <span className="uid">
                  211.45.***
                </span>
                <span className="trigger">
                  rate_limit
                </span>
                <span>
                  <strong style={{ color: "#d32f2f" }}>
                    9.2
                  </strong>
                  · 2분 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    15초당 12회 시도
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-error" style={{ height: "20px", fontSize: "10px" }}>
                    자동 차단
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    상세 →
                  </button>
                </span>
              </div>
              <div className="susp-row">
                <span className="severity-dot" style={{ background: "#ed6c02" }}>
                </span>
                <span className="uid">
                  u_91c2e7f4...
                </span>
                <span className="uid">
                  110.45.***
                </span>
                <span className="trigger">
                  multi_account
                </span>
                <span>
                  <strong style={{ color: "#ed6c02" }}>
                    7.4
                  </strong>
                  · 8분 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    동일 디바이스 5계정
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-warning" style={{ height: "20px", fontSize: "10px" }}>
                    검토 대기
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    상세 →
                  </button>
                </span>
              </div>
              <div className="susp-row">
                <span className="severity-dot" style={{ background: "#ed6c02" }}>
                </span>
                <span className="uid">
                  u_a05e9c33...
                </span>
                <span className="uid">
                  175.118.***
                </span>
                <span className="trigger">
                  bot_signature
                </span>
                <span>
                  <strong style={{ color: "#ed6c02" }}>
                    7.0
                  </strong>
                  · 14분 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    User-Agent 누락
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-warning" style={{ height: "20px", fontSize: "10px" }}>
                    검토 대기
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    상세 →
                  </button>
                </span>
              </div>
              <div className="susp-row">
                <span className="severity-dot" style={{ background: "#d32f2f" }}>
                </span>
                <span className="uid">
                  u_5b9d12a8...
                </span>
                <span className="uid">
                  203.227.***
                </span>
                <span className="trigger">
                  concurrent_jobs
                </span>
                <span>
                  <strong style={{ color: "#d32f2f" }}>
                    8.6
                  </strong>
                  · 22분 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    동시 12건 업로드
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-error" style={{ height: "20px", fontSize: "10px" }}>
                    자동 차단
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    상세 →
                  </button>
                </span>
              </div>
              <div className="susp-row">
                <span className="severity-dot" style={{ background: "#ed6c02" }}>
                </span>
                <span className="uid">
                  u_2e7e1f99...
                </span>
                <span className="uid">
                  59.10.***
                </span>
                <span className="trigger">
                  repeat_pattern
                </span>
                <span>
                  <strong style={{ color: "#ed6c02" }}>
                    6.8
                  </strong>
                  · 31분 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    동일 해시 8회
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-warning" style={{ height: "20px", fontSize: "10px" }}>
                    검토 대기
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    상세 →
                  </button>
                </span>
              </div>
              <div className="susp-row">
                <span className="severity-dot" style={{ background: "#2e7d32" }}>
                </span>
                <span className="uid">
                  u_88a4b3c1...
                </span>
                <span className="uid">
                  121.190.***
                </span>
                <span className="trigger">
                  rate_limit
                </span>
                <span>
                  <strong>
                    4.2
                  </strong>
                  · 1시간 전
                  <div className="caption-k" style={{ fontSize: "11px" }}>
                    정상화 (해제됨)
                  </div>
                </span>
                <span className="action">
                  <span className="mui-chip mui-chip--soft-success" style={{ height: "20px", fontSize: "10px" }}>
                    정상
                  </span>
                </span>
                <span>
                  <button className="mui-btn mui-btn--text mui-btn--sm">
                    이력 →
                  </button>
                </span>
              </div>
              <div style={{ padding: "12px 16px", textAlign: "center", color: "var(--fg-2)", font: "400 12px var(--font-sans)" }}>
                … 44건 더 보기
              </div>
            </div>
            <aside className="adm-card">
              <div className="head">
                <h3>
                  활동 상세 — u_3f4a8b21
                </h3>
                <span className="mui-chip mui-chip--soft-error">
                  자동 차단됨
                </span>
              </div>
              <div className="log-detail">
                <h4>
                  식별 정보
                </h4>
                <div className="meta-row">
                  <span className="k">
                    사용자 해시
                  </span>
                  <span className="v">
                    u_3f4a8b21c9e74a82
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    디바이스 핑거
                  </span>
                  <span className="v">
                    d_91e2f3a4b5
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    IP
                  </span>
                  <span className="v">
                    211.45.***.***
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    국가
                  </span>
                  <span className="v">
                    KR · 서울
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    User-Agent
                  </span>
                  <span className="v" style={{ fontSize: "11px" }}>
                    curl/7.88.1
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    계정 생성
                  </span>
                  <span className="v">
                    8분 전
                  </span>
                </div>
                <h4 style={{ marginTop: "16px" }}>
                  트리거된 룰
                </h4>
                <div className="meta-row">
                  <span className="k">
                    룰 ID
                  </span>
                  <span className="v">
                    rate_limit_v2.1
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    임계값
                  </span>
                  <span className="v">
                    10회/60초
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    실측
                  </span>
                  <span className="v" style={{ color: "#d32f2f" }}>
                    12회/15초
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    자동 조치
                  </span>
                  <span className="v">
                    30분 차단
                  </span>
                </div>
                <h4 style={{ marginTop: "16px" }}>
                  최근 15분 로그
                </h4>
                <div className="timeline-log">
                  <div>
                    <span className="ts">
                      14:42:18
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:19
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:20
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:21
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:22
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:23
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:24
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:25
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:26
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:27
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:28
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div>
                    <span className="ts">
                      14:42:29
                    </span>
                    POST /api/upload → 200
                  </div>
                  <div className="err">
                    <span className="ts">
                      14:42:30
                    </span>
                    → AUTOBLOCK rate_limit_v2.1 (12/15s)
                  </div>
                  <div>
                    <span className="ts">
                      14:42:31
                    </span>
                    GET /api/me → 429
                  </div>
                </div>
                <h4 style={{ marginTop: "8px" }}>
                  관리자 액션
                </h4>
                <textarea className="reason-input" placeholder="조치 사유를 입력하세요 (감사 로그에 기록)">
                </textarea>
                <div className="reason-actions">
                  <button className="mui-btn mui-btn--outlined" style={{ flex: "1", color: "#2e7d32", borderColor: "rgba(46,125,50,0.5)" }}>
                    차단 해제
                  </button>
                  <button className="mui-btn mui-btn--outlined" style={{ flex: "1", color: "#ed6c02", borderColor: "rgba(237,108,2,0.5)" }}>
                    잠금 연장
                  </button>
                  <button className="mui-btn mui-btn--contained" style={{ flex: "1", background: "#d32f2f" }}>
                    영구 차단
                  </button>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
