// The reduced-motion search icon: a small glass badge with a magnifier (and a skin hint), or a check
// mark when the answer was found. Drawn once into a 128 x 128 canvas, only when the kind changes.
// No letters, no text.

const CORE = '#7DF5E6';
const HI = '#E9FFFB';
const GOLD = '#FFD36E';
const PLATE = 'rgba(11, 46, 53, 0.82)';

function badge(ctx, s, color) {
  const r = s * 0.5;
  ctx.beginPath();
  ctx.arc(r, r, r * 0.92, 0, Math.PI * 2);
  ctx.fillStyle = PLATE;
  ctx.fill();
  ctx.lineWidth = s * 0.04;
  ctx.strokeStyle = color;
  ctx.stroke();
}

function magnifier(ctx, s) {
  ctx.lineCap = 'round';
  ctx.strokeStyle = HI;
  ctx.lineWidth = s * 0.07;
  ctx.beginPath();
  ctx.arc(s * 0.45, s * 0.45, s * 0.2, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(s * 0.6, s * 0.6);
  ctx.lineTo(s * 0.76, s * 0.76);
  ctx.stroke();
}

function hint(ctx, s, kind) {
  ctx.fillStyle = CORE;
  ctx.strokeStyle = CORE;
  ctx.lineWidth = s * 0.03;
  if (kind === 'library') {
    // three book spines inside the lens
    for (let i = 0; i < 3; i++) ctx.fillRect(s * (0.37 + i * 0.07), s * (0.4 - (i % 2) * 0.04), s * 0.045, s * (0.15 + (i % 2) * 0.04));
  } else if (kind === 'folders') {
    ctx.beginPath();
    ctx.roundRect(s * 0.35, s * 0.4, s * 0.2, s * 0.14, s * 0.02);
    ctx.fill();
  } else {
    ctx.beginPath();
    ctx.arc(s * 0.45, s * 0.45, s * 0.07, 0, Math.PI * 2);
    ctx.fill();
  }
}

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {'library'|'folders'|'web'|'check'} kind
 * @param {number} s the canvas size in pixels
 */
export function drawHoloIcon(ctx, kind, s) {
  if (!ctx) return;
  ctx.clearRect(0, 0, s, s);
  if (kind === 'check') {
    badge(ctx, s, GOLD);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = GOLD;
    ctx.lineWidth = s * 0.09;
    ctx.beginPath();
    ctx.moveTo(s * 0.3, s * 0.52);
    ctx.lineTo(s * 0.45, s * 0.66);
    ctx.lineTo(s * 0.72, s * 0.36);
    ctx.stroke();
    return;
  }
  badge(ctx, s, CORE);
  magnifier(ctx, s);
  hint(ctx, s, kind);
}
