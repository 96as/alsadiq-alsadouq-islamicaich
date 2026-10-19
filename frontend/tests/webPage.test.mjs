// w3: tests for the held web page (BEHAVIOUR-SPEC section 6): layout and truncation, RTL, the content filter,
// the scroll physics, the reading gaze, the hero rect, and the state machine fed by al.search plus al.activity.
// Pure JS: runs under `node --test` without a browser. Time is simulated at 60 fps. Fixtures only, no scripture.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { createAvatarContextStore } from '../src/features/child/components/avatar/context/avatarSignals.js';
import { createDirector, makeDirectorOutput } from '../src/features/child/components/avatar/context/avatarDirector.js';
import { CLIP } from '../src/features/child/components/avatar/avatarConfig.js';
import { HP } from '../src/features/child/components/avatar/context/holoTimeline.js';
import {
  GROWNUP, LIMITS, NONE_TEXT, buildPageModel, cleanDomain, cleanText, diacriticShare, foldArabic, hasMetaWord, spokenSummary, topicOf,
} from '../src/features/child/components/avatar/hologram/webPage/contentFilter.js';
import { FIXTURES, fixtureMessage, flaggedMessage, metaWordMessage } from '../src/features/child/components/avatar/hologram/webPage/fixtures.js';
import {
  PAGE_MAX, WIN, foundScroll, layoutPage, layoutSkeleton, scrollInfo, wrapWords,
} from '../src/features/child/components/avatar/hologram/webPage/pageLayout.js';
import { TILE, chromeText, drawTile, makeMeasure } from '../src/features/child/components/avatar/hologram/webPage/pageRenderer.js';
import { SCROLL, createScroll } from '../src/features/child/components/avatar/hologram/webPage/scrollPhysics.js';
import { GAZE, createReadingGaze } from '../src/features/child/components/avatar/hologram/webPage/readingGaze.js';
import { heroRect, minJerk, rectHitsCircle } from '../src/features/child/components/avatar/hologram/webPage/heroLayout.js';

const DT = 1 / 60;
const measure = (text) => String(text).length * 7.5; // a fake, deterministic measurer (px per character)
const model = (name, lang, hl) => {
  const msg = fixtureMessage(name, lang, 'results', 'fx-test');
  if (hl !== undefined) msg.hl = hl;
  const store = createAvatarContextStore({ now: () => 0 });
  store.onSearchMessage(msg);
  return buildPageModel(store.ctx.signals.web, lang);
};

// ---------------------------------------------------------------------------------------------------------------
// The content filter (WP-6)

test('cleanText truncates a title to 70 characters and a snippet to 140 with an ellipsis, never mid-surrogate', () => {
  const long = 'word '.repeat(60);
  const t = cleanText(long, LIMITS.title);
  assert.ok([...t].length <= LIMITS.title, `title ${[...t].length}`);
  assert.ok(t.endsWith('…'));
  const s = cleanText(long, LIMITS.snippet);
  assert.ok([...s].length <= LIMITS.snippet);
  assert.equal(cleanText('Short title', 70), 'Short title');
  const emoji = cleanText('a'.repeat(68) + '😀😀😀', 70);
  assert.ok(!/[\uD800-\uDBFF]$/.test(emoji.replace('…', '')), 'no lone high surrogate');
});

test('cleanText removes control and bidi spoofing characters and collapses whitespace', () => {
  assert.equal(cleanText('a\u0000b\u202Ec\u200Fd   e\n\nf', 70), 'a bcd e f', 'a control character becomes a space; bidi controls vanish');
});

test('cleanDomain keeps only a plain domain: no scheme, path, query, port, or junk', () => {
  assert.equal(cleanDomain('https://www.skykids.example/path/to?q=1#x'), 'skykids.example');
  assert.equal(cleanDomain('skykids.example:8080'), 'skykids.example');
  assert.equal(cleanDomain('javascript:alert(1)'), '');
  assert.equal(cleanDomain('not a domain'), '');
  assert.equal(cleanDomain(''), '');
  assert.equal(cleanDomain(42), '');
});

test('meta words (scripture words) are found with and without marks and with a prefix; ordinary words never trip', () => {
  assert.ok(hasMetaWord('A hadith for children'));
  assert.ok(hasMetaWord('what is a surah'));
  assert.ok(hasMetaWord('معنى سورة'));
  assert.ok(hasMetaWord('معنى السُّورَة'), 'with tashkeel');
  for (const ok of ['why is the sky blue', 'how do bees make honey', 'stories for kids', 'لماذا السماء زرقاء', 'كيف يصنع النحل العسل', 'نهاية القصة']) {
    assert.ok(!hasMetaWord(ok), `must not trip: ${ok}`);
  }
});

