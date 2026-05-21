import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/History.css";

import GarimPage from "../../components/garim/GarimPage";

export default function History() {
  useDocumentTitle("처리 이력 · Garim");

  return (
    <GarimPage bodyClass="page-app" screenLabel="20 History">
      <div className="hist-page">
        <div className="hist-head">
          <h1>
            처리 이력
          </h1>
          <span className="caption-k">
            총 24건
          </span>
          <a href="/upload" className="mui-btn mui-btn--contained">
            <span className="material-icons" style={{ fontSize: "18px" }}>
              add
            </span>
            새 검출
          </a>
        </div>
        <div className="hist-toolbar">
          <div className="search-mini">
            <span className="material-icons">
              search
            </span>
            <input placeholder="파일명·날짜로 검색" />
          </div>
          <div className="filter-bar">
            <span className="mui-chip mui-chip--primary mui-chip--md">
              전체 24
            </span>
            <span className="mui-chip mui-chip--outlined mui-chip--md">
              완료 19
            </span>
            <span className="mui-chip mui-chip--outlined mui-chip--md">
              진행 중 2
            </span>
            <span className="mui-chip mui-chip--outlined mui-chip--md">
              실패 3
            </span>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
            <button className="mui-btn mui-btn--outlined mui-btn--sm">
              정렬: 최신순 ↓
            </button>
            <button className="mui-btn mui-btn--text mui-btn--sm" style={{ color: "#d32f2f" }}>
              <span className="material-icons" style={{ fontSize: "18px" }}>
                delete_sweep
              </span>
              일괄 삭제
            </button>
          </div>
        </div>
        <div className="hist-list">
          <div className="hist-row head">
            <span>
            </span>
            <span>
              파일
            </span>
            <span>
              처리 일시
            </span>
            <span>
              검출/치환
            </span>
            <span>
              상태
            </span>
            <span>
              액션
            </span>
          </div>
          <div className="hist-row warn-delete">
            <div className="thumb">
              <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=200&amp;q=60" alt="" />
            </div>
            <div>
              <div className="name">
                new_desk_unboxing.mp4
                <span className="mui-chip mui-chip--soft-warning" style={{ height: "18px", fontSize: "10px", marginLeft: "4px" }}>
                  24시간 후 삭제
                </span>
              </div>
              <div className="sub">
                MP4 · 1080p · 1분 47초 · 412 MB
              </div>
            </div>
            <div className="date">
              2026.05.12
              <br />
              <span className="caption-k" style={{ fontSize: "11px" }}>
                13:42
              </span>
            </div>
            <div className="detected">
              5
              <small>
                / 5
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-success">
              완료
            </span>
            <div className="actions">
              <button title="다운로드">
                <span className="material-icons">
                  download
                </span>
              </button>
              <button title="삭제">
                <span className="material-icons">
                  delete
                </span>
              </button>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb">
              <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&amp;q=60" alt="" />
            </div>
            <div>
              <div className="name">
                cafe_date_2026.jpg
              </div>
              <div className="sub">
                JPG · 3024×4032 · 4.2 MB
              </div>
            </div>
            <div className="date">
              2026.05.08
              <br />
              <span className="caption-k" style={{ fontSize: "11px" }}>
                21:18
              </span>
            </div>
            <div className="detected">
              2
              <small>
                / 2
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-success">
              완료
            </span>
            <div className="actions">
              <button>
                <span className="material-icons">
                  download
                </span>
              </button>
              <button>
                <span className="material-icons">
                  delete
                </span>
              </button>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb" style={{ background: "linear-gradient(135deg,#0288d1,#01579b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-icons" style={{ color: "#fff" }}>
                graphic_eq
              </span>
            </div>
            <div>
              <div className="name">
                interview_recording.mp3
              </div>
              <div className="sub">
                MP3 · 5분 22초 · 7.8 MB
              </div>
            </div>
            <div className="date">
              2026.05.05
              <br />
              <span className="caption-k" style={{ fontSize: "11px" }}>
                10:04
              </span>
            </div>
            <div className="detected">
              3
              <small>
                / 3
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-success">
              완료
            </span>
            <div className="actions">
              <button>
                <span className="material-icons">
                  download
                </span>
              </button>
              <button>
                <span className="material-icons">
                  delete
                </span>
              </button>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb">
              <img src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=200&amp;q=60" alt="" />
            </div>
            <div>
              <div className="name">
                family_picnic_2026.mp4
              </div>
              <div className="sub">
                MP4 · 1080p · 2분 14초 · 847 MB
              </div>
            </div>
            <div className="date">
              방금 전
            </div>
            <div className="detected">
              17
              <small>
                검출
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-info">
              처리 중 · 47%
            </span>
            <div className="actions">
              <a href="/processing" style={{ textDecoration: "none", color: "inherit" }}>
                <button>
                  <span className="material-icons">
                    visibility
                  </span>
                </button>
              </a>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb" style={{ background: "linear-gradient(45deg,#424242,#212121)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-icons" style={{ color: "#fff" }}>
                videocam
              </span>
            </div>
            <div>
              <div className="name">
                vlog_episode_07.mp4
              </div>
              <div className="sub">
                MP4 · 1080p · 8분 24초 · 1.4 GB
              </div>
            </div>
            <div className="date">
              2026.04.28
              <br />
              <span className="caption-k" style={{ fontSize: "11px" }}>
                15:22
              </span>
            </div>
            <div className="detected">
              23
              <small>
                / 22
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-warning">
              부분 실패
            </span>
            <div className="actions">
              <button>
                <span className="material-icons">
                  replay
                </span>
              </button>
              <button>
                <span className="material-icons">
                  delete
                </span>
              </button>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb">
              <img src="https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=200&amp;q=60" alt="" />
            </div>
            <div>
              <div className="name">
                2026_grocery_delivery.jpg
              </div>
              <div className="sub">
                JPG · 1920×1080 · 1.2 MB
              </div>
            </div>
            <div className="date">
              2026.04.21
            </div>
            <div className="detected">
              1
              <small>
                / 1
              </small>
            </div>
            <span className="mui-chip mui-chip--soft-success">
              완료
            </span>
            <div className="actions">
              <button>
                <span className="material-icons">
                  download
                </span>
              </button>
              <button>
                <span className="material-icons">
                  delete
                </span>
              </button>
            </div>
          </div>
          <div className="hist-row">
            <div className="thumb" style={{ background: "linear-gradient(135deg,#d32f2f,#c62828)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-icons" style={{ color: "#fff" }}>
                videocam_off
              </span>
            </div>
            <div>
              <div className="name">
                huge_video_file.mp4
              </div>
              <div className="sub">
                MP4 · 4K · 45분 · 8.9 GB · 거부 · 입력 사양 초과
              </div>
            </div>
            <div className="date">
              2026.04.15
            </div>
            <div className="detected">
              —
            </div>
            <span className="mui-chip mui-chip--soft-error">
              실패
            </span>
            <div className="actions">
              <button>
                <span className="material-icons">
                  info
                </span>
              </button>
            </div>
          </div>
        </div>
        <div className="pagination">
          <button>
            ‹
          </button>
          <button className="active">
            1
          </button>
          <button>
            2
          </button>
          <button>
            3
          </button>
          <button>
            ›
          </button>
        </div>
      </div>
    </GarimPage>
  );
}
