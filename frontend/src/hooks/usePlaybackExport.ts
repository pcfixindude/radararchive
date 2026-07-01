import { useCallback, useState } from 'react';
import { fetchPlaybackExport, type PlaybackExportManifest } from '../api/client';

export function usePlaybackExport() {
  const [manifest, setManifest] = useState<PlaybackExportManifest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copyNotice, setCopyNotice] = useState('');

  const exportClip = useCallback(
    async ({
      rangeStart,
      rangeEnd,
      playbackTimes,
      loopActive,
    }: {
      rangeStart: string;
      rangeEnd: string;
      playbackTimes: string[];
      loopActive: boolean;
    }) => {
      setLoading(true);
      setError('');
      setCopyNotice('');
      try {
        const payload = await fetchPlaybackExport({
          rangeStart,
          rangeEnd,
          playbackTimes,
          loopActive,
        });
        setManifest(payload);
        return payload;
      } catch (err) {
        setManifest(null);
        setError(err instanceof Error ? err.message : 'Failed to export clip');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const clearExport = useCallback(() => {
    setManifest(null);
    setError('');
    setCopyNotice('');
  }, []);

  const markCopied = useCallback((message = 'Manifest copied to clipboard.') => {
    setCopyNotice(message);
  }, []);

  return {
    manifest,
    loading,
    error,
    copyNotice,
    exportClip,
    clearExport,
    markCopied,
  };
}
