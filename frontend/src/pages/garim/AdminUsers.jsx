import { useState, useEffect } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminUsers.css";

import GarimPage from "../../components/garim/GarimPage";
import { getAdminUsers, updateAdminUser } from "../../utils/api";

const STATUS_CHIP = {
  active:    "mui-chip--soft-success",
  suspended: "mui-chip--soft-warning",
  deleted:   "mui-chip--soft-error",
};

// 사용자 상태 한글 매핑 정의
const STATUS_LABEL = {
  active:    "활성",
  suspended: "정지",
  deleted:   "탈퇴",
};

// 사용자 역할 한글 매핑 정의
const ROLE_LABEL = {
  user:      "일반 사용자",
  admin:     "관리자",
};

// 제공자별 칩 스타일 매핑 정의
const PROVIDER_CHIP = {
  google: "mui-chip--soft-primary", // 구글: 파란색
  kakao:  "mui-chip--soft-warning", // 카카오: 노란색
  naver:  "mui-chip--soft-success", // 네이버: 초록색
};

// 역할별 칩 스타일 매핑 정의
const ROLE_CHIP = {
  admin:  "mui-chip--soft-warning", // 관리자: 노란색
  user:   "",                       // 일반 사용자: 기본 스타일
};

const PAGE_LIMIT = 20;

