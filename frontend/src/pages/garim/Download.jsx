import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Download.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Download() {
  useDocumentTitle("다운로드 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="18 Download">
      <div className="dl-page">
        <div className="dl-shell">
          <section className="dl-success">
            <div className="check-circle">
              <span className="material-icons">
                check
              </span>
            </div>
            <div>
              <h1>
                처리가 완료됐어요!
              </h1>
              <div className="sub">
                17건 모두 처리됐습니다. 1분 27초 소요 · 워터마크 적용됨 (MVP1)
              </div>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <span className="mui-chip mui-chip--soft-success">
                자동 9건
              </span>
              <span className="mui-chip mui-chip--soft-success">
                지정 3건
              </span>
              <span className="mui-chip mui-chip--soft-success">
                마스킹 4건
              </span>
            </div>
          </section>
          <div className="dl-grid">
            <div className="dl-main">
              <div className="video-result">
                <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=1200&amp;q=80" alt="처리 완료 영상" style={{ filter: "contrast(1.02)" }} />
                <svg viewBox="0 0 1200 675" preserveAspectRatio="none" style={{ position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" }}>
                  <rect x="420" y="180" width="220" height="220" fill="#fafafa" />
                  <text x="436" y="220" fill="#212121" fontFamily="Pretendard" fontSize="14" fontWeight="600">
                    CJ대한통운 송장
                  </text>
                  <text x="436" y="245" fill="#757575" fontFamily="Pretendard" fontSize="12">
                    받는분: 김OO 님
                  </text>
                  <text x="436" y="265" fill="#757575" fontFamily="Pretendard" fontSize="12">
                    서울특별시 ○○구
                  </text>
                  <rect x="700" y="240" width="140" height="160" fill="rgba(189,189,189,0.6)" filter="url(#bf)" />
                  <defs>
                    <filter id="bf">
                      <fegaussianblur stddeviation="8" />
                    </filter>
                  </defs>
                </svg>
                <div className="play">
                  <span className="material-icons">
                    play_arrow
                  </span>
                </div>
                <div className="wmk">
                  garim · 워터마크
                </div>
              </div>
              <div className="dl-options">
                <div className="dl-card primary">
                  <h3>
                    <span className="material-icons">
                      download
                    </span>
                    전체 다운로드
                  </h3>
                  <p>
                    처리된 전체 영상 (MP4, 1920×1080, 2분 14초)
                  </p>
                  <button className="mui-btn mui-btn--contained mui-btn--lg mui-btn--block" style={{ marginTop: "8px" }}>
                    847 MB 다운로드
                  </button>
                  <span className="caption-k" style={{ fontSize: "11px", marginTop: "4px" }}>
                    링크는 30분간 유효합니다. 만료 시 재발급 가능.
                  </span>
                </div>
                <div className="dl-card">
                  <h3>
                    <span className="material-icons">
                      content_cut
                    </span>
                    구간 다운로드
                  </h3>
                  <p>
                    일부 구간만 잘라서 받기
                  </p>
                  <div className="range-grid">
                    <input value="00:30" placeholder="시작" />
                    <span className="dash">
                      →
                    </span>
                    <input value="01:45" placeholder="끝" />
                  </div>
                  <button className="mui-btn mui-btn--outlined mui-btn--block" style={{ marginTop: "4px" }}>
                    1분 15초 구간 받기
                  </button>
                </div>
              </div>
            </div>
            <aside>
              <div className="summary-card">
                <h3>
                  처리 요약
                </h3>
                <div className="sumrow">
                  <span className="k">
                    파일명
                  </span>
                  <span className="v" style={{ fontSize: "12px" }}>
                    family_picnic_2026_garim.mp4
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    검출 항목
                  </span>
                  <span className="v">
                    17건
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    치환 완료
                  </span>
                  <span className="v">
                    16건
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    건너뛰기
                  </span>
                  <span className="v">
                    1건
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    처리 시간
                  </span>
                  <span className="v">
                    1분 27초
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    출력 포맷
                  </span>
                  <span className="v">
                    MP4 · H.264
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    파일 크기
                  </span>
                  <span className="v">
                    847 MB
                  </span>
                </div>
                <div className="sumrow">
                  <span className="k">
                    워터마크
                  </span>
                  <span className="v" style={{ color: "#9747ff" }}>
                    적용됨
                  </span>
                </div>
              </div>
              <div className="delete-card" style={{ marginBottom: "16px" }}>
                <span className="material-icons">
                  schedule
                </span>
                <div>
                  <div className="t">
                    7일 후 자동 삭제 (Free 플랜)
                  </div>
                  <div className="s">
                    2026.05.21 13:42 까지 다운로드 가능. 마이페이지에서 수동 삭제도 가능합니다.
                  </div>
                </div>
              </div>
              <div className="next-card">
                <h3>
                  다음 단계 — 인스타에 다시 올리기
                </h3>
                <div className="guide-step">
                  <span className="n">
                    1
                  </span>
                  <div>
                    <div className="t">
                      결과 영상 다운로드
                    </div>
                    <div className="s">
                      위에서 받으세요 ✓
                    </div>
                  </div>
                </div>
                <div className="guide-step">
                  <span className="n">
                    2
                  </span>
                  <div>
                    <div className="t">
                      인스타에서 기존 게시물 삭제
                    </div>
                    <div className="s">
                      앱·웹에서 직접 삭제하세요
                    </div>
                  </div>
                </div>
                <div className="guide-step">
                  <span className="n">
                    3
                  </span>
                  <div>
                    <div className="t">
                      새 버전 업로드
                    </div>
                    <div className="s">
                      캡션·해시태그 그대로 유지 권장
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          </div>
          <div style={{ marginTop: "32px", display: "flex", gap: "12px", justifyContent: "center" }}>
            <a href="/upload" className="mui-btn mui-btn--outlined">
              다른 영상 처리
            </a>
            <a href="/dashboard" className="mui-btn mui-btn--text">
              대시보드로
            </a>
            <button className="mui-btn mui-btn--text">
              <span className="material-icons" style={{ fontSize: "18px" }}>
                share
              </span>
              친구 점검 권유
            </button>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
