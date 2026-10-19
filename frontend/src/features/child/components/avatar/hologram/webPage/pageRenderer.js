// w3: draws the held web page onto 2D canvases (BEHAVIOUR-SPEC 6.1, 6.2 and 6.3). Everything here takes a 2D
// context, so it runs under a recording stub in the unit tests as well as on a real canvas.
//
// The atlas is the window in logical px (360 wide). Row 0 to 56 is the fixed chrome; the page starts at atlas y 56.
// It is cut into three horizontal TILES of TILE.h logical px. Each tile is its own canvas (and its own texture),
// and carries TILE.pad extra px above and below so mip-mapping never shows a seam where two tiles meet.
//
// Text: whole lines only, from pageLayout's wrapWords. Arabic lines use direction rtl and textAlign right. Domains
// are always drawn left-to-right (direction ltr), at the start edge of the card.

import { FOOTER_TEXT } from './contentFilter.js';
import { drawHero } from './heroArt.js';
import { CARD, FONT, PAD, QUERY_BOX, WIN, fontString } from './pageLayout.js';

// 3 x 480 = 1440 >= chrome 56 + PAGE_MAX 1200. One tile is exactly the window (56 chrome + 424 viewport), so the
// skeleton, which is the first view of the page, is a single tile: one upload before anything shows. A tile is
// painted in `bands` slices (one per idle frame) so no single frame pays for a whole tile.
export const TILE = { h: 480, pad: 4, count: 3, bands: 2 };

export const INK = {
  page: '#F7F9FA',
  chrome: '#FFFFFF',
  hairline: '#DDE3E6',
  pill: '#EEF2F3',
  title: '#0B2E35',
  body: '#42555B',
  domain: '#2B8C86',
  muted: '#7A8C92',
  card: '#FFFFFF',
  bar: '#E3E7EA',
  dots: ['#FF8A7A', '#FFD36E', '#8EF0D2'],
  mint: '#7DF5E6',
};

const TAB_TEXT = { en: 'Kids search', ar: 'بحث للأطفال' };
const SEARCHING_PILL = { en: 'searching…', ar: 'جارٍ البحث…' };

/** A measurer over a 2D context: width of `text` in the font token `key`. */
export function makeMeasure(ctx) {
  return (text, key) => {
    ctx.font = fontString(key);
    return ctx.measureText(text).width;
  };
}

function rrect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.lineTo(x + w - rr, y);
  ctx.arcTo(x + w, y, x + w, y + rr, rr);
  ctx.lineTo(x + w, y + h - rr);
  ctx.arcTo(x + w, y + h, x + w - rr, y + h, rr);
  ctx.lineTo(x + rr, y + h);
  ctx.arcTo(x, y + h, x, y + h - rr, rr);
  ctx.lineTo(x, y + rr);
  ctx.arcTo(x, y, x + rr, y, rr);
  ctx.closePath();
}

function setText(ctx, key, color, rtl, align) {
  ctx.font = fontString(key);
  ctx.fillStyle = color;
  ctx.direction = rtl ? 'rtl' : 'ltr';
  ctx.textAlign = align; // 'left' | 'right' | 'center' (physical, whatever the direction)
  ctx.textBaseline = 'middle';
}

function magnifier(ctx, x, y, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.2;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.arc(x, y, 6, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x + 4.5, y + 4.5);
  ctx.lineTo(x + 9.5, y + 9.5);
  ctx.stroke();
}

/** What the chrome shows: the tab title, and the URL pill (a plain domain, never a full address). */
export function chromeText(model, layout) {
  const lang = model ? model.lang : 'en';
  let pill = '';
  if (model && model.state === 'results' && layout && layout.cards.length) {
    const c = layout.cards[model.hl >= 0 ? model.hl : 0];
    pill = (c && c.domain) || '';
  }
  return { tab: TAB_TEXT[lang], pill, searching: model && model.state === 'skeleton' ? SEARCHING_PILL[lang] : '' };
}