export default function AdminUsers() {
  useDocumentTitle("사용자 관리 · Garim Admin");

  const [users,      setUsers]      = useState([]);
  const [metrics,    setMetrics]    = useState({ total: 0, active: 0, suspended: 0, deleted: 0 });
  const [page,       setPage]       = useState(1);
  const [pageLimit,  setPageLimit]  = useState(PAGE_LIMIT);
  const [total,      setTotal]      = useState(0);
  const [roleFilter, setRoleFilter] = useState("");
  const [statFilter, setStatFilter] = useState("");
  const [search,     setSearch]     = useState("");
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [queryVersion, setQueryVersion] = useState(0); // 강제 목록 갱신용 카운터

  // 사용자 편집 모달용 상태 관리
  const [editOpen,   setEditOpen]   = useState(false);
  const [editUser,   setEditUser]   = useState(null);
  const [editRole,   setEditRole]   = useState("user");
  const [editStatus, setEditStatus] = useState("active");
  const [editSaving, setEditSaving] = useState(false);
  const [editError,  setEditError]  = useState(null);

  useEffect(() => {
    let ignore = false;

    Promise.resolve()
      .then(() => {
        if (ignore) return null;
        setLoading(true);
        setError(null);
        return getAdminUsers({ page, limit: pageLimit, role: roleFilter || undefined, status: statFilter || undefined });
      })
      .then((res) => {
        if (ignore || !res) return;
        const d = res.data;
        setUsers(d.users);
        setTotal(d.total);
        setMetrics({ total: d.total, active: d.active, suspended: d.suspended, deleted: d.deleted });
      })
      .catch((e) => {
        if (!ignore) setError(e.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [page, pageLimit, roleFilter, statFilter, queryVersion]);

  // 편집 모달 활성화 핸들러 함수
  const handleOpenEdit = (user) => {
    setEditUser(user);
    setEditRole(user.role || "user");
    setEditStatus(user.status || "active");
    setEditError(null);
    setEditOpen(true);
  };

  // 사용자 역할(role) 및 상태(status) 업데이트 저장 요청 핸들러 함수
  const handleSaveEdit = async () => {
    if (!editUser) return;
    setEditSaving(true);
    setEditError(null);
    try {
      await updateAdminUser(editUser.user_id, {
        role: editRole,
        status: editStatus,
      });
      setQueryVersion((v) => v + 1); // 테이블 목록 리로드
      setEditOpen(false);
      setEditUser(null);
    } catch (e) {
      setEditError(e.message || "사용자 정보를 변경하지 못했습니다.");
    } finally {
      setEditSaving(false);
    }
  };

  // 사용자의 요청에 따라 검색 시 UID 매칭을 배제하고 이메일로만 필터링하도록 수정합니다.
  const filteredUsers = search
    ? users.filter(
        (u) =>
          u.email.toLowerCase().includes(search.toLowerCase())
      )
    : users;

  const totalPages = Math.ceil(total / pageLimit);

  return (
    <GarimPage bodyClass="" screenLabel="28 Admin users">
      <div className="adm-shell">
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
          <a href="/admin/users" className="active">
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
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <div>
              <h1>사용자 관리</h1>
              <p>전체 가입 회원 목록을 조회하고 역할 및 관리 상태를 편집합니다.</p>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <div className="lbl">전체 사용자</div>
              <div className="num">{metrics.total.toLocaleString()}</div>
            </div>
            <div className="metric">
              <div className="lbl">활성</div>
              <div className="num">{metrics.active.toLocaleString()}</div>
              <div className="delta">{metrics.total ? ((metrics.active / metrics.total) * 100).toFixed(1) : 0}%</div>
            </div>
            <div className="metric warn">
              <div className="lbl">정지</div>
              <div className="num">{metrics.suspended.toLocaleString()}</div>
              <div className="delta">{metrics.total ? ((metrics.suspended / metrics.total) * 100).toFixed(1) : 0}%</div>
            </div>
            <div className="metric danger">
              <div className="lbl">탈퇴</div>
              <div className="num">{metrics.deleted.toLocaleString()}</div>
              <div className="delta">{metrics.total ? ((metrics.deleted / metrics.total) * 100).toFixed(1) : 0}%</div>
            </div>
          </div>

          <div className="adm-card">
            <div className="usr-card-head">
              <div>
                <h2>사용자 목록</h2>
                <p>가입 회원 목록을 이메일, 역할, 상태 필터 기준으로 조회합니다.</p>
              </div>

              <div className="usr-card-controls">
                <div className="usr-card-title-tools">
                  <select
                    className="usr-limit-sel"
                    value={pageLimit}
                    onChange={(e) => { setPageLimit(Number(e.target.value)); setPage(1); }}
                    aria-label="페이지당 사용자 개수"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                  <span className="usr-limit-label">개씩 보기</span>
                </div>

                <div className="usr-toolbar">
                  <select
                    className="usr-filter-sel"
                    value={roleFilter}
                    onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
                    aria-label="역할 필터"
                  >
                    <option value="">전체 역할</option>
                    <option value="user">일반 사용자</option>
                    <option value="admin">관리자</option>
                  </select>
                  <select
                    className="usr-filter-sel"
                    value={statFilter}
                    onChange={(e) => { setStatFilter(e.target.value); setPage(1); }}
                    aria-label="상태 필터"
                  >
                    <option value="">전체 상태</option>
                    <option value="active">활성</option>
                    <option value="suspended">정지</option>
                    <option value="deleted">탈퇴</option>
                  </select>
                  <div className="usr-search-wrap">
                    <input
                      className="usr-search"
                      type="search"
                      placeholder="이메일 검색…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      aria-label="사용자 검색"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="usr-data-table">
              <div className="usr-row tbl-head">
                <span>이메일</span>
                <span>제공자</span>
                <span>역할</span>
                <span>상태</span>
                <span>가입일</span>
                <span>작업</span>
              </div>

              {loading && (
                <div style={{ padding: "32px 16px", textAlign: "center", color: "var(--fg-2)", font: "400 13px var(--font-sans)" }}>
                  불러오는 중…
                </div>
              )}
              {!loading && error && (
                <div style={{ padding: "32px 16px", textAlign: "center", color: "#d32f2f", font: "400 13px var(--font-sans)" }}>
                  {error}
                </div>
              )}
              {!loading && !error && filteredUsers.length === 0 && (
                <div style={{ padding: "32px 16px", textAlign: "center", color: "var(--fg-3)", font: "400 13px var(--font-sans)" }}>
                  등록된 사용자가 없습니다.
                </div>
              )}
              {!loading && !error && filteredUsers.map((u) => (
                <div className="usr-row" key={u.user_id}>
                  <span>{u.email}</span>
                  <span>
                    {/* 제공자에 맞는 색상 칩 적용 (google: 파란색, kakao: 노란색, naver: 초록색) */}
                    <span className={`mui-chip ${PROVIDER_CHIP[u.provider] || ""}`}>
                      {u.provider || "—"}
                    </span>
                  </span>
                  <span>
                    {/* 역할에 맞는 색상 칩 적용 (admin: 노란색) 및 한글화 */}
                    <span className={`mui-chip ${ROLE_CHIP[u.role] || ""}`}>
                      {ROLE_LABEL[u.role] || u.role}
                    </span>
                  </span>
                  <span>
                    {/* 영문 상태값을 한글 레이블로 변환하여 출력 */}
                    <span className={`mui-chip ${STATUS_CHIP[u.status] || ""}`}>
                      {STATUS_LABEL[u.status] || u.status}
                    </span>
                  </span>
                  <span className="mono">{u.created_at}</span>
                  <span className="usr-actions">
                    <button className="mui-btn mui-btn--outlined mui-btn--sm" onClick={() => handleOpenEdit(u)}>편집</button>
                  </span>
                </div>
              ))}
            </div>

            {/* [5번 박스] 페이지 변경 통합 Footer */}
            <div className="usr-pagination">
              <span className="meta">
                {total === 0 ? "0건" : `${(page - 1) * pageLimit + 1}–${Math.min(page * pageLimit, total)} / ${total.toLocaleString()}`}
              </span>

              <div className="usr-pagination-actions">
                <button
                  className="mui-btn mui-btn--outlined mui-btn--sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  이전
                </button>
                <button
                  className="mui-btn mui-btn--outlined mui-btn--sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  다음
                </button>
              </div>
            </div>

          </div>
        </main>
      </div>

      {/* 노란 박스 필드들이 모두 제외된 깔끔한 사용자 역할/상태 편집 모달 팝업 */}
      {editOpen && editUser && (
        <div className="usr-modal-backdrop" onClick={() => setEditOpen(false)}>
          <div className="usr-modal" onClick={(e) => e.stopPropagation()}>
            <div className="usr-modal-head">
              <div>
                <h2>사용자 편집</h2>
                <p>사용자 계정 정보와 상태를 수정합니다.</p>
              </div>
              <button
                type="button"
                className="usr-icon-btn"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "34px",
                  height: "34px",
                  border: "1px solid var(--mui-border)",
                  borderRadius: "4px",
                  background: "#fff",
                  color: "var(--fg-2)",
                  cursor: "pointer"
                }}
                onClick={() => setEditOpen(false)}
                aria-label="닫기"
              >
                <span className="material-icons">close</span>
              </button>
            </div>

            <div className="usr-modal-body">
              {editError && (
                <div style={{ color: "#d32f2f", fontSize: "13px", marginBottom: "8px", textAlign: "left" }}>
                  {editError}
                </div>
              )}

              <div className="usr-modal-row">
                <div className="usr-form-group">
                  <label>이메일</label>
                  <input type="text" value={editUser.email} disabled />
                </div>
                <div className="usr-form-group">
                  <label>제공자</label>
                  <div className="usr-provider-badge">
                    {editUser.provider ? editUser.provider.toUpperCase() : "자체 가입"}
                  </div>
                </div>
              </div>

              <div className="usr-modal-row">
                <div className="usr-form-group">
                  <label>역할</label>
                  <select value={editRole} onChange={(e) => setEditRole(e.target.value)}>
                    <option value="user">일반 사용자</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
                <div className="usr-form-group">
                  <label>상태</label>
                  <div className="usr-radio-group">
                    <label className="usr-radio-label">
                      <input
                        type="radio"
                        name="editStatus"
                        value="active"
                        checked={editStatus === "active"}
                        onChange={() => setEditStatus("active")}
                      />
                      활성
                    </label>
                    <label className="usr-radio-label">
                      <input
                        type="radio"
                        name="editStatus"
                        value="suspended"
                        checked={editStatus === "suspended"}
                        onChange={() => setEditStatus("suspended")}
                      />
                      정지
                    </label>
                    <label className="usr-radio-label">
                      <input
                        type="radio"
                        name="editStatus"
                        value="deleted"
                        checked={editStatus === "deleted"}
                        onChange={() => setEditStatus("deleted")}
                      />
                      탈퇴
                    </label>
                  </div>
                </div>
              </div>

              <div className="usr-modal-row">
                <div className="usr-form-group">
                  <label>가입일</label>
                  <input type="text" value={editUser.created_at || "-"} disabled />
                </div>
                <div className="usr-form-group">
                  <label>최근 로그인</label>
                  <input type="text" value={editUser.last_login_at || "-"} disabled />
                </div>
              </div>

              <div className="usr-modal-actions">
                <button
                  type="button"
                  className="mui-btn mui-btn--outlined"
                  onClick={() => setEditOpen(false)}
                  disabled={editSaving}
                >
                  취소
                </button>
                <button
                  type="button"
                  className="mui-btn mui-btn--contained"
                  onClick={handleSaveEdit}
                  disabled={editSaving}
                >
                  {editSaving ? "저장 중…" : "저장"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </GarimPage>
  );
}
