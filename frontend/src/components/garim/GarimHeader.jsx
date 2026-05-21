import { Link } from "react-router-dom";

const publicNav = [
  { id: "detect", label: "탐지", to: "/upload" },
  { id: "sns", label: "SNS 점검", to: "/sns-connect" },
  { id: "pricing", label: "요금제", to: "/pricing" },
  { id: "help", label: "도움말", to: "/faq" },
];

export default function GarimHeader({ layout = "public", current = "" }) {
  const isAuthed = layout === "app" || layout === "admin";

  if (layout === "admin") {
    return (
      <header className="gh gh--admin">
        <Link to="/admin/abuse" className="gh__logo"><img src="/garim/logo.svg" alt="Garim" style={{ filter: "brightness(0) invert(1)" }} /></Link>
        <span className="overline-k" style={{ color: "rgba(255,255,255,0.5)", marginLeft: 12, letterSpacing: 1.5 }}>ADMIN</span>
        <div className="spacer" />
        <div className="gh__right">
          <button className="gh__icon" title="알림" type="button"><span className="material-icons">notifications</span></button>
          <div className="gh__avatar" style={{ background: "#1976d2" }}>A</div>
        </div>
      </header>
    );
  }

  if (layout === "auth") {
    return (
      <header className="gh gh--minimal">
        <Link to="/" className="gh__logo"><img src="/garim/logo.svg" alt="Garim" /></Link>
      </header>
    );
  }

  return (
    <header className={`gh ${layout === "app" ? "gh--app" : ""} ${layout === "landing" || current === "landing" ? "gh--landing" : ""}`}>
      <Link to={isAuthed ? "/dashboard" : "/"} className="gh__logo"><img src="/garim/logo.svg" alt="Garim" /></Link>
      <nav className="gh__nav">
        {publicNav.map((item) => (
          <Link key={item.id} to={item.to} className={current === item.id ? "active" : ""}>{item.label}</Link>
        ))}
      </nav>
      <div className="gh__right">
        {isAuthed ? (
          <>
            <button className="gh__icon" title="검색" type="button"><span className="material-icons">search</span></button>
            <span className="gh__icon-wrap">
              <button className="gh__icon" title="알림" type="button"><span className="material-icons">notifications</span></button>
              <span className="gh__badge">2</span>
            </span>
            <Link to="/dashboard" className="gh__avatar" title="대시보드">M</Link>
          </>
        ) : (
          <>
            <Link to="/login" className="mui-btn mui-btn--text">로그인</Link>
            <Link to="/signup" className="mui-btn mui-btn--contained mui-btn--sm">무료 시작</Link>
          </>
        )}
      </div>
    </header>
  );
}
