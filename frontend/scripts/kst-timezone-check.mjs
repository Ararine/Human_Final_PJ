import assert from "node:assert/strict";

import {
  formatKstDate,
  formatKstDateTime,
  parseKstDate,
} from "../src/utils/timezone.js";

const naiveKst = parseKstDate("2026-06-29T10:15:30");
assert.equal(naiveKst.toISOString(), "2026-06-29T01:15:30.000Z");

const spacedNaiveKst = parseKstDate("2026-06-29 10:15:30");
assert.equal(spacedNaiveKst.toISOString(), "2026-06-29T01:15:30.000Z");

const explicitUtc = parseKstDate("2026-06-29T10:15:30Z");
assert.equal(explicitUtc.toISOString(), "2026-06-29T10:15:30.000Z");

assert.match(formatKstDateTime("2026-06-29T10:15:30"), /10:15/);
assert.match(formatKstDate("2026-06-29T10:15:30"), /2026/);
assert.equal(formatKstDateTime(null), "-");

console.log("kst timezone check passed");
