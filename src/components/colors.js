export const COLORS = {
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

/**
 * Cor baseada na meta real do indicador (vinda da API) — vermelho ou
 * verde, sem faixa intermediária inventada.
 *
 * `invertido`: use true quando MENOR é melhor (ex: Corretiva, onde a
 * meta é um teto — "no máximo 6%"). Para OEE/Performance/Disponibilidade,
 * a meta é um piso — "no mínimo X%" — então invertido fica false.
 */
export function corPelaMeta(valor, meta, invertido = false) {
  if (valor == null || meta == null) return COLORS.textFaint;
  const atingiu = invertido ? valor <= meta : valor >= meta;
  return atingiu ? COLORS.green : COLORS.red;
}
