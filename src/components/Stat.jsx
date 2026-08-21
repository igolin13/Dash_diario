import { COLORS } from "./colors";

export function Stat({ label, value, sub, color, subSize = "text-[11px]" }) {
  const temValor = value != null && value !== "";
  return (
    <div>
      <div className="font-mono font-semibold text-2xl leading-none" style={{ color: temValor ? color || COLORS.text : COLORS.textFaint }}>
        {temValor ? value : "—"}
      </div>
      <div className="mt-1 text-[11px] uppercase tracking-[0.1em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
        {label}
      </div>
      {sub && (
        <div className={`${subSize} mt-0.5`} style={{ color: COLORS.textFaint }}>
          {sub}
        </div>
      )}
    </div>
  );
}

/**
 * Estado honesto para painéis sem fonte de dados real conectada ainda.
 * Propositalmente NÃO mostra números — nem placeholder, nem mock.
 */
export function EmptyState({ mensagem = "Aguardando integração com a fonte de dados" }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-2 py-6 text-center">
      <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ border: `1.5px dashed ${COLORS.textFaint}` }}>
        <span style={{ color: COLORS.textFaint, fontSize: 15 }}>?</span>
      </div>
      <p className="text-[12px] max-w-[190px]" style={{ color: COLORS.textFaint }}>
        {mensagem}
      </p>
    </div>
  );
}

/** Barra horizontal pra quantidade produzida por linha (dado real da API). */
export function BarRow({ label, value, max, format, color, flag }) {
  const pct = Math.max((value / max) * 100, 3);
  const textoFormatado = format ? format(value) : value;
  // Só a barra mais alta do grupo (100% — sem espaço sobrando depois
  // dela) mantém o número por dentro. Todas as outras, mesmo já bem
  // cheias, mostram o número FORA, na cor da barra — texto escuro por
  // dentro ficava ilegível quando a barra não preenchia até a borda.
  const textoFora = pct < 99.5;

  return (
    <div className="flex items-center gap-2.5">
      <span className="w-12 shrink-0 text-[15px] font-medium" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
        {label}
      </span>
      <div className="flex-1 h-[18px] rounded-[2px] relative" style={{ background: COLORS.borderSoft }}>
        <div
          className="h-full rounded-[2px]"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}99, ${color})`, minWidth: "10px" }}
        />
        <span
          className="font-mono text-[12px] font-semibold absolute top-1/2 -translate-y-1/2 whitespace-nowrap"
          style={textoFora ? { left: `calc(${pct}% + 6px)`, color } : { right: "6px", color: "#0A1220" }}
        >
          {textoFormatado}
        </span>
      </div>
      {flag && (
        <span
          className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded-[2px] shrink-0"
          style={{ background: `${COLORS.red}22`, color: COLORS.red, border: `1px solid ${COLORS.red}55` }}
        >
          {flag}
        </span>
      )}
    </div>
  );
}