import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();
app.use(express.json({ limit: '1mb' }));

const PORT = process.env.PORT ? Number(process.env.PORT) : 4317;
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, '..', 'data');
const CONFIG_DIR = process.env.CONFIG_DIR || path.join(__dirname, '..', 'config');

fs.mkdirSync(DATA_DIR, { recursive: true });

const KNOWN_GOOD_PATH = path.join(CONFIG_DIR, 'known_good_domains.json');
const ALLOWED_PATH = path.join(DATA_DIR, 'allowed_domains.json');
const PENDING_PATH = path.join(DATA_DIR, 'pending_approvals.json');
const LOG_PATH = path.join(DATA_DIR, 'audit.log.jsonl');

function readJson(filePath, fallback) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); }
  catch { return fallback; }
}
function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n');
}

function nowIso() { return new Date().toISOString(); }
function audit(event) {
  fs.appendFileSync(LOG_PATH, JSON.stringify({ t: nowIso(), ...event }) + '\n');
}

function normalizeHost(host) {
  return (host || '').toLowerCase().trim();
}
function baseDomain(host) {
  // Simple base-domain heuristic: last 2 labels.
  // Good enough for MVP; can swap for PSL-based extraction later.
  const parts = normalizeHost(host).split('.').filter(Boolean);
  if (parts.length <= 2) return parts.join('.');
  return parts.slice(-2).join('.');
}

function loadKnownGood() {
  return new Set(readJson(KNOWN_GOOD_PATH, []).map(s => s.toLowerCase()));
}
function loadAllowed() {
  return new Set(readJson(ALLOWED_PATH, []).map(s => s.toLowerCase()));
}
function saveAllowed(set) {
  writeJson(ALLOWED_PATH, [...set].sort());
}
function loadPending() {
  return readJson(PENDING_PATH, []);
}
function savePending(arr) {
  writeJson(PENDING_PATH, arr);
}

function isAllowedDomain(host) {
  const known = loadKnownGood();
  const allowed = loadAllowed();
  const bd = baseDomain(host);
  return known.has(host) || known.has(bd) || allowed.has(host) || allowed.has(bd);
}

function ensureDomainApprovedOrThrow(urlStr) {
  const u = new URL(urlStr);
  const host = normalizeHost(u.hostname);
  const bd = baseDomain(host);

  if (isAllowedDomain(host)) {
    audit({ type: 'domain.allow.auto', host, base: bd, url: urlStr });
    return { host, base: bd, allowed: true };
  }

  const pending = loadPending();
  const key = bd;
  if (!pending.some(p => p.domain === key)) {
    pending.push({ domain: key, firstSeen: nowIso(), exampleUrl: urlStr });
    savePending(pending);
    audit({ type: 'domain.approval.requested', host, base: bd, url: urlStr });
  }

  const err = new Error('Domain not approved');
  err.status = 403;
  err.payload = { needsApproval: true, domain: key, host, url: urlStr };
  throw err;
}

let context;
let page;

const PROFILE_DIR = process.env.PROFILE_DIR || path.join(DATA_DIR, 'profile');
const HEADED = String(process.env.HEADED || '').toLowerCase() === 'true';

async function getPage() {
  // if our cached page got closed, clear it.
  if (page && page.isClosed()) page = null;

  if (context) {
    try {
      if (context.pages().length) {
        page = context.pages().find(p => !p.isClosed()) || page;
      }
    } catch {
      context = null;
      page = null;
    }
  }

  if (context && page && !page.isClosed()) return page;

  // Persistent profile so logins survive restarts.
  context = await chromium.launchPersistentContext(PROFILE_DIR, {
    headless: !HEADED,
    viewport: { width: 1280, height: 720 }
  });

  page = context.pages().find(p => !p.isClosed()) || await context.newPage();
  audit({ type: 'browser.started', headed: HEADED, profileDir: PROFILE_DIR });
  return page;
}

app.get('/health', (req, res) => res.json({ ok: true }));

app.get('/policy', (req, res) => {
  res.json({
    level: 6,
    knownGoodCount: loadKnownGood().size,
    allowedCount: loadAllowed().size,
    pendingCount: loadPending().length,
    subdomainsOk: true
  });
});

app.get('/approvals/pending', (req, res) => {
  res.json({ pending: loadPending() });
});

