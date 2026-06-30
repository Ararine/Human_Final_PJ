import { useState, useEffect } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { formatKstDateTime } from "../../utils/timezone";
import "../../css/garim-pages/AdminLoginHistory.css";

import GarimPage from "../../components/garim/GarimPage";
import {
  getAdminLoginHistories,
  getAdminLoginHistoryDetail,
  getAdminLoginHistoriesExportUrl,
} from "../../utils/api";
import { normalizeLoginHistoryListResponse } from "../../utils/adminLoginHistoryResponse";

// 로그인 결과 한글 라벨 매핑 정의
const RESULT_LABEL = {
  success: "성공",
  failed: "실패",
  blocked: "차단",
  deleted: "삭제",
  error: "오류",
};

// 로그인 결과 칩 클래스 매핑 정의
const RESULT_CLASS = {
  success: "result-success",
  failed: "result-failed",
  blocked: "result-blocked",
  deleted: "result-deleted",
  error: "result-error",
};

// 날짜시간 포맷팅 헬퍼 함수
function formatDateTimeSeconds(value) {
  if (!value) return "-";
  return formatKstDateTime(value, { second: "2-digit", hour12: false });
}

export default function AdminLoginHistory() {
  useDocumentTitle("로그인 히스토리 · Garim Admin");

  // 상태값 정의
  const [items, setItems] = useState([]);
  const [metrics, setMetrics] = useState({
    total_attempts: 0,
    success_count: 0,
    failed_count: 0,
    blocked_count: 0,
    success_rate: "0%",
    failed_rate: "0%",
    blocked_rate: "0%",
  });
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 필터 상태 정의
  const [searchType, setSearchType] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [period, setPeriod] = useState("30"); // 기본값 30일
  const [result, setResult] = useState("all");
  const [provider, setProvider] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // 현재 적용되어 동작 중인 필터 파라미터 (조회 버튼 클릭 시 갱신)
  const [activeFilters, setActiveFilters] = useState({
    search_type: "all",
    search_keyword: "",
    period: "30",
    result: "all",
    provider: "all",
    start_date: "",
    end_date: "",
  });

  // 상세 모달 상태 정의
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // 로그인 이력 조회 함수
  const fetchLoginHistories = async (currentPage, currentLimit, filters) => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        limit: currentLimit,
        search_type: filters.search_type || undefined,
        search_keyword: filters.search_keyword || undefined,
        period: filters.period !== "custom" ? filters.period : undefined,
        result: filters.result !== "all" ? filters.result : undefined,
        provider: filters.provider !== "all" ? filters.provider : undefined,
        start_date: filters.period === "custom" && filters.start_date ? filters.start_date : undefined,
        end_date: filters.period === "custom" && filters.end_date ? filters.end_date : undefined,
      };

      const res = await getAdminLoginHistories(params);
      const payload = normalizeLoginHistoryListResponse(res);
      setItems(payload.items);
      setTotal(payload.total);
      if (payload.metrics) {
        setMetrics(payload.metrics);
      }
    } catch (err) {
      console.error("Failed to load login histories", err);
      setError(err.message || "로그인 히스토리를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 페이지나 한 페이지당 개수, 적용 필터가 변경될 때 데이터 조회 실행
  useEffect(() => {
    fetchLoginHistories(page, limit, activeFilters);
  }, [page, limit, activeFilters]);

  // 검색/조회 버튼 핸들러
  const handleSearch = (e) => {
    if (e) e.preventDefault();
    setPage(1);
    setActiveFilters({
      search_type: searchType,
      search_keyword: searchKeyword,
      period,
      result,
      provider,
      start_date: startDate,
      end_date: endDate,
    });
  };

  // 필터 초기화 핸들러
  const handleReset = () => {
    setSearchType("all");
    setSearchKeyword("");
    setPeriod("30");
    setResult("all");
    setProvider("all");
    setStartDate("");
    setEndDate("");
    setPage(1);
    setActiveFilters({
      search_type: "all",
      search_keyword: "",
      period: "30",
      result: "all",
      provider: "all",
      start_date: "",
      end_date: "",
    });
  };

  // CSV 다운로드 핸들러
  const handleExportCsv = () => {
    const params = {
      search_type: activeFilters.search_type || undefined,
      search_keyword: activeFilters.search_keyword || undefined,
      period: activeFilters.period !== "custom" ? activeFilters.period : undefined,
      result: activeFilters.result !== "all" ? activeFilters.result : undefined,
      provider: activeFilters.provider !== "all" ? activeFilters.provider : undefined,
      start_date: activeFilters.period === "custom" && activeFilters.start_date ? activeFilters.start_date : undefined,
      end_date: activeFilters.period === "custom" && activeFilters.end_date ? activeFilters.end_date : undefined,
    };
    const exportUrl = getAdminLoginHistoriesExportUrl(params);
    window.open(exportUrl, "_blank");
  };

  // 상세 모달 열기 핸들러
  const handleOpenDetail = async (historyId) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailError(null);
    setSelectedHistory(null);
    try {
      const res = await getAdminLoginHistoryDetail(historyId);
      if (res && res.data) {
        setSelectedHistory(res.data);
      } else {
        throw new Error("상세 내역 데이터를 찾을 수 없습니다.");
      }
    } catch (err) {
      console.error("Failed to load history detail", err);
      setDetailError(err.message || "로그인 상세 정보를 불러오는데 실패했습니다.");
    } finally {
      setDetailLoading(false);
    }
  };

  // 상세 모달 닫기 핸들러
  const handleCloseDetail = () => {
    setDetailOpen(false);
    setSelectedHistory(null);
    setDetailError(null);
  };

  const totalPages = Math.ceil(total / limit) || 1;
  const startIdx = total === 0 ? 0 : (page - 1) * limit + 1;
  const endIdx = Math.min(page * limit, total);

  return (
    <GarimPage bodyClass="" screenLabel="32 Admin login history">
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
          <a href="/admin/login-history" className="active">
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
          <a href="/admin/reports">
            <span className="material-icons">report_problem</span>
            문의 내역
          </a>
        </aside>

        {/* 본문 영역 */}
        <main className="adm-main">
          {/* 상단 헤더 */}
          <div className="adm-head">
            <div>
              <h1>로그인 히스토리</h1>
              <p>사용자 로그인 성공/실패 이력 · 최근 30일 기준 요약 정보 및 전체 기록을 조회합니다.</p>
            </div>
            <button className="mui-btn mui-btn--contained admin-export-btn" onClick={handleExportCsv}>
              <span className="material-icons">download</span>
              CSV 내보내기
            </button>
          </div>

          {/* KPI 카드 4개 */}
          <div className="metric-row">
            <div className="metric">
              <div className="lbl">전체 시도</div>
              <div className="num">{(metrics.total_attempts || 0).toLocaleString()}</div>
              <div className="delta">최근 시도 건수 합계</div>
            </div>
            <div className="metric ok">
              <div className="lbl">성공</div>
              <div className="num">{(metrics.success_count || 0).toLocaleString()}</div>
              <div className="delta">성공률: {metrics.success_rate || "0%"}</div>
            </div>
            <div className="metric warn">
              <div className="lbl">실패</div>
              <div className="num">{(metrics.failed_count || 0).toLocaleString()}</div>
              <div className="delta">실패율: {metrics.failed_rate || "0%"}</div>
            </div>
            <div className="metric danger">
              <div className="lbl">차단 / 삭제</div>
              <div className="num">{(metrics.blocked_count || 0).toLocaleString()}</div>
              <div className="delta">비율: {metrics.blocked_rate || "0%"}</div>
            </div>
          </div>

          {/* 로그인 이력 목록 테이블 카드 (필터 및 페이징이 통합됨) */}
          <div className="adm-card table-card">
            <div className="table-card-header">
              <h2>로그인 이력 목록</h2>
              <div className="table-controls-bar">
                <div className="limit-selector">
                  <select
                    value={limit}
                    onChange={(e) => {
                      setLimit(Number(e.target.value));
                      setPage(1);
                    }}
                    aria-label="페이지당 표시 건수"
                  >
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                  <span className="limit-label">개씩 보기</span>
                </div>

                <div className="table-card-controls">
                  <form onSubmit={handleSearch} className="table-filter-form">
                    <div className="table-filter-grid">
                      <div className="filter-group">
                        <select
                          id="filter-period"
                          value={period}
                          onChange={(e) => setPeriod(e.target.value)}
                        >
                          <option value="7">최근 7일</option>
                          <option value="30">최근 30일</option>
                          <option value="90">최근 90일</option>
                          <option value="custom">직접 지정</option>
                        </select>
                      </div>

                      <div className="filter-group">
                        <select
                          id="filter-result"
                          value={result}
                          onChange={(e) => setResult(e.target.value)}
                        >
                          <option value="all">전체 결과</option>
                          <option value="success">성공</option>
                          <option value="failed">실패</option>
                          <option value="blocked">차단</option>
                          <option value="deleted">삭제</option>
                          <option value="error">오류</option>
                        </select>
                      </div>

                      <div className="filter-group">
                        <select
                          id="filter-provider"
                          value={provider}
                          onChange={(e) => setProvider(e.target.value)}
                        >
                          <option value="all">전체 제공자</option>
                          <option value="kakao">Kakao</option>
                          <option value="google">Google</option>
                          <option value="naver">Naver</option>
                          <option value="facebook">Facebook</option>
                          <option value="x">X (Twitter)</option>
                        </select>
                      </div>

                      <div className="filter-group search-select-input-group">
                        <select
                          id="filter-search-type"
                          value={searchType}
                          onChange={(e) => setSearchType(e.target.value)}
                          className="search-type-select"
                        >
                          <option value="all">전체 검색</option>
                          <option value="email">이메일</option>
                          <option value="user_id">사용자 ID</option>
                          <option value="ip">IP 주소</option>
                        </select>
                        <input
                          id="filter-search-keyword"
                          type="text"
                          placeholder={
                            searchType === "email"
                              ? "이메일 검색"
                              : searchType === "user_id"
                              ? "사용자 ID 검색"
                              : searchType === "ip"
                              ? "IP 주소 검색"
                              : "전체 검색"
                          }
                          value={searchKeyword}
                          onChange={(e) => setSearchKeyword(e.target.value)}
                          className="search-keyword-input"
                        />
                      </div>

                      <div className="filter-actions">
                        <button type="submit" className="mui-btn mui-btn--contained btn-submit">
                          <span className="material-icons">search</span>
                          조회
                        </button>
                        <button type="button" className="mui-btn mui-btn--outlined btn-reset" onClick={handleReset}>
                          초기화
                        </button>
                      </div>
                    </div>

                    {/* 직접 지정 기간 필터 (period === 'custom'인 경우 노출) */}
                    {period === "custom" && (
                      <div className="filter-date-range">
                        <div className="filter-group">
                          <input
                            id="filter-start-date"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                          />
                        </div>
                        <span>~</span>
                        <div className="filter-group">
                          <input
                            id="filter-end-date"
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                  </form>
                </div>
              </div>
            </div>

            {/* 테이블 뷰 포트 */}
            <div className="table-wrapper">
              <table className="login-history-table">
                <thead>
                  <tr>
                    <th>로그인 시각</th>
                    <th>사용자 정보</th>
                    <th>제공자</th>
                    <th>결과</th>
                    <th>실패 사유</th>
                    <th>IP 주소</th>
                    <th>브라우저 / OS</th>
                    <th>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8" className="table-state-cell">
                        데이터를 불러오는 중입니다...
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td colSpan="8" className="table-state-cell error-cell">
                        {error}
                      </td>
                    </tr>
                  ) : items.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="table-state-cell">
                        로그인 히스토리 이력이 존재하지 않습니다.
                      </td>
                    </tr>
                  ) : (
                    items.map((row) => {
                      const isHighlighted = selectedHistory && selectedHistory.login_history_id === row.login_history_id;
                      return (
                        <tr
                          key={row.login_history_id}
                          className={isHighlighted ? "highlighted-row" : ""}
                        >
                          <td className="mono">{formatDateTimeSeconds(row.logged_in_at)}</td>
                          <td>
                            <div className="user-email">{row.user_email || "-"}</div>
                          </td>
                          <td>
                            <span className={`provider-pill provider-${row.provider}`}>
                              {row.provider || "-"}
                            </span>
                          </td>
                          <td>
                            <span className={`result-badge ${RESULT_CLASS[row.login_result] || ""}`}>
                              {RESULT_LABEL[row.login_result] || row.login_result || "-"}
                            </span>
                          </td>
                          <td className="reason-cell" title={row.failure_reason || ""}>
                            {row.failure_reason || "-"}
                          </td>
                          <td className="mono">{row.ip_address || "-"}</td>
                          <td>{row.browser_device || "-"}</td>
                          <td>
                            <button
                              type="button"
                              className="mui-btn mui-btn--outlined mui-btn--sm btn-detail-trigger"
                              onClick={() => handleOpenDetail(row.login_history_id)}
                            >
                              상세
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* 페이지당 표시 개수 설정 및 페이지네이션 푸터 영역 */}
            <div className="table-footer-controls">
              <span className="summary-text">
                {total === 0 ? "0건" : `${startIdx}-${endIdx} / ${total.toLocaleString()}`}
              </span>
              <div className="pagination-actions">
                <button
                  type="button"
                  className="mui-btn mui-btn--outlined mui-btn--sm"
                  disabled={page <= 1 || loading}
                  onClick={() => setPage((p) => p - 1)}
                >
                  이전
                </button>
                <button
                  type="button"
                  className="mui-btn mui-btn--outlined mui-btn--sm"
                  disabled={page >= totalPages || loading}
                  onClick={() => setPage((p) => p + 1)}
                >
                  다음
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* 로그인 상세 정보 모달 팝업 */}
      {detailOpen && (
        <div className="login-detail-overlay" onClick={handleCloseDetail} role="dialog" aria-modal="true">
          <div className="login-detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="login-detail-modal__head">
              <h2>로그인 상세</h2>
              <button type="button" className="modal-close-btn" onClick={handleCloseDetail} aria-label="모달 닫기">
                <span className="material-icons">close</span>
              </button>
            </div>

            <div className="login-detail-modal__body">
              {detailLoading ? (
                <div className="modal-loading-state">상세 정보를 불러오는 중입니다...</div>
              ) : detailError ? (
                <div className="modal-error-state">{detailError}</div>
              ) : selectedHistory ? (
                <div className="login-detail-grid">
                  <div className="detail-label">사용자 이메일</div>
                  <div className="detail-value">{selectedHistory.user_email || "-"}</div>

                  <div className="detail-label">제공자</div>
                  <div className="detail-value">
                    <span className={`provider-pill provider-${selectedHistory.provider}`}>
                      {selectedHistory.provider || "-"}
                    </span>
                  </div>

                  <div className="detail-label">결과</div>
                  <div className="detail-value">
                    <span className={`result-badge ${RESULT_CLASS[selectedHistory.login_result] || ""}`}>
                      {RESULT_LABEL[selectedHistory.login_result] || selectedHistory.login_result || "-"}
                    </span>
                  </div>

                  <div className="detail-label">실패 사유</div>
                  <div className="detail-value reason-value">{selectedHistory.failure_reason || "-"}</div>

                  <div className="detail-label">로그인 시각</div>
                  <div className="detail-value mono">{formatDateTimeSeconds(selectedHistory.logged_in_at)}</div>

                  <div className="detail-label">IP 주소</div>
                  <div className="detail-value mono">{selectedHistory.ip_address || "-"}</div>

                  <div className="detail-label">브라우저/기기</div>
                  <div className="detail-value">{selectedHistory.browser_device || "-"}</div>

                  <div className="detail-label">OAuth 계정</div>
                  <div className="detail-value">{selectedHistory.oauth_account || "-"}</div>

                  <div className="detail-label">IP / User-Agent</div>
                  <div className="detail-value detail-user-agent">
                    <div>{selectedHistory.ip_address || "-"}</div>
                    <div className="ua-text">{selectedHistory.user_agent || "-"}</div>
                  </div>

                  <div className="detail-label">비고 (Note)</div>
                  <div className="detail-value">{selectedHistory.note || "-"}</div>
                </div>
              ) : null}
            </div>

            <div className="login-detail-modal__foot">
              <button type="button" className="mui-btn mui-btn--outlined btn-secondary" onClick={handleCloseDetail}>
                닫기
              </button>
              <button type="button" className="mui-btn mui-btn--contained btn-primary" onClick={handleCloseDetail}>
                확인
              </button>
            </div>
          </div>
        </div>
      )}
    </GarimPage>
  );
}