test('heavy diacritics (more than 20 percent of the letters) count as vocalised text', () => {
  assert.ok(diacriticShare('لماذا السماء زرقاء') < 0.01);
  // review: an everyday, fully voweled sentence (no religious text anywhere in the tests, BEHAVIOUR-SPEC 8.0)
  assert.ok(diacriticShare('السَّمَاءُ زَرْقَاءُ جَمِيلَةٌ') > 0.2);
  assert.equal(foldArabic('أَرْنَبٌ'), 'ارنب');
});

test('every fixture builds a page and none trips a filter', () => {
  for (const name of Object.keys(FIXTURES)) {
    for (const lang of ['en', 'ar']) {
      const m = model(name, lang);
      assert.equal(m.state, 'results', `${name}/${lang}`);
      assert.equal(m.results.length, FIXTURES[name][lang].r.length);
      assert.equal(m.hero, true);
      assert.equal(m.fixture, true);
      assert.equal(m.rtl, lang === 'ar');
      for (const r of m.results) {
        assert.ok(!r.d.includes('/') && !r.d.includes('?'), 'only the domain');
        assert.ok(r.d.endsWith('.example'), 'fixtures use .example domains');
      }
    }
  }
});

test('a flagged query (sf) gives the whole grown-up card, with no query and no results', () => {
  for (const lang of ['en', 'ar']) {
    const store = createAvatarContextStore({ now: () => 0 });
    store.onSearchMessage(flaggedMessage(lang));
    const m = buildPageModel(store.ctx.signals.web, lang);
    assert.equal(m.state, 'grownup');
    assert.equal(m.results.length, 0);
    assert.equal(m.query, '');
    assert.equal(m.hero, false);
    assert.equal(spokenSummary(m), GROWNUP[lang].title);
  }
});

test('a meta word in any result title turns the WHOLE page into the grown-up card (WP-6)', () => {
  for (const lang of ['en', 'ar']) {
    const store = createAvatarContextStore({ now: () => 0 });
    store.onSearchMessage(metaWordMessage(lang));
    const m = buildPageModel(store.ctx.signals.web, lang);
    assert.equal(m.state, 'grownup');
    assert.equal(m.results.length, 0, 'none of the clean results leak through either');
  }
});

test('none, skeleton and empty results states', () => {
  const store = createAvatarContextStore({ now: () => 0 });
  store.onSearchMessage(fixtureMessage('sky', 'en', 'searching'));
  assert.equal(buildPageModel(store.ctx.signals.web, 'en').state, 'skeleton');
  assert.equal(buildPageModel(store.ctx.signals.web, 'en').hero, false);
  store.onSearchMessage(fixtureMessage('sky', 'en', 'none'));
  const none = buildPageModel(store.ctx.signals.web, 'en');
  assert.equal(none.state, 'none');
  assert.equal(none.hero, false);
  assert.equal(spokenSummary(none), NONE_TEXT.en.title);
  store.onSearchMessage({ st: 'results', kind: 'web', q: 'sky', r: [{ t: '' }, null, 5] });
  assert.equal(buildPageModel(store.ctx.signals.web, 'en').state, 'none', 'unusable results are none');
});

test('the store keeps only what the page can show and never more than 5 results', () => {
  const store = createAvatarContextStore({ now: () => 0 });
  assert.equal(store.onSearchMessage({ st: 'results', kind: 'library' }), false, 'library searches are not web pages');
  assert.equal(store.onSearchMessage({ st: 'bogus' }), false);
  assert.equal(store.onSearchMessage(null), false);
  const r = Array.from({ length: 9 }, (_, i) => ({ t: `T${i}`, d: 'a.example', s: 's', evil: '<script>' }));
  store.onSearchMessage({ st: 'results', kind: 'web', q: 'x', r, url: 'https://elsewhere.example/page' });
  const w = store.ctx.signals.web;
  assert.equal(w.r.length, 5);
  assert.deepEqual(Object.keys(w.r[0]).sort(), ['d', 's', 't']);
  assert.equal(w.url, undefined, 'a full URL is never kept');
  const m = buildPageModel(w, 'en');
  assert.equal(m.results.length, LIMITS.results);
});

test('the query topic picks a picture category', () => {
  assert.equal(topicOf('why is the sky blue'), 'weather');
  assert.equal(topicOf('how do bees make honey'), 'animals');
  assert.equal(topicOf('لماذا السماء زرقاء'), 'weather');
  assert.equal(topicOf('كيف يصنع النحل العسل'), 'animals');
  assert.equal(topicOf('zzz'), 'generic');
});

