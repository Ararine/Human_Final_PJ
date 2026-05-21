import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Preview.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Preview() {
  useDocumentTitle("처리 전 미리보기 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="16 Preview">
      <div className="pv-page">
        <div className="pv-toolbar">
          <a href="/replace-options" className="gh__icon" style={{ marginLeft: "-8px" }}>
            <span className="material-icons">
              arrow_back
            </span>
          </a>
          <h1>
            처리 전 미리보기
          </h1>
          <span className="meta">
            family_picnic_2026.mp4 · 17건 처리
          </span>
          <span className="mui-chip mui-chip--soft-info mui-chip--md">
            샘플 프레임 · 본 처리는 영상 전체에 적용
          </span>
        </div>
        <div className="pv-grid">
          <div className="pv-left">
            <div className="ba-compare" id="compare">
              <div className="layer before">
                <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=1200&amp;q=80" alt="원본" />
                <svg viewBox="0 0 1200 675" preserveAspectRatio="none" style={{ position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" }}>
                  <rect x="420" y="180" width="220" height="220" fill="none" stroke="#d32f2f" strokeWidth="3" strokeDasharray="8 4" rx="2" />
                  <rect x="700" y="240" width="140" height="160" fill="none" stroke="#ed6c02" strokeWidth="3" strokeDasharray="8 4" rx="2" />
                </svg>
              </div>
              <div className="layer after">
                <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=1200&amp;q=80" alt="처리 후" style={{ filter: "contrast(1.02)" }} />
                <svg viewBox="0 0 1200 675" preserveAspectRatio="none" style={{ position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" }}>
                  <rect x="420" y="180" width="220" height="220" fill="#fafafa" />
                  <rect x="420" y="180" width="220" height="220" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                  <text x="436" y="220" fill="#212121" fontFamily="Pretendard" fontSize="14" fontWeight="600">
                    CJ대한통운 송장
                  </text>
                  <text x="436" y="245" fill="#757575" fontFamily="Pretendard" fontSize="12">
                    받는분: 김OO 님
                  </text>
                  <text x="436" y="265" fill="#757575" fontFamily="Pretendard" fontSize="12">
                    서울특별시 ○○구
                  </text>
                  <text x="436" y="285" fill="#757575" fontFamily="Pretendard" fontSize="12">
                    010-****-****
                  </text>
                  <text x="436" y="318" fill="#9e9e9e" fontFamily="monospace" fontSize="10">
                    ‖‖‖ ‖‖ ‖‖‖‖ ‖‖‖
                  </text>
                  <rect x="700" y="240" width="140" height="160" fill="url(#blurp)" />
                  <defs>
                    <pattern id="blurp" patternunits="userSpaceOnUse" width="20" height="20">
                      <circle cx="10" cy="10" r="8" fill="rgba(189,189,189,0.7)" filter="blur(3px)" />
                    </pattern>
                    <filter id="blr">
                      <fegaussianblur stddeviation="10" />
                    </filter>
                  </defs>
                  <text x="1180" y="650" fill="rgba(151,71,255,0.55)" fontFamily="Pretendard" fontSize="14" fontWeight="600" textAnchor="end">
                    garim · 워터마크
                  </text>
                </svg>
              </div>
              <div className="handle" id="handle" style={{ left: "50%" }}>
                <span className="grip" style={{ color: "var(--fg-1)" }}>
                  <span className="material-icons">
                    drag_handle
                  </span>
                </span>
              </div>
              <span className="badge before">
                원본
              </span>
              <span className="badge after">
                처리 후
              </span>
            </div>
            <div className="pv-mode">
              <button className="active" data-mode="slider">
                Before/After 슬라이더
              </button>
              <button data-mode="before">
                원본만
              </button>
              <button data-mode="after">
                처리 후만
              </button>
            </div>
          </div>
          <aside className="pv-right">
            <div className="head">
              <h2>
                이 결과 어떠세요?
              </h2>
              <div className="sub">
                아래에서 각 항목이 자연스러운지 확인하고, 어색하면 옵션을 수정해주세요.
              </div>
            </div>
            <div className="pv-summary">
              <span className="mui-chip mui-chip--soft-info">
                자동 9건
              </span>
              <span className="mui-chip mui-chip--soft-info">
                지정 3건
              </span>
              <span className="mui-chip mui-chip--soft-info">
                마스킹 4건
              </span>
              <span className="mui-chip">
                건너뛰기 1건
              </span>
            </div>
            <div className="item-list">
              <div className="pv-item">
                <div className="thumb">
                  <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=200&amp;q=60" alt="" />
                </div>
                <div className="body">
                  <div className="time">
                    00:11
                  </div>
                  <div className="title">
                    택배 송장 → 자동
                  </div>
                  <div className="change">
                    <s>
                      박OO · 강남구...
                    </s>
                    →
                    <strong>
                      김OO · ○○구...
                    </strong>
                  </div>
                </div>
              </div>
              <div className="pv-item">
                <div className="thumb" style={{ background: "linear-gradient(45deg,#424242,#212121)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-icons" style={{ color: "#fff", fontSize: "20px" }}>
                    directions_car
                  </span>
                </div>
                <div className="body">
                  <div className="time">
                    00:31
                  </div>
                  <div className="title">
                    번호판 → 지정
                  </div>
                  <div className="change">
                    <s>
                      12가 3456
                    </s>
                    →
                    <strong>
                      98나 7777
                    </strong>
                  </div>
                </div>
              </div>
              <div className="pv-item">
                <div className="thumb">
                  <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=200&amp;q=60" alt="" />
                </div>
                <div className="body">
                  <div className="time">
                    00:47
                  </div>
                  <div className="title">
                    얼굴 → 마스킹 (블러 중)
                  </div>
                  <div className="change">
                    미등록 인물 3명 블러 처리
                  </div>
                </div>
              </div>
              <div className="pv-item">
                <div className="thumb" style={{ background: "linear-gradient(135deg,#9c27b0,#7b1fa2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-icons" style={{ color: "#fff", fontSize: "20px" }}>
                    graphic_eq
                  </span>
                </div>
                <div className="body">
                  <div className="time">
                    01:08
                  </div>
                  <div className="title">
                    음성 → 지정
                  </div>
                  <div className="change">
                    <s>
                      "수민아!"
                    </s>
                    →
                    <strong>
                      "민지야!"
                    </strong>
                  </div>
                </div>
              </div>
              <div className="pv-item">
                <div className="thumb" style={{ background: "linear-gradient(135deg,#0288d1,#01579b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-icons" style={{ color: "#fff", fontSize: "20px" }}>
                    location_on
                  </span>
                </div>
                <div className="body">
                  <div className="time">
                    EXIF
                  </div>
                  <div className="title">
                    GPS → 제거
                  </div>
                  <div className="change">
                    메타데이터에서 위치 좌표 삭제
                  </div>
                </div>
              </div>
              <div style={{ padding: "8px", textAlign: "center", font: "400 12px var(--font-sans)", color: "var(--fg-3)" }}>
                … 12개 항목 더 보기
              </div>
            </div>
            <div className="rating-block">
              <h3>
                이 결과가 자연스러운가요?
              </h3>
              <div className="rating-row">
                <button className="rating-btn selected">
                  <span className="face">
                    😊
                  </span>
                  좋음
                </button>
                <button className="rating-btn">
                  <span className="face">
                    😐
                  </span>
                  보통
                </button>
                <button className="rating-btn">
                  <span className="face">
                    😬
                  </span>
                  이상함
                </button>
              </div>
            </div>
            <div className="wmk-note">
              <div className="watermark-note">
                <strong>
                  워터마크 안내
                </strong>
                <br />
                미리보기는 검토용으로 큰 워터마크가 표시됩니다. 본 처리 결과에는 우하단 작은 워터마크 + 비식별 워터마크만 삽입됩니다.
              </div>
            </div>
          </aside>
        </div>
        <div className="pv-footer">
          <span className="info">
            미리보기는 영상 중 샘플 5프레임으로 생성됐습니다. 본 처리는 전체 영상에 적용됩니다.
          </span>
          <a href="/replace-options" className="mui-btn mui-btn--outlined">
            ← 옵션 수정
          </a>
          <a href="/processing" className="mui-btn mui-btn--contained mui-btn--lg">
            <span className="material-icons" style={{ fontSize: "20px" }}>
              play_arrow
            </span>
            처리 진행
          </a>
        </div>
      </div>
    </GarimPage>
  );
}
