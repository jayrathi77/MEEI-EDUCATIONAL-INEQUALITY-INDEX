import { useState, useEffect, useCallback } from 'react';
import type { AxiosError } from 'axios';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (e: unknown) {
      // Extract meaningful error message from Axios or standard errors
      let msg = 'API error';
      if (e && typeof e === 'object' && 'isAxiosError' in e) {
        const axErr = e as AxiosError<{ detail?: string }>;
        const status = axErr.response?.status;
        const detail = (axErr.response?.data as any)?.detail;
        if (detail) {
          let detailStr = '';
          if (typeof detail === 'string') {
            detailStr = detail;
          } else if (Array.isArray(detail)) {
            detailStr = detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
          } else {
            detailStr = JSON.stringify(detail);
          }
          msg = `${status ? status + ': ' : ''}${detailStr}`;
        } else if (status) {
          msg = `Request failed (HTTP ${status})`;
        } else if (axErr.message) {
          msg = axErr.message;
        }
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refetch: load };
}