// ---------------------------------------------------------------------------------------------------------------
// Layout and truncation

test('wrapWords never splits a word, never exceeds the width, and ends a truncated last line with an ellipsis', () => {
  const text = 'The quick brown fox jumps over the lazy dog and keeps running through the whole green meadow';
  const lines = wrapWords(text, measure, 'cardTitle', 150, 2);
  assert.ok(lines.length <= 2);
  for (const l of lines) assert.ok(measure(l) <= 150 + 0.01, `"${l}" is ${measure(l)}`);
  assert.ok(lines[lines.length - 1].endsWith('…'), 'truncated');
  const words = new Set(text.split(' '));
  for (const l of lines) for (const w of l.replace('…', '').split(' ').filter(Boolean)) assert.ok(words.has(w) || text.includes(w), `broken word ${w}`);
  assert.deepEqual(wrapWords('', measure, 'cardTitle', 150, 2), []);
  assert.deepEqual(wrapWords('short', measure, 'cardTitle', 150, 2), ['short']);
});

test('a word longer than the line is cut with an ellipsis (no overflow past the card)', () => {
  const lines = wrapWords('A' + 'x'.repeat(80), measure, 'cardTitle', 120, 2);
  for (const l of lines) assert.ok(measure(l) <= 120 + 0.01);
});

test('the layout for every fixture: cards stack without overlap, fit the page, and the page stays under the cap', () => {
  for (const name of Object.keys(FIXTURES)) {
    for (const lang of ['en', 'ar']) {
      const lay = layoutPage(model(name, lang), measure);
      assert.equal(lay.state, 'results');
      assert.ok(lay.cards.length >= 2);
      let prev = lay.hero.y + lay.hero.h;
      for (const c of lay.cards) {
        assert.ok(c.y >= prev, `card ${c.i} overlaps the one above`);
        assert.ok(c.titleLines.length <= 2 && c.snipLines.length <= 2);
        assert.ok(c.x + c.w <= WIN.w, 'inside the window');
        prev = c.y + c.h;
      }
      assert.ok(lay.pageH <= PAGE_MAX);
      assert.ok(lay.pageH > WIN.view, 'there is something to scroll');
      assert.ok(lay.pitch > 100 && lay.pitch < 260, `pitch ${lay.pitch}`);
      const mm = model(name, lang);
      assert.ok(lay.hl && lay.hl.y === lay.cards[mm.hl].y, 'the found card rectangle');
      assert.ok(lay.atlasH <= TILE.h * TILE.count, 'the atlas fits 3 tiles');
    }
  }
});

test('scroll limits: max is pageH minus the viewport, and the found scroll puts the card at 25 percent', () => {
  const lay = layoutPage(model('sky', 'en', 2), measure);
  const info = scrollInfo(lay);
  assert.equal(info.max, lay.pageH - WIN.view);
  const f = foundScroll(lay);
  assert.ok(f >= 0 && f <= info.max);
  if (f > 0 && f < info.max) assert.ok(Math.abs(lay.hl.y - f - WIN.view * 0.25) < 0.5);
});

test('the skeleton and the grown-up page both lay out inside one atlas', () => {
  const sk = layoutSkeleton({ id: 'a', lang: 'en', rtl: false, query: 'why is the sky blue' }, measure);
  assert.equal(sk.state, 'skeleton');
  assert.ok(sk.atlasH <= TILE.h * TILE.count);
  for (const b of sk.bars) assert.ok(b.wFrac >= 0.6 - 1e-9 && b.wFrac <= 1);
  const store = createAvatarContextStore({ now: () => 0 });
  store.onSearchMessage(flaggedMessage('ar'));
  const lay = layoutPage(buildPageModel(store.ctx.signals.web, 'ar'), measure);
  assert.ok(lay.card && lay.card.titleLines.length >= 1);
  assert.equal(lay.cards.length, 0);
});

// ---------------------------------------------------------------------------------------------------------------
// RTL (WP-5): a recording 2D context

function recorder() {
  const calls = [];
  const state = { font: '', fillStyle: '', direction: 'ltr', textAlign: 'left', textBaseline: 'alphabetic' };
  const target = {
    measureText: (t) => ({ width: String(t).length * 7.5 }),
    fillText: (text, x, y) => calls.push({ text, x, y, direction: state.direction, textAlign: state.textAlign, font: state.font }),
  };
  const ctx = new Proxy(target, {
    get(t, k) {
      if (k in t) return t[k];
      if (k in state) return state[k];
      if (k === 'createLinearGradient' || k === 'createRadialGradient') return () => ({ addColorStop() {} });
      return () => {};
    },
    set(t, k, v) {
      state[k] = v;
      return true;
    },
  });
  return { ctx, calls };
}

