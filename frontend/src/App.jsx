import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";

/* css */
import "./css/index.css";
import "./css/App.css";
import "./css/garim.css";
import { GarimRouteProvider } from "./context/GarimRouteContext.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { NotificationProvider } from "./context/NotificationContext.jsx";
import { ThemeProvider } from "./context/ThemeContext.jsx";
import { garimPages } from "./data/garim/pages";
import { useAuthUser } from "./hooks/useAuthStatus";

const PROTECTED_LAYOUTS = new Set(["app", "admin"]);

function isProtectedRoute(route) {
  return route.requiresAuth ?? PROTECTED_LAYOUTS.has(route.layout);
}

function ProtectedRoute({ children, requireAdmin = false }) {
  const location = useLocation();
  const { isAuthenticated, user, loading } = useAuthUser();

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

  if (requireAdmin && user?.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AdminIndexRoute() {
  return <Navigate to="/admin/monitoring" replace />;
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

  return <ProtectedRoute requireAdmin={route.layout === "admin"}>{page}</ProtectedRoute>;
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
      <AuthProvider>
      <NotificationProvider>
        <Routes>
        {garimPages.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={renderRouteElement(route)}
          />
        ))}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminIndexRoute />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </NotificationProvider>
      </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