/** The fixed chrome, atlas y 0 to 56: the three dots and the tab title, and the URL pill. */
export function drawChrome(ctx, model, layout) {
  const rtl = !!(model && model.rtl);
  const t = chromeText(model, layout);
  ctx.fillStyle = INK.chrome;
  ctx.fillRect(0, 0, WIN.w, WIN.chrome);
  ctx.fillStyle = INK.hairline;
  ctx.fillRect(0, WIN.chrome - 1, WIN.w, 1);
  // three dots (mirrored for Arabic, like a mirrored browser)
  for (let i = 0; i < 3; i++) {
    const x = rtl ? WIN.w - 20 - i * 15 : 20 + i * 15;
    ctx.fillStyle = INK.dots[i];
    ctx.beginPath();
    ctx.arc(x, 14, 4.6, 0, Math.PI * 2);
    ctx.fill();
  }
  setText(ctx, 'tab', INK.muted, rtl, 'center');
  ctx.fillText(t.tab, WIN.w / 2, 14);
  // the pill: x 12 to 348, y 26 to 52, radius 15 (a full pill)
  ctx.fillStyle = INK.pill;
  rrect(ctx, 12, 24, WIN.w - 24, 28, 14);
  ctx.fill();
  ctx.fillStyle = INK.mint;
  ctx.beginPath();
  ctx.arc(28, 38, 4, 0, Math.PI * 2);
  ctx.fill();
  const label = t.pill || t.searching;
  if (label) {
    setText(ctx, 'pill', t.pill ? INK.title : INK.muted, t.pill ? false : rtl, t.pill || !rtl ? 'left' : 'right');
    if (t.pill || !rtl) ctx.fillText(label, 42, 38.5);
    else ctx.fillText(label, WIN.w - 42, 38.5);
  }
}

function drawQueryBox(ctx, layout, model) {
  const rtl = layout.rtl;
  const y = WIN.chrome + layout.query.y;
  const w = WIN.w - PAD * 2;
  ctx.save();
  ctx.shadowColor = 'rgba(11,46,53,0.10)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 2;
  ctx.fillStyle = INK.card;
  rrect(ctx, PAD, y, w, QUERY_BOX.h, 22);
  ctx.fill();
  ctx.restore();
  ctx.strokeStyle = '#D4E3E5';
  ctx.lineWidth = 1;
  rrect(ctx, PAD + 0.5, y + 0.5, w - 1, QUERY_BOX.h - 1, 21.5);
  ctx.stroke();
  const iconX = rtl ? WIN.w - PAD - 22 : PAD + 22;
  magnifier(ctx, iconX - 4, y + QUERY_BOX.h / 2 - 3, INK.domain);
  const line = layout.query.lines[0];
  if (line) {
    setText(ctx, 'query', INK.title, rtl, rtl ? 'right' : 'left');
    ctx.fillText(line, rtl ? WIN.w - PAD - 42 : PAD + 42, y + QUERY_BOX.h / 2 + 0.5);
  }
  void model;
}

function drawHeroBlock(ctx, layout, model) {
  const y = WIN.chrome + layout.hero.y;
  const w = WIN.w - PAD * 2;
  ctx.save();
  ctx.translate(PAD, 0);
  rrect(ctx, 0, y, w, layout.hero.h, 20);
  ctx.clip();
  if (model.state === 'skeleton') {
    ctx.fillStyle = INK.bar;
    ctx.fillRect(0, y, w, layout.hero.h);
  } else {
    drawHero(ctx, model.topic, y, w, layout.hero.h);
  }
  ctx.restore();
}

