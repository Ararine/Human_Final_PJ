import { useState, useEffect } from "react";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminUsers.css";

import GarimPage from "../../components/garim/GarimPage";
import { getAdminUsers } from "../../utils/api";

const STATUS_CHIP = {
  active:    "mui-chip--soft-success",
  suspended: "mui-chip--soft-warning",
  deleted:   "mui-chip--soft-error",
};

const PAGE_LIMIT = 20;

export default function AdminUsers() {
  useDocumentTitle("사용자 관리 · Garim Admin");

  const [users,      setUsers]      = useState([]);
  const [metrics,    setMetrics]    = useState({ total: 0, active: 0, suspended: 0, deleted: 0 });
  const [page,       setPage]       = useState(1);
  const [pageLimit,  setPageLimit]  = useState(20);
  const [total,      setTotal]      = useState(0);
  const [roleFilter, setRoleFilter] = useState("");
  const [statFilter, setStatFilter] = useState("");
  const [search,     setSearch]     = useState("");
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAdminUsers({ page, limit: pageLimit, role: roleFilter || undefined, status: statFilter || undefined })
      .then((res) => {
        const d = res.data;
        setUsers(d.users);
        setTotal(d.total);
        setMetrics({ total: d.total, active: d.active, suspended: d.suspended, deleted: d.deleted });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, pageLimit, roleFilter, statFilter]);

  const filteredUsers = search
    ? users.filter(
        (u) =>
          u.email.toLowerCase().includes(search.toLowerCase()) ||
          u.user_id.toLowerCase().includes(search.toLowerCase())
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
          <a href="/admin/analytics">
            <span className="material-icons">analytics</span>
            분석
          </a>
          <a href="/admin/policy">
            <span className="material-icons">tune</span>
            정책 설정
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>사용자 관리</h1>
            <span className="meta">전체 가입 회원 · 역할·상태 편집</span>
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

          <div className="usr-toolbar">
            <input
              className="usr-search"
              type="search"
              placeholder="이메일·UID 검색…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="usr-filter-sel"
              value={roleFilter}
              onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
            >
              <option value="">전체 역할</option>
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
            <select
              className="usr-filter-sel"
              value={statFilter}
              onChange={(e) => { setStatFilter(e.target.value); setPage(1); }}
            >
              <option value="">전체 상태</option>
              <option value="active">active</option>
              <option value="suspended">suspended</option>
              <option value="deleted">deleted</option>
            </select>
          </div>
          <div className="usr-limit-row">
            <select
              className="usr-limit-sel"
              value={pageLimit}
              onChange={(e) => { setPageLimit(Number(e.target.value)); setPage(1); }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            <span className="usr-limit-label">개씩 보기</span>
          </div>

          <div className="adm-card">
            <div className="usr-row tbl-head">
              <span>UID</span>
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
                <span className="mono">{u.user_id}</span>
                <span>{u.email}</span>
                <span>
                  <span className="mui-chip">{u.provider || "—"}</span>
                </span>
                <span>
                  <span className={`mui-chip ${u.role === "admin" ? "mui-chip--soft-primary" : ""}`}>
                    {u.role}
                  </span>
                </span>
                <span>
                  <span className={`mui-chip ${STATUS_CHIP[u.status] || ""}`}>
                    {u.status}
                  </span>
                </span>
                <span className="mono">{u.created_at}</span>
                <span className="usr-actions">
                  <button className="mui-btn mui-btn--outlined mui-btn--sm">편집</button>
                </span>
              </div>
            ))}
          </div>

          <div className="usr-pagination">
            <span className="meta">
              {total === 0 ? "0건" : `${(page - 1) * pageLimit + 1}–${Math.min(page * pageLimit, total)} / ${total.toLocaleString()}`}
            </span>
            <div style={{ display: "flex", gap: "4px" }}>
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
        </main>
      </div>
    </GarimPage>
  );
}
