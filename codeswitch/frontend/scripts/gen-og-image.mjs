/**
 * Generates codeswitch/frontend/public/og-image.png (1200x630)
 * Run with: node scripts/gen-og-image.mjs
 */
import { createCanvas } from '@napi-rs/canvas';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dir, '../public/og-image.png');

const W = 1200;
const H = 630;

const canvas = createCanvas(W, H);
const ctx = canvas.getContext('2d');

// ── Background ────────────────────────────────────────────
ctx.fillStyle = '#0d1117';
ctx.fillRect(0, 0, W, H);

// Subtle grid lines
ctx.strokeStyle = 'rgba(91,168,245,0.05)';
ctx.lineWidth = 1;
for (let x = 0; x < W; x += 60) {
  ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
}
for (let y = 0; y < H; y += 60) {
  ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
}

// ── Accent top bar ────────────────────────────────────────
const grad = ctx.createLinearGradient(0, 0, W, 0);
grad.addColorStop(0, '#5ba8f5');
grad.addColorStop(1, '#3b82f6');
ctx.fillStyle = grad;
ctx.fillRect(0, 0, W, 6);

// ── "CS" badge ────────────────────────────────────────────
const BADGE_X = 80;
const BADGE_Y = 100;
const BADGE_R = 14;
const BADGE_W = 84;
const BADGE_H = 72;

// Rounded rect helper
function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

roundRect(BADGE_X, BADGE_Y, BADGE_W, BADGE_H, BADGE_R);
ctx.fillStyle = 'rgba(91,168,245,0.12)';
ctx.fill();
ctx.strokeStyle = 'rgba(91,168,245,0.4)';
ctx.lineWidth = 2;
ctx.stroke();

ctx.fillStyle = '#5ba8f5';
ctx.font = 'bold 38px monospace';
ctx.textAlign = 'center';
ctx.textBaseline = 'middle';
ctx.fillText('CS', BADGE_X + BADGE_W / 2, BADGE_Y + BADGE_H / 2);

// ── Title ─────────────────────────────────────────────────
ctx.fillStyle = '#ffffff';
ctx.font = 'bold 82px sans-serif';
ctx.textAlign = 'left';
ctx.textBaseline = 'alphabetic';
ctx.fillText('CodeSwitch', BADGE_X, 260);

// ── Tagline ───────────────────────────────────────────────
ctx.fillStyle = 'rgba(255,255,255,0.55)';
ctx.font = '36px sans-serif';
ctx.fillText('Convert code between Python, Java & C — instantly with AI', BADGE_X, 330);

// ── Feature pills ─────────────────────────────────────────
const pills = ['13 Learning Modules', 'Live Playground', 'Cloud File Manager', 'Free'];
const PILL_Y = 430;
let px = BADGE_X;

ctx.font = 'bold 22px sans-serif';
for (const label of pills) {
  const tw = ctx.measureText(label).width;
  const pw = tw + 32;
  const ph = 40;
  const py = PILL_Y;

  roundRect(px, py, pw, ph, 8);
  ctx.fillStyle = 'rgba(91,168,245,0.10)';
  ctx.fill();
  ctx.strokeStyle = 'rgba(91,168,245,0.30)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = '#5ba8f5';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, px + 16, py + ph / 2);

  px += pw + 16;
}

// ── URL ────────────────────────────────────────────────────
ctx.fillStyle = 'rgba(255,255,255,0.25)';
ctx.font = '24px monospace';
ctx.textAlign = 'left';
ctx.textBaseline = 'alphabetic';
ctx.fillText('code-switch-learntoconquer.vercel.app', BADGE_X, 570);

// ── Save ───────────────────────────────────────────────────
const buf = canvas.toBuffer('image/png');
writeFileSync(OUT, buf);
console.log(`Written ${buf.length} bytes → ${OUT}`);
