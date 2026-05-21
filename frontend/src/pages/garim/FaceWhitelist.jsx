import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/FaceWhitelist.css";

import GarimPage from "../../components/garim/GarimPage";

export default function FaceWhitelist() {
  useDocumentTitle("본인 얼굴 화이트리스트 · Garim [v2]");

  return (
    <GarimPage bodyClass="page-app" screenLabel="24 Face whitelist (v2)">
      <div className="wl-page">
        <a href="/settings" className="wl-back">
          <span className="material-icons" style={{ fontSize: "18px" }}>
            arrow_back
          </span>
          설정으로 돌아가기
        </a>
        <h1>
          본인 얼굴 화이트리스트
        </h1>
        <p className="sub">
          본인 얼굴을 등록하면 자동 마스킹에서 제외됩니다. 내가 등장하는 영상에서 내가 가려지는 어색함을 해결합니다.
        </p>
        <div className="v2-banner">
          <span className="material-icons" style={{ fontSize: "48px", color: "#9747ff" }}>
            schedule
          </span>
          <div style={{ flex: "1" }}>
            <span className="badge">
              v2 예정
            </span>
            <h3>
              이 기능은 v2에 출시됩니다
            </h3>
            <p>
              MVP1·v1 정식 단계에서는 비활성화되어 있어요. 출시되면 이메일로 알려드릴게요. 아래는 출시 후 예상 UI입니다.
            </p>
          </div>
        </div>
        <div className="preview-section">
          <div className="empty-state">
            <div className="ico-box">
              <span className="material-icons">
                face_retouching_natural
              </span>
            </div>
            <h2>
              등록된 얼굴이 없습니다
            </h2>
            <p>
              본인 얼굴 사진 3~5장을 업로드하면, 얼굴 임베딩 벡터로 변환 후 원본 사진은 삭제됩니다. 등록 후 마스킹 처리 시 본인 얼굴은 자동으로 제외됩니다.
            </p>
            <button className="mui-btn mui-btn--contained">
              사진 업로드해서 등록 →
            </button>
          </div>
          <div className="perm-card">
            <h3>
              권한·보안 정책
            </h3>
            <ul>
              <li>
                업로드한 얼굴 사진은 임베딩 벡터로 변환 후
                <strong>
                  원본 사진은 즉시 삭제
                </strong>
                됩니다
              </li>
              <li>
                임베딩 벡터는 본인 식별 용도로만 사용,
                <strong>
                  외부 전송 없음
                </strong>
              </li>
              <li>
                등록 해제 시 임베딩이
                <strong>
                  즉시 영구 삭제
                </strong>
                됩니다
              </li>
              <li>
                법적 분쟁 시 본인 식별 확인 외 용도로 사용되지 않습니다
              </li>
            </ul>
          </div>
        </div>
      </div>
    </GarimPage>
  );
}
