// w3: the hero picture at the top of the held page (BEHAVIOUR-SPEC 6.9). Drawn on the canvas, from shapes, by
// topic. No image files, no external art: nothing to license and nothing that can show a face or a letter.
// The hologram palette: teal plate, mint core, gold, coral, soft sky.

const P = {
  plate: '#0B2E35',
  teal: '#14505A',
  mint: '#7DF5E6',
  mint2: '#8EF0D2',
  gold: '#FFD36E',
  coral: '#FF8A7A',
  cream: '#FFF4CF',
  sky: '#BFEFF5',
  sky2: '#7DC8F5',
  white: '#FFFFFF',
  leaf: '#4CC9A0',
  leaf2: '#2E9E80',
};

function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function grad(ctx, x0, y0, x1, y1, stops) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  for (const [o, c] of stops) g.addColorStop(o, c);
  return g;
}

function circle(ctx, x, y, r, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function cloud(ctx, x, y, s, fill = P.white) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.arc(x, y, 16 * s, 0, Math.PI * 2);
  ctx.arc(x + 18 * s, y - 9 * s, 21 * s, 0, Math.PI * 2);
  ctx.arc(x + 42 * s, y - 2 * s, 17 * s, 0, Math.PI * 2);
  ctx.arc(x + 22 * s, y + 6 * s, 17 * s, 0, Math.PI * 2);
  ctx.fill();
}

function star(ctx, x, y, r, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4;
    const rr = i % 2 === 0 ? r : r * 0.28;
    ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  ctx.closePath();
  ctx.fill();
}

function hills(ctx, w, h, c1, c2) {
  ctx.fillStyle = c1;
  ctx.beginPath();
  ctx.moveTo(0, h);
  ctx.bezierCurveTo(w * 0.2, h * 0.5, w * 0.4, h * 0.55, w * 0.55, h * 0.72);
  ctx.bezierCurveTo(w * 0.7, h * 0.9, w * 0.85, h * 0.6, w, h * 0.66);
  ctx.lineTo(w, h);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = c2;
  ctx.beginPath();
  ctx.moveTo(0, h);
  ctx.lineTo(0, h * 0.82);
  ctx.bezierCurveTo(w * 0.25, h * 0.7, w * 0.5, h * 0.95, w * 0.75, h * 0.8);
  ctx.bezierCurveTo(w * 0.88, h * 0.74, w * 0.95, h * 0.78, w, h * 0.8);
  ctx.lineTo(w, h);
  ctx.closePath();
  ctx.fill();
}

function nature(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, P.sky2], [1, P.sky]]);
  ctx.fillRect(0, 0, w, h);
  circle(ctx, w * 0.8, h * 0.28, 22, P.gold);
  circle(ctx, w * 0.8, h * 0.28, 32, 'rgba(255,211,110,0.28)');
  cloud(ctx, w * 0.12, h * 0.3, 0.8);
  hills(ctx, w, h, P.leaf, P.leaf2);
  // a tree
  ctx.fillStyle = '#8A5A3C';
  ctx.fillRect(w * 0.42 - 4, h * 0.5, 8, h * 0.3);
  circle(ctx, w * 0.42, h * 0.42, 24, P.leaf2);
  circle(ctx, w * 0.42 - 15, h * 0.52, 16, P.leaf);
  circle(ctx, w * 0.42 + 16, h * 0.52, 17, P.leaf);
  // flowers
  const r = rng(11);
  for (let i = 0; i < 7; i++) {
    const x = w * (0.08 + r() * 0.84);
    const y = h * (0.82 + r() * 0.14);
    circle(ctx, x, y, 3.2, i % 2 ? P.coral : P.gold);
  }
}

