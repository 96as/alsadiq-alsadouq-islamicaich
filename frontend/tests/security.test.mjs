// Run: node --test tests/security.test.mjs
// Source-level guards for the frontend security hardening (no browser, no network).
import test from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const read = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8');
const caddy = read('../../infra/caddy/Caddyfile');

test('rotated refresh tokens are kept (the backend rotates and blacklists the old one)', () => {
  for (const f of ['../src/services/api.js', '../src/services/authService.js']) {
    assert.match(read(f), /if \(data\.refresh\) localStorage\.setItem\('refresh_token', data\.refresh\)/, f);
  }
});

test('logout clears both token keys and the demo session', () => {
  assert.match(read('../src/services/authService.js'), /removeItem\('access_token'\)[\s\S]*removeItem\('refresh_token'\)/);
  assert.match(read('../src/context/AuthContext.jsx'), /await logoutService\(\);[\s\S]*clearDemoSession\(\)/);
});

test('no raw HTML or eval sinks in src', () => {
  const hits = execSync(
    String.raw`grep -rnE "dangerouslySetInnerHTML|\.innerHTML\s*=|insertAdjacentHTML|document\.write|\beval\(|new Function\(" src || true`,
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' },
  ).trim();
  assert.equal(hits, '', hits);
});

test('Caddy: Django responses keep Django\'s own Referrer-Policy; Permissions-Policy has no interest-cohort', () => {
  const snippet = caddy.match(/\(django_hardening\) \{([^}]*)\}/);
  assert.ok(snippet, 'django_hardening snippet missing');
  assert.ok(!/Referrer-Policy/.test(snippet[1]), 'Caddy must not override Django\'s same-origin Referrer-Policy');
  assert.ok(!/interest-cohort/.test(caddy), 'interest-cohort is obsolete');
});

test('Caddy: the SPA gets the baseline headers and a Report-Only CSP', () => {
  for (const h of [
    'X-Content-Type-Options "nosniff"',
    'Referrer-Policy "strict-origin-when-cross-origin"',
    'X-Frame-Options "DENY"',
  ]) assert.ok(caddy.includes(h), h);
  assert.match(caddy, /Permissions-Policy "microphone=\(self\), camera=\(\)/);
  const m = caddy.match(/Content-Security-Policy-Report-Only "([^"]+)"/);
  assert.ok(m, 'CSP report-only header missing');
  const csp = m[1];
  assert.ok(!/^\s*Content-Security-Policy "/m.test(caddy), 'CSP must stay report-only until the lead enforces it');
  assert.ok(!csp.includes("'unsafe-eval'"));
  assert.match(csp, /script-src 'self' 'wasm-unsafe-eval';/);
  assert.match(csp, /object-src 'none'/);
  assert.match(csp, /frame-ancestors 'none'/);
  assert.match(csp, /connect-src [^;]*wss:\/\/\*\.livekit\.cloud/);
});

test('Caddy: Django proxies (api, admin, static) get the baseline but no CSP', () => {
  assert.equal((caddy.match(/import django_hardening/g) || []).length, 3);
  assert.equal((caddy.match(/^\s*Content-Security-Policy-Report-Only /gm) || []).length, 1);
});
