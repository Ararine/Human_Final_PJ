import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { cancelAnalysisJob, getAnalysisJob } from "../../utils/api";
import "../../css/garim-pages/AnalysisProgress.css";

import GarimPage from "../../components/garim/GarimPage";

const POLL_INTERVAL_MS = 2500;
const ACTIVE_STATUSES = new Set(["queued", "processing", "retrying", "cancelling"]);

const STAGES = [
  { key: "upload_completed", label: "업로드 완료", detail: "원본 파일 병합과 무결성 확인 완료" },
  { key: "queued", label: "대기열 등록", detail: "분석 작업이 처리 순서를 기다리는 중" },
  { key: "visual_detection", label: "시각 탐지", detail: "얼굴, 번호판, 주소 등 프레임 기반 개인정보 탐지" },
  { key: "audio_detection", label: "음성 탐지", detail: "STT와 텍스트 분석 기반 개인정보 탐지" },
  { key: "report_generation", label: "리포트 생성", detail: "탐지 결과 통합 및 위험도 산출" },
  { key: "completed", label: "완료", detail: "결과 확인 준비 완료" },
];

function formatBytes(size) {
  if (!size) return "";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatEta(seconds) {
  if (seconds === null || seconds === undefined) return "계산 중";
  if (seconds <= 0) return "곧 완료";
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return min > 0 ? `${min}분 ${sec}초` : `${sec}초`;
}

function clampPercent(value) {
  const n = Number(value || 0);
  return Math.max(0, Math.min(100, Math.round(n)));
}

function statusLabel(status) {
  const labels = {
    queued: "대기 중",
    processing: "분석 중",
    retrying: "재시도 중",
    completed: "완료",
    failed: "실패",
    cancelling: "취소 요청됨",
    cancelled: "취소됨",
  };
  return labels[status] || "상태 확인 중";
}

function stageIndex(currentStage, status) {
  if (status === "completed") return STAGES.length - 1;
  const index = STAGES.findIndex((stage) => stage.key === currentStage);
  return index >= 0 ? index : 1;
}

export default function AnalysisProgress() {
  useDocumentTitle("분석 진행 - Garim");
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const initialState = location.state || {};
  const jobId = initialState.jobId || searchParams.get("jobId");

  const [job, setJob] = useState(null);
  const [error, setError] = useState(jobId ? "" : "분석 작업 ID가 없습니다.");
  const [loading, setLoading] = useState(Boolean(jobId));
  const [canceling, setCanceling] = useState(false);

  const jobStatus = job?.status;
  const isActive = job ? ACTIVE_STATUSES.has(jobStatus) : Boolean(jobId);
  const totalProgress = clampPercent(job?.total_progress);
  const currentStageIndex = stageIndex(job?.current_stage, job?.status);
  const fileMeta = useMemo(() => {
    const parts = [];
    if (initialState.fileName) parts.push(initialState.fileName);
    if (initialState.fileSize) parts.push(formatBytes(initialState.fileSize));
    if (initialState.contentType) parts.push(initialState.contentType);
    return parts.join(" · ");
  }, [initialState.contentType, initialState.fileName, initialState.fileSize]);

  useEffect(() => {
    if (!jobId) return undefined;

    let cancelled = false;
    const shouldPoll = !jobStatus || ACTIVE_STATUSES.has(jobStatus);

    async function loadJob() {
      try {
        const nextJob = await getAnalysisJob(jobId);
        if (!cancelled) {
          setJob(nextJob);
          setError("");
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      }
    }

    loadJob();
    if (!shouldPoll) {
      return () => {
        cancelled = true;
      };
    }

    const timer = window.setInterval(() => {
      if (!cancelled) loadJob();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [jobId, jobStatus]);

  async function handleCancel() {
    if (!jobId || canceling || !job || !ACTIVE_STATUSES.has(job.status)) return;
    setCanceling(true);
    try {
      const result = await cancelAnalysisJob(jobId);
      setJob((prev) => ({ ...prev, ...result }));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setCanceling(false);
    }
  }

  const heading =
    error && !job ? "분석 상태를 불러올 수 없습니다" :
    loading ? "분석 상태 확인 중" :
    job?.status === "completed" ? "분석이 완료되었습니다" :
    job?.status === "failed" ? "분석에 실패했습니다" :
    job?.status === "cancelled" ? "분석이 취소되었습니다" :
    "분석이 진행 중입니다";

  const statusMessage = job?.message || (loading ? "서버에서 최신 진행률을 가져오고 있습니다." : error);

  return (
    <GarimPage bodyClass="page-app" screenLabel="09 Analysis progress">
      <div className="ana-page">
        <div className="ana-grid">
          <div className="ana-main">
            <div className="ana-head">
              <div className="thumb">
                <span className="material-icons">manage_search</span>
                {isActive && <div className="pulse" />}
              </div>
              <div style={{ flex: "1" }}>
                <h1>{heading}</h1>
                <div className="meta">
                  {fileMeta || `Job ${jobId || "unknown"}`}
                </div>
                <div style={{ marginTop: "8px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  <span className="mui-chip mui-chip--soft-info">{statusLabel(job?.status)}</span>
                  <span className="mui-chip mui-chip--soft-info">{job?.job_type || "analysis"}</span>
                  {job?.current_stage && (
                    <span className="mui-chip mui-chip--soft-info">{job.current_stage}</span>
                  )}
                </div>
              </div>
            </div>

            {error && (
              <div className="mui-alert mui-alert--error" style={{ marginBottom: "16px" }}>
                <span className="material-icons">error</span>
                <div className="mui-alert__body">{error}</div>
              </div>
            )}

            <div className="stepper-wrap">
              <div className="vstep">
                {STAGES.map((stage, index) => {
                  const done = index < currentStageIndex || job?.status === "completed";
                  const active = index === currentStageIndex && !["completed", "failed", "cancelled"].includes(job?.status);
                  const className =
                    done ? "vstep__item vstep__item--done" :
                    active ? "vstep__item vstep__item--active" :
                    "vstep__item vstep__item--pending";

                  return (
                    <div key={stage.key}>
                      <div className={className}>
                        <div className="vstep__dot">
                          {!done && <span className="num">{index + 1}</span>}
                        </div>
                        <div className="vstep__body">
                          <div className="vstep__title">{stage.label}</div>
                          <div className="vstep__sub">
                            {active && statusMessage ? statusMessage : stage.detail}
                          </div>
                          {active && (
                            <div className="progress" style={{ marginTop: "8px", maxWidth: "300px" }}>
                              <div
                                className="progress__bar"
                                style={{ width: `${clampPercent(job?.stage_progress)}%` }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                      {index < STAGES.length - 1 && <div className="vstep__connector" />}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="progress-summary">
              <span className="caption-k" style={{ fontSize: "13px" }}>전체 진행</span>
              <div className="progress">
                <div className="progress__bar" style={{ width: `${totalProgress}%` }} />
              </div>
              <span className="pct">{totalProgress}%</span>
            </div>

            <div className="caption-k" style={{ fontSize: "13px", marginTop: "12px" }}>
              예상 남은 시간 <strong style={{ color: "var(--fg-1)" }}>{formatEta(job?.eta_seconds)}</strong>
              {job?.queue_position ? ` · 대기 순번 ${job.queue_position}` : ""}
            </div>

            <div className="actions">
              <Link to="/dashboard" className="mui-btn mui-btn--outlined">
                백그라운드 처리
              </Link>
              <button
                className="mui-btn mui-btn--text"
                style={{ color: "#d32f2f" }}
                type="button"
                disabled={!job || !ACTIVE_STATUSES.has(job.status) || canceling}
                onClick={handleCancel}
              >
                {canceling ? "취소 요청 중" : "취소"}
              </button>
              <div style={{ flex: "1" }} />
              <Link
                to="/analysis-report"
                className="mui-btn mui-btn--contained"
                aria-disabled={job?.status !== "completed"}
              >
                결과 보기
              </Link>
            </div>
          </div>

          <aside>
            <div className="sidebar-card">
              <h3>작업 위치</h3>
              <div className="info-row">
                <span className="k">상태</span>
                <span className="v">{statusLabel(job?.status)}</span>
              </div>
              <div className="info-row">
                <span className="k">대기 순번</span>
                <span className="v">{job?.queue_position ?? "-"}</span>
              </div>
              <div className="info-row">
                <span className="k">단계 진행</span>
                <span className="v">{clampPercent(job?.stage_progress)}%</span>
              </div>
              <div className="info-row">
                <span className="k">Job ID</span>
                <span className="v">{jobId || "-"}</span>
              </div>
            </div>

            <div className="sidebar-card">
              <h3>최근 로그</h3>
              <div className="models-list">
                {(job?.stage_logs || []).slice(0, 5).map((log, index) => (
                  <span className="mui-chip mui-chip--md mui-chip--outlined" key={`${log.stage_name}-${index}`}>
                    {log.stage_name} · {log.total_progress}%
                  </span>
                ))}
                {(!job?.stage_logs || job.stage_logs.length === 0) && (
                  <span className="mui-chip mui-chip--md mui-chip--outlined">로그 대기 중</span>
                )}
              </div>
            </div>

            <div className="sidebar-card" style={{ background: "rgba(25,118,210,0.04)" }}>
              <h3 style={{ color: "#1976d2" }}>알림</h3>
              <div style={{ font: "400 13px/1.5 var(--font-sans)", color: "var(--fg-1)" }}>
                페이지를 벗어나도 서버 작업은 계속됩니다. 완료 후 대시보드와 기록 화면에서 결과를 다시 확인할 수 있습니다.
              </div>
            </div>
          </aside>
        </div>
      </div>
    </GarimPage>
  );
}
