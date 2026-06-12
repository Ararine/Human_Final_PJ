import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/AdminAnalytics.css";

import GarimPage from "../../components/garim/GarimPage";

export default function AdminAnalytics() {
  useDocumentTitle("분석 · Garim Admin");

  return (
    <GarimPage bodyClass="" screenLabel="29 Admin analytics">
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
          <a href="/admin/analytics" className="active">
            <span className="material-icons">analytics</span>
            분석
          </a>
        </aside>
        <main className="adm-main">
          <div className="adm-head">
            <h1>분석</h1>
            <span className="meta">서비스 지표 · 최근 30일</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
              <select className="an-period-sel">
                <option>최근 7일</option>
                <option selected>최근 30일</option>
                <option>최근 90일</option>
              </select>
              <button className="mui-btn mui-btn--outlined mui-btn--sm">
                <span className="material-icons" style={{ fontSize: "16px" }}>file_download</span>
                CSV Export
              </button>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <div className="lbl">처리 건수</div>
              <div className="num">8,432</div>
              <div className="delta">↑ 14% vs 전월</div>
            </div>
            <div className="metric">
              <div className="lbl">신규 가입</div>
              <div className="num">312</div>
              <div className="delta">↑ 7% vs 전월</div>
            </div>
            <div className="metric warn">
              <div className="lbl">평균 처리 시간</div>
              <div className="num">4.2s</div>
              <div className="delta">↑ 0.3s vs 전월</div>
            </div>
            <div className="metric">
              <div className="lbl">처리 성공률</div>
              <div className="num">98.1%</div>
              <div className="delta">↓ 0.2% vs 전월</div>
            </div>
          </div>

          <div className="an-grid">
            <div className="adm-card">
              <div className="head">
                <h3>일별 처리 건수</h3>
                <span className="meta">최근 30일</span>
              </div>
              <div className="body an-chart-placeholder">
                <span className="material-icons an-chart-icon">bar_chart</span>
                <p>차트 영역 (v2 예정)</p>
              </div>
            </div>
            <div className="adm-card">
              <div className="head">
                <h3>제공자별 가입 비율</h3>
              </div>
              <div className="body an-chart-placeholder">
                <span className="material-icons an-chart-icon">pie_chart</span>
                <p>차트 영역 (v2 예정)</p>
              </div>
            </div>
          </div>

          <div className="adm-card" style={{ marginTop: "16px" }}>
            <div className="head">
              <h3>요금제별 사용 현황</h3>
            </div>
            <div className="body">
              <div className="an-plan-row tbl-head">
                <span>요금제</span>
                <span>사용자 수</span>
                <span>처리 건수</span>
                <span>평균 파일 크기</span>
                <span>비율</span>
              </div>
              {[
                { plan: "Free", users: "1,018", jobs: "3,241", avgSize: "2.4 MB", pct: "38.4%" },
                { plan: "Pro", users: "221", jobs: "4,891", avgSize: "18.7 MB", pct: "58.0%" },
                { plan: "Enterprise", users: "45", jobs: "300", avgSize: "64.2 MB", pct: "3.6%" },
              ].map((r) => (
                <div className="an-plan-row" key={r.plan}>
                  <span><span className="mui-chip">{r.plan}</span></span>
                  <span>{r.users}</span>
                  <span>{r.jobs}</span>
                  <span>{r.avgSize}</span>
                  <span>{r.pct}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="adm-card" style={{ marginTop: "16px" }}>
            <div className="head">
              <h3>처리 실패 유형</h3>
            </div>
            <div className="body">
              <div className="an-err-row tbl-head">
                <span>오류 유형</span>
                <span>건수</span>
                <span>비율</span>
              </div>
              {[
                { type: "파일 형식 불가", count: "89", pct: "54.3%" },
                { type: "파일 크기 초과", count: "41", pct: "25.0%" },
                { type: "처리 시간 초과", count: "22", pct: "13.4%" },
                { type: "기타", count: "12", pct: "7.3%" },
              ].map((r) => (
                <div className="an-err-row" key={r.type}>
                  <span>{r.type}</span>
                  <span>{r.count}</span>
                  <span>{r.pct}</span>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </GarimPage>
  );
}
