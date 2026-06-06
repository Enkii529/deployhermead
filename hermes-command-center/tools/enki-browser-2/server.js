// Enki Browser 2 – upgraded AI‑first browser service
// Stack: Node.js (CommonJS), Express, Playwright
// Implements persistent Chromium context, run folder artifacts, open‑mode/approval‑gate logic.

const express = require('express');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const app = express();
app.use(express.json({ limit: '2mb' }));

// ==== Configuration ====
const PORT = process.env.PORT ? Number(process.env.PORT) : 4318; // default to 4318 (avoid conflict with MVP)
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');
const CONFIG_DIR = process.env.CONFIG_DIR || path.join(__dirname, 'config');
const RUNS_DIR = path.join(__dirname, 'runs');
const PROFILE_DIR = process.env.PROFILE_DIR || path.join(DATA_DIR, 'profile');
const ENKI_OPEN_MODE = String(process.env.ENKI_OPEN_MODE || 'true').toLowerCase() === 'true';

// Ensure directories exist
fs.mkdirSync(DATA_DIR, { recursive: true });
fs.mkdirSync(CONFIG_DIR, { recursive: true });
fs.mkdirSync(RUNS_DIR, { recursive: true });
fs.mkdirSync(PROFILE_DIR, { recursive: true });

// ==== Helper utilities ====
function nowIso() { return new Date().toISOString(); }
function readJson(filePath, fallback) { try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); } catch { return fallback; } }
function writeJson(filePath, data) { fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n'); }
function logRun(runId, data) {
  const runPath = path.join(RUNS_DIR, runId);
  fs.mkdirSync(runPath, { recursive: true });
  writeJson(path.join(runPath, 'run.json'), data);
}

// ==== Policy / Approval logic ====
const KNOWN_GOOD_PATH = path.join(CONFIG_DIR, 'known_good_domains.json');
const ALLOWED_PATH = path.join(DATA_DIR, 'allowed_domains.json');
const PENDING_PATH = path.join(DATA_DIR, 'pending_approvals.json');
function loadSet(file) { return new Set(readJson(file, [])); }
function saveSet(file, set) { writeJson(file, [...set].sort()); }
function loadKnownGood() { return loadSet(KNOWN_GOOD_PATH); }
function loadAllowed() { return loadSet(ALLOWED_PATH); }
function saveAllowed(set) { saveSet(ALLOWED_PATH, set); }
function loadPending() { return readJson(PENDING_PATH, []); }
function savePending(arr) { writeJson(PENDING_PATH, arr); }
function baseDomain(host) { const parts = host.split('.').filter(Boolean); return parts.length <= 2 ? parts.join('.') : parts.slice(-2).join('.'); }
function isAllowedDomain(host) {
  const known = loadKnownGood();
  const allowed = loadAllowed();
  const bd = baseDomain(host);
  return known.has(host) || known.has(bd) || allowed.has(host) || allowed.has(bd);
}
function ensureDomain(urlStr) {
  const u = new URL(urlStr);
  const host = u.hostname.toLowerCase();
  if (ENKI_OPEN_MODE) {
    // Open mode: log but allow any domain
    audit({ type: 'domain.open_allowed', host, url: urlStr });
    return { host, base: baseDomain(host), allowed: true };
  }
  if (isAllowedDomain(host)) {
    audit({ type: 'domain.allow.auto', host, url: urlStr });
    return { host, base: baseDomain(host), allowed: true };
  }
  const pending = loadPending();
  const key = baseDomain(host);
  if (!pending.some(p => p.domain === key)) {
    pending.push({ domain: key, firstSeen: nowIso(), exampleUrl: urlStr });
    savePending(pending);
    audit({ type: 'domain.approval.requested', host, url: urlStr });
  }
  const err = new Error('Domain not approved');
  err.status = 403;
  err.payload = { needsApproval: true, domain: key, host, url: urlStr };
  throw err;
}

// ==== Browser context & logging ====
let context; // persistent context
let page;   // active page
let activeRunId = null; // current run folder ID
let consoleEvents = [];
let pageErrorEvents = [];
let networkFailEvents = [];

async function getPage() {
  if (page && !page.isClosed()) return page;
  if (!context) {
    context = await chromium.launchPersistentContext(PROFILE_DIR, { headless: true, viewport: { width: 1280, height: 720 } });
    // attach listeners once per context
    context.on('page', p => {
      page = p;
      attachPageListeners(p);
    });
    // ensure at least one page exists
    const pages = context.pages();
    page = pages.length ? pages[0] : await context.newPage();
    attachPageListeners(page);
    audit({ type: 'browser.started', profile: PROFILE_DIR });
  }
  return page;
}

function attachPageListeners(p) {
  p.on('console', msg => {
    const event = { timestamp: nowIso(), url: p.url(), type: msg.type(), text: msg.text(), location: msg.location() };
    consoleEvents.push(event);
  });
  p.on('pageerror', err => {
    const event = { timestamp: nowIso(), url: p.url(), message: err.message, stack: err.stack };
    pageErrorEvents.push(event);
  });
  p.on('requestfailed', req => {
    const event = { timestamp: nowIso(), url: p.url(), requestUrl: req.url(), method: req.method(), resourceType: req.resourceType(), errorText: req.failure()?.errorText };
    networkFailEvents.push(event);
  });
}

function ensureRunFolder() {
  if (!activeRunId) {
    // generate timestamp safe ID
    activeRunId = nowIso().replace(/[:]/g, '-');
  }
  const runPath = path.join(RUNS_DIR, activeRunId);
  fs.mkdirSync(runPath, { recursive: true });
  return runPath;
}

function writeArtifacts(artifacts) {
  const runPath = ensureRunFolder();
  Object.entries(artifacts).forEach(([file, data]) => {
    const fp = path.join(runPath, file);
    if (typeof data === 'string') fs.writeFileSync(fp, data, 'utf-8');
    else if (Buffer.isBuffer(data)) fs.writeFileSync(fp, data);
    else fs.writeFileSync(fp, JSON.stringify(data, null, 2) + '\n');
  });
}

function audit(event) { writeJson(path.join(DATA_DIR, 'audit.log.jsonl'), { t: nowIso(), ...event }); }

// ==== Endpoints ====
app.get('/health', (req, res) => {
  res.json({ ok: true, pid: process.pid, port: PORT, openMode: ENKI_OPEN_MODE, profile: PROFILE_DIR, runsPath: RUNS_DIR });
});

app.get('/policy', (req, res) => {
  const policy = {
    openMode: ENKI_OPEN_MODE,
    knownGoodCount: loadKnownGood().size,
    allowedCount: loadAllowed().size,
    pendingCount: loadPending().length
  };
  res.json(policy);
});

app.post('/navigate', async (req, res, next) => {
  try {
    const url = req.body?.url;
    if (!url) return res.status(400).json({ error: 'url required' });
    ensureDomain(url);
    const p = await getPage();
    await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    audit({ type: 'navigate', url: p.url() });
    // reset run id for a fresh run
    activeRunId = null;
    // optionally create metadata artifact now
    const meta = {
      runId: nowIso().replace(/[:]/g, '-'),
      created: nowIso(),
      url: p.url(),
      openMode: ENKI_OPEN_MODE,
      profile: PROFILE_DIR,
      service: 'enki-browser-2'
    };
    writeArtifacts({ 'metadata.json': JSON.stringify(meta, null, 2) + '\n' });
    res.json({ ok: true, url: p.url() });
  } catch (e) { next(e); }
});

app.post('/open', async (req, res, next) => { // alias for navigate
  req.body = req.body || {};
  req.body.url = req.body.url || '';
  app._router.handle({ ...req, method: 'POST', url: '/navigate' }, res, next);
});

app.post('/screenshot', async (req, res, next) => {
  try {
    const p = await getPage();
    const buf = await p.screenshot({ fullPage: true });
    audit({ type: 'screenshot', url: p.url() });
    res.set('Content-Type', 'image/png');
    res.send(buf);
  } catch (e) { next(e); }
});

app.post('/screenshot/save', async (req, res, next) => {
  try {
    const p = await getPage();
    const buf = await p.screenshot({ fullPage: true });
    const runPath = ensureRunFolder();
    const filename = 'screenshot.png';
    const fp = path.join(runPath, filename);
    fs.writeFileSync(fp, buf);
    // also write metadata if not yet present
    const metaPath = path.join(runPath, 'metadata.json');
    if (!fs.existsSync(metaPath)) {
      const meta = { runId: activeRunId, created: nowIso(), url: p.url(), openMode: ENKI_OPEN_MODE };
      fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2) + '\n');
    }
    audit({ type: 'screenshot.save', path: fp });
    res.json({ ok: true, runId: activeRunId, screenshotPath: fp });
  } catch (e) { next(e); }
});

