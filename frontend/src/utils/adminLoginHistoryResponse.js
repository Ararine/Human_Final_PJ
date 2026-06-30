export function normalizeLoginHistoryListResponse(response) {
  const payload = response?.data || {};

  return {
    items: Array.isArray(payload.items) ? payload.items : [],
    total: Number(payload.total || 0),
    metrics: payload.metrics || null,
  };
}
