import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { confirmConsent } from "../../utils/api";
import "../../css/garim-pages/Consent.css";
import GarimPage from "../../components/garim/GarimPage";

export default function Consent() {
  useDocumentTitle("서비스 이용 동의 · Garim");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || new URLSearchParams(window.location.search).get("token");
  const timerRef = useRef(null); // [한글 주석] 자동 리다이렉트용 타이머 Ref

  // [한글 주석] 컴포넌트 언마운트 시 혹시 구동 중인 타이머가 있다면 클리어하여 메모리 누수를 방지합니다.
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  // [한글 주석] 각 약관 동의 여부 상태를 관리합니다.
  const [agreements, setAgreements] = useState({
    terms: false,       // 서비스 이용약관 (필수)
    privacy: false,     // 개인정보 수집 및 이용 (필수)
    thirdParty: false,  // 제3자 정보 제공 동의 (필수)
    marketing: false,   // 마케팅 정보 수신 동의 (선택)
  });

  // [한글 주석] 약관 상세 보기 토글 상태를 관리합니다.
  const [showDetail, setShowDetail] = useState({
    terms: false,
    privacy: false,
    thirdParty: false,
    marketing: false,
  });

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // [한글 주석] 유효한 가입 임시 토큰이 없을 경우 홈으로 내보냅니다.
  useEffect(() => {
    const rawToken = new URLSearchParams(window.location.search).get("token") || token;
    if (!rawToken) {
      navigate("/");
    }
  }, [token, navigate]);

  // [한글 주석] 전체 동의 핸들러
  const handleAllAgree = (e) => {
    const checked = e.target.checked;
    setAgreements({
      terms: checked,
      privacy: checked,
      thirdParty: checked,
      marketing: checked,
    });
  };

  // [한글 주석] 단일 약관 동의 핸들러
  const handleAgreeChange = (key) => {
    setAgreements((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // [한글 주석] 약관 상세 보기 토글 핸들러
  const toggleDetail = (key) => {
    setShowDetail((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // [한글 주석] 필수 약관 동의 완료 여부 판별
  const isRequiredAgreed = agreements.terms && agreements.privacy && agreements.thirdParty;

  // [한글 주석] 전체 동의 체크박스 상태 판별
  const isAllAgreed = Object.values(agreements).every(Boolean);

  // [한글 주석] 동의 완료 및 회원 가입 요청
  const handleConfirm = async () => {
    if (!isRequiredAgreed || loading) return;
    setLoading(true);
    setErrorMsg("");
    try {
      const res = await confirmConsent(token, agreements);
      if (res.success) {
        // [한글 주석] 가입 성공 시 메인 페이지로 이동 (쿠키 세션 자동 세팅됨)
        window.location.assign("/");
      } else {
        setErrorMsg("가입 처리 중 오류가 발생했습니다. 다시 시도해 주세요.");
      }
    } catch (err) {
      const errMsg = err.message || "약관 동의 처리에 실패했습니다. 유효기간이 만료되었을 수 있습니다.";
      setErrorMsg(`${errMsg} (10초 후 메인 페이지로 자동 이동합니다.)`);

      // [한글 주석] 기존에 구동 중인 자동 이동 타이머가 있을 시 클리어하고 새로 등록합니다.
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        navigate("/");
      }, 10000);
    } finally {
      setLoading(false);
    }
  };

  // [한글 주석] 가입 취소 시 메인 페이지로 돌려보냅니다.
  const handleCancel = () => {
    navigate("/");
  };

  if (!token) return null;

  return (
    <GarimPage bodyClass="page-auth" screenLabel="07 Consent">
      <main className="auth-main">
        <div className="auth-card consent-card">
          <h1>서비스 이용 및 약관 동의</h1>
          <p className="sub">Garim 서비스를 시작하기 위해 아래 약관에 동의해 주세요.</p>

          {errorMsg && <div className="consent-error">{errorMsg}</div>}

          <div className="consent-all-box">
            <label className="consent-checkbox-label all-agree">
              <input
                type="checkbox"
                checked={isAllAgreed}
                onChange={handleAllAgree}
              />
              <span className="checkbox-custom"></span>
              <span className="label-text">전체 동의하기</span>
            </label>
            <p className="all-agree-desc">필수 약관 및 선택적 마케팅 정보 수신 약관에 모두 동의합니다.</p>
          </div>

          <div className="consent-stack">
            {/* 1. 서비스 이용약관 */}
            <div className="consent-item">
              <div className="consent-item-header">
                <label className="consent-checkbox-label">
                  <input
                    type="checkbox"
                    checked={agreements.terms}
                    onChange={() => handleAgreeChange("terms")}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="label-text">
                    <span className="badge badge--required">필수</span> 서비스 이용약관 동의
                  </span>
                </label>
                <button
                  type="button"
                  className="detail-toggle-btn"
                  onClick={() => toggleDetail("terms")}
                >
                  {showDetail.terms ? "접기" : "보기"}
                </button>
              </div>
              {showDetail.terms && (
                <div className="consent-detail-box">
                  <h4>제 1 조 (목적)</h4>
                  <p>본 약관은 주식회사 Garim(이하 "회사")이 제공하는 개인정보 분석 및 비식별화 처리 서비스 "Garim"(이하 "서비스")의 이용 조건 및 절차에 관한 사항을 규정함을 목적으로 합니다.</p>
                  <h4>제 2 조 (이용계약의 성립)</h4>
                  <p>이용 계약은 이용자가 본 약관에 동의하고 소셜 계정 연동을 완료하여 서비스 회원가입 절차를 성립한 시점에 체결됩니다.</p>
                  <h4>제 3 조 (서비스의 이용 및 제한)</h4>
                  <p>회사는 이용자에게 이미지, 영상, 음성 파일 내 개인정보 탐지 및 가림 처리 도구를 제공합니다. 회원의 상태가 정지(suspended) 등 비정상적인 상태일 경우 이용이 제한될 수 있습니다.</p>
                </div>
              )}
            </div>

            {/* 2. 개인정보 수집 및 이용 */}
            <div className="consent-item">
              <div className="consent-item-header">
                <label className="consent-checkbox-label">
                  <input
                    type="checkbox"
                    checked={agreements.privacy}
                    onChange={() => handleAgreeChange("privacy")}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="label-text">
                    <span className="badge badge--required">필수</span> 개인정보 수집 및 이용 동의
                  </span>
                </label>
                <button
                  type="button"
                  className="detail-toggle-btn"
                  onClick={() => toggleDetail("privacy")}
                >
                  {showDetail.privacy ? "접기" : "보기"}
                </button>
              </div>
              {showDetail.privacy && (
                <div className="consent-detail-box">
                  <p>회사는 안정적인 서비스 제공을 위해 아래와 같이 최소한의 개인정보를 수집 및 이용합니다.</p>
                  <ul>
                    <li><strong>수집 항목</strong>: 소셜 계정 식별자, 이메일 주소, 이름, 프로필 이미지 URL, 접속 IP, User-Agent 및 브라우저 환경 데이터</li>
                    <li><strong>수집 목적</strong>: 회원 식별, 계정 정지 및 불공정 행위 감시, 요금제 적용 및 분석 작업 이력 제공, 보안 감사 로그 기록</li>
                    <li><strong>보유 기간</strong>: 회원 탈퇴 신청 즉시 삭제(단, 법적 의무 및 중복 가입 방지를 위해 특정 이력은 최대 30일간 보관)</li>
                  </ul>
                </div>
              )}
            </div>

            {/* 3. 제3자 정보 제공 */}
            <div className="consent-item">
              <div className="consent-item-header">
                <label className="consent-checkbox-label">
                  <input
                    type="checkbox"
                    checked={agreements.thirdParty}
                    onChange={() => handleAgreeChange("thirdParty")}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="label-text">
                    <span className="badge badge--required">필수</span> 제3자 개인정보 제공 동의
                  </span>
                </label>
                <button
                  type="button"
                  className="detail-toggle-btn"
                  onClick={() => toggleDetail("thirdParty")}
                >
                  {showDetail.thirdParty ? "접기" : "보기"}
                </button>
              </div>
              {showDetail.thirdParty && (
                <div className="consent-detail-box">
                  <p>Garim 인프라 연동 및 결제 게이트웨이 서비스 처리를 위해 제3자에게 아래와 같이 정보가 제공됩니다.</p>
                  <ul>
                    <li><strong>제공받는 자</strong>: Garim Cloud Infrastructure Provider, 토스페이먼츠(결제 연동 시)</li>
                    <li><strong>제공 목적</strong>: 클라우드 연동 파일 정밀 분석 도구 실행 및 분석 큐(Queue) 처리, 이용 요금 결제 대행</li>
                    <li><strong>제공 항목</strong>: 파일 업로드 메타데이터, 결제 금액 정보, 이메일 정보</li>
                    <li><strong>보유 및 이용 기간</strong>: 서비스 제공 목적 달성 및 관계 법령에 따른 보존 의무 기간 종료 시까지</li>
                  </ul>
                </div>
              )}
            </div>

            {/* 4. 마케팅 정보 수신 */}
            <div className="consent-item">
              <div className="consent-item-header">
                <label className="consent-checkbox-label">
                  <input
                    type="checkbox"
                    checked={agreements.marketing}
                    onChange={() => handleAgreeChange("marketing")}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="label-text">
                    <span className="badge badge--optional">선택</span> 마케팅 및 광고 정보 수신 동의
                  </span>
                </label>
                <button
                  type="button"
                  className="detail-toggle-btn"
                  onClick={() => toggleDetail("marketing")}
                >
                  {showDetail.marketing ? "접기" : "보기"}
                </button>
              </div>
              {showDetail.marketing && (
                <div className="consent-detail-box">
                  <p>이벤트 혜택 및 신규 인공지능 분석 모델 갱신 안내, 요금제 특별 프로모션 등 다양한 마케팅 소식을 전달해 드립니다.</p>
                  <p>본 동의는 선택 사항이며 동의하지 않으셔도 가림 분석 서비스의 모든 핵심 기능을 동일하게 이용하실 수 있습니다. 동의 여부는 설정(Settings) 마이페이지에서 언제든지 변경할 수 있습니다.</p>
                </div>
              )}
            </div>
          </div>

          <div className="consent-actions">
            <button
              type="button"
              className="mui-btn mui-btn--outlined"
              onClick={handleCancel}
              disabled={loading}
            >
              동의 안함
            </button>
            <button
              type="button"
              className="mui-btn mui-btn--contained"
              onClick={handleConfirm}
              disabled={!isRequiredAgreed || loading}
            >
              {loading ? "가입 처리 중..." : "동의하고 시작"}
            </button>
          </div>
        </div>
      </main>
    </GarimPage>
  );
}
