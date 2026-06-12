import assert from "node:assert/strict";

import { normalizeLoginHistoryListResponse } from "../src/utils/adminLoginHistoryResponse.js";

const apiResponse = {
  data: {
    items: [
      {
        login_history_id: "11111111-1111-1111-1111-111111111111",
        user_email: "user@example.com",
      },
    ],
    total: 1,
    metrics: {
      total_attempts: 1,
      success_count: 1,
      failed_count: 0,
      blocked_count: 0,
    },
  },
  message: "Login histories loaded successfully.",
};

const normalized = normalizeLoginHistoryListResponse(apiResponse);

assert.equal(normalized.items.length, 1);
assert.equal(normalized.items[0].user_email, "user@example.com");
assert.equal(normalized.total, 1);
assert.equal(normalized.metrics.total_attempts, 1);

const empty = normalizeLoginHistoryListResponse(null);

assert.deepEqual(empty.items, []);
assert.equal(empty.total, 0);
assert.equal(empty.metrics, null);
