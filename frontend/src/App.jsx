import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";

/* css */
import "./css/index.css";
import "./css/App.css";
import "./css/garim.css";
import { GarimRouteProvider } from "./context/GarimRouteContext.jsx";
import { garimPages } from "./data/garim/pages";
import { useAuthUser } from "./hooks/useAuthStatus";

const PROTECTED_LAYOUTS = new Set(["app", "admin"]);

function isProtectedRoute(route) {
  return route.requiresAuth ?? PROTECTED_LAYOUTS.has(route.layout);
}

function ProtectedRoute({ children }) {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuthUser();

  if (loading) {
    return (
      <div className="app-loading-container">
        <div className="app-loading-spinner" role="progressbar" aria-label="로딩 중" />
        <div className="app-loading-text">세션 확인 중...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    const nextPath = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(nextPath)}`} replace />;
  }

  return children;
}

function renderRouteElement(route) {
  const page = (
    <GarimRouteProvider route={route}>
      <route.component />
    </GarimRouteProvider>
  );

  if (!isProtectedRoute(route)) {
    return page;
  }

  return <ProtectedRoute>{page}</ProtectedRoute>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {garimPages.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={renderRouteElement(route)}
          />
        ))}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