function textCalls(m) {
  const { ctx, calls } = recorder();
  const lay = layoutPage(m, makeMeasure(ctx));
  for (let k = 0; k < TILE.count; k++) drawTile(ctx, k, 2, lay, m, 0, 1);
  return { calls, lay };
}

test('Arabic: every text is drawn right-aligned in a right-to-left run, except the domains (left to right)', () => {
  const m = model('sky', 'ar');
  const { calls, lay } = textCalls(m);
  assert.ok(calls.length > 8);
  const domains = new Set(m.results.map((r) => r.d));
  for (const c of calls) {
    if (domains.has(c.text)) {
      assert.equal(c.direction, 'ltr', `domain ${c.text} is left to right`);
    } else if (/[ء-ي]/.test(c.text) && c.textAlign !== 'center') {
      assert.equal(c.direction, 'rtl', `"${c.text}" direction`);
      assert.equal(c.textAlign, 'right', `"${c.text}" is right aligned`);
      assert.ok(c.x > WIN.w / 2, `"${c.text}" sits on the right half (x ${c.x})`);
    }
  }
  for (const c of lay.cards) assert.ok(c.titleLines.every((l) => /[ء-ي]/.test(l)));
});

test('English: text is left-aligned in a left-to-right run, and every domain is drawn', () => {
  const m = model('sky', 'en');
  const { calls } = textCalls(m);
  for (const r of m.results) assert.ok(calls.some((c) => c.text === r.d), `domain ${r.d} drawn`);
  for (const c of calls) if (c.textAlign === 'left') assert.equal(c.direction, 'ltr');
});

test('no drawn line is a broken word: each line is a run of whole words from the source text', () => {
  for (const lang of ['en', 'ar']) {
    const m = model('bees', lang);
    const { calls } = textCalls(m);
    const source = [m.query, ...m.results.flatMap((r) => [r.t, r.s])].join(' ');
    const sourceWords = new Set(source.split(/\s+/));
    for (const c of calls) {
      if (c.textAlign === 'center') continue;
      for (const w of c.text.replace('…', '').split(/\s+/).filter(Boolean)) {
        assert.ok(sourceWords.has(w) || m.results.some((r) => r.d === w) || w.length < 3, `"${w}" is a broken word in "${c.text}"`);
      }
    }
  }
});

test('the URL pill shows a plain domain (never a full address) once there are results', () => {
  const m = model('sky', 'en');
  const lay = layoutPage(m, measure);
  const t = chromeText(m, lay);
  assert.equal(t.pill, m.results[m.hl].d);
  assert.ok(!/[/:?]/.test(t.pill));
  const sk = chromeText({ state: 'skeleton', lang: 'ar' }, null);
  assert.equal(sk.pill, '');
  assert.ok(sk.searching.length > 0);
});

// ---------------------------------------------------------------------------------------------------------------
// Scroll physics (WP-4)

function newScroll(max = 800, pitch = 170) {
  const s = createScroll();
  s.reset(max, pitch);
  s.read();
  return s;
}

test('drift is 12 to 16 px per second while reading', () => {
  const s = newScroll();
  const p0 = s.pos;
  for (let i = 0; i < 60 * 3; i++) s.step(DT);
  const rate = (s.pos - p0) / 3;
  assert.ok(rate >= 12 && rate <= 16, `drift ${rate} px/s`);
});

test('a flick travels one card, within 15 percent, and never past the rubber band', () => {
  const s = newScroll(900, 170);
  s.step(2); // past the min gap
  const p0 = s.pos;
  assert.ok(s.flick());
  const drift = SCROLL.drift;
  for (let i = 0; i < 60 * 1.4; i++) s.step(DT);
  const moved = s.pos - p0 - drift * 1.4;
  assert.ok(Math.abs(moved - 170) <= 170 * 0.15, `moved ${moved}`);
  assert.ok(s.pos <= s.max + SCROLL.rubber + 1e-6);
});

test('the page never stalls between flicks: the drift keeps running under a decaying flick (review)', () => {
  const s = newScroll(5000, 170);
  s.step(2);
  assert.ok(s.flick());
  let slowest = Infinity;
  for (let i = 0; i < 60 * 1.6; i++) {
    const p = s.pos;
    s.step(DT);
    slowest = Math.min(slowest, (s.pos - p) / DT);
  }
  assert.ok(slowest >= SCROLL.drift * 0.95, `the page slowed to ${slowest.toFixed(1)} px/s before the next flick`);
});

