import { useEffect, useState, useCallback } from "react";

const INTERVALO_ATUALIZACAO_MS = 5 * 60 * 1000; // 5 minutos

/**
 * Hook genérico: busca `fetchFn(date)` e mantém atualizado. Refaz a
 * busca sempre que `date` muda (filtro de data) ou a cada 5 minutos.
 * Nunca cai para dado mockado — em erro, `data` permanece null.
 */
export function useApiResource(fetchFn, date) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [atualizadoEm, setAtualizadoEm] = useState(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      setError(null);
      const resultado = await fetchFn(date);
      setData(resultado);
      setAtualizadoEm(new Date());
    } catch (err) {
      setError(err.message || "Falha ao buscar dados da API");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- busca ao montar/trocar filtro de data é o padrão esperado aqui
    carregar();
    const intervalo = setInterval(carregar, INTERVALO_ATUALIZACAO_MS);
    return () => clearInterval(intervalo);
  }, [carregar]);

  return { data, loading, error, atualizadoEm, recarregar: carregar };
}
