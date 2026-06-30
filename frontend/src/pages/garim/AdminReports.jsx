import { useState, useEffect, useCallback, useMemo } from "react";
import { Link } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { getAdminReports, getAdminReportDetail, updateAdminReportStatus, deleteAdminReport, getApiBaseUrl } from "../../utils/api";
import { formatKstDateTime } from "../../utils/timezone";
import GarimHeader from "../../components/garim/GarimHeader";
import "../../css/garim-pages/AdminReports.css";

// 탭 정의 (report_type)
const TABS = [
  { id: "all",        label: "전체", tabLabel: "전체" },
  { id: "general",    label: "일반 문의", tabLabel: "일반" },
  { id: "billing",    label: "결제/환불", tabLabel: "결제" },
  { id: "bug_report", label: "버그 및 오탐지 신고", tabLabel: "오탐지" },
  { id: "abuse_report", label: "불법 콘텐츠 및 악용 신고", tabLabel: "악용" },
  { id: "other",      label: "기타", tabLabel: "기타" },
];

const STATUS_META = {
  received: { label: "대기중", chip: "mui-chip--warning" },
  in_progress: { label: "처리중", chip: "mui-chip--primary" },
  completed: { label: "완료", chip: "mui-chip--success" },
};

function getTypeLabel(type) {
  return TABS.find((tab) => tab.id === type)?.label || type || "-";
}

function getStatusMeta(status) {
  return STATUS_META[status] || STATUS_META.received;
}