test('flicks are limited: at most 6 per search, 1.6 s apart, never near the end, never in reduced motion', () => {
  const s = newScroll(5000, 170);
  let n = 0;
  for (let i = 0; i < 60 * 60; i++) {
    s.step(DT);
    if (s.flick()) n += 1;
  }
  assert.equal(n, SCROLL.maxFlicks);
  const r = newScroll(900, 170);
  r.reduced = true;
  r.step(5);
  assert.equal(r.flick(), false);
  const e = newScroll(900, 170);
  e.step(2);
  e.pos = e.max - 10;
  assert.equal(e.flick(), false, 'not within the end zone');
  const g = newScroll(900, 170);
  g.step(0.2);
  assert.ok(g.flick());
  g.step(0.3);
  assert.equal(g.flick(), false, 'min gap');
});

test('the rubber band never stretches past 24 px, even with a flick that lands on the end', () => {
  const s = newScroll(300, 250);
  let worst = 0;
  s.step(2);
  s.pos = 150;
  s.flick();
  for (let i = 0; i < 60 * 6; i++) {
    s.step(DT);
    worst = Math.max(worst, s.pos - s.max);
  }
  assert.ok(worst <= SCROLL.rubber + 1e-6, `stretch ${worst}`);
  for (let i = 0; i < 60 * 3; i++) s.step(DT);
  assert.ok(s.pos <= s.max + 1e-6 || s.pos - s.max < 1, 'settles back');
});

test('the drift turns around at the far end and returns, and never goes below the top', () => {
  const s = newScroll(60, 170);
  let min = 0;
  let max = 0;
  for (let i = 0; i < 60 * 30; i++) {
    s.step(DT);
    min = Math.min(min, s.pos);
    max = Math.max(max, s.pos);
  }
  assert.ok(min > -1, `min ${min}`);
  assert.ok(max < 60 + SCROLL.rubber);
});

test('found: a critically damped spring brings the card to the target without overshoot; reduced motion jumps', () => {
  const s = newScroll(800, 170);
  s.pos = 300;
  s.found(120, false);
  let over = 0;
  for (let i = 0; i < 60 * 3; i++) {
    s.step(DT);
    over = Math.max(over, 120 - s.pos);
  }
  assert.ok(Math.abs(s.pos - 120) < 0.5, `pos ${s.pos}`);
  assert.ok(over < 1, `overshoot ${over}`);
  const r = newScroll(800, 170);
  r.reduced = true;
  r.found(200, true);
  assert.equal(r.pos, 200);
  r.step(1);
  assert.equal(r.pos, 200, 'no motion after the jump');
});

test('the physics allocates nothing per step (the same object, finite numbers)', () => {
  const s = newScroll();
  const keys = Object.keys(s).join();
  for (let i = 0; i < 600; i++) {
    s.step(DT);
    s.flick();
  }
  assert.equal(Object.keys(s).join(), keys);
  assert.ok(Number.isFinite(s.pos) && Number.isFinite(s.vel));
});

// ---------------------------------------------------------------------------------------------------------------
// Reading gaze

test('the gaze sweeps left to right in English and right to left in Arabic, and stays inside the window', () => {
  for (const rtl of [false, true]) {
    const g = createReadingGaze(() => 0.5);
    g.reset(rtl);
    let lo = 1e9;
    let hi = -1e9;
    for (let i = 0; i < 60 * 12; i++) {
      g.step(DT, 0, true);
      lo = Math.min(lo, g.x);
      hi = Math.max(hi, g.x);
      assert.ok(g.x >= 0 && g.x <= WIN.w && g.y >= 0 && g.y <= WIN.h, `gaze ${g.x},${g.y}`);
    }
    if (rtl) assert.ok(hi > WIN.w - GAZE.margin - 1 && lo < WIN.w - GAZE.margin - GAZE.lineLen + 1);
    else assert.ok(lo < GAZE.margin + 1 && hi > GAZE.margin + GAZE.lineLen - 1);
  }
});

test('a sweep takes 0.6 s out and 0.15 s back, then steps down 22 px', () => {
  const g = createReadingGaze(() => 0.5);
  g.reset(false);
  const y0 = g.y;
  for (let i = 0; i < Math.round(60 * 0.75) + 2; i++) g.step(DT, 0, true);
  assert.ok(Math.abs(g.y - (y0 + GAZE.stepDown)) < 1, `step ${g.y - y0}`);
});