app.get('/content', async (req, res, next) => {
  try {
    const p = await getPage();
    const html = await p.content();
    audit({ type: 'content', url: p.url() });
    res.json({ ok: true, url: p.url(), html });
  } catch (e) { next(e); }
});

app.post('/content', async (req, res, next) => {
  try {
    const p = await getPage();
    const html = await p.content();
    audit({ type: 'content', url: p.url() });
    res.json({ ok: true, url: p.url(), html });
  } catch (e) { next(e); }
});

app.get('/visible-text', async (req, res, next) => {
  try {
    const p = await getPage();
    const txt = await p.evaluate(() => document.body.innerText);
    const runPath = ensureRunFolder();
    const fp = path.join(runPath, 'visible-text.txt');
    fs.writeFileSync(fp, txt, 'utf-8');
    audit({ type: 'visible-text', path: fp });
    res.json({ ok: true, text: txt });
  } catch (e) { next(e); }
});

app.get('/dom-summary', async (req, res, next) => {
  try {
    const p = await getPage();
    const summary = await p.evaluate(() => {
      const title = document.title;
      const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.href);
      return { title, linkCount: links.length, links: links.slice(0, 20) };
    });
    const runPath = ensureRunFolder();
    const fp = path.join(runPath, 'dom-summary.json');
    fs.writeFileSync(fp, JSON.stringify(summary, null, 2) + '\n');
    audit({ type: 'dom-summary', path: fp });
    res.json({ ok: true, summary });
  } catch (e) { next(e); }
});