function drawCard(ctx, c, rtl) {
  const x = c.x;
  const y = WIN.chrome + c.y;
  ctx.save();
  ctx.shadowColor = 'rgba(11,46,53,0.12)';
  ctx.shadowBlur = 10;
  ctx.shadowOffsetY = 3;
  ctx.fillStyle = INK.card;
  rrect(ctx, x, y, c.w, c.h, CARD.radius);
  ctx.fill();
  ctx.restore();
  const head = Math.max(CARD.badge, c.titleLines.length * FONT.cardTitle.lh);
  // the letter badge
  const bx = rtl ? x + c.w - CARD.padX - CARD.badge : x + CARD.padX;
  const by = y + CARD.padY + (head - CARD.badge) / 2;
  ctx.fillStyle = c.badge.color;
  ctx.beginPath();
  ctx.arc(bx + CARD.badge / 2, by + CARD.badge / 2, CARD.badge / 2, 0, Math.PI * 2);
  ctx.fill();
  setText(ctx, 'badge', INK.title, false, 'center');
  ctx.fillText(c.badge.letter, bx + CARD.badge / 2, by + CARD.badge / 2 + 1);
  // the title, beside the badge
  const tx = rtl ? bx - 10 : bx + CARD.badge + 10;
  const top = y + CARD.padY + (head - c.titleLines.length * FONT.cardTitle.lh) / 2;
  setText(ctx, 'cardTitle', INK.title, rtl, rtl ? 'right' : 'left');
  for (let i = 0; i < c.titleLines.length; i++) ctx.fillText(c.titleLines[i], tx, top + FONT.cardTitle.lh * (i + 0.5));
  // the domain, always left to right, at the start edge
  let cy = y + CARD.padY + head;
  const sx = rtl ? x + c.w - CARD.padX : x + CARD.padX;
  if (c.domain) {
    setText(ctx, 'domain', INK.domain, false, rtl ? 'right' : 'left');
    ctx.fillText(c.domain, sx, cy + CARD.textGap + FONT.domain.lh / 2);
    cy += CARD.textGap + FONT.domain.lh;
  }
  if (c.snipLines.length) {
    cy += 8;
    setText(ctx, 'snippet', INK.body, rtl, rtl ? 'right' : 'left');
    for (let i = 0; i < c.snipLines.length; i++) ctx.fillText(c.snipLines[i], sx, cy + FONT.snippet.lh * (i + 0.5));
  }
}

function drawNotice(ctx, layout) {
  const c = layout.card;
  const rtl = layout.rtl;
  const y = WIN.chrome + c.y;
  ctx.save();
  ctx.shadowColor = 'rgba(11,46,53,0.12)';
  ctx.shadowBlur = 10;
  ctx.shadowOffsetY = 3;
  ctx.fillStyle = INK.card;
  rrect(ctx, c.x, y, c.w, c.h, CARD.radius);
  ctx.fill();
  ctx.restore();
  // a gold bar on the start side
  ctx.fillStyle = '#FFD36E';
  rrect(ctx, rtl ? c.x + c.w - 6 : c.x, y + 14, 6, c.h - 28, 3);
  ctx.fill();
  const sx = rtl ? c.x + c.w - 20 : c.x + 20;
  setText(ctx, 'cardTitle', INK.title, rtl, rtl ? 'right' : 'left');
  for (let i = 0; i < c.titleLines.length; i++) ctx.fillText(c.titleLines[i], sx, y + CARD.padY + FONT.cardTitle.lh * (i + 0.5));
  const by = y + CARD.padY + c.titleLines.length * FONT.cardTitle.lh + 8;
  setText(ctx, 'snippet', INK.body, rtl, rtl ? 'right' : 'left');
  for (let i = 0; i < c.bodyLines.length; i++) ctx.fillText(c.bodyLines[i], sx, by + FONT.snippet.lh * (i + 0.5));
}