test('a flick jumps the gaze to the top of the new view and asks for exactly one blink', () => {
  const g = createReadingGaze(() => 0.5);
  g.reset(false);
  for (let i = 0; i < 60 * 3; i++) g.step(DT, 0, true);
  g.onFlick();
  assert.equal(g.blink, true);
  g.step(DT, 0, true);
  assert.equal(g.blink, false, 'a blink is one frame');
  for (let i = 0; i < 20; i++) g.step(DT, 0, true);
  assert.ok(g.y < GAZE.topY + GAZE.stepDown + 1, `y ${g.y}`);
});

test('a glance at the child happens every 4 to 6 s and lasts about 0.6 s', () => {
  const g = createReadingGaze(() => 0.5);
  g.reset(false);
  const glances = [];
  let on = -1;
  for (let i = 0; i < 60 * 16; i++) {
    g.step(DT, 0, true);
    if (g.glance > 0.5 && on < 0) on = i * DT;
    if (g.glance <= 0.5 && on >= 0) {
      glances.push([on, i * DT]);
      on = -1;
    }
  }
  assert.ok(glances.length >= 2 && glances.length <= 4, `${glances.length} glances`);
  assert.ok(glances[0][0] >= 3.9 && glances[0][0] <= 6.5);
  for (const [a, b] of glances) assert.ok(b - a > 0.2 && b - a < 0.8);
});

test('when not reading, the glance fades out and the gaze stops sweeping', () => {
  const g = createReadingGaze(() => 0.5);
  g.reset(false);
  for (let i = 0; i < 60 * 5; i++) g.step(DT, 0, true);
  for (let i = 0; i < 60; i++) g.step(DT, 0, false);
  assert.ok(g.glance < 0.01);
});

// ---------------------------------------------------------------------------------------------------------------
// The hero rect (WP-1): never meets his head, never covers his mouth

const STAGES = [[390, 844], [360, 640], [1440, 900], [2000, 713], [1024, 768]];

test('the hero rect never meets the head circle, stays on the stage, and keeps the 3:4 shape', () => {
  for (const [W, H] of STAGES) {
    for (const side of [1, -1]) {
      for (const hx of [0.35, 0.5, 0.65]) {
        const r = H >= W ? 0.12 * H : 0.2 * H;
        const head = { x: hx * W, y: 0.35 * H, r, mouthY: 0.35 * H + 0.55 * r };
        const o = heroRect(W, H, head, side);
        assert.ok(!rectHitsCircle(o.x, o.y, o.w, o.h, head.x, head.y, head.r), `${W}x${H} side ${side}: hits the head`);
        assert.ok(o.x >= 0 && o.y >= 0 && o.x + o.w <= W + 0.5 && o.y + o.h <= H + 0.5, `${W}x${H}: on stage ${JSON.stringify(o)}`);
        assert.ok(Math.abs(o.w / o.h - 0.75) < 0.01);
        if (H >= W) assert.ok(o.y >= head.mouthY + 0.04 * H - 0.5, `${W}x${H}: top ${o.y} vs mouth ${head.mouthY}`);
      }
    }
  }
});

test('min-jerk easing is 0 to 1 with a flat start and end', () => {
  assert.equal(minJerk(0), 0);
  assert.equal(minJerk(1), 1);
  assert.ok(minJerk(0.01) < 1e-6 * 100);
  assert.ok(Math.abs(minJerk(0.5) - 0.5) < 1e-9);
  assert.equal(minJerk(-3), 0);
  assert.equal(minJerk(4), 1);
});

// ---------------------------------------------------------------------------------------------------------------
// The state machine: al.search + al.activity through the director (hero, reduced, flicks, webReady)

const ALL = new Set(Object.values(CLIP));

/**
 * Run a web search. `plan` is a list of [seconds, fn(store)] steps. The page model is rebuilt on a new rev exactly
 * the way ClipAvatar does it. Records the holo output every frame.
 */
