import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Signup.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Signup() {
  useDocumentTitle("회원가입 · Garim");

  return (
    <GarimPage bodyClass="page-auth" screenLabel="05 Signup">
      <main className="auth-main">
        <div className="auth-card">
          <h1>
            30초면 가입 끝
          </h1>
          <p className="sub">
            실명·전화번호 받지 않습니다. 이메일 하나면 충분합니다. (B-1 최소 수집 원칙)
          </p>
          <button className="sso-btn">
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path fill="#3C1E1E" d="M12 3C6.5 3 2 6.6 2 11c0 2.9 1.9 5.5 4.8 6.9-.2.7-.7 2.6-.8 3-.1.5.2.5.4.4l3.5-2.4c.7.1 1.4.2 2.1.2 5.5 0 10-3.6 10-8.1S17.5 3 12 3z" />
            </svg>
            카카오 계정으로 시작
          </button>
          <div className="divider-or">
            또는
          </div>
          <form id="signup-form" className="form-fields" novalidate>
            <div className="mui-field" id="f-email">
              <input type="email" className="mui-input" placeholder="이메일" autoComplete="email" required />
              <span className="mui-field__helper" id="h-email">
                로그인에 사용할 이메일을 입력하세요.
              </span>
            </div>
            <div className="mui-field" id="f-pwd">
              <div className="pwd-wrap">
                <input type="password" className="mui-input" id="pwd" placeholder="비밀번호" autoComplete="new-password" required />
                <button type="button" className="toggle" id="pwd-toggle" tabIndex="-1">
                  <span className="material-icons" style={{ fontSize: "20px" }}>
                    visibility
                  </span>
                </button>
              </div>
              <div className="strength" id="strength">
                <div className="bar">
                </div>
                <div className="bar">
                </div>
                <div className="bar">
                </div>
                <div className="bar">
                </div>
              </div>
              <span className="mui-field__helper strength-label" id="h-pwd">
                영문·숫자·특수문자 포함 8자 이상
              </span>
            </div>
            <div className="mui-field" id="f-pwd2">
              <div className="pwd-wrap">
                <input type="password" className="mui-input" id="pwd2" placeholder="비밀번호 확인" autoComplete="new-password" required />
                <button type="button" className="toggle" id="pwd2-toggle" tabIndex="-1">
                  <span className="material-icons" style={{ fontSize: "20px" }}>
                    visibility
                  </span>
                </button>
              </div>
              <span className="mui-field__helper" id="h-pwd2">
                위에서 입력한 비밀번호와 동일해야 합니다.
              </span>
            </div>
            <div className="consent">
              <div className="consent-row consent-row--all">
                <span className="checkbox" id="cb-all" data-c="all">
                </span>
                <label htmlFor="cb-all">
                  전체 동의 (선택 항목 포함)
                </label>
              </div>
              <div className="consent-row">
                <span className="checkbox" data-c="age">
                </span>
                <label>
                  <span className="req">
                    필수
                  </span>
                  만 14세 이상입니다
                </label>
              </div>
              <div className="consent-row">
                <span className="checkbox" data-c="tos">
                </span>
                <label>
                  <span className="req">
                    필수
                  </span>
                  이용약관 동의
                </label>
                <a href="/terms">
                  전문
                </a>
              </div>
              <div className="consent-row">
                <span className="checkbox" data-c="privacy">
                </span>
                <label>
                  <span className="req">
                    필수
                  </span>
                  개인정보처리방침 동의
                </label>
                <a href="/terms">
                  전문
                </a>
              </div>
              <div className="consent-row">
                <span className="checkbox" data-c="marketing">
                </span>
                <label>
                  <span className="opt">
                    선택
                  </span>
                  마케팅 정보 수신 (이메일)
                </label>
              </div>
              <div className="consent-row">
                <span className="checkbox" data-c="learning">
                </span>
                <label>
                  <span className="opt">
                    선택
                  </span>
                  AI 학습 데이터 활용 — 처리량 10% 환원
                  <span className="mui-chip mui-chip--soft-info" style={{ marginLeft: "4px", fontSize: "11px", height: "20px", padding: "0 8px" }}>
                    v1 정식 환원
                  </span>
                </label>
              </div>
            </div>
            <button type="submit" className="mui-btn mui-btn--contained mui-btn--lg mui-btn--block" disabled id="submit-btn" style={{ marginTop: "24px" }}>
              가입하고 무료 검출 시작
            </button>
          </form>
          <div className="footer-link">
            이미 계정이 있으신가요?
            <a href="/login">
              로그인
            </a>
          </div>
        </div>
      </main>
    </GarimPage>
  );
}
