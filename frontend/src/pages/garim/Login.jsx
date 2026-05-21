import { Link } from "react-router-dom";

import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { getOAuthStartUrl } from "../../utils/api";
import "../../css/garim-pages/Login.css";

import GarimPage from "../../components/garim/GarimPage";

const socialButtons = [
  {
    provider: "kakao",
    label: "카카오 계정으로 로그인",
    className: "login-social login-social--kakao",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#3C1E1E"
          d="M12 3C6.5 3 2 6.6 2 11c0 2.9 1.9 5.5 4.8 6.9-.2.7-.7 2.6-.8 3-.1.5.2.5.4.4l3.5-2.4c.7.1 1.4.2 2.1.2 5.5 0 10-3.6 10-8.1S17.5 3 12 3z"
        />
      </svg>
    ),
  },
  {
    provider: "google",
    label: "구글 로그인",
    className: "login-social login-social--google",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
        <path fill="#4285F4" d="M21.8 12.2c0-.7-.1-1.3-.2-1.9H12v3.6h5.5c-.2 1.2-.9 2.3-2 3v2.4h3.2c1.9-1.7 3.1-4.2 3.1-7.1z" />
        <path fill="#34A853" d="M12 22c2.7 0 5-.9 6.7-2.6l-3.2-2.4c-.9.6-2 .9-3.5.9-2.6 0-4.8-1.8-5.6-4.1H3.1v2.5C4.8 19.7 8.2 22 12 22z" />
        <path fill="#FBBC05" d="M6.4 13.8c-.2-.6-.3-1.2-.3-1.8s.1-1.2.3-1.8V7.7H3.1C2.4 9 2 10.4 2 12s.4 3 1.1 4.3l3.3-2.5z" />
        <path fill="#EA4335" d="M12 6.1c1.5 0 2.8.5 3.8 1.5l2.8-2.8C17 3.1 14.7 2 12 2 8.2 2 4.8 4.3 3.1 7.7l3.3 2.5c.8-2.3 3-4.1 5.6-4.1z" />
      </svg>
    ),
  },
  {
    provider: "facebook",
    label: "facebook 로그인",
    className: "login-social login-social--facebook",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#1877F2"
          d="M12 2C6.5 2 2 6.5 2 12c0 5 3.7 9.1 8.4 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7C18.3 21.1 22 17 22 12c0-5.5-4.5-10-10-10z"
        />
      </svg>
    ),
  },
  {
    provider: "x",
    label: "X 로그인",
    className: "login-social login-social--x",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="currentColor"
          d="M18.9 2h3.3l-7.3 8.3L23.4 22h-6.7l-5.2-6.8L5.5 22H2.2l7.8-8.9L1.8 2h6.9l4.7 6.2L18.9 2zm-1.2 18h1.8L7.7 3.9H5.8L17.7 20z"
        />
      </svg>
    ),
  },
];

export default function Login() {
  useDocumentTitle("로그인 · Garim");

  const startOAuth = (provider) => {
    window.location.assign(getOAuthStartUrl(provider));
  };

  return (
    <GarimPage bodyClass="page-auth" screenLabel="06 Login">
      <main className="auth-main">
        <div className="auth-card">
          <h1>다시 만나서 반가워요</h1>
          <p className="sub">로그인 후 이전에 작업하던 곳으로 안내해드릴게요.</p>

          <div className="social-stack">
            {socialButtons.map((button) => (
              <button
                key={button.provider}
                type="button"
                className={button.className}
                onClick={() => startOAuth(button.provider)}
              >
                {button.icon}
                <span>{button.label}</span>
              </button>
            ))}
          </div>

          <div className="footer-link">
            아직 계정이 없나요? <Link to="/signup">무료로 가입하기</Link>
          </div>
        </div>
      </main>
    </GarimPage>
  );
}
