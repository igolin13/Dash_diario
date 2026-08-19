import { Calendar } from "lucide-react";
import { COLORS } from "./colors";
import { formatarDataISO } from "../lib/api";

function ehMesmoDia(a, b) {
  return formatarDataISO(a) === formatarDataISO(b);
}

/**
 * Três caixinhas: Hoje / Ontem / Escolher qualquer data do ano.
 * Nenhuma trava — o backend aceita qualquer data com histórico no SQL.
 */
export function FiltroData({ dataSelecionada, onMudarData }) {
  const hoje = new Date();
  const ontem = new Date(hoje);
  ontem.setDate(hoje.getDate() - 1);

  const isHoje = ehMesmoDia(dataSelecionada, hoje);
  const isOntem = ehMesmoDia(dataSelecionada, ontem);

  function estiloBox(ativo) {
    return {
      background: ativo ? `${COLORS.gold}22` : COLORS.panelAlt,
      border: `1px solid ${ativo ? COLORS.gold : COLORS.border}`,
      color: ativo ? COLORS.goldBright : COLORS.textMuted,
    };
  }

  return (
    <div className="flex items-center gap-1.5">
      <button
        onClick={() => onMudarData(new Date())}
        className="text-[12.5px] uppercase tracking-wider font-medium px-3 py-1.5 rounded-[2px] transition-colors"
        style={estiloBox(isHoje)}
      >
        Dia atual
      </button>
      <button
        onClick={() => onMudarData(ontem)}
        className="text-[12.5px] uppercase tracking-wider font-medium px-3 py-1.5 rounded-[2px] transition-colors"
        style={estiloBox(isOntem)}
      >
        Dia anterior
      </button>
      <label
        className="flex items-center gap-1.5 text-[12.5px] px-2.5 py-1.5 rounded-[2px] cursor-pointer font-mono transition-colors"
        style={estiloBox(!isHoje && !isOntem)}
      >
        <Calendar size={13} />
        <input
          type="date"
          value={formatarDataISO(dataSelecionada)}
          max={formatarDataISO(hoje)}
          onChange={(e) => {
            if (!e.target.value) return;
            const [ano, mes, dia] = e.target.value.split("-").map(Number);
            onMudarData(new Date(ano, mes - 1, dia));
          }}
          className="bg-transparent outline-none cursor-pointer"
          style={{ colorScheme: "dark", color: "inherit" }}
        />
      </label>
    </div>
  );
}
