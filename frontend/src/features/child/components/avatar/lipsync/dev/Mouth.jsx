import { useId } from 'react';
import { blendShape, mouthGeometry } from './mouthShapes.js';

/** A flat mouth drawn from 14 viseme weights. Pure: the same weights give the same picture. */
export default function Mouth({ weights, size = 160, label }) {
  const clipId = useId();
  const shape = blendShape(weights);
  const g = mouthGeometry(shape);
  const lipWidth = 4 + 6 * shape.press;
  const teethH = Math.min(g.up + g.down, 20) * shape.teeth;
  return (
    <svg
      viewBox="0 0 200 124"
      width={size}
      height={(size * 124) / 200}
      role="img"
      aria-label={label ?? 'mouth'}
      style={{ background: 'var(--face, #f2c9a5)', borderRadius: 14 }}
    >
      <defs>
        <clipPath id={clipId}>
          <path d={g.inner} />
        </clipPath>
      </defs>
      <path d={g.inner} fill="#4a1520" />
      <g clipPath={`url(#${clipId})`}>
        <rect x={g.left} y={g.cy - g.up - 1} width={g.half * 2} height={teethH + 2} fill="#fffaf0" />
        <ellipse
          cx={g.cx}
          cy={g.cy + g.down * (0.95 - 0.5 * shape.tongue)}
          rx={g.half * 0.55}
          ry={4 + 14 * (1 - shape.tongue) + 6 * shape.tongue}
          fill="#d9606f"
        />
      </g>
      <path d={g.inner} fill="none" stroke="#b8453f" strokeWidth={lipWidth} strokeLinejoin="round" />
    </svg>
  );
}
