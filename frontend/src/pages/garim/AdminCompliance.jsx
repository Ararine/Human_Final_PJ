import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminCompliance.css";

import GarimPage from "../../components/garim/GarimPage";

export default function AdminCompliance() {
  useDocumentTitle("컴플라이언스 로그·감사 · Garim Admin");

  return (
    <GarimPage bodyClass="" screenLabel="27 Admin compliance">
      <div className="adm-shell">
        <aside className="adm-side">
          <div className="sec">
            운영
          </div>
          <a href="/admin/monitoring">
            <span className="material-icons">
              monitor_heart
            </span>
            사용자 모니터링
          </a>
          <a href="/admin/queue">
            <span className="material-icons">
              queue
            </span>
            처리 큐
          </a>
          <a href="/admin/compliance" className="active">
            <span className="material-icons">
              verified_user
            </span>
            컴플라이언스
          </a>
          <div className="sec">
            시스템
          </div>
          <a href="/admin/users">
            <span className="material-icons">
              people
            </span>
            사용자
          </a>
          <a href="/admin/analytics">
            <span className="material-icons">
              analytics
            </span>
            분석
          </a>
          <a href="/admin/policy">
            <span className="material-icons">
              tune
            </span>
            정책 및 상품 관리
          </a>
          <a href="/admin/payments">
            <span className="material-icons">
              payments
            </span>
            사용자 결제 확인
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>
              컴플라이언스 로그·감사
            </h1>
            <span className="caption-k">
              B-1 자동 삭제 · B-3 워터마크 역추적 · 약관 동의 이력 · 외부 요청 응답
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>
                  file_download
                </span>
                CSV Export
              </button>
            </div>
          </div>
          <div className="tabs-bar">
            <button className="tab-btn active" data-tab="auto">
              <span className="material-icons">
                auto_delete
              </span>
              자동 삭제 모니터
            </button>
            <button className="tab-btn" data-tab="search">
              <span className="material-icons">
                search
              </span>
              처리 이력 검색
            </button>
            <button className="tab-btn" data-tab="consent">
              <span className="material-icons">
                checklist
              </span>
              약관 동의 이력
            </button>
            <button className="tab-btn" data-tab="report">
              <span className="material-icons">
                gavel
              </span>
              신고·수사 응답
            </button>
          </div>
          <div className="panel active" id="panel-auto">
            <div className="compliance-row">
              <div className="adm-card">
                <div className="head">
                  <h3>
                    데이터 종류별 보존·삭제 정책 (B-1)
                  </h3>
                </div>
                <div className="policy-row tbl-head">
                  <span>
                    데이터 종류
                  </span>
                  <span>
                    보존 정책
                  </span>
                  <span>
                    현재 잔존
                  </span>
                  <span>
                    준수율
                  </span>
                </div>
                <div className="policy-row">
                  <div>
                    <div className="data-type">
                      업로드 원본 파일
                    </div>
                    <div className="caption-k" style={{ fontSize: "11px" }}>
                      모든 플랜 공통
                    </div>
                  </div>
                  <div className="policy">
                    처리 후 12h
                  </div>
                  <div>
                    847개
                  </div>
                  <div>
                    <span className="compliance-pill ok">
                      <span className="material-icons" style={{ fontSize: "14px" }}>
                        check
                      </span>
                      100.0%
                    </span>
                  </div>
                </div>
                <div className="policy-row">
                  <div>
                    <div className="data-type">
                      치환 결과 파일 (Free)
                    </div>
                    <div className="caption-k" style={{ fontSize: "11px" }}>
                      Free 플랜
                    </div>
                  </div>
                  <div className="policy">
                    7일
                  </div>
                  <div>
                    14,228개
                  </div>
                  <div>
                    <span className="compliance-pill ok">
                      <span className="material-icons" style={{ fontSize: "14px" }}>
                        check
                      </span>
                      100.0%
                    </span>
                  </div>
                </div>
                <div className="policy-row">
                  <div>
                    <div className="data-type">
                      치환 결과 파일 (1회권)
                    </div>
                    <div className="caption-k" style={{ fontSize: "11px" }}>
                      v1 정식 출시 후
                    </div>
                  </div>
                  <div className="policy">
                    30일
                  </div>
                  <div>
                    —
                  </div>
                  <div>
                    <span className="compliance-pill ok">
                      N/A
                    </span>
                  </div>
                </div>
                <div className="policy-row">
                  <div>
                    <div className="data-type">
                      처리 이력 메타데이터
                    </div>
                    <div className="caption-k" style={{ fontSize: "11px" }}>
                      워터마크 역추적용
                    </div>
                  </div>
                  <div className="policy">
                    90일
                  </div>
                  <div>
                    342,108개
                  </div>
                  <div>
                    <span className="compliance-pill warn">
                      <span className="material-icons" style={{ fontSize: "14px" }}>
                        warning
                      </span>
                      99.4%
                    </span>
                  </div>
                </div>
                <div className="policy-row" style={{ borderBottom: "none" }}>
                  <div>
                    <div className="data-type">
                      탈퇴 회원 식별 정보
                    </div>
                    <div className="caption-k" style={{ fontSize: "11px" }}>
                      7일 유예 후 영구 삭제
                    </div>
                  </div>
                  <div className="policy">
                    탈퇴 + 7d
                  </div>
                  <div>
                    12개 (유예 중)
                  </div>
                  <div>
                    <span className="compliance-pill ok">
                      <span className="material-icons" style={{ fontSize: "14px" }}>
                        check
                      </span>
                      100.0%
                    </span>
                  </div>
                </div>
              </div>
              <div className="adm-card">
                <div className="head">
                  <h3>
                    24시간 내 삭제 예정 데이터
                  </h3>
                </div>
                <div className="body">
                  <div className="donut-mini">
                    <svg viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#e0e0e0" strokeWidth="14" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#ed6c02" strokeWidth="14" strokeDasharray="138 251" transform="rotate(-90 50 50)" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#9747ff" strokeWidth="14" strokeDasharray="78 251" strokeDashoffset="-138" transform="rotate(-90 50 50)" />
                      <text x="50" y="48" textAnchor="middle" fontFamily="Pretendard" fontSize="15" fontWeight="500" fill="#212121">
                        2,847
                      </text>
                      <text x="50" y="62" textAnchor="middle" fontFamily="Pretendard" fontSize="8" fill="#757575">
                        건
                      </text>
                    </svg>
                    <div className="legend">
                      <div className="row">
                        <span className="dot" style={{ background: "#ed6c02" }}>
                        </span>
                        원본 (12h) — 1,567개
                      </div>
                      <div className="row">
                        <span className="dot" style={{ background: "#9747ff" }}>
                        </span>
                        결과 (7d) — 892개
                      </div>
                      <div className="row">
                        <span className="dot" style={{ background: "#0288d1" }}>
                        </span>
                        메타 (90d) — 388개
                      </div>
                    </div>
                  </div>
                  <hr style={{ margin: "16px 0", border: "none", borderTop: "1px dashed var(--mui-divider)" }} />
                  <div style={{ font: "400 12px/1.5 var(--font-sans)", color: "var(--fg-2)" }}>
                    자동 삭제 잡은 매 시간 정각에 실행됩니다. 다음 실행:
                    <strong style={{ color: "#1976d2" }}>
                      15:00
                    </strong>
                    (12분 후)
                  </div>
                </div>
              </div>
            </div>
            <div className="adm-card">
              <div className="head">
                <h3>
                  최근 자동 삭제 로그
                </h3>
                <span className="caption-k">
                  최근 24시간
                </span>
              </div>
              <div style={{ padding: "8px 18px", font: "400 12px/1.8 var(--font-sans)", fontFamily: "var(--font-mono)", color: "var(--fg-2)" }}>
                <div>
                  <span style={{ color: "var(--fg-3)" }}>
                    14:00:01
                  </span>
                  [auto-delete] 결과 파일 124개 삭제 (Free 7d 정책)
                  <span style={{ color: "#2e7d32" }}>
                    ✓
                  </span>
                </div>
                <div>
                  <span style={{ color: "var(--fg-3)" }}>
                    14:00:00
                  </span>
                  [auto-delete] 원본 파일 287개 삭제 (12h 정책)
                  <span style={{ color: "#2e7d32" }}>
                    ✓
                  </span>
                </div>
                <div>
                  <span style={{ color: "var(--fg-3)" }}>
                    13:00:02
                  </span>
                  [auto-delete] 메타데이터 58개 삭제 (90d 정책)
                  <span style={{ color: "#2e7d32" }}>
                    ✓
                  </span>
                </div>
                <div>
                  <span style={{ color: "var(--fg-3)" }}>
                    13:00:00
                  </span>
                  [auto-delete] 원본 파일 312개 삭제 (12h 정책)
                  <span style={{ color: "#2e7d32" }}>
                    ✓
                  </span>
                </div>
                <div>
                  <span style={{ color: "#d32f2f" }}>
                    12:00:04
                  </span>
                  [auto-delete] 메타데이터 1개 삭제 실패 — DB lock contention (재시도 큐로)
                </div>
                <div>
                  <span style={{ color: "var(--fg-3)" }}>
                    12:00:00
                  </span>
                  [auto-delete] 원본 파일 245개 삭제 (12h 정책)
                  <span style={{ color: "#2e7d32" }}>
                    ✓
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="panel" id="panel-search">
            <div className="search-block">
              <h3>
                처리 이력 검색
              </h3>
              <div className="search-tabs">
                <button className="active">
                  사용자 ID로
                </button>
                <button>
                  워터마크 해시로
                </button>
                <button>
                  처리 ID로
                </button>
              </div>
              <div className="search-row">
                <input value="wm_3f4a8b21c9e74a82_5f9b" placeholder="해시값 또는 ID 입력" />
                <button className="mui-btn mui-btn--contained">
                  검색
                </button>
              </div>
              <div className="caption-k" style={{ fontSize: "11px", marginTop: "8px" }}>
                평문 사용자 ID를 입력하면 자동으로 해시화됩니다. 모든 검색은 감사 로그에 기록됩니다.
              </div>
            </div>
            <div className="result-grid">
              <div className="meta-card">
                <h3>
                  처리 이력 메타데이터
                </h3>
                <div className="meta-row">
                  <span className="k">
                    처리 ID
                  </span>
                  <span className="v">
                    j_5f9b1c8e4f2a3b87
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    사용자 (해시)
                  </span>
                  <span className="v">
                    u_3f4a8b21c9e74a82
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    처리 시점
                  </span>
                  <span className="v">
                    2026.04.21 13:42:18
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    파일 유형
                  </span>
                  <span className="v">
                    video/mp4
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    파일 크기
                  </span>
                  <span className="v">
                    847 MB
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    영상 길이
                  </span>
                  <span className="v">
                    00:02:14
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    해상도
                  </span>
                  <span className="v">
                    1920×1080
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    검출 건수
                  </span>
                  <span className="v">
                    17
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    치환 완료
                  </span>
                  <span className="v">
                    16 (건너뛰기 1)
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    워터마크 해시
                  </span>
                  <span className="v">
                    wm_3f4a8b21..._5f9b
                  </span>
                </div>
              </div>
              <div className="meta-card">
                <h3>
                  처리 옵션 (메타데이터)
                </h3>
                <div className="meta-row">
                  <span className="k">
                    자동 치환
                  </span>
                  <span className="v">
                    9건
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    사용자 지정
                  </span>
                  <span className="v">
                    3건
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    마스킹
                  </span>
                  <span className="v">
                    4건 (블러 중)
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    건너뛰기
                  </span>
                  <span className="v">
                    1건 (EXIF 일부)
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    음성 마스킹
                  </span>
                  <span className="v">
                    삐 1000Hz
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    얼굴 마스킹
                  </span>
                  <span className="v">
                    블러
                  </span>
                </div>
                <div className="meta-row">
                  <span className="k">
                    학습 동의
                  </span>
                  <span className="v">
                    OFF
                  </span>
                </div>
                <div className="deleted-note">
                  <span className="material-icons">
                    visibility_off
                  </span>
                  <div>
                    <strong>
                      원본·결과 영상은 이미 자동 삭제되었습니다.
                    </strong>
                    <br />
                    메타데이터만 워터마크 역추적용으로 90일 보존됩니다 (B-1 정책).
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="panel" id="panel-consent">
            <div className="search-block">
              <h3>
                약관 동의 이력 조회
              </h3>
              <div className="search-row">
                <input value="u_3f4a8b21c9e74a82" placeholder="사용자 해시 입력" />
                <button className="mui-btn mui-btn--contained">
                  검색
                </button>
              </div>
            </div>
            <div className="adm-card">
              <div className="head">
                <h3>
                  u_3f4a8b21 · 동의 이력
                </h3>
              </div>
              <div style={{ padding: "8px 18px", font: "400 13px/1.8 var(--font-sans)" }}>
                <div style={{ display: "flex", gap: "16px", padding: "10px 0", borderBottom: "1px solid var(--mui-divider)" }}>
                  <span className="v" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--fg-2)", minWidth: "160px" }}>
                    2026.05.14 14:22
                  </span>
                  <span style={{ flex: "1" }}>
                    가입 · 필수 동의 + 마케팅 OFF + 학습 OFF (약관 버전 v1.0)
                  </span>
                </div>
                <div style={{ display: "flex", gap: "16px", padding: "10px 0", borderBottom: "1px solid var(--mui-divider)" }}>
                  <span className="v" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--fg-2)", minWidth: "160px" }}>
                    2026.05.14 14:24
                  </span>
                  <span style={{ flex: "1" }}>
                    마케팅 정보 수신 동의 →
                    <strong>
                      ON
                    </strong>
                    (소스: 가입 직후 안내)
                  </span>
                </div>
                <div style={{ display: "flex", gap: "16px", padding: "10px 0" }}>
                  <span className="v" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--fg-2)", minWidth: "160px" }}>
                    현재
                  </span>
                  <span style={{ flex: "1", color: "var(--fg-2)" }}>
                    변경 사항 없음. 학습 동의 OFF 유지 중.
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="panel" id="panel-report">
            <div className="adm-card" style={{ marginBottom: "16px" }}>
              <div className="head">
                <h3>
                  외부 요청 접수
                </h3>
                <span className="caption-k">
                  법원 명령·수사 협조·신고 등
                </span>
              </div>
              <div className="body">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                  <div className="set-field">
                    <label style={{ font: "500 12px var(--font-sans)", color: "var(--fg-2)", marginBottom: "4px", display: "block" }}>
                      요청 유형
                    </label>
                    <select style={{ padding: "10px", border: "1px solid var(--mui-border)", borderRadius: "4px", fontFamily: "var(--font-sans)" }}>
                      <option>
                        위변조 의심 신고
                      </option>
                      <option>
                        법원 명령
                      </option>
                      <option>
                        수사 협조 요청
                      </option>
                    </select>
                  </div>
                  <div className="set-field">
                    <label style={{ font: "500 12px var(--font-sans)", color: "var(--fg-2)", marginBottom: "4px", display: "block" }}>
                      워터마크 해시
                    </label>
                    <input style={{ padding: "10px", border: "1px solid var(--mui-border)", borderRadius: "4px", fontFamily: "var(--font-mono)" }} placeholder="wm_..." />
                  </div>
                </div>
                <button className="mui-btn mui-btn--contained">
                  처리 이력 조회 →
                </button>
              </div>
            </div>
            <div className="adm-card">
              <div className="head">
                <h3>
                  응답 이력 — 최근 30일
                </h3>
              </div>
              <div className="policy-row tbl-head" style={{ gridTemplateColumns: "130px 130px 1fr 100px 100px" }}>
                <span>
                  요청 일시
                </span>
                <span>
                  유형
                </span>
                <span>
                  대상 / 메모
                </span>
                <span>
                  처리자
                </span>
                <span>
                  상태
                </span>
              </div>
              <div className="policy-row" style={{ gridTemplateColumns: "130px 130px 1fr 100px 100px" }}>
                <span className="caption-k" style={{ fontFamily: "var(--font-mono)" }}>
                  2026.05.10
                </span>
                <span>
                  <span className="mui-chip mui-chip--soft-info" style={{ height: "20px", fontSize: "11px" }}>
                    위변조 신고
                  </span>
                </span>
                <span className="caption-k">
                  워터마크 wm_3f4a...5f9b 조회 — 처리 이력 확인 후 답변
                </span>
                <span className="caption-k">
                  법무팀 P
                </span>
                <span>
                  <span className="compliance-pill ok">
                    완료
                  </span>
                </span>
              </div>
              <div className="policy-row" style={{ gridTemplateColumns: "130px 130px 1fr 100px 100px" }}>
                <span className="caption-k" style={{ fontFamily: "var(--font-mono)" }}>
                  2026.05.03
                </span>
                <span>
                  <span className="mui-chip mui-chip--soft-warning" style={{ height: "20px", fontSize: "11px" }}>
                    법원 명령
                  </span>
                </span>
                <span className="caption-k">
                  서울중앙지법 · 처리 이력 제출 요구 (사건 2026가합1234)
                </span>
                <span className="caption-k">
                  법무팀 P
                </span>
                <span>
                  <span className="compliance-pill ok">
                    완료
                  </span>
                </span>
              </div>
              <div className="policy-row" style={{ gridTemplateColumns: "130px 130px 1fr 100px 100px", borderBottom: "none" }}>
                <span className="caption-k" style={{ fontFamily: "var(--font-mono)" }}>
                  2026.04.28
                </span>
                <span>
                  <span className="mui-chip mui-chip--soft-info" style={{ height: "20px", fontSize: "11px" }}>
                    위변조 신고
                  </span>
                </span>
                <span className="caption-k">
                  우리 영상이 도용됐다는 신고 — 메타데이터 보존 만료 (90일 경과)로 답변 불가
                </span>
                <span className="caption-k">
                  법무팀 P
                </span>
                <span>
                  <span className="compliance-pill warn">
                    불가
                  </span>
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
