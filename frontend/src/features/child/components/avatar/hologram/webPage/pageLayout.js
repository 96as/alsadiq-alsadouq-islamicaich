// w3: where everything on the held page goes (BEHAVIOUR-SPEC 6.1 and 6.2). Pure: no canvas, no three.js. The
// text measurer is passed in (canvas measureText in the browser, a fixed-width fake in the tests), so line
// wrapping, truncation and the card positions are all unit tested.
//
// Logical pixels: the window is 360 x 480. The first 56 are the fixed chrome (title row and URL pill); the
// page under it scrolls through a 424 px viewport. The atlas stores the chrome at the top and the page below it.

import { FOOTER_TEXT, GROWNUP, NONE_TEXT } from './contentFilter.js';

export const WIN = { w: 360, h: 480, chrome: 56, view: 424, radius: 27, rim: 6 };
export const PAGE_MAX = 1200;

// Font tokens. Weights and sizes follow the spec; the families are the two the app already loads from index.html.
export const FONT = {
  title: { size: 30, weight: 800, lh: 36, family: '"Baloo Bhaijaan 2", "IBM Plex Sans Arabic", system-ui, sans-serif' },
  cardTitle: { size: 21, weight: 600, lh: 26, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  domain: { size: 14, weight: 400, lh: 18, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  snippet: { size: 17, weight: 400, lh: 22, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  tab: { size: 12, weight: 600, lh: 14, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  pill: { size: 13, weight: 400, lh: 16, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  query: { size: 16, weight: 400, lh: 20, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
  badge: { size: 19, weight: 800, lh: 22, family: '"Baloo Bhaijaan 2", system-ui, sans-serif' },
  footer: { size: 13, weight: 400, lh: 16, family: '"IBM Plex Sans Arabic", system-ui, sans-serif' },
};

export const fontString = (k) => `${FONT[k].weight} ${FONT[k].size}px ${FONT[k].family}`;

export const PAD = 14; // side margin of the page
export const CARD = { padY: 16, padX: 14, gap: 14, badge: 36, radius: 16, titleLines: 2, snipLines: 2, textGap: 4 };
export const HERO = { y: 68, h: 150 };
export const QUERY_BOX = { y: 14, h: 44 };
const ELLIPSIS = '…';

/**
 * Wrap `text` into at most `maxLines` lines no wider than `maxW`, breaking only between words. A word that
 * is wider than a whole line is shortened with an ellipsis (it is never split over two lines). When the text
 * does not fit, the last line ends with an ellipsis at a word boundary.
 * @param {string} text
 * @param {(text: string, font: string) => number} measure
 * @param {string} font a key of FONT
 * @param {number} maxW
 * @param {number} maxLines
 * @returns {string[]}
 */
export function wrapWords(text, measure, font, maxW, maxLines) {
  const words = String(text).split(' ').filter(Boolean);
  if (words.length === 0) return [];
  const w = (s) => measure(s, font);
  const fit = (word) => {
    if (w(word) <= maxW) return word;
    // one over-long word: shorten it from the end (it stays whole, as one line)
    let cut = word;
    while (cut.length > 1 && w(cut + ELLIPSIS) > maxW) cut = cut.slice(0, -1);
    return cut + ELLIPSIS;
  };
  const lines = [];
  let cur = '';
  let i = 0;
  for (; i < words.length; i++) {
    const word = words[i];
    const next = cur ? `${cur} ${word}` : word;
    if (w(next) <= maxW || !cur) {
      cur = next;
      if (!cur.includes(' ') && w(cur) > maxW) cur = fit(cur);
      continue;
    }
    if (lines.length === maxLines - 1) break; // the last line is the one that gets the ellipsis
    lines.push(cur);
    cur = word;
    if (w(cur) > maxW) cur = fit(cur);
  }
  if (i < words.length) {
    // more words than lines: close the last line with an ellipsis, at a word boundary
    let parts = cur.split(' ');
    let line = parts.join(' ');
    while (parts.length > 1 && w(line + ELLIPSIS) > maxW) {
      parts = parts.slice(0, -1);
      line = parts.join(' ');
    }
    if (parts.length === 1 && w(line + ELLIPSIS) > maxW) line = fit(parts[0]).replace(new RegExp(`${ELLIPSIS}$`), '');
    cur = line.replace(/[\s.,;:!?-]+$/, '') + ELLIPSIS;
  }
  lines.push(cur);
  return lines;
}

/** A deterministic hash of a string to an unsigned 32-bit integer (FNV-1a). */
export function hash32(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

// Badge palette (the hologram palette, soft versions for a white card).
export const BADGE_COLORS = ['#FF8A7A', '#FFD36E', '#8EF0D2', '#7DC8F5', '#C3A6F5', '#F5A6D0'];
const LATIN = /[A-Za-z]/;
const ARABIC = /[ء-ي]/;

/** The letter in a result's badge (the first letter of the domain, else of the title) and its colour. */
export function badgeOf(result) {
  const src = result.d || result.t || '?';
  let letter = '';
  for (const ch of src) {
    if (LATIN.test(ch) || ARABIC.test(ch)) {
      letter = ch.toUpperCase();
      break;
    }
  }
  return { letter: letter || '?', color: BADGE_COLORS[hash32(result.d || result.t || '') % BADGE_COLORS.length] };
}

/**
 * The full layout of a results page.
 * @param {object} model from buildPageModel
 * @param {(text: string, font: string) => number} measure
 */
export function layoutPage(model, measure) {
  const rtl = model.rtl;
  const lang = model.lang;
  const out = {
    state: model.state,
    rtl,
    lang,
    pageH: 0,
    atlasH: 0,
    query: { y: QUERY_BOX.y, h: QUERY_BOX.h, lines: [] },
    hero: null,
    title: { y: 0, lines: [] },
    cards: [],
    pitch: 0,
    foot: { y: 0, text: FOOTER_TEXT[lang] },
    hl: null, // the found card's rectangle in page space
    card: null, // grown-up / none card
  };
  const innerW = WIN.w - PAD * 2;
  out.query.lines = wrapWords(model.query, measure, 'query', innerW - 56, 1);

  let y = HERO.y;
  if (model.state === 'grownup' || model.state === 'none') {
    const T = model.state === 'grownup' ? GROWNUP[lang] : NONE_TEXT[lang];
    out.hero = { y: HERO.y, h: HERO.h };
    y = HERO.y + HERO.h + PAD;
    const titleLines = wrapWords(T.title, measure, 'cardTitle', innerW - 40, 2);
    const bodyLines = wrapWords(T.body, measure, 'snippet', innerW - 40, 3);
    const h = CARD.padY * 2 + titleLines.length * FONT.cardTitle.lh + 8 + bodyLines.length * FONT.snippet.lh;
    out.card = { y, h, x: PAD, w: innerW, titleLines, bodyLines };
    out.title = { y: 0, lines: [] };
    y += h + CARD.gap;
  } else {
    out.hero = { y: HERO.y, h: HERO.h };
    y = HERO.y + HERO.h + PAD;
    const tl = model.query ? wrapWords(model.query, measure, 'title', innerW, 2) : [];
    out.title = { y, lines: tl };
    y += tl.length * FONT.title.lh + (tl.length ? 10 : 0);
    const textW = innerW - CARD.padX * 2 - CARD.badge - 10;
    for (let i = 0; i < model.results.length; i++) {
      const r = model.results[i];
      const titleLines = wrapWords(r.t, measure, 'cardTitle', textW, CARD.titleLines);
      const snipLines = wrapWords(r.s, measure, 'snippet', innerW - CARD.padX * 2, CARD.snipLines);
      const head = Math.max(CARD.badge, titleLines.length * FONT.cardTitle.lh);
      const h =
        CARD.padY * 2 +
        head +
        (r.d ? CARD.textGap + FONT.domain.lh : 0) +
        (snipLines.length ? 8 + snipLines.length * FONT.snippet.lh : 0);
      out.cards.push({ i, y, h, x: PAD, w: innerW, titleLines, snipLines, domain: r.d, badge: badgeOf(r) });
      y += h + CARD.gap;
    }
    if (out.cards.length) {
      let sum = 0;
      for (const c of out.cards) sum += c.h + CARD.gap;
      out.pitch = sum / out.cards.length;
      if (model.hl >= 0 && out.cards[model.hl]) {
        const c = out.cards[model.hl];
        out.hl = { x: c.x, y: c.y, w: c.w, h: c.h };
      }
    }
  }
  out.foot.y = y + 4;
  out.pageH = Math.min(PAGE_MAX, Math.ceil(out.foot.y + FONT.footer.lh + PAD * 2));
  out.atlasH = WIN.chrome + out.pageH;
  return out;
}

/** The skeleton page: placeholder bars (10 px, radius 5, widths 60 to 95 percent) where the results will be. */
export function layoutSkeleton(model, measure) {
  const qlines = model && model.query && measure ? wrapWords(model.query, measure, 'query', WIN.w - PAD * 2 - 56, 1) : [];
  const seed = hash32(model && model.id ? model.id : 'skeleton');
  const bars = [];
  const innerW = WIN.w - PAD * 2;
  const rnd = (k) => ((hash32(`${seed}:${k}`) % 1000) / 1000) * 0.35 + 0.6; // 0.60 .. 0.95
  let y = HERO.y + HERO.h + PAD;
  bars.push({ y, h: 16, wFrac: 0.7 });
  y += 30;
  for (let c = 0; c < 3; c++) {
    bars.push({ y, h: 10, wFrac: rnd(c * 3), x: PAD, kind: 'badge' });
    y += 20;
    bars.push({ y, h: 10, wFrac: rnd(c * 3 + 1) });
    y += 16;
    bars.push({ y, h: 10, wFrac: rnd(c * 3 + 2) });
    y += 46; // a placeholder card is 74 px tall (see drawSkeleton), 8 px apart
  }
  return { state: 'skeleton', rtl: !!(model && model.rtl), lang: model ? model.lang : 'en', query: { y: QUERY_BOX.y, h: QUERY_BOX.h, lines: qlines }, cards: [], hl: null, pitch: 0, bars, innerW, hero: { y: HERO.y, h: HERO.h }, pageH: y, atlasH: WIN.chrome + y };
}

/** The scroll limits and the stops of a layout (page px, 0 = top). */
export function scrollInfo(layout) {
  const max = Math.max(0, layout.pageH - WIN.view);
  const stops = [];
  for (const c of layout.cards) stops.push(Math.min(max, Math.max(0, c.y - 12)));
  return { max, pitch: layout.pitch || 170, stops };
}

/** The scroll position (page px) that puts the found card's top at 25 percent of the viewport. */
export function foundScroll(layout) {
  if (!layout.hl) return 0;
  const max = Math.max(0, layout.pageH - WIN.view);
  return Math.min(max, Math.max(0, layout.hl.y - WIN.view * 0.25));
}
