import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useAuthUser } from "../../hooks/useAuthStatus";
import {
  getUserSettings,
  logout as requestLogout,
  updateUserSettings,
  deleteAccount,
} from "../../utils/api";
import "../../css/garim-pages/Settings.css";

import GarimPage from "../../components/garim/GarimPage";

const DEFAULT_SETTINGS = {
  email_notification: true,
  browser_notification: true,
  data_usage_consent: true,
};

export default function Settings() {
  useDocumentTitle("프로필·환경 설정 · Garim");
  const navigate = useNavigate();
  const { user } = useAuthUser();
  const [activeSection, setActiveSection] = useState("profile");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [savingField, setSavingField] = useState("");
  const userEmail = user?.email || "";

  useEffect(() => {
    const syncActiveSection = () => {
      setActiveSection(window.location.hash.replace("#", "") || "profile");
    };

    syncActiveSection();
    window.addEventListener("hashchange", syncActiveSection);
    return () => window.removeEventListener("hashchange", syncActiveSection);
  }, []);

  useEffect(() => {
    let isMounted = true;

    getUserSettings()
      .then((result) => {
        if (!isMounted) return;
        setSettings({
          email_notification: Boolean(result.data?.email_notification),
          browser_notification: Boolean(result.data?.browser_notification),
          data_usage_consent: Boolean(result.data?.data_usage_consent),
        });
      })
      .catch((error) => {
        console.error("Failed to load user settings", error);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const getNavClassName = (section) =>
    activeSection === section ? "active" : "";

  const handleNavClick = (e, section) => {
    e.preventDefault();
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleLogout = async () => {
    if (isLoggingOut) return;

    try {
      setIsLoggingOut(true);
      await requestLogout();
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout failed", error);
      setIsLoggingOut(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (isDeletingAccount) return;

    try {
      setIsDeletingAccount(true);
      await deleteAccount();
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Account deletion failed", error);
      setIsDeletingAccount(false);
    }
  };

  const openDeleteModal = () => {
    setDeleteConfirmText("");
    setShowDeleteModal(true);
  };

  const closeDeleteModal = () => {
    setShowDeleteModal(false);
    setDeleteConfirmText("");
  };

  const handleToggleSetting = async (field) => {
    if (savingField) return;

    const nextSettings = {
      ...settings,
      [field]: !settings[field],
    };
    const previousSettings = settings;

    setSettings(nextSettings);
    setSavingField(field);

    try {
      const result = await updateUserSettings(nextSettings);
      setSettings({
        email_notification: Boolean(result.data?.email_notification),
        browser_notification: Boolean(result.data?.browser_notification),
        data_usage_consent: Boolean(result.data?.data_usage_consent),
      });
    } catch (error) {
      console.error("Failed to update user settings", error);
      setSettings(previousSettings);
    } finally {
      setSavingField("");
    }
  };

  const renderSwitch = (field, label) => (
    <button
      type="button"
      className={`switch ${settings[field] ? "on" : ""}`}
      role="switch"
      aria-checked={settings[field]}
      aria-label={label}
      disabled={savingField === field}
      onClick={() => handleToggleSetting(field)}
    >
      <span className="knob"></span>
    </button>
  );

  return (
    <GarimPage bodyClass="" screenLabel="22 Settings">
      <div className="set-page">
        <aside className="set-nav">
          <h2>설정</h2>
          <a
            href="#profile"
            className={getNavClassName("profile")}
            onClick={(e) => handleNavClick(e, "profile")}
          >
            <span className="material-icons">person</span>
            프로필
          </a>
          <a
            href="#notif"
            className={getNavClassName("notif")}
            onClick={(e) => handleNavClick(e, "notif")}
          >
            <span className="material-icons">notifications</span>
            알림
          </a>
          <a
            href="#security"
            className={getNavClassName("security")}
            onClick={(e) => handleNavClick(e, "security")}
          >
            <span className="material-icons">lock</span>
            보안
          </a>
          <a
            href="#data"
            className={getNavClassName("data")}
            onClick={(e) => handleNavClick(e, "data")}
          >
            <span className="material-icons">storage</span>
            데이터
          </a>
          <a href="/terms">
            <span className="material-icons">description</span>
            약관
          </a>
          <a
            href="#danger"
            className={`set-nav-danger ${getNavClassName("danger")}`}
            onClick={(e) => handleNavClick(e, "danger")}
          >
            <span className="material-icons" style={{ color: "#d32f2f" }}>
              warning
            </span>
            위험 영역
          </a>
        </aside>
        <main className="set-main">
          <h1>프로필·환경 설정</h1>
          <div className="set-section" id="profile">
            <div className="set-section-head">
              <h3>프로필</h3>
              <button
                className="mui-btn mui-btn--outlined mui-btn--sm"
                type="button"
                onClick={handleLogout}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? "로그아웃 중" : "로그아웃"}
              </button>
            </div>
            <p className="sub">실명·전화번호는 받지 않습니다.</p>
            <div className="set-field">
              <label>이메일</label>
              <input value={userEmail} readOnly />
            </div>
            {/* <div className="set-field">
              <label>
                표시명 (닉네임)
              </label>
              <input value="민지" />
              <div className="helper">
                선택 항목. 처리 이력·SNS 진단 결과 등에 표시됩니다.
              </div>
            </div> */}
          </div>
          <div className="set-section" id="notif">
            <h3>알림</h3>
            <p className="sub">
              처리 완료·자동 삭제 임박 등 알림 채널을 선택합니다.
            </p>
            <div className="row-toggle">
              <div className="text">
                <div className="t">처리 완료 이메일</div>
                <div className="s">치환 완료·실패 시 이메일 발송</div>
              </div>
              {renderSwitch("email_notification", "처리 완료 이메일")}
            </div>
            <div className="row-toggle">
              <div className="text">
                <div className="t">처리 완료 브라우저 푸시</div>
                <div className="s">웹 브라우저 푸시 알림 (권한 허용 시)</div>
              </div>
              {renderSwitch("browser_notification", "처리 완료 브라우저 푸시")}
            </div>
            {/* <div className="row-toggle">
              <div className="text">
                <div className="t">자동 삭제 임박 알림</div>
                <div className="s">
                  결과 파일이 24시간 후 삭제될 때 이메일 발송
                </div>
              </div>
              {renderSwitch("data_usage_consent", "AI 학습 데이터 활용 동의")}
            </div>
            <div className="row-toggle">
              <div className="text">
                <div className="t">
                  마케팅 정보 수신
                  <span className="caption-k" style={{ fontSize: "11px" }}>
                    (가입 시 동의 분리)
                  </span>
                </div>
                <div className="s">새 기능·할인 이벤트 안내</div>
              </div>
              <div className="switch">
                <div className="knob"></div>
              </div>
            </div>
            <div className="row-toggle" style={{ opacity: "0.5" }}>
              <div className="text">
                <div className="t">
                  정기 SNS 스캔 알림
                  <span
                    className="mui-chip"
                    style={{
                      marginLeft: "4px",
                      height: "18px",
                      fontSize: "10px",
                    }}
                  >
                    v2
                  </span>
                </div>
                <div className="s">자동 스캔 결과 안내</div>
              </div>
              <div className="switch">
                <div className="knob"></div>
              </div>
            </div> */}
          </div>
          <div className="set-section" id="security">
            <h3>보안</h3>
            <p className="sub">로그인 이력 관리</p>
            <div style={{ marginTop: "24px" }}>
              <label
                style={{
                  font: "500 13px var(--font-sans)",
                  display: "block",
                  marginBottom: "12px",
                }}
              >
                최근 로그인 (최근 5건)
              </label>
              <div className="login-list">
                <div className="row">
                  <span style={{ flex: "1" }}>방금 전 · Chrome / macOS</span>
                  <span className="ip">211.123.***.***</span>
                  <span className="mui-chip mui-chip--soft-success">
                    현재 세션
                  </span>
                </div>
                <div className="row">
                  <span style={{ flex: "1" }}>
                    2026.05.13 21:04 · Safari / iOS
                  </span>
                  <span className="ip">211.123.***.***</span>
                </div>
                <div className="row">
                  <span style={{ flex: "1" }}>
                    2026.05.11 09:42 · Chrome / macOS
                  </span>
                  <span className="ip">211.123.***.***</span>
                </div>
              </div>
            </div>
            {/* <div
              className="row-toggle"
              style={{ marginTop: "24px", opacity: "0.5" }}
            >
              <div className="text">
                <div className="t">
                  2단계 인증 (2FA)
                  <span
                    className="mui-chip"
                    style={{
                      marginLeft: "4px",
                      height: "18px",
                      fontSize: "10px",
                    }}
                  >
                    v2
                  </span>
                </div>
                <div className="s">로그인 시 SMS 또는 앱 인증 추가</div>
              </div>
              <div className="switch">
                <div className="knob"></div>
              </div>
            </div> */}
          </div>
          <div className="set-section" id="data">
            <h3>데이터</h3>
            <p className="sub">처리 데이터 활용·자동 삭제·내려받기 설정.</p>
            <div className="row-toggle">
              <div className="text">
                <div className="t set-title-row">
                  AI 학습 데이터 활용 동의
                  <a
                    href="/learning-consent"
                    className="mui-btn mui-btn--outlined mui-btn--sm set-detail-link"
                  >
                    자세히
                  </a>
                </div>
              </div>
              {renderSwitch("data_usage_consent", "AI 학습 데이터 활용 동의")}
            </div>
            {/* <a
              href="/face-whitelist"
              style={{
                display: "flex",
                gap: "16px",
                alignItems: "center",
                padding: "14px 0",
                borderBottom: "1px solid var(--mui-divider)",
                textDecoration: "none",
                color: "inherit",
                opacity: "0.6",
              }}
            >
              <div className="text">
                <div className="t">
                  본인 얼굴 화이트리스트
                  <span
                    className="mui-chip"
                    style={{
                      marginLeft: "4px",
                      height: "18px",
                      fontSize: "10px",
                    }}
                  >
                    v2
                  </span>
                </div>
                <div className="s">본인 얼굴은 자동 마스킹에서 제외</div>
              </div>
              <span className="mui-chip">v2 예정</span>
            </a>
            <div
              style={{
                display: "flex",
                gap: "16px",
                alignItems: "center",
                padding: "14px 0",
              }}
            >
              <div className="text">
                <div className="t">내 데이터 내려받기</div>
                <div className="s">처리 이력·동의 이력 JSON 파일로 받기</div>
              </div>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                받기
              </button>
            </div> */}
            <div
              style={{
                marginTop: "16px",
                padding: "12px 16px",
                background: "rgba(25,118,210,0.04)",
                borderRadius: "4px",
                font: "400 12px/1.5 var(--font-sans)",
                color: "var(--fg-2)",
              }}
            >
              <strong style={{ color: "#1976d2" }}>자동 삭제 정책</strong>— 원본
              파일은 처리 후 12시간 / 결과 파일은 플랜별 (Free 7일·Pro 90일) /
              처리 메타데이터는 90일 (워터마크 역추적용).
            </div>
          </div>
          <div className="set-section" id="danger">
            <h3 style={{ color: "#d32f2f" }}>위험 영역</h3>
            <div className="danger">
              <h4>계정 삭제</h4>
              <p>
                계정과 모든 데이터가 영구히 삭제됩니다. 결제 이력은 법적 보관
                의무로 90일간 별도 보존됩니다.
              </p>
              <button
                className="mui-btn mui-btn--outlined"
                style={{ color: "#d32f2f", borderColor: "rgba(211,47,47,0.5)" }}
                onClick={openDeleteModal}
              >
                계정 삭제 신청 →
              </button>
            </div>
          </div>
        </main>
      </div>
      {showDeleteModal && (
        <div className="delete-modal-overlay" onClick={closeDeleteModal}>
          <div className="delete-modal" onClick={(e) => e.stopPropagation()}>
            <h3>계정 삭제</h3>
            <p>
              계정과 모든 데이터가 영구히 삭제됩니다. 결제 이력은 법적 보관
              의무로 90일간 별도 보존됩니다.
            </p>
            <p className="delete-modal-instruction">
              삭제를 진행하시려면 아래에 &lsquo;복구 안됨&rsquo; 이라는 메세지를
              작성해주세요.
            </p>
            <input
              className="delete-modal-input"
              type="text"
              placeholder="복구 안됨"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
            />
            <div className="delete-modal-actions">
              <button
                className="mui-btn mui-btn--outlined mui-btn--sm"
                onClick={closeDeleteModal}
              >
                취소
              </button>
              <button
                className="mui-btn mui-btn--sm delete-modal-confirm-btn"
                onClick={handleDeleteAccount}
                disabled={
                  deleteConfirmText !== "복구 안됨" || isDeletingAccount
                }
              >
                {isDeletingAccount ? "처리 중…" : "삭제"}
              </button>
            </div>
          </div>
        </div>
      )}
    </GarimPage>
  );
}
