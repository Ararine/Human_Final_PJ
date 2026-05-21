import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Dashboard.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Dashboard() {
  useDocumentTitle("마이 대시보드 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="19 Dashboard">
      <div className="dash-page">
        <div className="dash-hero">
          <div>
            <h1>
              안녕하세요, 민지님 👋
            </h1>
            <p>
              지난주 검출한 영상은 안전하게 가려졌어요. 오늘은 어떤 영상을 점검해볼까요?
            </p>
          </div>
          <div className="cta-stack">
            <a href="/sns-connect" className="mui-btn mui-btn--outlined mui-btn--lg">
              <span className="material-icons" style={{ fontSize: "20px" }}>
                share
              </span>
              인스타 점검
            </a>
            <a href="/upload" className="mui-btn mui-btn--contained mui-btn--lg">
              <span className="material-icons" style={{ fontSize: "20px" }}>
                cloud_upload
              </span>
              새 검출 시작
            </a>
          </div>
        </div>
        <div className="stat-row">
          <div className="stat">
            <span className="ico">
              <span className="material-icons">
                visibility
              </span>
            </span>
            <div className="lbl">
              누적 검출
            </div>
            <div className="num">
              24
              <small style={{ fontSize: "18px", color: "var(--fg-3)" }}>
                건
              </small>
            </div>
            <div className="delta">
              +5 이번 달
            </div>
          </div>
          <div className="stat">
            <span className="ico">
              <span className="material-icons" style={{ color: "#9747ff" }}>
                visibility_off
              </span>
            </span>
            <div className="lbl">
              치환 완료
            </div>
            <div className="num">
              19
              <small style={{ fontSize: "18px", color: "var(--fg-3)" }}>
                건
              </small>
            </div>
            <div className="delta">
              +4 이번 달
            </div>
          </div>
          <div className="stat">
            <span className="ico">
              <span className="material-icons" style={{ color: "#d32f2f" }}>
                shield
              </span>
            </span>
            <div className="lbl">
              발견된 개인정보
            </div>
            <div className="num">
              147
              <small style={{ fontSize: "18px", color: "var(--fg-3)" }}>
                건
              </small>
            </div>
            <div className="delta warn">
              평균 6.1건/영상
            </div>
          </div>
          <div className="stat">
            <span className="ico">
              <span className="material-icons" style={{ color: "#2e7d32" }}>
                savings
              </span>
            </span>
            <div className="lbl">
              남은 무료 처리
            </div>
            <div className="num">
              3
              <small style={{ fontSize: "18px", color: "var(--fg-3)" }}>
                /5회
              </small>
            </div>
            <div className="delta">
              월 1일 초기화
            </div>
          </div>
        </div>
        <div className="dash-grid">
          <div>
            <div className="card-block">
              <h2>
                진행 중인 작업
                <span className="mui-chip mui-chip--soft-info">
                  2
                </span>
                <span className="spacer">
                </span>
              </h2>
              <div className="progress-row">
                <div className="thumb">
                  <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=200&amp;q=60" alt="" />
                </div>
                <div className="body">
                  <div className="name">
                    family_picnic_2026.mp4
                  </div>
                  <div className="meta">
                    처리 진행 중 · 47% · 약 32초 남음
                  </div>
                  <div className="progress">
                    <div className="progress__bar" style={{ width: "47%" }}>
                    </div>
                  </div>
                </div>
                <a href="/processing" className="mui-btn mui-btn--text mui-btn--sm">
                  상세 →
                </a>
              </div>
              <div className="progress-row">
                <div className="thumb" style={{ background: "linear-gradient(135deg,#9c27b0,#7b1fa2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-icons" style={{ color: "#fff", fontSize: "24px" }}>
                    photo_library
                  </span>
                </div>
                <div className="body">
                  <div className="name">
                    2026_birthday_album/ — 12장
                  </div>
                  <div className="meta">
                    분석 진행 중 · 큐 대기 · 평균 38초
                  </div>
                </div>
                <a href="/analysis-progress" className="mui-btn mui-btn--text mui-btn--sm">
                  상세 →
                </a>
              </div>
            </div>
            <div className="card-block">
              <h2>
                최근 처리 이력
                <span className="spacer">
                </span>
                <a href="/history">
                  전체 보기 →
                </a>
              </h2>
              <div className="hist-row">
                <div className="thumb">
                  <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=200&amp;q=60" alt="" />
                </div>
                <div className="body">
                  <div className="name">
                    new_desk_unboxing.mp4
                  </div>
                  <div className="meta">
                    2026.05.12 · 처리 완료 · 5건 치환
                  </div>
                </div>
                <div className="right">
                  <span className="mui-chip mui-chip--soft-success">
                    완료
                  </span>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    6일 후 자동 삭제
                  </span>
                </div>
              </div>
              <div className="hist-row">
                <div className="thumb">
                  <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&amp;q=60" alt="" />
                </div>
                <div className="body">
                  <div className="name">
                    cafe_date_2026.jpg
                  </div>
                  <div className="meta">
                    2026.05.08 · 처리 완료 · 2건 치환
                  </div>
                </div>
                <div className="right">
                  <span className="mui-chip mui-chip--soft-success">
                    완료
                  </span>
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    2일 후 자동 삭제
                  </span>
                </div>
              </div>
              <div className="hist-row">
                <div className="thumb" style={{ background: "linear-gradient(135deg,#0288d1,#01579b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-icons" style={{ color: "#fff" }}>
                    graphic_eq
                  </span>
                </div>
                <div className="body">
                  <div className="name">
                    interview_recording.mp3
                  </div>
                  <div className="meta">
                    2026.05.05 · 처리 완료 · 3건 음성 치환
                  </div>
                </div>
                <div className="right">
                  <span className="mui-chip mui-chip--soft-success">
                    완료
                  </span>
                </div>
              </div>
            </div>
          </div>
          <aside>
            <div className="card-block sns-widget">
              <h2>
                SNS 셀프 점검
              </h2>
              <div className="big-num">
                9
                <small style={{ fontSize: "18px", color: "var(--fg-2)" }}>
                  건
                </small>
              </div>
              <p className="desc">
                최근 스캔에서 위험 게시물 9건이 발견됐어요. 1주일 전 점검 결과입니다.
              </p>
              <a href="/sns-results" className="mui-btn mui-btn--contained mui-btn--block" style={{ background: "#9747ff" }}>
                결과 다시 보기 →
              </a>
            </div>
            <div className="card-block">
              <h2>
                알림
              </h2>
              <div style={{ font: "400 13px/1.6 var(--font-sans)", color: "var(--fg-1)", padding: "8px 0", borderBottom: "1px solid var(--mui-divider)" }}>
                <strong>
                  family_picnic_2026.mp4
                </strong>
                분석이 완료되었습니다.
                <div className="caption-k" style={{ fontSize: "11px" }}>
                  3분 전
                </div>
              </div>
              <div style={{ font: "400 13px/1.6 var(--font-sans)", color: "var(--fg-2)", padding: "8px 0" }}>
                처리 결과 영상
                <strong>
                  2026_summer.mp4
                </strong>
                가 24시간 후 자동 삭제됩니다.
                <div className="caption-k" style={{ fontSize: "11px" }}>
                  2시간 전
                </div>
              </div>
            </div>
            <div className="card-block tip-card">
              <h3>
                💡 팁 — Pro 플랜 전환
              </h3>
              <p>
                지난 30일간 무료 한도(월 5회)에 가까웠어요. v1 정식 출시 시 Pro 플랜으로 월 50회까지 처리할 수 있어요.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
