import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AnalysisProgress.css";

import GarimPage from "../../components/garim/GarimPage";

export default function AnalysisProgress() {
  useDocumentTitle("분석 진행 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="09 Analysis progress">
      <div className="ana-page">
        <div className="ana-grid">
          <div className="ana-main">
            <div className="ana-head">
              <div className="thumb">
                <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=400&amp;q=60" alt="처리 중 영상" />
                <div className="pulse">
                </div>
              </div>
              <div style={{ flex: "1" }}>
                <h1>
                  분석 중입니다...
                </h1>
                <div className="meta">
                  family_picnic_2026.mp4 · 847 MB · 2분 14초
                </div>
                <div style={{ marginTop: "8px", display: "flex", gap: "6px" }}>
                  <span className="mui-chip mui-chip--soft-info">
                    시각 검출
                  </span>
                  <span className="mui-chip mui-chip--soft-info">
                    음성 검출
                  </span>
                  <span className="mui-chip mui-chip--soft-info">
                    EXIF 분석
                  </span>
                </div>
              </div>
            </div>
            <div className="stepper-wrap">
              <div className="vstep">
                <div className="vstep__item vstep__item--done">
                  <div className="vstep__dot">
                  </div>
                  <div className="vstep__body">
                    <div className="vstep__title">
                      업로드 완료
                    </div>
                    <div className="vstep__sub">
                      847 MB 업로드, 무결성 검증 완료
                    </div>
                  </div>
                </div>
                <div className="vstep__connector">
                </div>
                <div className="vstep__item vstep__item--done">
                  <div className="vstep__dot">
                  </div>
                  <div className="vstep__body">
                    <div className="vstep__title">
                      큐 대기 완료
                    </div>
                    <div className="vstep__sub">
                      8초 대기 후 처리 시작
                    </div>
                  </div>
                </div>
                <div className="vstep__connector">
                </div>
                <div className="vstep__item vstep__item--active">
                  <div className="vstep__dot">
                    <span className="num">
                      3
                    </span>
                  </div>
                  <div className="vstep__body">
                    <div className="vstep__title">
                      시각 검출 중
                    </div>
                    <div className="vstep__sub">
                      YOLOv8 + SAM으로 134프레임 분석 중 — 67% 진행
                    </div>
                    <div className="progress" style={{ marginTop: "8px", maxWidth: "300px" }}>
                      <div className="progress__bar" style={{ width: "67%" }}>
                      </div>
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
                      음성 검출 대기
                    </div>
                    <div className="vstep__sub">
                      Whisper + KoELECTRA
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
                      리포트 생성 대기
                    </div>
                    <div className="vstep__sub">
                      검출 결과 통합 및 위험도 산출
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="progress-summary">
              <span className="caption-k" style={{ fontSize: "13px" }}>
                전체 진행
              </span>
              <div className="progress">
                <div className="progress__bar" id="bar" style={{ width: "46%" }}>
                </div>
              </div>
              <span className="pct" id="pct">
                46%
              </span>
            </div>
            <div className="caption-k" style={{ fontSize: "13px", marginTop: "12px" }}>
              예상 남은 시간
              <strong style={{ color: "var(--fg-1)" }}>
                약 24초
              </strong>
              · 완료 시 이메일·푸시로 알려드립니다.
            </div>
            <div className="actions">
              <button className="mui-btn mui-btn--outlined">
                백그라운드 처리 →
              </button>
              <button className="mui-btn mui-btn--text" style={{ color: "#d32f2f" }}>
                취소
              </button>
              <div style={{ flex: "1" }}>
              </div>
              <a href="/analysis-report" className="mui-btn mui-btn--contained">
                데모: 결과 보기 →
              </a>
            </div>
          </div>
          <aside>
            <div className="sidebar-card">
              <h3>
                큐 위치
              </h3>
              <div className="info-row">
                <span className="k">
                  내 앞
                </span>
                <span className="v">
                  0명
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  우선순위
                </span>
                <span className="v">
                  표준 (Free)
                </span>
              </div>
              <div className="info-row">
                <span className="k">
                  시작 시각
                </span>
                <span className="v">
                  방금 전
                </span>
              </div>
              <a href="/pricing" style={{ display: "block", marginTop: "12px", padding: "12px", background: "rgba(151,71,255,0.06)", borderRadius: "4px", font: "400 12px/1.5 var(--font-sans)", color: "#9747ff", textAlign: "center" }}>
                Pro 플랜으로
                <strong>
                  2배 빠르게
                </strong>
                →
              </a>
            </div>
            <div className="sidebar-card">
              <h3>
                사용 중인 모델
              </h3>
              <div className="models-list">
                <span className="mui-chip mui-chip--md mui-chip--outlined">
                  YOLOv8 — 객체 검출
                </span>
                <span className="mui-chip mui-chip--md mui-chip--outlined">
                  SAM — 영역 분할
                </span>
                <span className="mui-chip mui-chip--md mui-chip--outlined">
                  Whisper Large — 음성 인식
                </span>
                <span className="mui-chip mui-chip--md mui-chip--outlined">
                  KoELECTRA — 개인정보 검출
                </span>
              </div>
            </div>
            <div className="sidebar-card" style={{ background: "rgba(25,118,210,0.04)" }}>
              <h3 style={{ color: "#1976d2" }}>
                알림
              </h3>
              <div style={{ font: "400 13px/1.5 var(--font-sans)", color: "var(--fg-1)" }}>
                페이지를 벗어나도 분석은 계속됩니다. 완료되면 이메일과 푸시 알림으로 알려드립니다.
              </div>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
