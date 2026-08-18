import { COLORS, corPelaMeta } from "./colors";

function polarToCartesian(cx, cy, r, angleDeg) {
  const a = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? "0" : "1";
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

/**
 * Gauge radial. Cor é SEMPRE vermelho ou verde, de acordo com a meta
 * real (vinda da API) — nunca uma faixa "amarela" arbitrária.
 *
 * value / meta: em percentual (0-100). invertido: true quando menor é
 * melhor (ex: Corretiva).
 */
export function Gauge({ value, meta, label, size = 148, big = false, invertido = false }) {
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;

  const temValor = value != null && !Number.isNaN(value);
  const color = temValor ? corPelaMeta(value, meta, invertido) : COLORS.textFaint;
  const valueAngle = -90 + (Math.min(temValor ? value : 0, 100) / 100) * 180;
  const metaAngle = meta != null ? -90 + (Math.min(meta, 100) / 100) * 180 : null;
  const ticks = [0, 25, 50, 75, 100];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size / 1.55 }}>
        <svg width={size} height={size / 1.55} viewBox={`0 0 ${size} ${size}`}>
          <path
            d={describeArc(cx, cy, r, -90, 90)}
            fill="none"
            stroke={COLORS.borderSoft}
            strokeWidth={big ? 10 : 8}
            strokeLinecap="round"
          />
          {ticks.map((t) => {
            const a = -90 + (t / 100) * 180;
            const p1 = polarToCartesian(cx, cy, r + (big ? 10 : 8), a);
            const p2 = polarToCartesian(cx, cy, r + (big ? 16 : 13), a);
            return (
              <line key={t} x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke={COLORS.textFaint} strokeWidth={1.5} />
            );
          })}
          {/* marcador da meta real (vinda da API) */}
          {metaAngle != null && (
            <line
              {...(() => {
                const p1 = polarToCartesian(cx, cy, r - (big ? 8 : 6), metaAngle);
                const p2 = polarToCartesian(cx, cy, r + (big ? 8 : 6), metaAngle);
                return { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y };
              })()}
              stroke={COLORS.goldBright}
              strokeWidth={2}
            />
          )}
          {temValor && (
            <path
              d={describeArc(cx, cy, r, -90, valueAngle)}
              fill="none"
              stroke={color}
              strokeWidth={big ? 10 : 8}
              strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 6px ${color}99)` }}
            />
          )}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-0" style={{ top: big ? 18 : 10 }}>
          <span
            className={`font-mono font-semibold ${big ? "text-3xl" : "text-2xl"}`}
            style={{ color: temValor ? COLORS.text : COLORS.textFaint, letterSpacing: "-0.02em" }}
          >
            {temValor ? value.toFixed(1).replace(".0", "") : "—"}
            <span className={big ? "text-xl" : "text-sm"} style={{ color: COLORS.textMuted }}>
              %
            </span>
          </span>
        </div>
      </div>
      <span
        className="mt-1 uppercase text-[12px] tracking-[0.14em] font-medium"
        style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}
      >
        {label}
      </span>
      {meta != null && (
        <span className="text-[10.5px]" style={{ color: COLORS.textFaint }}>
          meta {meta.toFixed(0)}%
        </span>
      )}
    </div>
  );
}