export default function AdminReports() {
  useDocumentTitle("문의 내역 관리 · Garim Admin");

  // 상태 관리
  const [activeTab, setActiveTab] = useState("all");
  const [page, setPage] = useState(1);
  const size = 10;
  
  // 뷰 모드: "list" 또는 "detail"
  const [viewMode, setViewMode] = useState("list");
  
  // 데이터 상태
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  
  // 상세 데이터 상태
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // 첨부파일 미리보기 상태
  const [selectedMediaUrl, setSelectedMediaUrl] = useState(null);
  const [selectedMediaIsVideo, setSelectedMediaIsVideo] = useState(false);
  const [selectedJsonContent, setSelectedJsonContent] = useState(null);

  // JSON 검색 상태
  const [jsonSearchTerm, setJsonSearchTerm] = useState("");
  const [jsonSearchIndex, setJsonSearchIndex] = useState(0);

  // 리스트 로딩
  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAdminReports(activeTab, page, size);
      if (res.success) {
        setReports(res.items || []);
        setTotal(res.total || 0);
        setTotalPages(res.totalPages || 1);
      }
    } catch (err) {
      console.error("Failed to fetch reports", err);
      alert("문의 내역을 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }, [activeTab, page, size]);

  useEffect(() => {
    if (viewMode === "list") {
      fetchReports();
    }
  }, [fetchReports, viewMode]);

  // 탭 변경
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setPage(1);
    setViewMode("list");
  };

  // 상세 보기 클릭
  const handleReportClick = async (reportId) => {
    setDetailLoading(true);
    setViewMode("detail");
    try {
      const res = await getAdminReportDetail(reportId);
      if (res.success) {
        setDetailData(res.report);
      }
    } catch (err) {
      console.error("Failed to fetch report detail", err);
      alert("문의 상세를 불러오는데 실패했습니다.");
      setViewMode("list");
    } finally {
      setDetailLoading(false);
    }
  };

  // 목록으로 돌아가기 (페이지, 탭 상태는 useState로 유지됨)
  const handleBackToList = () => {
    setViewMode("list");
    setDetailData(null);
    setSelectedMediaUrl(null);
    setSelectedMediaIsVideo(false);
    setSelectedJsonContent(null);
    setJsonSearchTerm("");
    setJsonSearchIndex(0);
  };

  // 첨부파일 클릭 핸들러
  const handleFileClick = async (e, file) => {
    e.preventDefault();
    const fullUrl = `${getApiBaseUrl()}${file.url}`;
    const isJson = file.filename.toLowerCase().endsWith('.json');
    const isVideo = file.filename.toLowerCase().endsWith('.mp4') || file.filename.toLowerCase().endsWith('.webm');
    
    if (isJson) {
      try {
        // 인증정보 포함 (admin 권한 필요) - getAdminReportDetail 등에서 사용하는 쿠키 방식이므로 별도 header 불필요
        const res = await fetch(fullUrl, {credentials: "include"});
        if (!res.ok) throw new Error("Failed to fetch JSON");
        const data = await res.json();
        setSelectedJsonContent(JSON.stringify(data, null, 2));
      } catch (err) {
        console.error(err);
        alert("JSON 데이터를 불러오는데 실패했습니다.");
      }
    } else {
      setSelectedMediaUrl(fullUrl);
      setSelectedMediaIsVideo(isVideo);
    }
  };

  // JSON 검색 핸들러
  const handleSearchChange = (e) => {
    setJsonSearchTerm(e.target.value);
    setJsonSearchIndex(0);
  };

  const getHighlightedJson = () => {
    if (!selectedJsonContent) return { elements: null, matchCount: 0 };
    if (!jsonSearchTerm) return { elements: selectedJsonContent, matchCount: 0 };
    
    // 특수문자 이스케이프
    const escapedTerm = jsonSearchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedTerm})`, 'gi');
    const parts = selectedJsonContent.split(regex);
    const matchCount = Math.floor(parts.length / 2);
    
    let matchIdx = 0;
    const elements = parts.map((part, i) => {
      if (i % 2 === 1) { // 캡처된 그룹 (매치된 문자열)
        const isCurrent = matchIdx === jsonSearchIndex;
        const el = <mark key={i} id={isCurrent ? "current-json-match" : undefined} style={{ background: isCurrent ? "#ff9800" : "#fff59d", color: "#000", borderRadius: "2px", padding: "0 2px" }}>{part}</mark>;
        matchIdx++;
        return el;
      }
      return part;
    });
    
    return { elements, matchCount };
  };

  const highlighted = getHighlightedJson();
  const matchCount = highlighted.matchCount;
  const currentTabLabel = TABS.find((tab) => tab.id === activeTab)?.label || "전체";
  const pageStatusCounts = useMemo(() => {
    return reports.reduce(
      (acc, report) => {
        if (report.status === "completed") acc.completed += 1;
        else if (report.status === "in_progress") acc.inProgress += 1;
        else acc.received += 1;
        return acc;
      },
      { received: 0, inProgress: 0, completed: 0 },
    );
  }, [reports]);

  const handleNextMatch = () => {
    if (matchCount > 0) {
      setJsonSearchIndex((prev) => (prev + 1) % matchCount);
    }
  };

  const handlePrevMatch = () => {
    if (matchCount > 0) {
      setJsonSearchIndex((prev) => (prev - 1 + matchCount) % matchCount);
    }
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (e.shiftKey) {
        handlePrevMatch();
      } else {
        handleNextMatch();
      }
    }
  };

  // 현재 매치된 항목으로 자동 스크롤
  useEffect(() => {
    if (jsonSearchTerm && matchCount > 0) {
      const el = document.getElementById("current-json-match");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [jsonSearchIndex, jsonSearchTerm, matchCount]);

  // 상태 변경
  const handleStatusChange = async (newStatus) => {
    if (!detailData) return;
    try {
      const res = await updateAdminReportStatus(detailData.id, newStatus);
      if (res.success) {
        setDetailData({ ...detailData, status: newStatus });
        alert("상태가 업데이트되었습니다.");
      }
    } catch (err) {
      console.error("Failed to update status", err);
      alert("상태 업데이트에 실패했습니다.");
    }
  };

  // 문의내역 삭제
  const handleDelete = async (e, reportId) => {
    e.stopPropagation(); // 행 클릭 이벤트(상세보기) 방지
    if (!window.confirm("해당 문의내역을 삭제하시겠습니까?")) return;

    try {
      const res = await deleteAdminReport(reportId);
      if (res.success) {
        alert("성공적으로 삭제되었습니다.");
        // 리스트에서 삭제된 항목 제거
        setReports(prev => prev.filter(r => r.id !== reportId));
        setTotal(prev => prev - 1);
        if (viewMode === "detail" && detailData && detailData.id === reportId) {
          handleBackToList();
        }
      }
    } catch (err) {
      console.error("Failed to delete report", err);
      alert("삭제 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="admin-layout">
      <GarimHeader layout="admin" />
      <div className="adm-shell">
        {/* 일관된 순서로 정비된 공통 관리자 사이드바 */}
        <aside className="adm-side">
          <div className="sec">운영</div>
          <a href="/admin/monitoring">
            <span className="material-icons">monitor_heart</span>
            사용자 모니터링
          </a>
          <a href="/admin/queue">
            <span className="material-icons">queue</span>
            처리 큐
          </a>
          <a href="/admin/compliance">
            <span className="material-icons">verified_user</span>
            컴플라이언스
          </a>
          <div className="sec">시스템</div>
          <a href="/admin/users">
            <span className="material-icons">people</span>
            사용자
          </a>
          <a href="/admin/login-history">
            <span className="material-icons">manage_history</span>
            로그인 히스토리
          </a>
          <a href="/admin/policy">
            <span className="material-icons">tune</span>
            정책 및 상품 관리
          </a>
          <a href="/admin/subscriptions">
            <span className="material-icons">subscriptions</span>
            구독 관리
          </a>
          <a href="/admin/payments">
            <span className="material-icons">payments</span>
            사용자 결제 확인
          </a>
          <a href="/admin/analytics">
            <span className="material-icons">analytics</span>
            분석
          </a>
          <a href="/admin/reports" className="active">
            <span className="material-icons">report_problem</span>
            문의 내역
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>문의 내역</h1>
            <span className="meta">사용자가 남긴 신고 및 고객 문의를 처리합니다.</span>
          </div>

          <div className="arp-pad-20">
            <div className="arp-summary-grid">
              <div className="arp-summary-card">
                <span className="lbl">선택 탭</span>
                <strong>{currentTabLabel}</strong>
                <span className="hint">{total.toLocaleString("ko-KR")}건</span>
              </div>
              <div className="arp-summary-card warn">
                <span className="lbl">현재 페이지 대기</span>
                <strong>{pageStatusCounts.received.toLocaleString("ko-KR")}</strong>
                <span className="hint">접수 후 확인 필요</span>
              </div>
              <div className="arp-summary-card info">
                <span className="lbl">현재 페이지 처리중</span>
                <strong>{pageStatusCounts.inProgress.toLocaleString("ko-KR")}</strong>
                <span className="hint">응대 진행 중</span>
              </div>
              <div className="arp-summary-card success">
                <span className="lbl">현재 페이지 완료</span>
                <strong>{pageStatusCounts.completed.toLocaleString("ko-KR")}</strong>
                <span className="hint">처리 완료</span>
              </div>
            </div>

            {/* 탭 헤더 */}
            <div className="arp-tabs">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={activeTab === tab.id ? "active" : ""}
                  onClick={() => handleTabChange(tab.id)}
                >
                  {tab.tabLabel || tab.label}
                </button>
              ))}
            </div>

            {viewMode === "list" && (
              <div className="report-list-view">
                <div className="arp-list-head">
                  <div>
                    <h2>문의 목록</h2>
                    <p>{currentTabLabel} 기준으로 접수 내역을 최신순으로 확인합니다.</p>
                  </div>
                  <span className="arp-list-count">
                    {total === 0
                      ? "0건"
                      : `${(page - 1) * size + 1}-${Math.min(page * size, total)} / ${total.toLocaleString("ko-KR")}건`}
                  </span>
                </div>
                {loading ? (
                  <div className="arp-loading">데이터를 불러오는 중입니다...</div>
                ) : reports.length === 0 ? (
                  <div className="arp-empty">해당 조건의 문의 내역이 없습니다.</div>
                ) : (
                  <>
                    <div className="arp-data-table">
                      <div className="arp-row arp-row--head">
                        <span>ID</span>
                        <span>유형</span>
                        <span>제목</span>
                        <span>작성자</span>
                        <span>작성일</span>
                        <span>상태</span>
                        <span>관리</span>
                      </div>
                      {reports.map((r) => (
                        <div
                          key={r.id}
                          onClick={() => handleReportClick(r.id)}
                          className="arp-row arp-row-click"
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              handleReportClick(r.id);
                            }
                          }}
                        >
                          <span className="arp-td-id">{r.id.substring(0, 8)}</span>
                          <span>
                            <span className="mui-chip mui-chip--sm mui-chip--outlined">
                              {getTypeLabel(r.type)}
                            </span>
                          </span>
                          <span className="arp-title-cell">{r.title || "-"}</span>
                          <span>{r.userId ? r.userId.substring(0, 8) : "비회원"}</span>
                          <span>{formatKstDateTime(r.createdAt)}</span>
                          <span>
                            <span className={`mui-chip mui-chip--sm ${getStatusMeta(r.status).chip}`}>
                              {getStatusMeta(r.status).label}
                            </span>
                          </span>
                          <span>
                            <button
                              className="mui-btn mui-btn--sm mui-btn--outlined arp-del-btn"
                              onClick={(e) => handleDelete(e, r.id)}
                            >
                              삭제
                            </button>
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="admin-pagination arp-pagination-row">
                        <button 
                          className="mui-btn mui-btn--outlined mui-btn--sm" 
                          disabled={page === 1}
                          onClick={() => setPage(p => p - 1)}
                        >
                          이전
                        </button>
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                          <button
                            key={p}
                            className={`mui-btn mui-btn--sm ${page === p ? "mui-btn--contained" : "mui-btn--text"}`}
                            onClick={() => setPage(p)}
                          >
                            {p}
                          </button>
                        ))}
                        <button 
                          className="mui-btn mui-btn--outlined mui-btn--sm"
                          disabled={page === totalPages}
                          onClick={() => setPage(p => p + 1)}
                        >
                          다음
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {viewMode === "detail" && (
              <div className="report-detail-view">
                {detailLoading || !detailData ? (
                  <div className="arp-loading">상세 정보를 불러오는 중입니다...</div>
                ) : (
                  <div className="report-detail-content">
                    <div className="arp-detail-head">
                      <div>
                        <div className="arp-mb-8">
                          <span className="mui-chip mui-chip--sm mui-chip--outlined arp-chip-mr">
                            {getTypeLabel(detailData.type)}
                          </span>
                          <span className={`mui-chip mui-chip--sm ${getStatusMeta(detailData.status).chip} arp-chip-mr`}>
                            {getStatusMeta(detailData.status).label}
                          </span>
                          <span className="arp-meta-date">
                            {formatKstDateTime(detailData.createdAt)}
                          </span>
                        </div>
                        <h2 className="arp-detail-title">{detailData.title}</h2>
                        <div className="arp-author">
                          작성자: {detailData.userId || "비회원"}
                        </div>
                      </div>
                      <button className="mui-btn mui-btn--outlined" onClick={handleBackToList}>
                        목록으로
                      </button>
                    </div>

                    <section className="arp-section">
                      <div className="arp-section-head">
                        <h3>문의 내용</h3>
                      </div>
                      <div className="arp-description">
                      {detailData.description}
                      </div>
                    </section>

                    {/* 오탐지 신고 관련 파일 첨부 */}
                    {detailData.targetJobId && detailData.files && detailData.files.length > 0 && (
                      <section className="arp-section">
                        <div className="arp-section-head">
                          <h3>첨부 파일</h3>
                          <span>관련 작업 ID: {detailData.targetJobId.substring(0, 8)}</span>
                        </div>
                        <div className="arp-attach-list">
                          {[...detailData.files].sort((a, b) => {
                            const aIsJson = a.filename.toLowerCase().endsWith('.json');
                            const bIsJson = b.filename.toLowerCase().endsWith('.json');
                            if (aIsJson && !bIsJson) return 1;
                            if (!aIsJson && bIsJson) return -1;
                            return 0;
                          }).map((file, idx) => (
                            <button 
                              key={idx} 
                              onClick={(e) => handleFileClick(e, file)}
                              className="mui-btn mui-btn--outlined mui-btn--sm arp-attach-btn"
                            >
                              <span className="material-icons arp-ico-18">
                                {file.filename.toLowerCase().endsWith('.json') ? 'data_object' : 'image'}
                              </span>
                              {file.filename}
                            </button>
                          ))}
                        </div>
                        <p className="arp-attach-note">
                          * 위 파일들은 신고 접수 시점에 안전하게 복사되어 보존된 원본(상세보기) 및 결과 데이터입니다.
                        </p>
                      </section>
                    )}

                    {/* 상태 처리 */}
                    <div className="arp-status-panel">
                      <div>
                        <span className="arp-status-label">처리 상태 관리</span>
                        <div className="arp-status-btns">
                          {['received', 'in_progress', 'completed'].map(status => (
                            <button
                              key={status}
                              onClick={() => handleStatusChange(status)}
                              className={`mui-btn mui-btn--sm ${detailData.status === status ? 'mui-btn--contained' : 'mui-btn--outlined'}`}
                            >
                              {status === 'received' ? '대기중' : status === 'in_progress' ? '처리중' : '처리완료'}
                            </button>
                          ))}
                        </div>
                      </div>
                      <button
                        className="mui-btn mui-btn--sm mui-btn--outlined arp-del-btn"
                        onClick={(e) => handleDelete(e, detailData.id)}
                      >
                        삭제
                      </button>
                    </div>

                    {/* 첨부파일 미리보기 영역 */}
                    {(selectedMediaUrl || selectedJsonContent) && (
                      <div className="arp-preview-grid">
                        <div className="arp-preview-panel arp-preview-panel--media">
                          <div className="arp-preview-head">미디어 미리보기</div>
                          {!selectedMediaUrl ? (
                            <span className="arp-media-empty">이미지/영상을 선택하세요</span>
                          ) : selectedMediaIsVideo ? (
                            <video src={selectedMediaUrl} controls autoPlay muted className="arp-media" />
                          ) : (
                            <img src={selectedMediaUrl} alt="preview" className="arp-media" />
                          )}
                        </div>

                        <div className="arp-preview-panel arp-preview-panel--json">
                          <div className="arp-preview-head">JSON 데이터</div>
                          {!selectedJsonContent ? (
                            <div className="arp-json-empty">
                              JSON 파일을 선택하세요
                            </div>
                          ) : (
                            <>
                              {/* 찾기 (Ctrl+F 기능) 헤더 */}
                              <div className="arp-json-toolbar">
                                <input
                                  type="text"
                                  placeholder="JSON 내에서 찾기... (Enter로 다음)"
                                  value={jsonSearchTerm}
                                  onChange={handleSearchChange}
                                  onKeyDown={handleSearchKeyDown}
                                />
                                {jsonSearchTerm && (
                                  <span className="arp-match-count">
                                    {matchCount > 0 ? `${jsonSearchIndex + 1} / ${matchCount}` : "0 / 0"}
                                  </span>
                                )}
                                <button
                                  onClick={handlePrevMatch}
                                  className="arp-nav-btn"
                                  title="이전 (Shift+Enter)"
                                >
                                  <span className="material-icons arp-ico-16">keyboard_arrow_up</span>
                                </button>
                                <button
                                  onClick={handleNextMatch}
                                  className="arp-nav-btn"
                                  title="다음 (Enter)"
                                >
                                  <span className="material-icons arp-ico-16">keyboard_arrow_down</span>
                                </button>
                              </div>

                              <pre className="arp-json-pre">
                                {jsonSearchTerm ? highlighted.elements : selectedJsonContent}
                              </pre>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
