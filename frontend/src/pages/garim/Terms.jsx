import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Terms.css";

import GarimPage from "../../components/garim/GarimPage";

export default function Terms() {
  useDocumentTitle("약관·개인정보처리방침 · Garim");

  return (
    <GarimPage bodyClass="" screenLabel="04 Terms">
      <div className="terms-page">
        <div className="terms-head">
          <h1>
            법적 고지
          </h1>
        </div>
        <div className="terms-tabs">
          <button className="active">
            이용약관
          </button>
          <button>
            개인정보처리방침
          </button>
          <button>
            마케팅 정보 수신
          </button>
          <button>
            위치기반 서비스
          </button>
          <button>
            AI 학습 데이터 활용
          </button>
        </div>
        <div className="terms-grid">
          <aside className="toc-side">
            <h3>
              목차
            </h3>
            <a href="#sec1" className="active">
              제1조 · 목적
            </a>
            <a href="#sec2">
              제2조 · 용어의 정의
            </a>
            <a href="#sec3">
              제3조 · 약관의 효력
            </a>
            <a href="#sec4">
              제4조 · 회원가입
            </a>
            <a href="#sec5">
              제5조 · 서비스 이용
            </a>
            <a href="#sec6">
              제6조 · 워터마크 정책
            </a>
            <a href="#sec7">
              제7조 · 콘텐츠 제한
            </a>
            <a href="#sec8">
              제8조 · 회원의 의무
            </a>
            <a href="#sec9">
              제9조 · 데이터 보관·삭제
            </a>
            <a href="#sec10">
              제10조 · 결제·환불 (v1)
            </a>
            <a href="#sec11">
              제11조 · 면책
            </a>
            <a href="#sec12">
              제12조 · 약관 변경
            </a>
          </aside>
          <main className="terms-content">
            <div className="terms-meta">
              <div>
                <div className="overline-k" style={{ color: "var(--fg-2)" }}>
                  서비스 이용약관 v1.0
                </div>
                <div className="caption-k">
                  적용일자 2026년 5월 14일 · 최종 수정 2026년 5월 14일
                </div>
              </div>
              <div className="terms-actions">
                <button className="mui-btn mui-btn--outlined mui-btn--sm">
                  <span className="material-icons" style={{ fontSize: "18px" }}>
                    print
                  </span>
                  인쇄
                </button>
                <button className="mui-btn mui-btn--outlined mui-btn--sm">
                  <span className="material-icons" style={{ fontSize: "18px" }}>
                    download
                  </span>
                  PDF
                </button>
              </div>
            </div>
            <h2 id="sec1">
              제1조 (목적)
            </h2>
            <p>
              본 약관은 Garim, Inc.(이하 "회사")가 제공하는 AI 기반 멀티모달 개인정보 검출·치환 서비스 "Garim"(이하 "서비스")의 이용과 관련하여 회사와 회원 간의 권리·의무 및 책임사항, 기타 필요한 사항을 규정함을 목적으로 합니다.
            </p>
            <h2 id="sec2">
              제2조 (용어의 정의)
            </h2>
            <ul>
              <li>
                <strong>
                  "서비스"
                </strong>
                란 회사가 운영하는 garim.kr 도메인 및 그 하위 도메인에서 제공하는 모든 기능을 의미합니다.
              </li>
              <li>
                <strong>
                  "회원"
                </strong>
                이란 본 약관에 동의하고 회사에 이메일을 제공하여 가입한 자를 의미합니다.
              </li>
              <li>
                <strong>
                  "개인정보"
                </strong>
                란 영상·이미지·음성에 포함된 식별 가능한 개인의 정보(얼굴, 이름, 전화번호, 주소, 차량번호, 송장 정보 등)를 의미합니다.
              </li>
              <li>
                <strong>
                  "검출"
                </strong>
                이란 업로드된 파일에서 개인정보의 존재·위치·시점을 자동으로 식별하는 행위를 의미합니다.
              </li>
              <li>
                <strong>
                  "치환"
                </strong>
                이란 검출된 개인정보를 회원이 선택한 방식(자동 생성, 사용자 지정, 마스킹)으로 가공하여 결과 파일을 생성하는 행위를 의미합니다.
              </li>
            </ul>
            <h2 id="sec6">
              제6조 (워터마크 정책)
            </h2>
            <p>
              회사는 모든 치환 결과물에 다음의 워터마크를 적용합니다.
            </p>
            <div className="callout">
              <strong>
                1) 시각적 워터마크
              </strong>
              — Free 플랜의 결과물 우하단에 작게 표시됩니다. 1회권·Pro 이상에서는 제거됩니다 (v1 정식).
              <br />
              <br />
              <strong>
                2) 비식별 워터마크
              </strong>
              — 모든 플랜의 결과물에 영구히 삽입됩니다. 위변조 의심 신고가 있을 경우, 회사는 본 워터마크를 통해 작업 이력을 역추적할 수 있습니다.
            </div>
            <h2 id="sec9">
              제9조 (데이터 보관·삭제)
            </h2>
            <p>
              회사는 B-1 자동 삭제 원칙에 따라 다음 표와 같이 데이터를 처리합니다.
            </p>
            <table>
              <thead>
                <tr>
                  <th>
                    데이터 종류
                  </th>
                  <th>
                    보관 기간
                  </th>
                  <th>
                    비고
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    업로드 원본 파일
                  </td>
                  <td>
                    처리 완료 후 12시간
                  </td>
                  <td>
                    모든 플랜 공통
                  </td>
                </tr>
                <tr>
                  <td>
                    치환 결과 파일
                  </td>
                  <td>
                    Free 7일 / 1회권 30일 / Pro 90일
                  </td>
                  <td>
                    마이페이지에서 수동 삭제 가능
                  </td>
                </tr>
                <tr>
                  <td>
                    처리 이력 메타데이터
                  </td>
                  <td>
                    90일
                  </td>
                  <td>
                    워터마크 역추적용
                  </td>
                </tr>
                <tr>
                  <td>
                    회원 가입 정보
                  </td>
                  <td>
                    회원 탈퇴 시까지
                  </td>
                  <td>
                    탈퇴 후 7일 유예 후 영구 삭제
                  </td>
                </tr>
                <tr>
                  <td>
                    결제 정보
                  </td>
                  <td>
                    회사 미보관
                  </td>
                  <td>
                    PG사가 보관 (B-1)
                  </td>
                </tr>
              </tbody>
            </table>
            <h2 id="sec10">
              제10조 (결제·환불)
              <span className="mui-chip mui-chip--soft-info" style={{ marginLeft: "8px" }}>
                v1 정식 적용
              </span>
            </h2>
            <p>
              본 조항은 v1 정식 출시 시점부터 효력이 발생합니다. MVP1 단계에서는 모든 기능이 무료로 제공되며, 결제 관련 분쟁의 여지가 없습니다.
            </p>
            <h2 id="sec12">
              제12조 (약관 변경)
            </h2>
            <p>
              회사는 약관을 개정할 경우 적용일자 7일 전부터 회원에게 이메일로 통지합니다. 변경된 약관에 동의하지 않는 회원은 회원 탈퇴를 통해 서비스 이용을 중단할 수 있습니다.
            </p>
          </main>
        </div>
      </div>
    </GarimPage>
  );
}
