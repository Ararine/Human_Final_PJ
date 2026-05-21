import { Link } from "react-router-dom";

export default function GarimFooter({ minimal = false }) {
  if (minimal) {
    return (
      <footer className="gf" style={{ padding: "16px 32px" }}>
        <div className="gf__bottom" style={{ border: 0, margin: 0 }}>
          <span>© 2026 Garim, Inc.</span>
          <span><Link to="/terms">이용약관</Link> · <Link to="/terms">개인정보처리방침</Link></span>
        </div>
      </footer>
    );
  }

  return (
    <footer className="gf">
      <div className="gf__inner">
        <div className="gf__brand">
          <img src="/garim/logo.svg" alt="Garim" style={{ height: 24 }} />
          <p>AI 기반 영상·이미지 개인정보 탐지와 비식별화를 돕는 Garim 프론트엔드 프로토타입입니다.</p>
        </div>
        <div className="gf__col">
          <h4>서비스</h4>
          <Link to="/upload">파일 탐지</Link>
          <Link to="/sns-connect">SNS 점검</Link>
          <Link to="/pricing">요금제</Link>
        </div>
        <div className="gf__col">
          <h4>지원</h4>
          <Link to="/faq">FAQ</Link>
          <a href="mailto:support@garim.kr">고객 문의</a>
          <Link to="/faq">처리 안내</Link>
        </div>
        <div className="gf__col">
          <h4>정책</h4>
          <Link to="/terms">이용약관</Link>
          <Link to="/terms">개인정보처리방침</Link>
          <Link to="/learning-consent">AI 학습 동의</Link>
        </div>
      </div>
      <div className="gf__bottom">
        <span>© 2026 Garim, Inc. · garim.kr</span>
        <span>made in Seoul</span>
      </div>
    </footer>
  );
}
