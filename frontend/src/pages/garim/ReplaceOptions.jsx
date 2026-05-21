import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/ReplaceOptions.css";

import GarimPage from "../../components/garim/GarimPage";

export default function ReplaceOptions() {
  useDocumentTitle("치환 옵션 설정 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="15 Replacement options">
      <div className="opt-page">
        <div className="opt-toolbar">
          <a href="/analysis-report" className="gh__icon" style={{ marginLeft: "-8px" }}>
            <span className="material-icons">
              arrow_back
            </span>
          </a>
          <h1>
            치환 옵션 설정
          </h1>
          <span className="meta">
            family_picnic_2026.mp4 · 17건
          </span>
          <button className="mui-btn mui-btn--text">
            임시 저장
          </button>
        </div>
        <div className="opt-grid">
          <div className="opt-left">
            <div className="player-wrap">
              <div className="player-box">
                <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=1200&amp;q=80" alt="" />
                <svg viewBox="0 0 1200 675" preserveAspectRatio="none" style={{ position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" }}>
                  <rect x="420" y="180" width="220" height="220" fill="none" stroke="#1976d2" strokeWidth="4" rx="2" strokeDasharray="0" />
                  <rect x="418" y="158" width="200" height="24" fill="#1976d2" />
                  <text x="425" y="175" fill="#fff" fontFamily="Pretendard, sans-serif" fontSize="13" fontWeight="500">
                    선택됨 · 택배 송장 · 자동
                  </text>
                  <rect x="700" y="240" width="140" height="160" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeDasharray="6 4" />
                  <rect x="120" y="450" width="180" height="100" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeDasharray="6 4" />
                </svg>
              </div>
            </div>
            <div className="player-ctrls">
              <button>
                <span className="material-icons">
                  play_arrow
                </span>
              </button>
              <span className="time">
                00:11 / 02:14
              </span>
              <div className="timeline">
                <div className="timeline__fill" style={{ height: "100%", position: "absolute", top: "0", left: "0", borderRadius: "3px" }}>
                </div>
                <div className="timeline__marker" style={{ left: "8%" }}>
                </div>
                <div className="timeline__marker timeline__marker--warning" style={{ left: "22%" }}>
                </div>
                <div className="timeline__marker timeline__marker--warning" style={{ left: "35%" }}>
                </div>
                <div className="timeline__marker" style={{ left: "42%" }}>
                </div>
                <div className="timeline__marker" style={{ left: "58%" }}>
                </div>
                <div className="timeline__marker timeline__marker--info" style={{ left: "71%" }}>
                </div>
                <div className="timeline__marker timeline__marker--warning" style={{ left: "86%" }}>
                </div>
              </div>
              <button>
                <span className="material-icons">
                  fullscreen
                </span>
              </button>
            </div>
          </div>
          <aside className="opt-right">
            <div className="head">
              <h2>
                17건의 검출 항목
              </h2>
              <div className="sub">
                각 항목에 처리 방식을 선택하세요. 항목을 클릭하면 영상이 해당 시점으로 이동합니다.
              </div>
            </div>
            <div className="bulk">
              <span className="label">
                일괄 설정:
              </span>
              <button className="active">
                자동 치환
              </button>
              <button>
                마스킹
              </button>
              <button>
                건너뛰기
              </button>
            </div>
            <div className="opt-list">
              <div className="opt-card selected" data-card="1">
                <div className="opt-card__head">
                  <div className="thumb">
                    <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=200&amp;q=60" alt="" />
                  </div>
                  <div className="info">
                    <div className="opt-card__time">
                      00:11
                    </div>
                    <div className="opt-card__title">
                      택배 송장 — 박OO 님, 강남구...
                    </div>
                  </div>
                  <span className="mui-chip mui-chip--error risk">
                    8.4
                  </span>
                </div>
                <div className="opt-card__methods">
                  <div className="method-pill selected">
                    <span className="material-icons">
                      auto_awesome
                    </span>
                    자동
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      edit
                    </span>
                    지정
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      blur_on
                    </span>
                    마스킹
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      visibility_off
                    </span>
                    건너뛰기
                  </div>
                </div>
                <div style={{ marginTop: "8px", padding: "8px 10px", background: "rgba(25,118,210,0.04)", borderRadius: "2px", font: "400 11px/1.5 var(--font-sans)", color: "var(--fg-2)" }}>
                  <span className="material-icons" style={{ fontSize: "14px", verticalAlign: "-2px" }}>
                    info
                  </span>
                  LLM이 형식 정보만 받아 가짜 송장 정보를 생성합니다. 원본은 전송되지 않습니다.
                </div>
              </div>
              <div className="opt-card" data-card="2">
                <div className="opt-card__head">
                  <div className="thumb" style={{ background: "linear-gradient(45deg,#424242,#212121)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span className="material-icons" style={{ color: "#fff", fontSize: "24px" }}>
                      directions_car
                    </span>
                  </div>
                  <div className="info">
                    <div className="opt-card__time">
                      00:31
                    </div>
                    <div className="opt-card__title">
                      차량 번호판 — "12가 3456"
                    </div>
                  </div>
                  <span className="mui-chip mui-chip--error risk">
                    7.2
                  </span>
                </div>
                <div className="opt-card__methods">
                  <div className="method-pill">
                    <span className="material-icons">
                      auto_awesome
                    </span>
                    자동
                  </div>
                  <div className="method-pill selected">
                    <span className="material-icons">
                      edit
                    </span>
                    지정
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      blur_on
                    </span>
                    마스킹
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      visibility_off
                    </span>
                    건너뛰기
                  </div>
                </div>
                <div className="opt-card__custom">
                  <input value="98나 7777" maxLength="7" />
                  <div className="helper">
                    <span>
                      한국식 7자리 (원본과 동일 길이 필수)
                    </span>
                    <span className="count">
                      7/7 ✓
                    </span>
                  </div>
                </div>
              </div>
              <div className="opt-card" data-card="3">
                <div className="opt-card__head">
                  <div className="thumb">
                    <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=200&amp;q=60" alt="" />
                  </div>
                  <div className="info">
                    <div className="opt-card__time">
                      00:47
                    </div>
                    <div className="opt-card__title">
                      얼굴 — 미등록 인물 3명
                    </div>
                  </div>
                  <span className="mui-chip mui-chip--warning risk">
                    6.1
                  </span>
                </div>
                <div className="opt-card__methods">
                  <div className="method-pill">
                    <span className="material-icons">
                      auto_awesome
                    </span>
                    자동
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      edit
                    </span>
                    지정
                  </div>
                  <div className="method-pill selected">
                    <span className="material-icons">
                      blur_on
                    </span>
                    마스킹
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      visibility_off
                    </span>
                    건너뛰기
                  </div>
                </div>
                <div className="opt-card__mask">
                  <span className="lbl">
                    강도
                  </span>
                  <div className="slider">
                    <div className="fill" style={{ width: "65%" }}>
                    </div>
                    <div className="knob" style={{ left: "65%" }}>
                    </div>
                  </div>
                  <span className="lbl">
                    중
                  </span>
                </div>
              </div>
              <div className="opt-card" data-card="4">
                <div className="opt-card__head">
                  <div className="thumb" style={{ background: "linear-gradient(135deg,#9c27b0,#7b1fa2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span className="material-icons" style={{ color: "#fff", fontSize: "24px" }}>
                      graphic_eq
                    </span>
                  </div>
                  <div className="info">
                    <div className="opt-card__time">
                      01:08
                    </div>
                    <div className="opt-card__title">
                      음성 호칭 — "수민아!"
                    </div>
                  </div>
                  <span className="mui-chip mui-chip--warning risk">
                    5.8
                  </span>
                </div>
                <div className="opt-card__methods">
                  <div className="method-pill">
                    <span className="material-icons">
                      auto_awesome
                    </span>
                    자동
                  </div>
                  <div className="method-pill selected">
                    <span className="material-icons">
                      edit
                    </span>
                    지정
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      volume_off
                    </span>
                    음소거
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      visibility_off
                    </span>
                    건너뛰기
                  </div>
                </div>
                <div className="opt-card__custom">
                  <input className="err" value="민지야아아" maxLength="10" />
                  <div className="helper">
                    <span style={{ color: "#d32f2f" }}>
                      원본 "수민아!" 4자와 동일해야 합니다
                    </span>
                    <span className="count err">
                      5/4
                    </span>
                  </div>
                </div>
              </div>
              <div className="opt-card" data-card="5">
                <div className="opt-card__head">
                  <div className="thumb" style={{ background: "linear-gradient(135deg,#0288d1,#01579b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span className="material-icons" style={{ color: "#fff", fontSize: "24px" }}>
                      location_on
                    </span>
                  </div>
                  <div className="info">
                    <div className="opt-card__time">
                      EXIF
                    </div>
                    <div className="opt-card__title">
                      EXIF GPS — 좌표 정보
                    </div>
                  </div>
                  <span className="mui-chip mui-chip--info risk">
                    4.2
                  </span>
                </div>
                <div className="opt-card__methods">
                  <div className="method-pill selected">
                    <span className="material-icons">
                      delete
                    </span>
                    제거
                  </div>
                  <div className="method-pill">
                    <span className="material-icons">
                      edit
                    </span>
                    변경
                  </div>
                  <div className="method-pill" style={{ gridColumn: "span 2", opacity: "0.5" }}>
                    <span className="material-icons">
                      visibility_off
                    </span>
                    건너뛰기 (권장 안 함)
                  </div>
                </div>
              </div>
              <div style={{ padding: "12px 8px", textAlign: "center", font: "400 12px var(--font-sans)", color: "var(--fg-3)" }}>
                … 12개 항목 더 보기
              </div>
            </div>
            <div className="global-opts">
              <h3>
                전체 옵션
              </h3>
              <div className="row">
                <span className="lbl">
                  음성 마스킹 방식
                </span>
                <div className="seg">
                  <button className="active">
                    삐 1000Hz
                  </button>
                  <button>
                    묵음
                  </button>
                </div>
              </div>
              <div className="row">
                <span className="lbl">
                  얼굴 마스킹 (전체 적용)
                </span>
                <div className="seg">
                  <button className="active">
                    블러
                  </button>
                  <button>
                    모자이크
                  </button>
                  <button>
                    없음
                  </button>
                </div>
              </div>
              <div className="row v2">
                <span className="lbl">
                  본인 얼굴 화이트리스트
                </span>
                <span className="mui-chip">
                  v2 예정
                </span>
              </div>
            </div>
            <div className="watermark-pill">
              <span className="material-icons">
                verified
              </span>
              <span>
                <strong style={{ color: "#9747ff", fontWeight: "600" }}>
                  워터마크 자동 적용 (MVP1)
                </strong>
                · 결과 영상 우하단에 작은 식별 워터마크가 표시됩니다 (B-3 정책).
              </span>
            </div>
          </aside>
        </div>
        <div className="opt-footer">
          <div className="est">
            예상 처리 시간
            <strong>
              약 1분 24초
            </strong>
            · 자동 9건 · 지정 3건 · 마스킹 4건 · 건너뛰기 1건
          </div>
          <a href="/analysis-report" className="mui-btn mui-btn--text">
            취소
          </a>
          <a href="/preview" className="mui-btn mui-btn--contained mui-btn--lg">
            <span className="material-icons" style={{ fontSize: "20px" }}>
              visibility
            </span>
            미리보기 생성
          </a>
        </div>
      </div>
    </GarimPage>
  );
}
