// Cliente da API do backend (FastAPI + SQL Server real).
// Nenhum dado aqui é inventado — tudo vem do backend.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function formatarDataISO(date) {
  // YYYY-MM-DD, formato que o backend espera (Query params data_inicio/data_fim)
  const ano = date.getFullYear();
  const mes = String(date.getMonth() + 1).padStart(2, "0");
  const dia = String(date.getDate()).padStart(2, "0");
  return `${ano}-${mes}-${dia}`;
}

async function getJSON(path, date) {
  const dia = formatarDataISO(date);
  const url = `${API_URL}${path}?data_inicio=${dia}&data_fim=${dia}`;
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`API respondeu ${resp.status} em ${path} (${dia})`);
  }
  return resp.json();
}

export function fetchKpis(date) {
  return getJSON("/api/kpis", date);
}

export function fetchProducaoPorLinha(date) {
  return getJSON("/api/producao-por-linha", date);
}

export function fetchCorretivaPorLinha(date) {
  return getJSON("/api/corretiva-por-linha", date);
}

/**
 * Estoque não aceita data — a base é viva (sem histórico por dia),
 * sempre reflete o momento atual. Por isso não usa getJSON (que exige
 * data_inicio/data_fim).
 */
export async function fetchEstoqueVencido() {
  const resp = await fetch(`${API_URL}/api/estoque-vencido`);
  if (!resp.ok) {
    throw new Error(`API respondeu ${resp.status} em /api/estoque-vencido`);
  }
  return resp.json();
}

/** OP's em aberto — também "vivo", sem filtro de data (usa GETDATE() no SQL). */
export async function fetchOpsAbertas() {
  const resp = await fetch(`${API_URL}/api/ops-abertas`);
  if (!resp.ok) {
    throw new Error(`API respondeu ${resp.status} em /api/ops-abertas`);
  }
  return resp.json();
}

/**
 * Qualidade — "RNC's em aberto" e "Fardos retidos" são sempre atuais,
 * mas "RNC's no mês" depende da data selecionada (mostra o mês dela).
 */
export async function fetchQualidade(date) {
  const dia = formatarDataISO(date);
  const resp = await fetch(`${API_URL}/api/qualidade?data=${dia}`);
  if (!resp.ok) {
    throw new Error(`API respondeu ${resp.status} em /api/qualidade`);
  }
  return resp.json();
}

/**
 * Histórico de programação (PCP) — consolidado a partir dos CSVs da
 * pasta de rede. Sem filtro de data (o backend lê tudo da pasta).
 */
export async function fetchHistoricoProgramacao() {
  const resp = await fetch(`${API_URL}/api/pcp/historico-programacao`);
  if (!resp.ok) {
    throw new Error(`API respondeu ${resp.status} em /api/pcp/historico-programacao`);
  }
  return resp.json();
}

/** Dispara o download do CSV consolidado direto no navegador. */
export function baixarHistoricoProgramacaoCsv() {
  window.open(`${API_URL}/api/pcp/historico-programacao/csv`, "_blank");
}

/**
 * Aderência real de PCP — só faz sentido pra dias já FECHADOS (ontem
 * pra trás). Bloqueia ANTES de bater na rede se a data selecionada for
 * hoje ou futuro, pra não gastar uma chamada à toa.
 */
export async function fetchAderenciaResumo(date) {
  const hoje = new Date();
  if (formatarDataISO(date) >= formatarDataISO(hoje)) {
    throw new Error("Aderência só está disponível para dias já fechados (ontem ou anteriores) — hoje ainda está em andamento.");
  }
  const dia = formatarDataISO(date);
  const resp = await fetch(`${API_URL}/api/pcp/aderencia/resumo?data=${dia}`);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `API respondeu ${resp.status} em /api/pcp/aderencia/resumo`);
  }
  return resp.json();
}