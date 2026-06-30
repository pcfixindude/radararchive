import { useCallback, useEffect, useState } from 'react';
import { fetchPlaybackCacheStatus, type PlaybackCacheStatus } from '../api/client';

export function usePlaybackCacheStatus(times: string[], enabled: boolean) {
  const [cacheStatus, setCacheStatus] = useState<PlaybackCacheStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [version, setVersion] = useState(0);

  const refetch = useCallback(() => {
    setVersion((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!enabled || times.length === 0) {
      setCacheStatus(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchPlaybackCacheStatus(times)
      .then((status) => {
        if (!cancelled) {
          setCacheStatus(status);
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
  }, [times, enabled, version]);

  return { cacheStatus, cacheLoading: loading, refetchCacheStatus: refetch };
}
