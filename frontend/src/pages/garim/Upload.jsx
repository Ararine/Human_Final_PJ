import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { uploadFile } from "../../utils/api";
import "../../css/garim-pages/Upload.css";

import GarimPage from "../../components/garim/GarimPage";

const fileTypes = ["MP4", "MOV", "MKV", "JPG", "PNG", "HEIC", "MP3", "WAV"];

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export default function Upload() {
  useDocumentTitle("파일 업로드 · Garim");
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [uploadResult, setUploadResult] = useState(null);

  const isUploading = status === "uploading";

  function handleSelectedFile(file) {
    if (!file) return;
    setSelectedFile(file);
    setStatus("ready");
    setMessage(`${file.name} 파일을 선택했습니다.`);
    setUploadResult(null);
  }

  async function handleUpload() {
    if (!selectedFile || isUploading) return;

    setStatus("uploading");
    setMessage("백엔드로 파일을 업로드하고 있습니다.");

    try {
      const result = await uploadFile(selectedFile);
      setUploadResult(result);
      setStatus("success");
      setMessage("업로드가 완료되었습니다. 분석 진행 화면으로 이동합니다.");
      window.setTimeout(() => navigate("/analysis-progress"), 700);
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    handleSelectedFile(event.dataTransfer.files?.[0]);
  }

  return (
    <GarimPage bodyClass="page-app" screenLabel="08 Upload">
      <div className="upload-page">
        <div className="upload-head">
          <h1>파일 업로드</h1>
          <div className="sub">
            영상, 이미지, 음성 파일을 업로드하면 Garim이 개인정보 노출 위험을 분석합니다.
          </div>
        </div>

        <div className="upload-banner">
          <div className={`mui-alert ${status === "error" ? "mui-alert--error" : "mui-alert--info"}`}>
            <span className="material-icons">{status === "error" ? "error" : "verified_user"}</span>
            <div className="mui-alert__body">
              {message || "업로드한 파일은 백엔드 저장소에 보관됩니다. 실제 분석 연동은 다음 단계에서 연결합니다."}
              {uploadResult ? (
                <span className="mui-chip mui-chip--soft-success" style={{ marginLeft: "8px" }}>
                  {uploadResult.upload_id}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        <div className="upload-grid">
          <div className="dropzone-card">
            <div
              className={`dropzone ${selectedFile ? "dropzone--selected" : ""}`}
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
              }}
            >
              <input
                ref={inputRef}
                className="upload-input"
                type="file"
                accept="video/*,image/*,audio/*"
                onChange={(event) => handleSelectedFile(event.target.files?.[0])}
              />
              <span className="material-icons">cloud_upload</span>
              <h2>{selectedFile ? selectedFile.name : "파일을 선택하거나 끌어다 놓으세요"}</h2>
              <p>
                {selectedFile
                  ? `${formatBytes(selectedFile.size)} · ${selectedFile.type || "알 수 없는 형식"}`
                  : "지원 형식: MP4, MOV, MKV, JPG, PNG, HEIC, MP3, WAV"}
              </p>
              <button
                className="mui-btn mui-btn--contained"
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  selectedFile ? handleUpload() : inputRef.current?.click();
                }}
                disabled={isUploading}
              >
                {isUploading ? "업로드 중..." : selectedFile ? "백엔드에 업로드" : "파일 선택"}
              </button>
              <div className="file-types">
                {fileTypes.map((type) => (
                  <span className="mui-chip" key={type}>
                    {type}
                  </span>
                ))}
              </div>
            </div>

            {status !== "idle" ? (
              <div className="progress-state show">
                <div className="file-info">
                  <span className="material-icons">videocam</span>
                  <div style={{ flex: "1" }}>
                    <div className="name">{selectedFile?.name}</div>
                    <div className="meta">
                      {uploadResult
                        ? `저장 위치: ${uploadResult.stored_path}`
                        : selectedFile
                          ? `${formatBytes(selectedFile.size)} · ${selectedFile.type || "unknown"}`
                          : ""}
                    </div>
                  </div>
                  <button
                    className="mui-btn mui-btn--text"
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setStatus("idle");
                      setMessage("");
                      setUploadResult(null);
                    }}
                  >
                    초기화
                  </button>
                </div>
                <div className="progress" style={{ margin: "16px 0 8px" }}>
                  <div
                    className="progress__bar"
                    style={{ width: status === "success" ? "100%" : isUploading ? "65%" : "20%" }}
                  />
                </div>
              </div>
            ) : null}
          </div>

          <aside>
            <div className="sidebar-card">
              <h3>지원 사양</h3>
              <div className="spec-row"><span className="k">최대 파일 크기</span><span className="v">2 GB</span></div>
              <div className="spec-row"><span className="k">최대 영상 길이</span><span className="v">30분</span></div>
              <div className="spec-row"><span className="k">권장 해상도</span><span className="v">1080p</span></div>
              <div className="spec-row"><span className="k">현재 저장 방식</span><span className="v">로컬 스토리지</span></div>
            </div>

            <div className="sidebar-card queue-card">
              <h3>처리 안내</h3>
              <div style={{ font: "400 13px/1.5 var(--font-sans)", color: "var(--fg-2)" }}>
                이번 단계에서는 파일을 백엔드에 저장합니다. 분석, 렌더링, 다운로드 파이프라인은 저장 이후 단계에서 연결합니다.
              </div>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
