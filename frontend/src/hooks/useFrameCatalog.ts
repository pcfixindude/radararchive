import { useCallback, useEffect, useState } from 'react';
import { fetchFrameCatalog, type FrameCatalogStatus } from '../api/client';

export function useFrameCatalog(times: string[], enabled: boolean, limit = 50) {
  const [catalog, setCatalog] = useState<FrameCatalogStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);

  const refresh = useCallback(() => {
    setVersion((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setCatalog(null);
      setError('');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    fetchFrameCatalog(times, limit)
      .then((status) => {
        if (!cancelled) {
          setCatalog(status);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setCatalog(null);
          setError(err instanceof Error ? err.message : 'Failed to load frame catalog');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [times, enabled, limit, version]);

  return { catalog, loading, error, refresh };
}
