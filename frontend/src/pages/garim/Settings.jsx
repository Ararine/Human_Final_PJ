import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Settings.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Settings() {
  useDocumentTitle("프로필·환경 설정 · Garim");

  return (
    <GarimPage bodyClass="" screenLabel="22 Settings">
      <div className="set-page">
        <aside className="set-nav">
          <h2>
            설정
          </h2>
          <a href="#profile" className="active">
            <span className="material-icons">
              person
            </span>
            프로필
          </a>
          <a href="#notif">
            <span className="material-icons">
              notifications
            </span>
            알림
          </a>
          <a href="#security">
            <span className="material-icons">
              lock
            </span>
            보안
          </a>
          <a href="#data">
            <span className="material-icons">
              storage
            </span>
            데이터
          </a>
          <a href="/terms">
            <span className="material-icons">
              description
            </span>
            약관
          </a>
          <a href="#danger" style={{ color: "#d32f2f" }}>
            <span className="material-icons" style={{ color: "#d32f2f" }}>
              warning
            </span>
            위험 영역
          </a>
        </aside>
        <main className="set-main">
          <h1>
            프로필·환경 설정
          </h1>
          <div className="set-section" id="profile">
            <h3>
              프로필
            </h3>
            <p className="sub">
              실명·전화번호는 받지 않습니다. 표시명만 자유롭게 설정하세요.
            </p>
            <div className="set-field">
              <label>
                이메일
              </label>
              <input value="minji@example.com" />
              <div className="helper">
                변경 시 새 이메일로 인증이 필요합니다.
              </div>
            </div>
            <div className="set-field">
              <label>
                표시명 (닉네임)
              </label>
              <input value="민지" />
              <div className="helper">
                선택 항목. 처리 이력·SNS 진단 결과 등에 표시됩니다.
              </div>
            </div>
            <div className="set-field">
              <label>
                프로필 사진
              </label>
              <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                <div style={{ width: "64px", height: "64px", borderRadius: "50%", background: "#9c27b0", color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center", font: "500 24px var(--font-sans)" }}>
                  M
                </div>
                <button className="mui-btn mui-btn--outlined">
                  사진 업로드
                </button>
                <button className="mui-btn mui-btn--text" style={{ color: "#d32f2f" }}>
                  제거
                </button>
              </div>
            </div>
          </div>
          <div className="set-section">
            <h3>
              알림
            </h3>
            <p className="sub">
              처리 완료·자동 삭제 임박 등 알림 채널을 선택합니다.
            </p>
            <div className="row-toggle">
              <div className="text">
                <div className="t">
                  처리 완료 이메일
                </div>
                <div className="s">
                  치환 완료·실패 시 이메일 발송
                </div>
              </div>
              <div className="switch on">
                <div className="knob">
                </div>
              </div>
            </div>
            <div className="row-toggle">
              <div className="text">
                <div className="t">
                  처리 완료 브라우저 푸시
                </div>
                <div className="s">
                  웹 브라우저 푸시 알림 (권한 허용 시)
                </div>
              </div>
              <div className="switch on">
                <div className="knob">
                </div>
              </div>
            </div>
            <div className="row-toggle">
              <div className="text">
                <div className="t">
                  자동 삭제 임박 알림
                </div>
                <div className="s">
                  결과 파일이 24시간 후 삭제될 때 이메일 발송
                </div>
              </div>
              <div className="switch on">
                <div className="knob">
                </div>
              </div>
            </div>
            <div className="row-toggle">
              <div className="text">
                <div className="t">
                  마케팅 정보 수신
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    (가입 시 동의 분리)
                  </span>
                </div>
                <div className="s">
                  새 기능·할인 이벤트 안내
                </div>
              </div>
              <div className="switch">
                <div className="knob">
                </div>
              </div>
            </div>
            <div className="row-toggle" style={{ opacity: "0.5" }}>
              <div className="text">
                <div className="t">
                  정기 SNS 스캔 알림
                  <span className="mui-chip" style={{ marginLeft: "4px", height: "18px", fontSize: "10px" }}>
                    v2
                  </span>
                </div>
                <div className="s">
                  자동 스캔 결과 안내
                </div>
              </div>
              <div className="switch">
                <div className="knob">
                </div>
              </div>
            </div>
          </div>
          <div className="set-section" id="security">
            <h3>
              보안
            </h3>
            <p className="sub">
              비밀번호·로그인 이력 관리.
            </p>
            <div className="set-field">
              <label>
                비밀번호 변경
              </label>
              <button className="mui-btn mui-btn--outlined" style={{ alignSelf: "flex-start" }}>
                비밀번호 변경 →
              </button>
            </div>
            <div style={{ marginTop: "24px" }}>
              <label style={{ font: "500 13px var(--font-sans)", display: "block", marginBottom: "12px" }}>
                최근 로그인 (최근 5건)
              </label>
              <div className="login-list">
                <div className="row">
                  <span style={{ flex: "1" }}>
                    방금 전 · Chrome / macOS
                  </span>
                  <span className="ip">
                    211.123.***.***
                  </span>
                  <span className="mui-chip mui-chip--soft-success">
                    현재 세션
                  </span>
                </div>
                <div className="row">
                  <span style={{ flex: "1" }}>
                    2026.05.13 21:04 · Safari / iOS
                  </span>
                  <span className="ip">
                    211.123.***.***
                  </span>
                </div>
                <div className="row">
                  <span style={{ flex: "1" }}>
                    2026.05.11 09:42 · Chrome / macOS
                  </span>
                  <span className="ip">
                    211.123.***.***
                  </span>
                </div>
              </div>
            </div>
            <div className="row-toggle" style={{ marginTop: "24px", opacity: "0.5" }}>
              <div className="text">
                <div className="t">
                  2단계 인증 (2FA)
                  <span className="mui-chip" style={{ marginLeft: "4px", height: "18px", fontSize: "10px" }}>
                    v2
                  </span>
                </div>
                <div className="s">
                  로그인 시 SMS 또는 앱 인증 추가
                </div>
              </div>
              <div className="switch">
                <div className="knob">
                </div>
              </div>
            </div>
          </div>
          <div className="set-section" id="data">
            <h3>
              데이터
            </h3>
            <p className="sub">
              처리 데이터 활용·자동 삭제·내려받기 설정.
            </p>
            <a href="/learning-consent" style={{ display: "flex", gap: "16px", alignItems: "center", padding: "14px 0", borderBottom: "1px solid var(--mui-divider)", textDecoration: "none", color: "inherit" }}>
              <div className="text">
                <div className="t">
                  AI 학습 데이터 활용 동의
                </div>
                <div className="s">
                  현재 OFF · 변경하기 →
                </div>
              </div>
              <span className="mui-chip mui-chip--outlined">
                OFF
              </span>
            </a>
            <a href="/face-whitelist" style={{ display: "flex", gap: "16px", alignItems: "center", padding: "14px 0", borderBottom: "1px solid var(--mui-divider)", textDecoration: "none", color: "inherit", opacity: "0.6" }}>
              <div className="text">
                <div className="t">
                  본인 얼굴 화이트리스트
                  <span className="mui-chip" style={{ marginLeft: "4px", height: "18px", fontSize: "10px" }}>
                    v2
                  </span>
                </div>
                <div className="s">
                  본인 얼굴은 자동 마스킹에서 제외
                </div>
              </div>
              <span className="mui-chip">
                v2 예정
              </span>
            </a>
            <div style={{ display: "flex", gap: "16px", alignItems: "center", padding: "14px 0" }}>
              <div className="text">
                <div className="t">
                  내 데이터 내려받기
                </div>
                <div className="s">
                  처리 이력·동의 이력 JSON 파일로 받기
                </div>
              </div>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                받기
              </button>
            </div>
            <div style={{ marginTop: "16px", padding: "12px 16px", background: "rgba(25,118,210,0.04)", borderRadius: "4px", font: "400 12px/1.5 var(--font-sans)", color: "var(--fg-2)" }}>
              <strong style={{ color: "#1976d2" }}>
                자동 삭제 정책
              </strong>
              — 원본 파일은 처리 후 12시간 / 결과 파일은 플랜별 (Free 7일·Pro 90일) / 처리 메타데이터는 90일 (워터마크 역추적용).
            </div>
          </div>
          <div className="set-section" id="danger">
            <h3 style={{ color: "#d32f2f" }}>
              위험 영역
            </h3>
            <div className="danger">
              <h4>
                계정 삭제
              </h4>
              <p>
                계정과 모든 데이터가 영구히 삭제됩니다. 삭제 신청 후 7일간 복구 유예 기간이 있습니다. 결제 이력은 법적 보관 의무로 90일간 별도 보존됩니다.
              </p>
              <button className="mui-btn mui-btn--outlined" style={{ color: "#d32f2f", borderColor: "rgba(211,47,47,0.5)" }}>
                계정 삭제 신청 →
              </button>
            </div>
          </div>
          <div className="save-bar">
            <button className="mui-btn mui-btn--text">
              취소
            </button>
            <button className="mui-btn mui-btn--contained">
              변경사항 저장
            </button>
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
