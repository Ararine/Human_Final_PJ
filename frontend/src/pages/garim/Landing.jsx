import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useAuthStatus } from "../../hooks/useAuthStatus";
import {
  formatFileSize,
  formatPrice,
  formatQuota,
  usePricingPlans,
} from "../../hooks/usePricingPlans";
import "../../css/garim-pages/Landing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Landing() {
  useDocumentTitle("Garim — 영상 속 개인정보, 자연스럽게 가립니다");
  const isAuthed = useAuthStatus();
  const startHref = isAuthed
    ? "/upload"
    : `/login?next=${encodeURIComponent("/upload")}`;
  const plans = usePricingPlans();

  return (
    <GarimPage bodyClass="page-public" screenLabel="01 Landing">
      <section className="hero">
        <span className="mui-chip mui-chip--secondary mui-chip--md hero__chip">
          🛡 데이터 도싱 방지 · 한국 특화
        </span>
        <h1>
          영상 속 개인정보,
          <br />
          <span className="accent">
            자연스럽게
          </span>
          가립니다.
        </h1>
        <p className="lead">
          택배 송장·번호판·얼굴·음성 — AI가 30초 안에 찾아내고, 보안 처리는 1분 안에 끝납니다.
        </p>
        <div className="hero__cta">
          <a href={startHref} className="mui-btn mui-btn--contained mui-btn--lg">
            무료로 시작하기
          </a>
          <a href="/pricing" className="mui-btn mui-btn--outlined mui-btn--lg">
            요금제 보기
          </a>
        </div>
        <div className="hero-vis">
          <img src="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=1200&amp;q=80" alt="택배 송장이 포함된 영상 예시" />
          <svg viewBox="0 0 1200 675" preserveAspectRatio="none" style={{ position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" }}>
            <rect x="380" y="220" width="320" height="180" fill="none" stroke="#d32f2f" strokeWidth="3" rx="2" />
            <rect x="378" y="198" width="170" height="24" fill="#d32f2f" />
            <text x="385" y="215" fill="#fff" fontFamily="Pretendard, sans-serif" fontSize="13" fontWeight="500">
              택배 송장 · 위험 8/10
            </text>
            <rect x="760" y="340" width="180" height="110" fill="none" stroke="#ed6c02" strokeWidth="3" rx="2" />
            <rect x="758" y="318" width="138" height="24" fill="#ed6c02" />
            <text x="765" y="335" fill="#fff" fontFamily="Pretendard, sans-serif" fontSize="13" fontWeight="500">
              차량 번호판 · 위험 6/10
            </text>
          </svg>
          <div className="badge-overlay">
            <span className="material-icons">
              visibility
            </span>
            검출 시연 · 0.8초 만에 5건 발견
          </div>
        </div>
      </section>
      <section className="section section--alt">
        <h2>
          지금 일어나고 있는 일
        </h2>
        <p className="lead">
          SNS에 무심코 올린 영상 한 컷이 신상 도싱·스토킹의 단서가 됩니다.
        </p>
        <div className="stat-grid" style={{ marginBottom: "48px" }}>
          <div className="stat-card">
            <div className="num">
              23.1
              <small style={{ fontSize: "32px" }}>
                %
              </small>
            </div>
            <div className="lbl">
              2024년 스토킹 신고 증가율
              <br />
              (경찰청 자료)
            </div>
          </div>
          <div className="stat-card">
            <div className="num">
              <span className="accent">
                4,128
              </span>
            </div>
            <div className="lbl">
              이번 주 Garim이 처리한 영상 평균
              <br />
              발견 개인정보 (영상당 평균 6.4건)
            </div>
          </div>
          <div className="stat-card">
            <div className="num">
              87
              <small style={{ fontSize: "32px" }}>
                %
              </small>
            </div>
            <div className="lbl">
              한국어 영상에서 기존 자동 모자이크
              <br />
              도구가 놓치는 정보 비율
            </div>
          </div>
        </div>
        <div className="problem-cards">
          <div className="problem-card">
            <span className="material-icons">
              local_shipping
            </span>
            <h4>
              택배 송장
            </h4>
            <p>
              이름·주소·전화번호가 한 장에 — 도싱의 1순위 단서
            </p>
          </div>
          <div className="problem-card">
            <span className="material-icons">
              directions_car
            </span>
            <h4>
              차량 번호판
            </h4>
            <p>
              아파트 주차장 영상이 거주지를 노출
            </p>
          </div>
          <div className="problem-card">
            <span className="material-icons">
              face
            </span>
            <h4>
              지인 얼굴
            </h4>
            <p>
              본인 동의 없이 등장한 친구·가족
            </p>
          </div>
          <div className="problem-card">
            <span className="material-icons">
              record_voice_over
            </span>
            <h4>
              음성 속 이름
            </h4>
            <p>
              "○○야!" — 한국어 호칭 자동 검출
            </p>
          </div>
        </div>
      </section>
      <section className="section">
        <h2>
          <span className="accent">
            세 가지가 다릅니다
          </span>
        </h2>
        <p className="lead">
          단순 모자이크가 아닙니다. 한국 환경에 맞춘 검출과, 자연스러운 치환.
        </p>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-card__ico">
              <span className="material-icons">
                visibility
              </span>
            </div>
            <h3>
              검출은 영원히 무료
            </h3>
            <p>
              내 영상에 어떤 개인정보가 있는지 보는 데에는 비용이 들지 않습니다. 결제는 가릴 때만.
            </p>
            <span className="mui-chip mui-chip--soft-success" style={{ alignSelf: "flex-start" }}>
              MVP1 무료 · 워터마크 포함
            </span>
          </div>
          <div className="feature-card">
            <div className="feature-card__ico feature-card__ico--secondary">
              <span className="material-icons">
                translate
              </span>
            </div>
            <h3>
              한국 데이터셋으로 학습
            </h3>
            <p>
              택배사 송장 양식·국내 번호판·한국어 호칭·EXIF GPS까지. 글로벌 도구가 놓치는 87%를 포착합니다.
            </p>
            <span className="mui-chip mui-chip--soft-info" style={{ alignSelf: "flex-start" }}>
              KoELECTRA + 자체 송장 데이터셋
            </span>
          </div>
          <div className="feature-card">
            <div className="feature-card__ico feature-card__ico--success">
              <span className="material-icons">
                layers
              </span>
            </div>
            <h3>
              영상 · 이미지 · 음성
            </h3>
            <p>
              한 번의 업로드로 시각·청각 모두 점검. 영상은 프레임마다, 음성은 1초 단위로 분석합니다.
            </p>
            <span className="mui-chip mui-chip--soft-warning" style={{ alignSelf: "flex-start" }}>
              YOLO + SAM + Whisper
            </span>
          </div>
        </div>
      </section>
      <section className="section section--alt">
        <h2>
          사용 흐름
        </h2>
        <p className="lead">
          파일을 올리고, 결과를 보고, 가립니다. 그게 전부입니다.
        </p>
        <div className="steps">
          <div className="step">
            <div className="step__num">
              1
            </div>
            <h4>
              업로드
            </h4>
            <p>
              영상·이미지·음성 파일을 드래그.
              <br />
              1080p / 2GB / 30분까지 지원.
            </p>
          </div>
          <div className="step">
            <div className="step__num step__num--secondary">
              2
            </div>
            <h4>
              검출 (무료)
            </h4>
            <p>
              30초 안에 위험 항목 리포트.
              <br />
              시점·위치·위험도까지 확인.
            </p>
          </div>
          <div className="step">
            <div className="step__num step__num--success">
              3
            </div>
            <h4>
              치환
            </h4>
            <p>
              자동/사용자 지정/마스킹 중 선택.
              <br />
              워터마크 포함된 결과 다운로드.
            </p>
          </div>
        </div>
      </section>
      <section className="section">
        <h2>
          요금제
        </h2>
        <p className="lead">
          관리자 정책에서 설정한 크레딧, 금액, 파일 처리 한도, 데이터 보존 기간을 기준으로 표시합니다.
        </p>
        <div className="pricing-grid">
          {plans.map((plan) => (
            <div
              key={plan.key}
              className={`price-card${plan.featured ? " price-card--featured" : ""}`}
            >
              <span className={`mui-chip ${plan.badgeClass} price-card__badge`}>
                {plan.badge}
              </span>
              <span className="overline-k">{plan.name}</span>
              <div className="price-card__price">
                {formatPrice(plan.payment.price)}
                <small>원</small>
              </div>
              <p className="caption-k" style={{ fontSize: "13px" }}>
                {plan.description}
              </p>
              <ul className="price-card__feats">
                <li>
                  <span className="material-icons">check</span>크레딧{" "}
                  {formatQuota(plan.payment.credits, "개")}
                </li>
                <li>
                  <span className="material-icons">check</span>월 처리 한도{" "}
                  {formatQuota(plan.file.monthlyQuota)}
                </li>
                <li>
                  <span className="material-icons">check</span>최대 파일 크기{" "}
                  {formatFileSize(plan.file.fileSizeLimit)}
                </li>
                <li>
                  <span className="material-icons">check</span>동시 처리 최대{" "}
                  {formatQuota(plan.file.maxJobs)}
                </li>
                <li>
                  <span className="material-icons">check</span>결과 파일{" "}
                  {formatQuota(plan.file.resultRetention, "일")} 보관
                </li>
                <li>
                  <span className="material-icons">check</span>원본 파일{" "}
                  {formatQuota(plan.retention.autoDeleteOriginalHours, "시간")}{" "}
                  후 삭제
                </li>
                <li>
                  <span className="material-icons">check</span>메타데이터{" "}
                  {formatQuota(plan.retention.metadataRetentionDays, "일")} 보존
                </li>
              </ul>
              {plan.key === "free" ? (
                <a
                  href={startHref}
                  className="mui-btn mui-btn--contained mui-btn--block"
                >
                  {plan.cta}
                </a>
              ) : (
                <a href="/pricing" className="mui-btn mui-btn--outlined mui-btn--block">
                  자세히 보기
                </a>
              )}
            </div>
          ))}
        </div>
      </section>
      <section className="closing-cta">
        <h2>
          30초면 충분합니다
        </h2>
        <p>
          지금 내 영상에 무엇이 노출돼 있는지, 한 번 확인해보세요. 가입 후 첫 검출까지 1분.
        </p>
        <a href={startHref} className="mui-btn mui-btn--contained mui-btn--lg">
          무료로 시작하기 →
        </a>
      </section>
    </GarimPage>
  );
}
