import { Calendar } from "lucide-react";
import { COLORS } from "./colors";
import { formatarDataISO } from "../lib/api";

/**
 * Filtro de data: mostra a data selecionada e abre um <input type="date">
 * nativo pra trocar. "Voltar para hoje" aparece só quando não está em hoje.
 */
export function FiltroData({ dataSelecionada, onMudarData }) {
  const hoje = new Date();
  const ehHoje = formatarDataISO(dataSelecionada) === formatarDataISO(hoje);

  return (
    <div className="flex items-center gap-2">
      <label
        className="relative flex items-center gap-1.5 text-[11.5px] px-2.5 py-1 rounded-[2px] cursor-pointer capitalize"
        style={{ background: COLORS.panelAlt, border: `1px solid ${COLORS.border}`, color: COLORS.textMuted }}
      >
        <Calendar size={12} style={{ color: COLORS.textFaint }} />
        {dataSelecionada.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" }).replace(".", "")}
        <input
          type="date"
          className="absolute opacity-0 w-0 h-0"
          value={formatarDataISO(dataSelecionada)}
          max={formatarDataISO(hoje)}
          onChange={(e) => {
            if (!e.target.value) return;
            const [ano, mes, dia] = e.target.value.split("-").map(Number);
            onMudarData(new Date(ano, mes - 1, dia));
          }}
        />
      </label>
      {!ehHoje && (
        <button
          onClick={() => onMudarData(new Date())}
          className="text-[10.5px] uppercase tracking-wider px-2 py-1 rounded-[2px]"
          style={{ background: `${COLORS.gold}1A`, border: `1px solid ${COLORS.gold}55`, color: COLORS.gold }}
        >
          Hoje
        </button>
      )}
    </div>
  );
}
