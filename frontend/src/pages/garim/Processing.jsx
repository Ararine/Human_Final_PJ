import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Processing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Processing() {
  useDocumentTitle("처리 진행 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="17 Processing">
      <div className="pp-page">
        <div className="pp-shell">
          <div className="pp-main">
            <div className="pp-head">
              <div className="thumb">
                <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=400&amp;q=60" alt="" />
                <div className="scan">
                </div>
              </div>
              <div style={{ flex: "1" }}>
                <h1>
                  처리 중입니다...
                </h1>
                <div className="meta">
                  family_picnic_2026.mp4 · 17건 처리 · 자동 9건 / 지정 3건 / 마스킹 4건 / 건너뛰기 1건
                </div>
                <div style={{ marginTop: "8px", display: "flex", gap: "6px" }}>
                  <span className="mui-chip mui-chip--soft-info">
                    STE 합성
                  </span>
                  <span className="mui-chip mui-chip--soft-info">
                    얼굴 블러
                  </span>
                  <span className="mui-chip mui-chip--soft-info">
                    음성 합성
                  </span>
                  <span className="mui-chip mui-chip--secondary">
                    워터마크
                  </span>
                </div>
              </div>
            </div>
            <div className="vstep">
              <div className="vstep__item vstep__item--done">
                <div className="vstep__dot">
                </div>
                <div className="vstep__body">
                  <div className="vstep__title">
                    검출 결과 검증 완료
                  </div>
                  <div className="vstep__sub">
                    17건 모두 검증, 거부 콘텐츠 없음
                  </div>
                </div>
              </div>
              <div className="vstep__connector">
              </div>
              <div className="vstep__item vstep__item--active">
                <div className="vstep__dot">
                  <span className="num">
                    2
                  </span>
                </div>
                <div className="vstep__body">
                  <div className="vstep__title">
                    치환 합성 중
                  </div>
                  <div className="vstep__sub" id="step2-sub">
                    STE 텍스트 합성 (8/9건) · 얼굴 블러 (3/3건)
                  </div>
                  <div className="progress" style={{ marginTop: "8px", maxWidth: "400px" }}>
                    <div className="progress__bar" id="step2-bar" style={{ width: "72%" }}>
                    </div>
                  </div>
                </div>
              </div>
              <div className="vstep__connector">
              </div>
              <div className="vstep__item vstep__item--pending">
                <div className="vstep__dot">
                  <span className="num">
                    3
                  </span>
                </div>
                <div className="vstep__body">
                  <div className="vstep__title">
                    워터마크 삽입 대기
                  </div>
                  <div className="vstep__sub">
                    시각적 + 비식별 워터마크 (B-3, 항상 적용)
                  </div>
                </div>
              </div>
              <div className="vstep__connector">
              </div>
              <div className="vstep__item vstep__item--pending">
                <div className="vstep__dot">
                  <span className="num">
                    4
                  </span>
                </div>
                <div className="vstep__body">
                  <div className="vstep__title">
                    재인코딩 대기
                  </div>
                  <div className="vstep__sub">
                    원본 포맷 유지 (MP4)
                  </div>
                </div>
              </div>
              <div className="vstep__connector">
              </div>
              <div className="vstep__item vstep__item--pending">
                <div className="vstep__dot">
                  <span className="num">
                    5
                  </span>
                </div>
                <div className="vstep__body">
                  <div className="vstep__title">
                    완료
                  </div>
                  <div className="vstep__sub">
                    다운로드 페이지로 자동 이동
                  </div>
                </div>
              </div>
            </div>
            <div className="pp-progress-summary">
              <span className="caption-k" style={{ fontSize: "13px" }}>
                전체 진행
              </span>
              <div className="progress">
                <div className="progress__bar" id="bar" style={{ width: "32%" }}>
                </div>
              </div>
              <span className="pct" id="pct">
                32%
              </span>
            </div>
            <div className="caption-k" style={{ fontSize: "13px", marginTop: "12px" }}>
              예상 남은 시간
              <strong style={{ color: "var(--fg-1)" }}>
                약 58초
              </strong>
              · 완료 시 자동으로 다운로드 페이지로 이동합니다.
            </div>
            <div className="pp-actions">
              <button className="mui-btn mui-btn--outlined">
                백그라운드 처리 →
              </button>
              <button className="mui-btn mui-btn--text" style={{ color: "#d32f2f" }}>
                취소
              </button>
              <div style={{ flex: "1" }}>
              </div>
              <a href="/download" className="mui-btn mui-btn--contained">
                데모: 결과 보기 →
              </a>
            </div>
          </div>
          <aside>
            <div className="sidebar-card">
              <h3>
                처리 사양
              </h3>
              <div className="info-row">
                <span className="k">
                  입력
                </span>
                <span className="v">
                  MP4 · 1920×1080
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  출력
                </span>
                <span className="v">
                  MP4 · 1920×1080
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  길이
                </span>
                <span className="v">
                  2분 14초
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  처리 항목
                </span>
                <span className="v">
                  17건
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  워터마크
                </span>
                <span className="v">
                  자동 적용
                </span>
              </div>
            </div>
            <div className="sidebar-card" style={{ background: "rgba(151,71,255,0.04)", border: "1px solid rgba(151,71,255,0.2)" }}>
              <h3 style={{ color: "#9747ff" }}>
                B-3 워터마크 정책
              </h3>
              <p style={{ font: "400 13px/1.5 var(--font-sans)", color: "var(--fg-1)", margin: "0" }}>
                모든 MVP1 결과물에 워터마크가 자동 삽입됩니다. 위변조 의심 신고 시 역추적 가능합니다.
              </p>
            </div>
            <div className="sidebar-card" style={{ background: "rgba(25,118,210,0.04)" }}>
              <h3 style={{ color: "#1976d2" }}>
                알림 안내
              </h3>
              <div style={{ font: "400 13px/1.5 var(--font-sans)" }}>
                페이지를 닫아도 처리는 계속됩니다. 완료되면 이메일·푸시 알림으로 알려드려요.
              </div>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
