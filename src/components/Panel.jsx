import { COLORS } from "./colors";

export function Panel({ icon: Icon, title, tone = "steel", children, className = "", badge }) {
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
          className="text-[14.5px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: COLORS.text, fontFamily: "Oswald, sans-serif" }}
        >
          {title}
        </h2>
        {badge && <div className="ml-auto">{badge}</div>}
      </header>
      <div className="p-4 flex-1 flex flex-col gap-4">{children}</div>
    </section>
  );
}