function animals(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, '#FFE9A8'], [1, '#FFD36E']]);
  ctx.fillRect(0, 0, w, h);
  // hexagon honeycomb
  const r = rng(5);
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 9; col++) {
      const hx = col * 44 + (row % 2) * 22 - 6;
      const hy = row * 38 + 10;
      ctx.fillStyle = `rgba(255,255,255,${0.18 + r() * 0.18})`;
      ctx.beginPath();
      for (let k = 0; k < 6; k++) {
        const a = (Math.PI / 3) * k + Math.PI / 6;
        ctx.lineTo(hx + Math.cos(a) * 21, hy + Math.sin(a) * 21);
      }
      ctx.closePath();
      ctx.fill();
    }
  }
  // the bee
  const cx = w * 0.5;
  const cy = h * 0.52;
  ctx.fillStyle = 'rgba(255,255,255,0.75)';
  ctx.beginPath();
  ctx.ellipse(cx - 12, cy - 30, 16, 26, -0.5, 0, Math.PI * 2);
  ctx.ellipse(cx + 14, cy - 30, 16, 26, 0.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = P.gold;
  ctx.beginPath();
  ctx.ellipse(cx, cy, 44, 32, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(cx, cy, 44, 32, 0, 0, Math.PI * 2);
  ctx.clip();
  ctx.fillStyle = P.plate;
  for (const dx of [-14, 8, 28]) ctx.fillRect(cx + dx, cy - 40, 9, 80);
  ctx.restore();
  circle(ctx, cx - 46, cy - 2, 17, P.plate);
  circle(ctx, cx - 52, cy - 6, 3.4, P.white);
  circle(ctx, cx - 41, cy - 6, 3.4, P.white);
  ctx.strokeStyle = P.plate;
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  ctx.arc(cx - 46, cy + 2, 6, 0.2, Math.PI - 0.2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx - 54, cy - 16);
  ctx.quadraticCurveTo(cx - 62, cy - 34, cx - 52, cy - 38);
  ctx.moveTo(cx - 42, cy - 17);
  ctx.quadraticCurveTo(cx - 40, cy - 36, cx - 30, cy - 38);
  ctx.stroke();
  // a dotted flight path
  ctx.fillStyle = 'rgba(11,46,53,0.35)';
  for (let i = 0; i < 9; i++) circle(ctx, w * 0.62 + i * 20, cy + 26 + Math.sin(i * 0.9) * 12, 2.2, ctx.fillStyle);
}

function space(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, w, h, [[0, '#0B2E35'], [0.6, '#122B52'], [1, '#2B2468']]);
  ctx.fillRect(0, 0, w, h);
  const r = rng(3);
  for (let i = 0; i < 46; i++) circle(ctx, r() * w, r() * h, 0.6 + r() * 1.5, `rgba(255,255,255,${0.4 + r() * 0.6})`);
  for (let i = 0; i < 5; i++) star(ctx, r() * w, r() * h * 0.9, 4 + r() * 4, P.cream);
  // planet with a ring
  const px = w * 0.62;
  const py = h * 0.52;
  ctx.save();
  ctx.strokeStyle = 'rgba(125,245,230,0.55)';
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.ellipse(px, py, 66, 17, -0.35, Math.PI, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
  circle(ctx, px, py, 36, grad(ctx, px - 30, py - 30, px + 30, py + 30, [[0, P.coral], [1, '#C9546A']]));
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  ctx.beginPath();
  ctx.ellipse(px - 6, py + 10, 30, 6, -0.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.save();
  ctx.strokeStyle = 'rgba(125,245,230,0.55)';
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.ellipse(px, py, 66, 17, -0.35, 0, Math.PI);
  ctx.stroke();
  ctx.restore();
  // a moon
  circle(ctx, w * 0.2, h * 0.32, 20, '#EDE8D8');
  circle(ctx, w * 0.2 - 6, h * 0.32 - 4, 5, 'rgba(0,0,0,0.12)');
  circle(ctx, w * 0.2 + 7, h * 0.32 + 7, 3.4, 'rgba(0,0,0,0.12)');
}

function weather(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, '#4BA8E8'], [1, '#BFEFF5']]);
  ctx.fillRect(0, 0, w, h);
  circle(ctx, w * 0.22, h * 0.34, 44, 'rgba(255,211,110,0.28)');
  circle(ctx, w * 0.22, h * 0.34, 26, P.gold);
  for (let i = 0; i < 12; i++) {
    const a = (i * Math.PI) / 6;
    ctx.strokeStyle = P.gold;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(w * 0.22 + Math.cos(a) * 33, h * 0.34 + Math.sin(a) * 33);
    ctx.lineTo(w * 0.22 + Math.cos(a) * 42, h * 0.34 + Math.sin(a) * 42);
    ctx.stroke();
  }
  cloud(ctx, w * 0.5, h * 0.52, 1.35);
  cloud(ctx, w * 0.12, h * 0.8, 0.8, 'rgba(255,255,255,0.85)');
  // a rainbow
  const cols = [P.coral, P.gold, P.mint2, P.sky2];
  for (let i = 0; i < cols.length; i++) {
    ctx.strokeStyle = cols[i];
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(w * 0.8, h * 1.05, 64 - i * 6, Math.PI, Math.PI * 2);
    ctx.stroke();
  }
}

