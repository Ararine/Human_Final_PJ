const KST_TIME_ZONE = "Asia/Seoul";
const TIMEZONE_SUFFIX_RE = /(Z|[+-]\d{2}:?\d{2})$/i;

export function normalizeKstDateInput(value) {
  if (!value) return null;
  if (value instanceof Date) return value;

  const raw = String(value).trim();
  if (!raw) return null;

  const normalized = raw.replace(" ", "T");
  if (TIMEZONE_SUFFIX_RE.test(normalized)) {
    return normalized;
  }

  return `${normalized}+09:00`;
}

export function parseKstDate(value) {
  const normalized = normalizeKstDateInput(value);
  if (!normalized) return null;

  const date = normalized instanceof Date ? normalized : new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatKstDateTime(value, options = {}) {
  const date = parseKstDate(value);
  if (!date) return "-";

  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: KST_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  }).format(date);
}

export function formatKstDate(value, options = {}) {
  const date = parseKstDate(value);
  if (!date) return "-";

  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: KST_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    ...options,
  }).format(date);
}
