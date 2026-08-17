import React, { useEffect, useState } from "react";
import {
  Factory,
  Boxes,
  ShieldCheck,
  Wrench,
  ClipboardList,
  Radio,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

/* ---------------------------------------------------------
   DESIGN TOKENS
   Painel de controle industrial — HMI de chão de fábrica.
   Navy profundo + latão/âmbar (identidade Incoflandres),
   tipografia condensada de painel + mono para leituras.
--------------------------------------------------------- */
const COLORS = {
  bg: "#0A1220",
  panel: "#0F1B2E",
  panelAlt: "#122036",
  border: "#22314A",
  borderSoft: "#1A2740",
  text: "#E7ECF4",
  textMuted: "#7C8CA6",
  textFaint: "#4C5A73",
  gold: "#CBA135",
  goldBright: "#E9C567",
  steel: "#5B84B1",
  steelSoft: "#3D5A7C",
  green: "#4FAE7A",
  amber: "#D99A3C",
  red: "#D9534F",
};

function statusColor(value, good, warn) {
  if (value >= good) return COLORS.green;
  if (value >= warn) return COLORS.amber;
  return COLORS.red;
}

/* ---------------- Gauge (industrial dial) ---------------- */
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

function Gauge({ value, label, size = 132, big = false, good = 75, warn = 50 }) {
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const color = statusColor(value, good, warn);
  const valueAngle = -90 + (Math.min(value, 100) / 100) * 180;
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
              <line
                key={t}
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={COLORS.textFaint}
                strokeWidth={1.5}
              />
            );
          })}
          <path
            d={describeArc(cx, cy, r, -90, valueAngle)}
            fill="none"
            stroke={color}
            strokeWidth={big ? 10 : 8}
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 6px ${color}99)` }}
          />
        </svg>
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-0"
          style={{ top: big ? 18 : 10 }}
        >
          <span
            className={`font-mono font-semibold ${big ? "text-4xl" : "text-xl"}`}
            style={{ color: COLORS.text, letterSpacing: "-0.02em" }}
          >
            {value.toFixed(1).replace(".0", "")}
            <span className={big ? "text-lg" : "text-xs"} style={{ color: COLORS.textMuted }}>
              %
            </span>
          </span>
        </div>
      </div>
      <span
        className="mt-1 uppercase text-[11px] tracking-[0.14em] font-medium"
        style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}
      >
        {label}
      </span>
    </div>
  );
}

/* ---------------- Panel shell ---------------- */
function Panel({ icon: Icon, title, tone = "steel", children, className = "" }) {
  const toneColor = { steel: COLORS.steel, gold: COLORS.gold, red: COLORS.red }[tone];
  return (
    <section
      className={`rounded-sm overflow-hidden flex flex-col ${className}`}
      style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}` }}
    >
      <header
        className="flex items-center gap-2.5 px-4 py-3"
        style={{
          background: "linear-gradient(180deg,#141F35 0%,#101A2C 100%)",
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <div
          className="w-7 h-7 rounded-sm flex items-center justify-center shrink-0"
          style={{ background: `${toneColor}1F`, border: `1px solid ${toneColor}55` }}
        >
          <Icon size={14} style={{ color: toneColor }} strokeWidth={2.25} />
        </div>
        <h2
          className="text-[13px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: COLORS.text, fontFamily: "Oswald, sans-serif" }}
        >
          {title}
        </h2>
      </header>
      <div className="p-4 flex-1 flex flex-col gap-4">{children}</div>
    </section>
  );
}