function body(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, '#FFD6D0'], [1, '#FFEFEA']]);
  ctx.fillRect(0, 0, w, h);
  const cx = w * 0.5;
  const cy = h * 0.5;
  // a heart
  ctx.fillStyle = P.coral;
  ctx.beginPath();
  ctx.moveTo(cx, cy + 40);
  ctx.bezierCurveTo(cx - 70, cy - 4, cx - 40, cy - 52, cx, cy - 18);
  ctx.bezierCurveTo(cx + 40, cy - 52, cx + 70, cy - 4, cx, cy + 40);
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.beginPath();
  ctx.ellipse(cx - 26, cy - 14, 10, 6, -0.7, 0, Math.PI * 2);
  ctx.fill();
  // a pulse line
  ctx.strokeStyle = P.plate;
  ctx.lineWidth = 3;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(10, cy + 2);
  ctx.lineTo(cx - 70, cy + 2);
  ctx.lineTo(cx - 52, cy - 22);
  ctx.lineTo(cx - 36, cy + 24);
  ctx.lineTo(cx - 22, cy + 2);
  ctx.moveTo(cx + 22, cy + 2);
  ctx.lineTo(cx + 40, cy - 10);
  ctx.lineTo(cx + 52, cy + 14);
  ctx.lineTo(cx + 62, cy + 2);
  ctx.lineTo(w - 10, cy + 2);
  ctx.stroke();
}

function values(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, w, h, [[0, '#C9F5EA'], [1, '#FFF1C9']]);
  ctx.fillRect(0, 0, w, h);
  const r = rng(9);
  for (let i = 0; i < 12; i++) star(ctx, r() * w, r() * h, 3 + r() * 5, i % 2 ? P.gold : P.mint2);
  // two simple hands (rounded shapes) holding a star
  const cx = w * 0.5;
  const cy = h * 0.62;
  ctx.fillStyle = '#F6C7A6';
  ctx.beginPath();
  ctx.ellipse(cx - 28, cy, 40, 17, -0.25, 0, Math.PI * 2);
  ctx.ellipse(cx + 28, cy, 40, 17, 0.25, 0, Math.PI * 2);
  ctx.fill();
  circle(ctx, cx, cy - 36, 40, 'rgba(255,211,110,0.35)');
  star(ctx, cx, cy - 36, 26, P.gold);
}

function generic(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, w, h, [[0, '#0F3F49'], [1, '#14505A']]);
  ctx.fillRect(0, 0, w, h);
  const r = rng(21);
  for (let i = 0; i < 26; i++) circle(ctx, r() * w, r() * h, 1 + r() * 2, 'rgba(125,245,230,0.35)');
  // an open book and a magnifier
  const cx = w * 0.46;
  const cy = h * 0.58;
  ctx.fillStyle = P.cream;
  ctx.beginPath();
  ctx.moveTo(cx, cy - 36);
  ctx.quadraticCurveTo(cx - 40, cy - 52, cx - 74, cy - 38);
  ctx.lineTo(cx - 74, cy + 30);
  ctx.quadraticCurveTo(cx - 40, cy + 14, cx, cy + 32);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#FFFFFF';
  ctx.beginPath();
  ctx.moveTo(cx, cy - 36);
  ctx.quadraticCurveTo(cx + 40, cy - 52, cx + 74, cy - 38);
  ctx.lineTo(cx + 74, cy + 30);
  ctx.quadraticCurveTo(cx + 40, cy + 14, cx, cy + 32);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = 'rgba(11,46,53,0.25)';
  ctx.lineWidth = 2;
  for (let i = 0; i < 4; i++) {
    ctx.beginPath();
    ctx.moveTo(cx + 12, cy - 22 + i * 12);
    ctx.lineTo(cx + 60, cy - 26 + i * 12);
    ctx.stroke();
  }
  ctx.strokeStyle = P.mint;
  ctx.lineWidth = 6;
  circle(ctx, w * 0.78, h * 0.36, 0, P.mint);
  ctx.beginPath();
  ctx.arc(w * 0.78, h * 0.36, 22, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(w * 0.78 + 16, h * 0.36 + 16);
  ctx.lineTo(w * 0.78 + 34, h * 0.36 + 34);
  ctx.stroke();
  ctx.fillStyle = 'rgba(125,245,230,0.15)';
  ctx.beginPath();
  ctx.arc(w * 0.78, h * 0.36, 20, 0, Math.PI * 2);
  ctx.fill();
}

const ART = { nature, animals, space, weather, body, values, generic };

/** Draw the hero picture for `topic` into (0, y) .. (w, y + h) of the current transform. */
export function drawHero(ctx, topic, y, w, h) {
  ctx.save();
  ctx.translate(0, y);
  ctx.beginPath();
  ctx.rect(0, 0, w, h);
  ctx.clip();
  (ART[topic] || generic)(ctx, w, h);
  ctx.restore();
}

export const HERO_TOPICS = Object.keys(ART);
