import { useCallback, useEffect, useState } from 'react';
import { fetchFrameQuality, type FrameQualityReport } from '../api/client';

export function useFrameQuality(inspectTimestamp: string, enabled: boolean) {
  const [report, setReport] = useState<FrameQualityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);

  const refresh = useCallback(() => {
    setVersion((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!enabled || !inspectTimestamp) {
      setReport(null);
      setError('');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    fetchFrameQuality([inspectTimestamp])
      .then((payload) => {
        if (!cancelled) {
          setReport(payload);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setReport(null);
          setError(err instanceof Error ? err.message : 'Failed to load frame quality');
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
  }, [inspectTimestamp, enabled, version]);

  return { report, loading, error, refresh };
}