function runWeb({ reduced = false, results = 'results', resultsAt = 1.5, foundAt = 9, outcome = 'found', total = 22, lang = 'en', modelOn = true } = {}) {
  let clock = 0;
  const store = createAvatarContextStore({ now: () => clock * 1000 });
  const director = createDirector({ rng: () => 0.5, has: (n) => ALL.has(n) });
  const out = makeDirectorOutput();
  store.applySnapshot({ 'al.sig_v': '1' });
  store.markConnected();
  const c = store.ctx;
  const frames = [];
  let rev = -1;
  let webModel = null;
  const done = new Set();
  const at = (t, key, fn) => {
    if (!done.has(key) && clock >= t) {
      done.add(key);
      fn();
    }
  };
  for (let i = 0; i * DT < total; i++) {
    clock = i * DT;
    at(0.5, 'start', () => {
      store.onSearchMessage(fixtureMessage('sky', lang, 'searching', 'w1'));
      store.applyChanged({ 'al.search_kind': 'web', 'al.activity': 'searching' });
    });
    at(0.5 + resultsAt, 'results', () => {
      if (results === 'results') store.onSearchMessage(fixtureMessage('sky', lang, 'results', 'w1'));
      else if (results === 'none') store.onSearchMessage(fixtureMessage('sky', lang, 'none', 'w1'));
      else if (results === 'meta') store.onSearchMessage(metaWordMessage(lang, 'w1'));
    });
    at(0.5 + foundAt, 'end', () => store.applyChanged({ 'al.activity': outcome === 'none' ? 'none' : outcome === 'interrupt' ? 'idle' : 'found' }));
    const sw = c.signals.web;
    if (!sw || sw.used) webModel = null;
    else if (sw.rev !== rev) {
      rev = sw.rev;
      webModel = buildPageModel(sw, lang);
    }
    director.step(
      DT,
      {
        agentState: 'listening', signals: c.signals, cues: c.cues, childSpeaking: false, voiceLevel: -1,
        gam: c.gam, sessionEndingSeq: c.sessionEndingSeq, connectSeq: c.connectSeq, awaySec: c.awaySec,
        walkIn: false, reduced, visible: true, waveAgo: 999, web: modelOn ? webModel : null,
      },
      out,
    );
    const h = out.holo;
    frames.push({
      t: clock, phase: h.phase, web: h.web, hero: h.hero, shift: h.shift, reduced: h.reduced, foundT: h.foundT, swipeT: h.swipeT,
      model: webModel ? webModel.state : null, swipeReq: out.oneShotLogical === CLIP.searchSwipe || out.oneShotLogical === CLIP.found,
    });
  }
  return { frames, out, store };
}

test('a web search latches the page model, opens the window, and closes it again', () => {
  const { frames } = runWeb();
  const open = frames.filter((f) => f.web);
  assert.ok(open.length > 60 * 5, 'the page is on show');
  assert.ok(frames.some((f) => f.phase === HP.HOLD && f.web));
  const last = frames[frames.length - 1];
  assert.equal(last.phase, HP.CLOSED);
  assert.equal(last.web, false);
});

test('hero hold: the hero value rises only after Found, once, and is back to 0 before the end (WP-1 timing)', () => {
  const { frames } = runWeb();
  const heroFrames = frames.filter((f) => f.hero > 0.001);
  assert.ok(heroFrames.length > 60 * 2, 'there is a hold');
  for (const f of heroFrames) assert.ok(f.foundT >= 0, 'never before Found');
  const peak = Math.max(...frames.map((f) => f.hero));
  assert.ok(peak > 0.999 && peak <= 1.0001);
  for (const f of frames) assert.ok(f.hero >= 0 && f.hero <= 1.0001);
  const lastHero = heroFrames[heroFrames.length - 1];
  assert.ok(lastHero.t < frames[frames.length - 1].t - 0.3);
  // one rise and one fall: the value goes up to 1 and down to 0 once
  let rises = 0;
  for (let i = 1; i < frames.length; i++) if (frames[i - 1].hero < 0.001 && frames[i].hero >= 0.001) rises += 1;
  assert.equal(rises, 1);
});

test('the hero hold shifts the collapse and the sparkle by about 2.9 s', () => {
  const { frames } = runWeb();
  const shifted = frames.find((f) => f.shift > 0);
  assert.ok(shifted && Math.abs(shifted.shift - 2.9) < 0.05, `shift ${shifted && shifted.shift}`);
});

test('no hero for none, for the grown-up card, or when no page model exists', () => {
  for (const cfg of [{ results: 'none', outcome: 'none' }, { results: 'meta' }, { modelOn: false }]) {
    const { frames } = runWeb(cfg);
    assert.ok(frames.every((f) => f.hero < 0.001), `no hero for ${JSON.stringify(cfg)}`);
    assert.ok(frames.every((f) => f.shift === 0 || !f.web), 'no shift without a hero');
  }
});

test('reduced motion: a quick fade, no hero, no flick, no clip (WP-7)', () => {
  const { frames } = runWeb({ reduced: true });
  assert.ok(frames.every((f) => f.hero < 0.001));
  assert.ok(frames.every((f) => f.swipeT < 0), 'no flick');
  assert.ok(frames.every((f) => !f.swipeReq));
  assert.ok(frames.some((f) => f.web && f.reduced));
});

