import { useCallback, useEffect, useState } from 'react';
import { fetchLocalReplayReady, type LocalReplayReadyStatus } from '../api/client';

export function useLocalReplayReady(enabled: boolean) {
  const [status, setStatus] = useState<LocalReplayReadyStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    if (!enabled) {
      setStatus(null);
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const next = await fetchLocalReplayReady();
      setStatus(next);
    } catch (err) {
      setStatus(null);
      setError(err instanceof Error ? err.message : 'Failed to load local replay setup status');
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { status, loading, error, refresh };
}
