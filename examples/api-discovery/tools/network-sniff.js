#!/usr/bin/env node
// FR-784: load a URL in headless Chromium, capture XHR/fetch traffic,
// emit one JSON object: {requests, auth_required, needs_manual_reason, warnings}.
"use strict";

const SETUP_HINT =
  "Setup: cd examples/api-discovery/tools && npm ci && npx playwright install chromium";

function fail(message) {
  process.stderr.write(`network-sniff: ${message}\n${SETUP_HINT}\n`);
  process.exit(2);
}

// Filter policy (judgement R-4)
const TELEMETRY_HOSTS = [
  "google-analytics.com",
  "googletagmanager.com",
  "doubleclick.net",
  "facebook.net",
  "hotjar.com",
  "matomo.cloud",
  "plausible.io",
  "segment.io",
  "sentry.io",
  "mixpanel.com",
  "clarity.ms",
];
const TELEMETRY_PATHS = ["/analytics/", "/telemetry/", "/collect", "/track", "/beacon", "/pixel"];
const TELEMETRY_HOST_LABELS = new Set(["telemetry", "analytics", "metrics", "tracking", "stats", "beacon", "collect"]);
const DATA_CONTENT_TYPES = /application\/json|\+json|application\/xml|text\/xml|\+xml/i;
const CAPTCHA_MARKERS = /recaptcha|hcaptcha|turnstile/i;
const TOKEN_PARAMS = new Set([
  "token", "key", "apikey", "api_key", "access_token", "auth", "authorization",
  "session", "secret", "password", "sig", "signature", "jwt", "bearer",
]);
// Prefix match for compound segments: sessionid, authcode, apikey2 (live: x-algolia-api-key)
const TOKEN_SEGMENT_PREFIXES = ["token", "secret", "passw", "session", "auth", "apikey", "signature", "bearer"];
const PREVIEW_LIMIT = 500;
const RANK = { data: 0, other: 1, telemetry: 2 };

function classify(rawUrl, status, contentType) {
  let url;
  try {
    url = new URL(rawUrl);
  } catch {
    return "other";
  }
  const host = url.hostname.toLowerCase();
  const path = url.pathname.toLowerCase();
  if (TELEMETRY_HOSTS.some((h) => host === h || host.endsWith(`.${h}`))) return "telemetry";
  if (host.split(".").some((label) => TELEMETRY_HOST_LABELS.has(label))) return "telemetry";
  if (TELEMETRY_PATHS.some((p) => path.includes(p))) return "telemetry";
  if (status === 200 && DATA_CONTENT_TYPES.test(contentType)) return "data";
  return "other";
}

function isTokenParam(name) {
  const lower = name.toLowerCase();
  if (TOKEN_PARAMS.has(lower)) return true;
  const segments = lower.split(/[-_.]/);
  return segments.some(
    (s) => TOKEN_PARAMS.has(s) || TOKEN_SEGMENT_PREFIXES.some((p) => s.startsWith(p))
  );
}

function redactUrl(rawUrl) {
  try {
    const url = new URL(rawUrl);
    for (const key of [...url.searchParams.keys()]) {
      if (isTokenParam(key)) {
        url.searchParams.set(key, "[REDACTED]");
      } else {
        // Token-shaped values leak under arbitrary names (live: 32-hex api keys)
        url.searchParams.set(key, redactText(url.searchParams.get(key) || ""));
      }
    }
    return url.toString();
  } catch {
    return rawUrl;
  }
}

function redactText(text) {
  return text
    .replace(/eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{5,}/g, "[REDACTED]") // JWT
    .replace(/\b[A-Fa-f0-9]{32,}\b/g, "[REDACTED]") // long hex tokens
    .replace(/\b[A-Za-z0-9+/_-]{40,}={0,2}\b/g, "[REDACTED]"); // long base64-ish tokens
}

function parseArgs(argv) {
  const url = argv.find((a) => !a.startsWith("--"));
  if (!url) fail("usage: node network-sniff.js <url> [--timeout <ms>]");
  const idx = argv.indexOf("--timeout");
  const timeoutMs = idx >= 0 ? Number.parseInt(argv[idx + 1], 10) : 10000;
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) fail("invalid --timeout value");
  return { url, timeoutMs };
}

async function capture(response, result) {
  const request = response.request();
  const status = response.status();
  const headers = await response.allHeaders().catch(() => ({}));
  const contentType = headers["content-type"] || "";
  const rawUrl = response.url();
  const classification = classify(rawUrl, status, contentType);
  if (status === 401 || status === 403 || headers["www-authenticate"]) {
    result.auth_required = true;
  }
  if (CAPTCHA_MARKERS.test(rawUrl)) result.needs_manual_reason = "captcha";
  let bodyPreview = "";
  if (classification === "data") {
    const text = await response.text().catch(() => "");
    bodyPreview = redactText(text.slice(0, PREVIEW_LIMIT));
  }
  result.requests.push({
    url: redactUrl(rawUrl),
    method: request.method(),
    status,
    content_type: contentType,
    body_preview: bodyPreview,
    classification,
  });
}

async function main() {
  const { url, timeoutMs } = parseArgs(process.argv.slice(2));
  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (err) {
    fail(`playwright package not found (${err.code || err.message}). Run npm ci first.`);
  }
  const deadline = Date.now() + timeoutMs;
  const remaining = () => Math.max(deadline - Date.now(), 1);
  const result = {
    requests: [],
    auth_required: false,
    needs_manual_reason: null,
    warnings: [],
  };

  let browser;
  try {
    browser = await chromium.launch({ headless: true, timeout: timeoutMs });
  } catch (err) {
    fail(`failed to launch Chromium: ${err.message}`);
  }

  try {
    const page = await browser.newPage();
    const pending = [];
    page.on("response", (response) => {
      const type = response.request().resourceType();
      if (type !== "xhr" && type !== "fetch") return;
      pending.push(capture(response, result));
    });
    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: remaining() });
    } catch (err) {
      result.warnings.push(
        `timeout: page did not settle within ${timeoutMs}ms (${err.name || "Error"})`
      );
    }
    // Bound body reads by the same deadline (AC-07). The timer is cleared on
    // the fast path: an uncleared timer keeps Node's event loop alive to the
    // deadline, turning --timeout into a floor instead of a ceiling (FR-921).
    let bodyTimer;
    await Promise.race([
      Promise.allSettled(pending),
      new Promise((resolve) => {
        bodyTimer = setTimeout(resolve, remaining());
      }),
    ]);
    clearTimeout(bodyTimer);
    const content = await page.content().catch(() => "");
    if (CAPTCHA_MARKERS.test(content) || /class="g-recaptcha"/i.test(content)) {
      result.needs_manual_reason = "captcha";
    }
  } finally {
    await browser.close().catch(() => {});
  }

  if (result.auth_required && result.needs_manual_reason === null) {
    result.needs_manual_reason = "auth_token";
  }
  result.requests.sort((a, b) => RANK[a.classification] - RANK[b.classification]);
  process.stdout.write(JSON.stringify(result));
}

if (require.main === module) {
  main().catch((err) => fail(err.message));
} else {
  module.exports = { classify, redactUrl, redactText, isTokenParam };
}