test('flicks only start after the results show, at most 6, and only when the page can scroll', () => {
  const { frames } = runWeb({ foundAt: 40, total: 60, resultsAt: 3 });
  const starts = [];
  for (let i = 1; i < frames.length; i++) if (frames[i - 1].swipeT < 0 && frames[i].swipeT >= 0) starts.push(frames[i].t);
  assert.ok(starts.length >= 1 && starts.length <= 6, `${starts.length} flicks`);
  for (const t of starts) assert.ok(t >= 0.5 + 3, `a flick at ${t} before the results`);
  for (let i = 1; i < starts.length; i++) assert.ok(starts[i] - starts[i - 1] >= 1.6 - 1e-6, 'min gap');
});

test('no flicks over a skeleton or a grown-up card (nothing to scroll)', () => {
  for (const cfg of [{ results: 'none', outcome: 'none', foundAt: 20, total: 30 }, { results: 'meta', foundAt: 20, total: 30 }]) {
    const { frames } = runWeb(cfg);
    assert.ok(frames.every((f) => f.swipeT < 0), `no flick for ${cfg.results}`);
  }
});

test('Found waits for the results to have been on show (webReady) but not for ever when none arrive', () => {
  const quick = runWeb({ resultsAt: 6, foundAt: 6.2, total: 24 });
  const foundFrame = quick.frames.find((f) => f.foundT >= 0);
  const resultFrame = quick.frames.find((f) => f.model === 'results');
  assert.ok(foundFrame && resultFrame);
  assert.ok(foundFrame.t - resultFrame.t >= 1.7, `Found ${foundFrame.t - resultFrame.t} s after the results`);
  const never = runWeb({ results: 'skeleton-only', resultsAt: 1, foundAt: 4, total: 24 });
  const f2 = never.frames.find((f) => f.foundT >= 0);
  assert.ok(f2, 'Found still plays');
  assert.ok(f2.t < 12);
  assert.ok(never.frames.every((f) => f.hero < 0.001), 'no hero without results');
});

test('an interrupt closes the page and the timeline never leaves a stuck state', () => {
  const { frames } = runWeb({ outcome: 'interrupt', foundAt: 6 });
  assert.equal(frames[frames.length - 1].phase, HP.CLOSED);
  assert.ok(frames.every((f) => f.hero < 0.001));
});

test('library and folder searches never see the page (WP-8)', () => {
  const store = createAvatarContextStore({ now: () => 0 });
  assert.equal(store.onSearchMessage({ st: 'results', kind: 'folders', r: [{ t: 'x' }] }), false);
  assert.equal(store.ctx.signals.web, null);
  const director = createDirector({ rng: () => 0.5, has: (n) => ALL.has(n) });
  const out = makeDirectorOutput();
  store.applySnapshot({ 'al.sig_v': '1' });
  store.markConnected();
  store.applyChanged({ 'al.search_kind': 'library', 'al.activity': 'searching' });
  const c = store.ctx;
  for (let i = 0; i < 60 * 8; i++) {
    director.step(
      DT,
      {
        agentState: 'listening', signals: c.signals, cues: c.cues, childSpeaking: false, voiceLevel: -1,
        gam: c.gam, sessionEndingSeq: c.sessionEndingSeq, connectSeq: c.connectSeq, awaySec: c.awaySec,
        walkIn: false, reduced: false, visible: true, waveAgo: 999, web: null,
      },
      out,
    );
    assert.equal(out.holo.web, false);
    assert.ok(out.holo.hero < 0.001);
    assert.equal(out.holo.shift, 0);
  }
});

test('a second search replaces the first: the old page is spent', () => {
  const store = createAvatarContextStore({ now: () => 0 });
  store.applySnapshot({ 'al.sig_v': '1' });
  store.markConnected();
  store.applyChanged({ 'al.search_kind': 'web', 'al.activity': 'searching' });
  store.onSearchMessage(fixtureMessage('sky', 'en', 'results', 'a'));
  store.applyChanged({ 'al.activity': 'found' });
  store.applyChanged({ 'al.activity': 'idle' });
  store.applyChanged({ 'al.activity': 'searching' });
  assert.equal(store.ctx.signals.web.used, true, 'the old message is spent when a new search starts');
  store.onSearchMessage(fixtureMessage('bees', 'en', 'searching', 'b'));
  assert.equal(store.ctx.signals.web.used, false);
  assert.equal(store.ctx.signals.web.id, 'b');
});

test('the page model is stable for the same input (the key only changes with the content)', () => {
  const a = model('sky', 'en');
  const b = model('sky', 'en');
  assert.equal(a.key, b.key);
  assert.notEqual(a.key, model('bees', 'en').key);
  assert.notEqual(a.key, model('sky', 'ar').key);
});