/* ---------------- Horizontal bar readouts ---------------- */
function BarRow({ label, value, max, format, color, flag }) {
  const pct = Math.max((value / max) * 100, 3);
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="w-11 shrink-0 text-[11px] font-medium"
        style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}
      >
        {label}
      </span>
      <div className="flex-1 h-4 rounded-[2px] relative" style={{ background: COLORS.borderSoft }}>
        <div
          className="h-full rounded-[2px] flex items-center justify-end px-1.5"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}99, ${color})`,
            minWidth: "34px",
          }}
        >
          <span className="font-mono text-[10.5px] font-semibold" style={{ color: "#0A1220" }}>
            {format ? format(value) : value}
          </span>
        </div>
      </div>
      {flag && (
        <span
          className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-[2px] shrink-0"
          style={{ background: `${COLORS.red}22`, color: COLORS.red, border: `1px solid ${COLORS.red}55` }}
        >
          {flag}
        </span>
      )}
    </div>
  );
}

/* ---------------- KPI stat block ---------------- */
function Stat({ label, value, sub, color }) {
  return (
    <div>
      <div
        className="font-mono font-semibold text-xl leading-none"
        style={{ color: color || COLORS.text }}
      >
        {value}
      </div>
      <div
        className="mt-1 text-[10px] uppercase tracking-[0.1em]"
        style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}
      >
        {label}
      </div>
      {sub && (
        <div className="text-[10px] mt-0.5" style={{ color: COLORS.textFaint }}>
          {sub}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------
   DATA (mock, espelhando o painel original)
--------------------------------------------------------- */
const IMPRESSORAS = [
  { label: "LITO4", value: 52755 },
  { label: "LITO5", value: 51059 },
  { label: "LITO2", value: 33444 },
  { label: "LITO6", value: 10651 },
];
const ENVERNIZADEIRAS = [
  { label: "ENV5", value: 64867 },
  { label: "ENV6", value: 55193 },
  { label: "ENV1", value: 30625 },
  { label: "ENV3", value: 9691 },
];
const IMPRESSORAS_MAX = Math.max(...IMPRESSORAS.map((d) => d.value));
const ENVERNIZADEIRAS_MAX = Math.max(...ENVERNIZADEIRAS.map((d) => d.value));

const MANUTENCAO = [
  { label: "LITO6", value: 48, flag: "CRÍTICO" },
  { label: "ENV6", value: 7 },
  { label: "LITO5", value: 5 },
  { label: "LITO4", value: 4 },
  { label: "ENV1", value: 3 },
  { label: "LITO2", value: 3 },
];

const RNC_TODAY = new Date(2026, 7, 13); // 13/08/2026
const RNC = [
  { cliente: "GDC", defeito: "Barba", prazo: "29/07/2026" },
  { cliente: "PAMPEANO", defeito: "Manchas", prazo: "29/07/2026" },
  { cliente: "CERVIFLAN", defeito: "Sem laudo", prazo: "22/07/2026" },
  { cliente: "PKG", defeito: "Amassada", prazo: "22/07/2026" },
  { cliente: "SANTA EDWIGES", defeito: "Fora de tonalidade", prazo: "22/07/2026" },
  { cliente: "GDC", defeito: "Barba", prazo: "14/08/2026" },
  { cliente: "CAMIL", defeito: "Manchas escuras", prazo: "13/08/2026" },
  { cliente: "GDC", defeito: "Fora de tonalidade", prazo: "13/08/2026" },
  { cliente: "GDC", defeito: "Arte errada", prazo: "09/08/2026" },
  { cliente: "GDC", defeito: "Falta de verniz", prazo: "07/08/2026" },
].map((r) => {
  const [d, m, y] = r.prazo.split("/").map(Number);
  const due = new Date(y, m - 1, d);
  const diff = (due - RNC_TODAY) / 86400000;
  const status = diff < 0 ? "ATRASADO" : diff === 0 ? "VENCE HOJE" : "NO PRAZO";
  const color = diff < 0 ? COLORS.red : diff === 0 ? COLORS.amber : COLORS.green;
  return { ...r, status, color };
});

/* ---------------------------------------------------------
   APP
--------------------------------------------------------- */
export default function App() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const hh = String(time.getHours()).padStart(2, "0");
  const mm = String(time.getMinutes()).padStart(2, "0");
  const ss = String(time.getSeconds()).padStart(2, "0");
  const dateLabel = time
    .toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
    .replace(".", "");

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: `radial-gradient(1200px 600px at 15% -10%, #14243D 0%, ${COLORS.bg} 55%)`,
        color: COLORS.text,
        fontFamily: "Inter, ui-sans-serif, system-ui",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
        .font-mono { font-family: 'IBM Plex Mono', monospace; }
        @keyframes pulse-dot { 0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(207,161,53,.5);} 50% {opacity:.55; box-shadow:0 0 0 5px rgba(207,161,53,0);} }
        .live-dot { animation: pulse-dot 2s ease-in-out infinite; }
        @keyframes scan { 0% { transform: translateY(-100%);} 100% { transform: translateY(100%);} }
        .scanline::after {
          content:""; position:absolute; inset:0; pointer-events:none; overflow:hidden;
          background: linear-gradient(180deg, transparent 0%, rgba(233,197,103,0.06) 45%, rgba(233,197,103,0.12) 50%, rgba(233,197,103,0.06) 55%, transparent 100%);
          animation: scan 5s linear infinite;
        }
      `}</style>

      {/* TOP BAR */}
   
      <div
        className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5"
        style={{ borderBottom: `1px solid ${COLORS.border}`, background: "#0C1526" }}
      >
        <div className="flex items-center gap-3">
          
          {/* IMAGEM DA PASTA PUBLIC */}
          <img 
            src="/LOGO CINBAL-INCO.png" 
            alt="Logo Incoflandres" 
            className="w-36 h-auto object-contain"
          />
          
          <div>
            <div
              className="text-[25px] font-semibold tracking-[0.02em]"
              style={{ fontFamily: "Oswald, sans-serif" }}
            >
              Gestão Industrial
            </div>
            <div className="text-[15px]" style={{ color: COLORS.textMuted }}>
              Resumo diário de performance
            </div>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full live-dot" style={{ background: COLORS.gold }} />
            <span
              className="text-[10.5px] uppercase tracking-[0.14em]"
              style={{ color: COLORS.gold, fontFamily: "Oswald, sans-serif" }}
            >
              Ao vivo
            </span>
          </div>
          <div className="font-mono text-[13px]" style={{ color: COLORS.text }}>
            {hh}:{mm}
            <span style={{ color: COLORS.textFaint }}>:{ss}</span>
          </div>
          <div
            className="text-[11.5px] px-2.5 py-1 rounded-[2px] capitalize"
            style={{ background: COLORS.panelAlt, border: `1px solid ${COLORS.border}`, color: COLORS.textMuted }}
          >
            {dateLabel}
          </div>
        </div>
      </div>

      {/* HERO — OEE */}
      <div
        className="relative overflow-hidden mx-5 mt-5 rounded-sm scanline"
        style={{
          background: "linear-gradient(135deg, #101B30 0%, #0D1727 100%)",
          border: `1px solid ${COLORS.border}`,
        }}
      >
        <div className="relative px-6 pt-5 flex items-center gap-2">
          <span className="w-1 h-4 rounded-full" style={{ background: COLORS.gold }} />
          <h1
            className="text-[13px] font-semibold uppercase tracking-[0.16em]"
            style={{ color: COLORS.goldBright, fontFamily: "Oswald, sans-serif" }}
          >
            Central de Controle Operacional - Produção
          </h1>
        </div>
        <div className="relative grid grid-cols-1 md:grid-cols-[auto_1px_1fr] gap-6 md:gap-8 p-6 pt-4 items-center">
          <div className="flex items-center gap-6">
            <Gauge value={49} label="Índice de OEE" size={168} big good={75} warn={50} />
            <div>
              <div
                className="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-[2px] w-fit"
                style={{ background: `${COLORS.green}1A`, border: `1px solid ${COLORS.green}55`, color: COLORS.green }}
              >
                <TrendingUp size={12} /> +17,0% vs. dia anterior
              </div>
              <p className="mt-3 text-[12.5px] max-w-[220px]" style={{ color: COLORS.textMuted }}>
                Eficiência global do equipamento — meta operacional: 75%
              </p>
            </div>
          </div>

          <div className="hidden md:block h-full" style={{ background: COLORS.border }} />

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            <Gauge value={81.8} label="Performance" good={80} warn={60} />
            <Gauge value={59.5} label="Disponibilidade" good={80} warn={60} />
            <div className="flex flex-col justify-center gap-3">
              <Stat label="Produção total" value="308.285" />
              <Stat label="Eficiência de setup" value="102%" color={COLORS.green} />
            </div>
            <div className="flex flex-col justify-center gap-3">
              <Stat label="Perdas" value="0,18%" color={COLORS.green} />
              <Stat label="Corretiva" value="6,14%" color={COLORS.amber} />
            </div>
          </div>
        </div>
      </div>

      {/* GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 p-5">
        {/* LITOGRAFIA */}
        <Panel icon={Factory} title="Litografia" tone="steel" className="lg:row-span-2">
          <div>
            <div
              className="text-[12px] uppercase tracking-[0.1em] mb-3"
              style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
            >
              Impressoras · quantidade produzida
            </div>
            <div className="flex flex-col gap-2.5">
              {IMPRESSORAS.map((d) => (
                <BarRow
                  key={d.label}
                  label={d.label}
                  value={d.value}
                  max={IMPRESSORAS_MAX}
                  color={COLORS.steel}
                  format={(v) => v.toLocaleString("pt-BR")}
                />
              ))}
            </div>
          </div>
          <div style={{ borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 14 }}>
            <div
              className="text-[12px] uppercase tracking-[0.1em] mb-3"
              style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
            >
              Envernizadeiras · quantidade produzida
            </div>
            <div className="flex flex-col gap-2.5">
              {ENVERNIZADEIRAS.map((d) => (
                <BarRow
                  key={d.label}
                  label={d.label}
                  value={d.value}
                  max={ENVERNIZADEIRAS_MAX}
                  color={COLORS.gold}
                  format={(v) => v.toLocaleString("pt-BR")}
                />
              ))}
            </div>
          </div>
        </Panel>

        {/* ESTOQUE */}
        <Panel icon={Boxes} title="Estoque" tone="steel">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Situação 84" value="15.649" />
            <Stat label="OP's em aberto +5 dias" value="230" color={COLORS.amber} />
          </div>
        </Panel>

        {/* MANUTENÇÃO */}
        <Panel icon={Wrench} title="Manutenção" tone="red">
          <div>
            <div
              className="text-[10.5px] uppercase tracking-[0.1em] mb-3"
              style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
            >
              Corretiva por linha
            </div>
            <div className="flex flex-col gap-2.5">
              {MANUTENCAO.map((d) => (
                <BarRow
                  key={d.label}
                  label={d.label}
                  value={d.value}
                  max={48}
                  color={d.value >= 30 ? COLORS.red : COLORS.amber}
                  format={(v) => `${v}%`}
                  flag={d.flag}
                />
              ))}
            </div>
          </div>
        </Panel>

        {/* QUALIDADE */}
        <Panel icon={ShieldCheck} title="Qualidade" tone="gold" className="lg:row-span-2">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Fardos retidos" value="16" color={COLORS.amber} />
            <Stat label="RNC em aberto" value="10" color={COLORS.red} />
          </div>
          <div>
            <div
              className="text-[10.5px] uppercase tracking-[0.1em] mb-2 flex items-center gap-1.5"
              style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
            >
              <AlertTriangle size={11} /> Visão geral das RNC's em aberto
            </div>
            <div className="rounded-[2px] overflow-hidden" style={{ border: `1px solid ${COLORS.border}` }}>
              <table className="w-full text-[11.5px] border-collapse">
                <thead>
                  <tr style={{ background: COLORS.panelAlt }}>
                    <th className="text-left font-medium px-2.5 py-2" style={{ color: COLORS.textMuted }}>
                      Cliente
                    </th>
                    <th className="text-left font-medium px-2.5 py-2" style={{ color: COLORS.textMuted }}>
                      Defeito
                    </th>
                    <th className="text-right font-medium px-2.5 py-2" style={{ color: COLORS.textMuted }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {RNC.map((r, i) => (
                    <tr key={i} style={{ borderTop: `1px solid ${COLORS.borderSoft}` }}>
                      <td className="px-2.5 py-2 font-medium" style={{ color: COLORS.text }}>
                        {r.cliente}
                      </td>
                      <td className="px-2.5 py-2" style={{ color: COLORS.textMuted }}>
                        {r.defeito}
                      </td>
                      <td className="px-2.5 py-2 text-right">
                        <span
                          className="font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded-[2px]"
                          style={{ background: `${r.color}1F`, color: r.color, border: `1px solid ${r.color}55` }}
                        >
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Panel>

        {/* PCP */}
        <Panel icon={ClipboardList} title="PCP" tone="steel">
          <div className="grid grid-cols-2 gap-4 items-center">
            <Stat label="Aderência ao planejado" value="13%" color={COLORS.red} />
            <div>
              <div className="text-[11px]" style={{ color: COLORS.textFaint }}>
                Métrica em definição
              </div>
              <div className="font-mono text-lg" style={{ color: COLORS.textFaint }}>
                — — —
              </div>
            </div>
          </div>
        </Panel>
      </div>

      <div className="flex items-center gap-1.5 justify-center pb-6 opacity-60">
        <Radio size={11} style={{ color: COLORS.textFaint }} />
        <span className="text-[10px]" style={{ color: COLORS.textFaint }}>
          CMC & Qualidade · Grupo Incoflandres
        </span>
      </div>
    </div>
  );
}