import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Pricing.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Pricing() {
  useDocumentTitle("요금제 · Garim");

  return (
    <GarimPage bodyClass="page-public" screenLabel="02 Pricing">
      <section className="page-head">
        <h1>
          이번 영상부터, 매달까지 — 골라 쓰는 요금제
        </h1>
        <p>
          MVP1 단계에서는 모든 결제 기능이 비활성화되어 있습니다. 모든 핵심 기능을 무료로 이용하세요.
        </p>
        <div className="billing-toggle">
          <button className="active">
            월 결제
          </button>
          <button>
            연 결제
            <span className="save">
              2개월 무료
            </span>
          </button>
        </div>
      </section>
      <section style={{ padding: "24px 32px 64px" }}>
        <div className="pricing-grid">
          <div className="price-card price-card--featured">
            <span className="mui-chip mui-chip--primary price-card__badge">
              현재 플랜 — MVP1
            </span>
            <span className="overline-k">
              Free
            </span>
            <div className="price-card__price">
              0
              <small>
                원
              </small>
            </div>
            <p className="caption-k" style={{ fontSize: "13px" }}>
              개인 사용자, 가끔 점검이 필요한 분들.
            </p>
            <ul className="price-card__feats">
              <li>
                <span className="material-icons">
                  check
                </span>
                월 무제한 검출 (영원히 무료)
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                월 5회 치환 처리
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                1080p · 30분 · 2GB
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                SNS 셀프 점검 (Instagram)
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                결과 영상 7일 보관
              </li>
              <li className="muted">
                <span className="material-icons">
                  close
                </span>
                워터마크 포함
              </li>
              <li className="muted">
                <span className="material-icons">
                  close
                </span>
                표준 큐 우선순위
              </li>
            </ul>
            <a href="/signup" className="mui-btn mui-btn--contained mui-btn--block">
              무료로 시작
            </a>
          </div>
          <div className="price-card">
            <span className="mui-chip mui-chip--soft-warning price-card__badge">
              추천 · 일회성
            </span>
            <span className="overline-k">
              1회권
            </span>
            <div className="price-card__price">
              2,900
              <small>
                원
              </small>
            </div>
            <p className="caption-k" style={{ fontSize: "13px" }}>
              이번 영상 하나만, 워터마크 없이.
            </p>
            <ul className="price-card__feats">
              <li>
                <span className="material-icons">
                  check
                </span>
                영상 1편 또는 사진 10장
              </li>
              <li>
                <span className="material-icons">
                  check"
                </span>
                워터마크 없음
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                4K · 60분 · 5GB
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                표준 큐 우선순위
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                결과 영상 30일 보관
              </li>
              <li className="muted">
                <span className="material-icons">
                  schedule
                </span>
                v1 정식 출시 후
              </li>
            </ul>
            <button className="mui-btn mui-btn--outlined mui-btn--block" disabled>
              v1 정식 출시 예정
            </button>
          </div>
          <div className="price-card">
            <span className="mui-chip mui-chip--secondary price-card__badge">
              베스트셀러
            </span>
            <span className="overline-k">
              Pro
            </span>
            <div className="price-card__price">
              19,800
              <small>
                원/월
              </small>
            </div>
            <p className="caption-k" style={{ fontSize: "13px" }}>
              크리에이터·자영업자 ·정기 처리.
            </p>
            <ul className="price-card__feats">
              <li>
                <span className="material-icons">
                  check
                </span>
                월 50회 치환 처리
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                우선 처리 큐 (2배 빠름)
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                4K · 60분 · 5GB
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                SNS 정기 자동 스캔 (v2)
              </li>
              <li>
                <span className="material-icons">
                  check
                </span>
                결과 영상 90일 보관
              </li>
              <li className="muted">
                <span className="material-icons">
                  schedule
                </span>
                v1 정식 출시 후
              </li>
            </ul>
            <button className="mui-btn mui-btn--outlined mui-btn--block" disabled>
              v1 정식 출시 예정
            </button>
          </div>
        </div>
        <div style={{ maxWidth: "1100px", margin: "24px auto 0", textAlign: "center" }}>
          <span className="caption-k">
            팀·크리에이터 그룹은
            <a href="mailto:sales@garim.kr" style={{ color: "#1976d2" }}>
              Studio·Enterprise 문의
            </a>
            를 보내주세요.
          </span>
        </div>
      </section>
      <section className="compare-section" style={{ background: "#fafafa" }}>
        <h2 style={{ textAlign: "center", font: "500 32px var(--font-sans)", margin: "0 0 32px" }}>
          기능 비교
        </h2>
        <table className="compare">
          <thead>
            <tr>
              <th>
              </th>
              <th>
                Free
                <span className="caption-k">
                  (MVP1 현재)
                </span>
              </th>
              <th>
                1회권
              </th>
              <th>
                Pro
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="row-head">
              <td colSpan="4">
                검출
              </td>
            </tr>
            <tr>
              <td>
                월 검출 횟수
              </td>
              <td>
                무제한
              </td>
              <td>
                —
              </td>
              <td>
                무제한
              </td>
            </tr>
            <tr>
              <td>
                한국어 음성·텍스트 검출
              </td>
              <td className="check">
                ●
              </td>
              <td className="check">
                ●
              </td>
              <td className="check">
                ●
              </td>
            </tr>
            <tr>
              <td>
                EXIF 메타데이터 분석
              </td>
              <td className="check">
                ●
              </td>
              <td className="check">
                ●
              </td>
              <td className="check">
                ●
              </td>
            </tr>
            <tr className="row-head">
              <td colSpan="4">
                치환
              </td>
            </tr>
            <tr>
              <td>
                월 치환 처리 횟수
              </td>
              <td>
                5회
              </td>
              <td>
                1회
              </td>
              <td>
                50회
              </td>
            </tr>
            <tr>
              <td>
                처리 결과 워터마크
              </td>
              <td>
                포함
              </td>
              <td className="x">
                없음
              </td>
              <td className="x">
                없음
              </td>
            </tr>
            <tr>
              <td>
                최대 해상도
              </td>
              <td>
                1080p
              </td>
              <td>
                4K
              </td>
              <td>
                4K
              </td>
            </tr>
            <tr>
              <td>
                최대 길이
              </td>
              <td>
                30분
              </td>
              <td>
                60분
              </td>
              <td>
                60분
              </td>
            </tr>
            <tr>
              <td>
                처리 큐 우선순위
              </td>
              <td>
                표준
              </td>
              <td>
                표준
              </td>
              <td className="check">
                우선
              </td>
            </tr>
            <tr className="row-head">
              <td colSpan="4">
                SNS·기타
              </td>
            </tr>
            <tr>
              <td>
                Instagram 셀프 점검
              </td>
              <td className="check">
                ●
              </td>
              <td>
                —
              </td>
              <td className="check">
                ●
              </td>
            </tr>
            <tr>
              <td>
                정기 자동 스캔 (v2)
              </td>
              <td className="x">
                —
              </td>
              <td className="x">
                —
              </td>
              <td className="check">
                ●
              </td>
            </tr>
            <tr>
              <td>
                결과 영상 보관 기간
              </td>
              <td>
                7일
              </td>
              <td>
                30일
              </td>
              <td>
                90일
              </td>
            </tr>
          </tbody>
        </table>
      </section>
      <section className="faq-short">
        <h2>
          자주 묻는 질문
        </h2>
        <div className="faq-item">
          <h4>
            MVP1 단계는 정말 모두 무료인가요?
          </h4>
          <p>
            네. 검출·치환·SNS 점검·다운로드 모두 무료입니다. 결과물에는 식별 워터마크가 포함됩니다. 결제 시스템은 v1 정식 출시 시점에 도입됩니다.
          </p>
        </div>
        <div className="faq-item">
          <h4>
            처리한 영상은 얼마나 보관되나요?
          </h4>
          <p>
            플랜별로 다릅니다. Free 7일, 1회권 30일, Pro 90일 후 자동 삭제됩니다. 원본 영상은 처리 완료 후 12시간 내에 모두 삭제됩니다 (B-1 정책).
          </p>
        </div>
        <div className="faq-item">
          <h4>
            한국어 음성 속 이름·전화번호도 잡나요?
          </h4>
          <p>
            네. Whisper로 음성을 텍스트로 변환한 후 자체 학습한 KoELECTRA 모델이 이름·주소·연락처·계좌번호 등을 검출합니다. 호칭("○○야"), 친밀어("○○이") 포함.
          </p>
        </div>
        <div className="faq-item">
          <h4>
            환불 정책은 어떻게 되나요?
          </h4>
          <p>
            MVP1 단계에서는 결제가 없어 해당사항 없습니다. v1 정식 출시 후: 1회권은 처리 시작 전 100% 환불 가능, 구독은 다음 결제일까지 사용 후 갱신 중단.
          </p>
        </div>
      </section>
    </GarimPage>
  );
}
