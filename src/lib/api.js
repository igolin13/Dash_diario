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
