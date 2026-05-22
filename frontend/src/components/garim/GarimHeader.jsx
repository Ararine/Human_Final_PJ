import { Link } from "react-router-dom";

import { useAuthStatus } from "../../hooks/useAuthStatus";

const publicNav = [
  { id: "detect", label: "탐지", to: "/upload" },
  { id: "sns", label: "SNS 점검", to: "/sns-connect" },
  { id: "pricing", label: "요금제", to: "/pricing" },
  { id: "help", label: "도움말", to: "/faq" },
];

export default function GarimHeader({ layout = "public", current = "" }) {
  const isAuthed = useAuthStatus();

  if (layout === "admin") {
    return (
      <header className="gh gh--admin">
        <Link to="/admin/abuse" className="gh__logo">
          <img
            src="/garim/logo.svg"
            alt="Garim"
            style={{ filter: "brightness(0) invert(1)" }}
          />
        </Link>
        <span
          className="overline-k"
          style={{
            color: "rgba(255,255,255,0.5)",
            marginLeft: 12,
            letterSpacing: 1.5,
          }}
        >
          ADMIN
        </span>
        <div className="spacer" />
        <div className="gh__right">
          <button className="gh__icon" title="알림" type="button">
            <span className="material-icons">notifications</span>
          </button>
          <div className="gh__avatar" style={{ background: "#1976d2" }}>
            A
          </div>
        </div>
      </header>
    );
  }

  if (layout === "auth") {
    return (
      <header className="gh gh--minimal">
        <Link to={isAuthed ? "/dashboard" : "/"} className="gh__logo">
          <img src="/garim/logo.svg" alt="Garim" />
        </Link>
      </header>
    );
  }

  return (
    <header
      className={`gh ${layout === "app" ? "gh--app" : ""} ${layout === "landing" || current === "landing" ? "gh--landing" : ""}`}
    >
      <Link to={isAuthed ? "/dashboard" : "/"} className="gh__logo">
        <img src="/garim/logo.svg" alt="Garim" />
      </Link>
      <nav className="gh__nav">
        {publicNav.map((item) => (
          <Link
            key={item.id}
            to={item.id === "detect" && !isAuthed ? "/login" : item.to}
            className={current === item.id ? "active" : ""}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="gh__right">
        {isAuthed ? (
          <>
            {/* TODO: 임시 버튼 — 어드민 링크 확정 후 제거 */}
            <Link
              to="/admin/monitoring"
              className="mui-btn mui-btn--outlined mui-btn--sm"
              style={{ fontSize: "12px" }}
            >
              관리자 페이지로 이동
            </Link>
            <span className="gh__icon-wrap">
              <button className="gh__icon" title="알림" type="button">
                <span className="material-icons">notifications</span>
              </button>
              <span className="gh__badge">2</span>
            </span>
            <Link
              to="/settings"
              className="gh__icon"
              title="프로필/환경 설정"
              aria-label="프로필/환경 설정"
            >
              <span className="material-icons">settings</span>
            </Link>
            <Link to="/dashboard" className="gh__avatar" title="대시보드">
              M
            </Link>
          </>
        ) : (
          <>
            <Link to="/login" className="mui-btn mui-btn--text">
              로그인
            </Link>
            <Link
              to={isAuthed ? "/upload" : "/login"}
              className="mui-btn mui-btn--contained mui-btn--sm"
            >
              무료 시작
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