function drawSkeleton(ctx, layout, model) {
  const bars = layout.bars;
  const rtl = layout.rtl;
  const innerW = layout.innerW;
  const bar = (x, y, w, h) => {
    ctx.fillStyle = INK.bar;
    rrect(ctx, rtl ? WIN.w - x - w : x, WIN.chrome + y, w, h, Math.min(5, h / 2));
    ctx.fill();
  };
  // the title bar
  bar(PAD, bars[0].y, innerW * bars[0].wFrac, 16);
  for (let g = 0; g < 3; g++) {
    const b0 = bars[1 + g * 3];
    const b1 = bars[2 + g * 3];
    const b2 = bars[3 + g * 3];
    if (!b0 || !b2) break;
    ctx.save();
    ctx.shadowColor = 'rgba(11,46,53,0.08)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 2;
    ctx.fillStyle = INK.card;
    rrect(ctx, PAD, WIN.chrome + b0.y - 14, innerW, 74, CARD.radius);
    ctx.fill();
    ctx.restore();
    const inner = innerW - CARD.padX * 2;
    ctx.fillStyle = INK.bar;
    ctx.beginPath();
    ctx.arc(rtl ? WIN.w - PAD - CARD.padX - 13 : PAD + CARD.padX + 13, WIN.chrome + b0.y + 5, 13, 0, Math.PI * 2);
    ctx.fill();
    bar(PAD + CARD.padX + 36, b0.y, (inner - 36) * b0.wFrac, 10);
    bar(PAD + CARD.padX, b1.y, inner * b1.wFrac, 10);
    bar(PAD + CARD.padX, b2.y, inner * b2.wFrac, 10);
  }
  void model;
}

/** The page body for a layout (no chrome): query box, hero, title, cards or notice, footer. */
export function drawPageBody(ctx, layout, model, lo, hi) {
  const inView = (y, h) => y + WIN.chrome + h >= lo && y + WIN.chrome <= hi;
  if (layout.state === 'skeleton') {
    drawQueryBox(ctx, layout, model);
    drawHeroBlock(ctx, layout, model);
    drawSkeleton(ctx, layout, model);
    return;
  }
  drawQueryBox(ctx, layout, model);
  drawHeroBlock(ctx, layout, model);
  if (layout.card) {
    drawNotice(ctx, layout);
  } else {
    if (layout.title.lines.length) {
      setText(ctx, 'title', INK.title, layout.rtl, layout.rtl ? 'right' : 'left');
      for (let i = 0; i < layout.title.lines.length; i++) {
        ctx.fillText(layout.title.lines[i], layout.rtl ? WIN.w - PAD - 2 : PAD + 2, WIN.chrome + layout.title.y + FONT.title.lh * (i + 0.5));
      }
    }
    for (const c of layout.cards) if (inView(c.y - 4, c.h + 20)) drawCard(ctx, c, layout.rtl);
  }
  setText(ctx, 'footer', INK.muted, layout.rtl, 'center');
  ctx.fillText(FOOTER_TEXT[layout.lang], WIN.w / 2, WIN.chrome + layout.foot.y + FONT.footer.lh / 2 + 6);
}

/**
 * Paint one tile. The context is for a canvas of (WIN.w x scale) by ((TILE.h + 2 pad) x scale) device px.
 * @param {CanvasRenderingContext2D} ctx
 * @param {number} k tile index 0..2
 * @param {number} scale texels per logical px
 * @param {object} layout from layoutPage or layoutSkeleton (with measured text)
 * @param {object} model the page model
 */
export function drawTile(ctx, k, scale, layout, model, band = 0, bands = 1) {
  const lo = k * TILE.h - TILE.pad; // atlas y at the top of the canvas
  const hi = (k + 1) * TILE.h + TILE.pad;
  // this band's slice, on a whole device pixel boundary so two bands never leave a seam
  const rows = Math.ceil((hi - lo) / bands / 2) * 2;
  const blo = lo + band * rows;
  const bhi = Math.min(hi, blo + rows);
  ctx.setTransform(scale, 0, 0, scale, 0, -lo * scale);
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, blo, WIN.w, bhi - blo);
  ctx.clip();
  ctx.clearRect(0, blo, WIN.w, bhi - blo);
  ctx.fillStyle = INK.page;
  ctx.fillRect(0, blo, WIN.w, bhi - blo);
  if (bhi > WIN.chrome) drawPageBody(ctx, layout, model, blo, bhi);
  if (blo < WIN.chrome) drawChrome(ctx, model, layout);
  ctx.restore();
}
