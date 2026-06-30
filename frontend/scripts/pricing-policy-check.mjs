import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const pricingHook = readFileSync(new URL("../src/hooks/usePricingPlans.js", import.meta.url), "utf8");
const pricingPage = readFileSync(new URL("../src/pages/garim/Pricing.jsx", import.meta.url), "utf8");
const paymentPage = readFileSync(new URL("../src/pages/garim/Payment.jsx", import.meta.url), "utf8");
const paymentSuccessPage = readFileSync(new URL("../src/pages/garim/PaymentSuccess.jsx", import.meta.url), "utf8");
const paymentSchema = readFileSync(new URL("../../backend/schemas/payment.py", import.meta.url), "utf8");
const paymentController = readFileSync(new URL("../../backend/controllers/payment.py", import.meta.url), "utf8");
const paymentService = readFileSync(new URL("../../backend/services/payment.py", import.meta.url), "utf8");

assert.equal(
  pricingHook.includes("DEFAULT_POLICY"),
  false,
  "DEFAULT_POLICY must be removed so pricing never falls back to hard-coded plan data",
);

assert.equal(
  /file:\s*policy\?\.file_processing\?\.plans\?\.\[key\]\s*\|\|\s*\{\}/.test(pricingHook),
  true,
  "missing API file policy should fall back only to an empty object",
);

assert.equal(
  /retention:\s*policy\?\.retention\?\.plans\?\.\[key\]\s*\|\|\s*\{\}/.test(pricingHook),
  true,
  "missing API retention policy should fall back only to an empty object",
);

assert.equal(
  /productType:\s*isCredit\s*\?\s*"credit"\s*:\s*"subscription"/.test(pricingPage),
  true,
  "pricing checkout must send subscription for plans and credit for credit plans",
);

assert.equal(
  /billingCycle/.test(pricingPage),
  true,
  "subscription checkout should preserve billing cycle data for billing auth",
);

assert.equal(
  /successUrl:[\s\S]*billingCycle/.test(paymentPage),
  true,
  "billing auth success URL must preserve billingCycle",
);

assert.equal(
  /billingCycle[\s\S]*confirmBillingPayment/.test(paymentSuccessPage),
  true,
  "billing confirm request must send billingCycle",
);

assert.equal(
  /billingCycle:\s*Literal\["monthly",\s*"yearly"\]/.test(paymentSchema),
  true,
  "billing confirm schema must accept monthly/yearly billingCycle",
);

assert.equal(
  /billing_cycle=body\.billingCycle/.test(paymentController),
  true,
  "payment controller must pass billingCycle to service",
);

assert.equal(
  /billing_cycle:\s*str\s*=\s*"monthly"/.test(paymentService),
  true,
  "payment service must default billing_cycle to monthly",
);

console.log("pricing policy check passed");