app.get('/console', (req, res) => {
  const runPath = ensureRunFolder();
  const fp = path.join(runPath, 'console.json');
  fs.writeFileSync(fp, JSON.stringify(consoleEvents, null, 2) + '\n');
  res.json({ ok: true, events: consoleEvents });
});

app.get('/network-failures', (req, res) => {
  const runPath = ensureRunFolder();
  const fp = path.join(runPath, 'network-failures.json');
  fs.writeFileSync(fp, JSON.stringify(networkFailEvents, null, 2) + '\n');
  res.json({ ok: true, events: networkFailEvents });
});

app.post('/click', async (req, res, next) => {
  try {
    const selector = req.body?.selector;
    if (!selector) return res.status(400).json({ error: 'selector required' });
    const p = await getPage();
    await p.click(selector, { timeout: 5000 });
    audit({ type: 'click', selector });
    res.json({ ok: true, selector });
  } catch (e) { next(e); }
});

app.post('/fill', async (req, res, next) => {
  try {
    const { selector, value } = req.body;
    if (!selector || value === undefined) return res.status(400).json({ error: 'selector and value required' });
    const p = await getPage();
    await p.fill(selector, String(value), { timeout: 5000 });
    audit({ type: 'fill', selector, value });
    res.json({ ok: true, selector, value });
  } catch (e) { next(e); }
});

app.post('/press', async (req, res, next) => {
  try {
    const key = req.body?.key;
    if (!key) return res.status(400).json({ error: 'key required' });
    const p = await getPage();
    await p.keyboard.press(key);
    audit({ type: 'press', key });
    res.json({ ok: true, key });
  } catch (e) { next(e); }
});

app.post('/run', async (req, res, next) => {
  try {
    const { url, actions } = req.body || {};
    if (!url) return res.status(400).json({ error: 'url required' });
    const p = await getPage();
    const runId = nowIso().replace(/[:]/g, '-');
    const runPath = path.join(RUNS_DIR, runId);
    fs.mkdirSync(runPath, { recursive: true });
    const runMeta = { runId, created: nowIso(), url, openMode: ENKI_OPEN_MODE, profile: PROFILE_DIR };
    const results = [];
    // Navigate first
    await ensureDomain(url);
    await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    results.push({ action: 'navigate', url: p.url() });
    // Process each requested action in order
    for (const act of actions || []) {
      switch (act.type) {
        case 'screenshot': {
          const buf = await p.screenshot({ fullPage: true });
          const fp = path.join(runPath, 'screenshot.png');
          fs.writeFileSync(fp, buf);
          results.push({ action: 'screenshot', path: fp });
          break;
        }
        case 'visibleText': {
          const txt = await p.evaluate(() => document.body.innerText);
          const fp = path.join(runPath, 'visible-text.txt');
          fs.writeFileSync(fp, txt, 'utf-8');
          results.push({ action: 'visibleText', path: fp });
          break;
        }
        case 'domSummary': {
          const summary = await p.evaluate(() => ({ title: document.title, linkCount: document.querySelectorAll('a[href]').length }));
          const fp = path.join(runPath, 'dom-summary.json');
          fs.writeFileSync(fp, JSON.stringify(summary, null, 2) + '\n');
          results.push({ action: 'domSummary', path: fp });
          break;
        }
        default:
          results.push({ action: act.type, error: 'unknown action' });
      }
    }
    // Write collected logs
    fs.writeFileSync(path.join(runPath, 'console.json'), JSON.stringify(consoleEvents, null, 2) + '\n');
    fs.writeFileSync(path.join(runPath, 'network-failures.json'), JSON.stringify(networkFailEvents, null, 2) + '\n');
    // Write run metadata and results
    const runData = { meta: runMeta, results, artifacts: { console: 'console.json', network: 'network-failures.json' } };
    writeJson(path.join(runPath, 'run.json'), runData);
    // Reset active run id for future calls
    activeRunId = runId;
    res.json({ ok: true, runId, results });
  } catch (e) { next(e); }
});

app.get('/runs', (req, res) => {
  const entries = fs.readdirSync(RUNS_DIR).filter(e => fs.statSync(path.join(RUNS_DIR, e)).isDirectory());
  res.json({ runs: entries });
});

app.get('/runs/:id', (req, res) => {
  const runId = req.params.id;
  const runPath = path.join(RUNS_DIR, runId);
  if (!fs.existsSync(runPath)) return res.status(404).json({ error: 'run not found' });
  const files = fs.readdirSync(runPath);
  res.json({ runId, files, path: runPath });
});

// Global error handler
app.use((err, _req, res, _next) => {
  const status = err.status || 500;
  const payload = err.payload || { error: err.message || 'error' };
  res.status(status).json(payload);
});

app.listen(PORT, () => {
  console.log(`Enki Browser 2 listening on http://127.0.0.1:${PORT}`);
  // record PID for later stopping
  fs.writeFileSync(path.join(__dirname, '.server.pid'), String(process.pid));
});