app.post('/approvals/allow', (req, res) => {
  const domain = (req.body?.domain || '').toLowerCase().trim();
  if (!domain) return res.status(400).json({ error: 'domain required' });
  const allowed = loadAllowed();
  allowed.add(domain);
  saveAllowed(allowed);

  // remove from pending
  const pending = loadPending().filter(p => p.domain !== domain);
  savePending(pending);

  audit({ type: 'domain.approved', domain });
  res.json({ ok: true, domain });
});

app.post('/navigate', async (req, res, next) => {
  try {
    const url = req.body?.url;
    if (!url) return res.status(400).json({ error: 'url required' });
    ensureDomainApprovedOrThrow(url);
    const p = await getPage();
    await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    audit({ type: 'nav', url });
    res.json({ ok: true, url: p.url() });
  } catch (e) { next(e); }
});

app.post('/screenshot', async (req, res, next) => {
  try {
    const p = await getPage();
    const fullPage = !!req.body?.fullPage;
    const buf = await p.screenshot({ fullPage });
    audit({ type: 'screenshot', fullPage, url: p.url() });
    res.setHeader('Content-Type', 'image/png');
    res.send(buf);
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

// --- ClawHub helpers (MVP) ---
async function clawhubEnsureSkillsPage(p) {
  const url = 'https://clawhub.ai/skills';
  if (!p.url().startsWith(url)) {
    await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  }
  // allow SPA to hydrate
  await p.waitForTimeout(1500);
}

app.get('/clawhub/skills', async (req, res, next) => {
  try {
    const q = String(req.query.q || '').trim();
    const limit = Math.min(50, Math.max(1, Number(req.query.limit || 20)));

    const p = await getPage();
    await p.goto('https://clawhub.ai/skills', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await p.waitForTimeout(2500);

    if (q) {
      const box = p.getByRole('textbox', { name: /filter by name/i });
      await box.click({ timeout: 10000 });
      await p.keyboard.press('Control+A');
      await p.keyboard.type(q, { delay: 10 });
      await p.waitForTimeout(1200);
    }

    // Scroll to load more items (infinite list)
    const scrolls = Math.min(20, Math.max(0, Number(req.query.scrolls || 8)));
    for (let i = 0; i < scrolls; i++) {
      await p.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await p.waitForTimeout(800);
    }

    // Collect visible skill links.
    const items = await p.evaluate(() => {
      const out = [];
      const anchors = Array.from(document.querySelectorAll('a[href^="/"]'));
      for (const a of anchors) {
        const href = a.getAttribute('href') || '';
        // skill URLs look like /owner/slug
        if (!/^\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(href)) continue;
        const text = (a.innerText || '').replace(/\s+/g, ' ').trim();
        if (!text) continue;
        const name = text.split(' /')[0].trim();
        out.push({ href, text, name });
      }
      const seen = new Set();
      return out.filter(x => (seen.has(x.href) ? false : (seen.add(x.href), true)));
    });

    const sliced = items.slice(0, limit).map(x => ({
      url: `https://clawhub.ai${x.href}`,
      path: x.href,
      name: x.name,
      raw: x.text
    }));

    audit({ type: 'clawhub.skills.list', q, limit, count: sliced.length });
    res.json({ ok: true, q, count: sliced.length, items: sliced });
  } catch (e) { next(e); }
});

app.get('/clawhub/skill', async (req, res, next) => {
  try {
    const pathQ = String(req.query.path || '').trim();
    if (!pathQ.startsWith('/')) return res.status(400).json({ error: 'path must start with /owner/slug' });
    const url = `https://clawhub.ai${pathQ}`;

    const p = await getPage();
    await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await p.waitForTimeout(2500);

    const data = await p.evaluate(() => {
      const title = document.title;
      // pull outbound links
      const links = Array.from(document.querySelectorAll('a[href^="http"]')).map(a => a.href);
      const uniq = Array.from(new Set(links));
      const github = uniq.filter(u => u.includes('github.com/'));
      const text = document.body.innerText.slice(0, 20000);
      return { title, links: uniq, github, textPreview: text };
    });

    audit({ type: 'clawhub.skill.open', path: pathQ });
    res.json({ ok: true, url, ...data });
  } catch (e) { next(e); }
});

app.use((err, req, res, _next) => {
  const status = err.status || 500;
  const payload = err.payload || { error: err.message || 'error' };
  res.status(status).json(payload);
});

app.listen(PORT, () => {
  audit({ type: 'service.started', port: PORT });
  console.log(`Enkii Browser Service listening on http://127.0.0.1:${PORT}`);
});
