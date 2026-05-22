import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { initUpload, uploadChunk, completeUpload, createAnalysisJob } from "../../utils/api";
import "../../css/garim-pages/Upload.css";

import GarimPage from "../../components/garim/GarimPage";

const CHUNK_SIZE = 5 * 1024 * 1024;
const MAX_RETRIES = 3;
const FILE_TYPES = ["MP4", "MOV", "MKV", "JPG", "PNG", "HEIC", "MP3", "WAV"];

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function getMediaType(file) {
  if (file.type.startsWith("video/")) return "video";
  if (file.type.startsWith("image/")) return "image";
  if (file.type.startsWith("audio/")) return "audio";
  return "video";
}

function getFileIcon(file) {
  if (file?.type?.startsWith("video/")) return "videocam";
  if (file?.type?.startsWith("audio/")) return "audiotrack";
  return "image";
}

export default function Upload() {
  useDocumentTitle("파일 업로드 · Garim");
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [phase, setPhase] = useState("idle"); // idle | ready | initializing | uploading | merging | analyzing | success | error
  const [message, setMessage] = useState("");
  const [uploadedChunks, setUploadedChunks] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);

  const isActive = ["initializing", "uploading", "merging", "analyzing"].includes(phase);
  const progress =
    phase === "merging" || phase === "success" ? 100
    : totalChunks > 0 ? Math.round((uploadedChunks / totalChunks) * 100)
    : 0;

  function handleSelectedFile(file) {
    if (!file || isActive) return;
    setSelectedFile(file);
    setPhase("ready");
    setMessage(`${file.name} 파일을 선택했습니다.`);
    setUploadedChunks(0);
    setTotalChunks(0);
  }

  async function handleUpload() {
    if (!selectedFile || isActive) return;

    const file = selectedFile;
    const numChunks = Math.max(1, Math.ceil(file.size / CHUNK_SIZE));

    setPhase("initializing");
    setTotalChunks(numChunks);
    setUploadedChunks(0);
    setMessage("업로드를 초기화하고 있습니다...");

    let uploadId;
    try {
      const init = await initUpload({
        original_filename: file.name,
        content_type: file.type || "application/octet-stream",
        file_size: file.size,
        media_type: getMediaType(file),
        chunk_size: CHUNK_SIZE,
        total_chunks: numChunks,
      });
      uploadId = init.upload_id;
    } catch (err) {
      setPhase("error");
      setMessage(err.message);
      return;
    }

    setPhase("uploading");
    setMessage(`업로드 중... 0/${numChunks}`);

    for (let i = 0; i < numChunks; i++) {
      const blob = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
      let sent = false;

      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
          await uploadChunk(uploadId, i, blob);
          sent = true;
          break;
        } catch {
          if (attempt === MAX_RETRIES - 1) {
            setPhase("error");
            setMessage(`chunk ${i + 1}/${numChunks} 전송에 실패했습니다. 다시 시도해주세요.`);
            return;
          }
        }
      }

      if (!sent) return;
      setUploadedChunks(i + 1);
      setMessage(`업로드 중... ${i + 1}/${numChunks}`);
    }

    setPhase("merging");
    setMessage("파일을 병합하고 있습니다...");

    try {
      await completeUpload(uploadId);
    } catch (err) {
      setPhase("error");
      setMessage(err.message);
      return;
    }

    setPhase("analyzing");
    setMessage("분석 작업을 등록하고 있습니다...");

    let jobId;
    try {
      const job = await createAnalysisJob(uploadId);
      jobId = job.job_id;
    } catch (err) {
      setPhase("error");
      setMessage(err.message);
      return;
    }

    setPhase("success");
    setMessage("분석 작업이 등록되었습니다. 분석 진행 화면으로 이동합니다.");
    window.setTimeout(() => navigate("/analysis-progress", { state: { jobId } }), 700);
  }

  function handleReset() {
    if (isActive) return;
    setSelectedFile(null);
    setPhase("idle");
    setMessage("");
    setUploadedChunks(0);
    setTotalChunks(0);
  }

  function handleDrop(e) {
    e.preventDefault();
    handleSelectedFile(e.dataTransfer.files?.[0]);
  }

  const alertClass = phase === "error" ? "mui-alert--error" : "mui-alert--info";
  const alertIcon = phase === "error" ? "error" : phase === "success" ? "check_circle" : "verified_user";
  const defaultMessage = "영상, 이미지, 음성 파일을 업로드하면 Garim이 개인정보 노출 위험을 분석합니다.";

  const btnLabel =
    isActive ? "업로드 중..." :
    phase === "success" ? "완료" :
    selectedFile ? "분석 시작" : "파일 선택";

  const metaText =
    phase === "uploading" ? `chunk ${uploadedChunks}/${totalChunks} · ${formatBytes(selectedFile?.size)}` :
    phase === "merging" ? `병합 중... · ${formatBytes(selectedFile?.size)}` :
    phase === "success" ? `완료 · ${formatBytes(selectedFile?.size)}` :
    selectedFile ? `${formatBytes(selectedFile.size)} · ${selectedFile.type || "알 수 없는 형식"}` : "";

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
          <div className={`mui-alert ${alertClass}`}>
            <span className="material-icons">{alertIcon}</span>
            <div className="mui-alert__body">
              {message || defaultMessage}
            </div>
          </div>
        </div>

        <div className="upload-grid">
          <div className="dropzone-card">
            <div
              className={`dropzone ${selectedFile ? "dropzone--selected" : ""}`}
              role="button"
              tabIndex={0}
              onClick={() => !isActive && inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") !isActive && inputRef.current?.click();
              }}
            >
              <input
                ref={inputRef}
                className="upload-input"
                type="file"
                accept="video/*,image/*,audio/*"
                onChange={(e) => handleSelectedFile(e.target.files?.[0])}
              />
              <span className="material-icons">cloud_upload</span>
              <h2>{selectedFile ? selectedFile.name : "파일을 선택하거나 끌어다 놓으세요"}</h2>
              <p>
                {selectedFile
                  ? metaText
                  : "지원 형식: MP4, MOV, MKV, JPG, PNG, HEIC, MP3, WAV"}
              </p>
              <button
                className="mui-btn mui-btn--contained"
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  selectedFile ? handleUpload() : inputRef.current?.click();
                }}
                disabled={isActive || phase === "success"}
              >
                {btnLabel}
              </button>
              <div className="file-types">
                {FILE_TYPES.map((type) => (
                  <span className="mui-chip" key={type}>{type}</span>
                ))}
              </div>
            </div>

            {phase !== "idle" && (
              <div className="progress-state show">
                <div className="file-info">
                  <span className="material-icons">{getFileIcon(selectedFile)}</span>
                  <div style={{ flex: "1" }}>
                    <div className="name">{selectedFile?.name}</div>
                    <div className="meta">{metaText}</div>
                  </div>
                  <button
                    className="mui-btn mui-btn--text"
                    type="button"
                    disabled={isActive}
                    onClick={handleReset}
                  >
                    초기화
                  </button>
                </div>
                <div className="progress" style={{ margin: "16px 0 4px" }}>
                  <div
                    className="progress__bar"
                    style={{ width: `${progress}%`, transition: "width 0.3s ease" }}
                  />
                </div>
                <div style={{ font: "400 11px var(--font-sans)", color: "var(--fg-2)", textAlign: "right" }}>
                  {progress}%
                </div>
              </div>
            )}
          </div>

          <aside>
            <div className="sidebar-card">
              <h3>지원 사양</h3>
              <div className="spec-row"><span className="k">최대 파일 크기</span><span className="v">2 GB</span></div>
              <div className="spec-row"><span className="k">최대 영상 길이</span><span className="v">30분</span></div>
              <div className="spec-row"><span className="k">권장 해상도</span><span className="v">1080p</span></div>
              <div className="spec-row"><span className="k">업로드 방식</span><span className="v">청크 업로드</span></div>
            </div>

            <div className="sidebar-card queue-card">
              <h3>처리 안내</h3>
              <div style={{ font: "400 13px/1.5 var(--font-sans)", color: "var(--fg-2)" }}>
                파일을 5MB 단위 chunk로 분할하여 전송합니다. 전송 실패 chunk는 최대 3회 자동 재시도합니다. 모든 chunk 전송 후 서버에서 병합합니다.
              </div>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
