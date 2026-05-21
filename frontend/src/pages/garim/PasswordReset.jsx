import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/PasswordReset.css";

import GarimPage from "../../components/garim/GarimPage";

export default function PasswordReset() {
  useDocumentTitle("비밀번호 재설정 · Garim");

  return (
    <GarimPage bodyClass="page-auth" screenLabel="07 Password reset">
      <main className="auth-main">
        <div className="auth-card">
          <h1>
            비밀번호 재설정
          </h1>
          <p className="sub">
            가입하신 이메일로 재설정 링크를 보내드립니다.
          </p>
          <div className="step-pills">
            <div className="step-pill active" id="pill-1">
              <span className="num">
                <span>
                  1
                </span>
              </span>
              이메일
            </div>
            <span className="step-dash">
            </span>
            <div className="step-pill" id="pill-2">
              <span className="num">
                <span>
                  2
                </span>
              </span>
              발송 확인
            </div>
            <span className="step-dash">
            </span>
            <div className="step-pill" id="pill-3">
              <span className="num">
                <span>
                  3
                </span>
              </span>
              새 비밀번호
            </div>
          </div>
          <div className="panel active" id="panel-1">
            <form id="form-1" className="form-fields" novalidate>
              <div className="mui-field">
                <input type="email" className="mui-input" id="reset-email" placeholder="가입한 이메일" autoComplete="email" required />
                <span className="mui-field__helper" id="h-reset-email">
                  계정에 등록된 이메일을 입력해주세요.
                </span>
              </div>
              <button type="submit" className="mui-btn mui-btn--contained mui-btn--lg mui-btn--block" id="submit-1" disabled style={{ marginTop: "8px" }}>
                재설정 메일 보내기
              </button>
            </form>
            <div className="footer-link">
              <a href="/login">
                ← 로그인으로 돌아가기
              </a>
            </div>
          </div>
          <div className="panel" id="panel-2">
            <div className="mui-alert mui-alert--info" style={{ marginBottom: "24px" }}>
              <span className="material-icons">
                mail
              </span>
              <div className="mui-alert__body">
                <strong id="email-mask">
                  t***@gmail.com
                </strong>
                으로 재설정 링크를 보냈습니다.
                <br />
                메일함을 확인하고 링크를 클릭해주세요. 링크는 1시간 동안 유효합니다.
              </div>
            </div>
            <div className="caption-k" style={{ fontSize: "13px" }}>
              메일이 도착하지 않았나요? 스팸함을 확인해보시고, 그래도 없으면 다시 보내드릴게요.
            </div>
            <div className="resend">
              <span>
                남은 재전송 시간
                <strong id="countdown">
                  60
                </strong>
                초
              </span>
              <button id="resend-btn" disabled>
                재전송
              </button>
            </div>
            <button className="mui-btn mui-btn--text mui-btn--block" style={{ marginTop: "24px" }} id="simulate-link">
              데모: 이메일 링크 클릭한 것처럼 진행 →
            </button>
          </div>
          <div className="panel" id="panel-3">
            <form id="form-3" className="form-fields" novalidate>
              <div className="mui-field">
                <div className="pwd-wrap">
                  <input type="password" className="mui-input" id="new-pwd" placeholder="새 비밀번호" autoComplete="new-password" required />
                  <button type="button" className="toggle" id="new-pwd-toggle" tabIndex="-1">
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
                <span className="mui-field__helper" id="h-new-pwd">
                  영문·숫자·특수문자 포함 8자 이상
                </span>
              </div>
              <div className="mui-field">
                <input type="password" className="mui-input" id="new-pwd2" placeholder="비밀번호 확인" autoComplete="new-password" required />
                <span className="mui-field__helper" id="h-new-pwd2">
                  동일한 비밀번호를 다시 한 번 입력해주세요.
                </span>
              </div>
              <button type="submit" className="mui-btn mui-btn--contained mui-btn--lg mui-btn--block" id="submit-3" disabled style={{ marginTop: "8px" }}>
                비밀번호 변경
              </button>
            </form>
          </div>
        </div>
      </main>
    </GarimPage>
  );
}
