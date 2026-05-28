const DEFAULT_API_PORT = "8000";

export function getApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window === "undefined") {
    return `http://localhost:${DEFAULT_API_PORT}`;
  }
  return `${window.location.protocol}//${window.location.hostname}:${DEFAULT_API_PORT}`;
}

export function getOAuthStartUrl(provider) {
  return `${getApiBaseUrl()}/auth/${provider}/start`;
}

export function getOAuthReregisterUrl(provider) {
  return `${getApiBaseUrl()}/auth/${provider}/start?reregister=true`;
}

export async function getAuthStatus() {
  return requestJson("/auth/status");
}

export async function getCurrentUser() {
  return requestJson("/auth/me");
}

export async function refreshAuthSession() {
  return requestJson("/auth/refresh", { method: "POST" });
}

export async function logout() {
  return requestJson("/auth/logout", { method: "POST" });
}

export async function getUserSettings() {
  return requestJson("/settings/me");
}

export async function deleteAccount() {
  return requestJson("/settings/me", { method: "DELETE" });
}

export async function updateUserSettings(settings) {
  return requestJson("/settings/me", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
}

export async function getAdminUsers(params = {}) {
  const query = new URLSearchParams();
  if (params.page)   query.set("page",   params.page);
  if (params.limit)  query.set("limit",  params.limit);
  if (params.role)   query.set("role",   params.role);
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return requestJson(`/admin/users${qs ? "?" + qs : ""}`);
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/uploads`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.message || "파일 업로드에 실패했습니다.");
  }

  return body;
}

async function requestJson(path, options = {}, isRetry = false) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    credentials: "include",
    ...options,
  });
  const body = await response.json().catch(() => ({}));

  if (response.status === 401 && !isRetry) {
    try {
      await fetch(`${getApiBaseUrl()}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      return requestJson(path, options, true);
    } catch {
      throw new Error("세션이 만료되었습니다. 다시 로그인해주세요.");
    }
  }

  if (!response.ok) {
    throw new Error(body.message || body.detail || "API request failed.");
  }

  return body;
}
