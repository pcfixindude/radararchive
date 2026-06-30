import { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchDecodedOverlay,
  prefetchDecodedFrames,
  type DecodedOverlayInfo,
} from '../api/client';
import {
  adjacentTimestamps,
  combinePlaybackStatus,
  overlayToFrameStatus,
  type PlaybackFrameStatus,
} from './framePlayback';

export function useFrameOverlay(
  times: string[],
  selectedTime: string,
  playing: boolean,
  enabled: boolean,
) {
  const [decodedOverlay, setDecodedOverlay] = useState<DecodedOverlayInfo | null>(null);
  const [frameStatus, setFrameStatus] = useState<PlaybackFrameStatus>('idle');
  const [refreshing, setRefreshing] = useState(false);
  const frameCacheRef = useRef(new Map<string, DecodedOverlayInfo>());
  const loadTokenRef = useRef(0);
  const prefetchTokenRef = useRef(0);

  const playbackStatus = combinePlaybackStatus(playing, frameStatus);

  const warmCache = useCallback((overlay: DecodedOverlayInfo | null, timestamp: string) => {
    if (overlay && timestamp) {
      frameCacheRef.current.set(timestamp, overlay);
    }
  }, []);

  const loadFrame = useCallback(
    async (timestamp: string, options: { refresh?: boolean } = {}) => {
      if (!timestamp || !enabled) {
        return null;
      }
      const token = ++loadTokenRef.current;
      if (!options.refresh) {
        const cached = frameCacheRef.current.get(timestamp);
        if (cached) {
          setDecodedOverlay(cached);
          setFrameStatus(overlayToFrameStatus(cached));
          return cached;
        }
      }

      setRefreshing(true);
      setFrameStatus('decoding');
      try {
        const overlay = await fetchDecodedOverlay(timestamp, { refresh: options.refresh });
        if (token !== loadTokenRef.current) {
          return overlay;
        }
        warmCache(overlay, timestamp);
        setDecodedOverlay(overlay);
        setFrameStatus(overlayToFrameStatus(overlay));
        return overlay;
      } finally {
        if (token === loadTokenRef.current) {
          setRefreshing(false);
        }
      }
    },
    [enabled, warmCache],
  );

  const prefetchAdjacent = useCallback(
    async (timestamp: string) => {
      if (!enabled || !timestamp || times.length === 0) {
        return;
      }
      const neighbors = adjacentTimestamps(times, timestamp);
      if (neighbors.length === 0) {
        return;
      }
      const token = ++prefetchTokenRef.current;
      try {
        await prefetchDecodedFrames(neighbors);
      } catch {
        // Prefetch is best-effort for playback responsiveness.
      }
      if (token !== prefetchTokenRef.current) {
        return;
      }
      for (const neighbor of neighbors) {
        if (frameCacheRef.current.has(neighbor)) {
          continue;
        }
        const overlay = await fetchDecodedOverlay(neighbor);
        warmCache(overlay, neighbor);
      }
    },
    [enabled, times, warmCache],
  );

  useEffect(() => {
    if (!enabled || !selectedTime) {
      return;
    }
    void loadFrame(selectedTime);
    void prefetchAdjacent(selectedTime);
  }, [enabled, selectedTime, loadFrame, prefetchAdjacent]);

  const refreshDecodedOverlay = useCallback(
    async (timestamp?: string) => {
      const target = timestamp ?? selectedTime;
      if (!target) {
        return;
      }
      await loadFrame(target, { refresh: true });
      await prefetchAdjacent(target);
    },
    [loadFrame, prefetchAdjacent, selectedTime],
  );

  return {
    decodedOverlay,
    frameStatus: playbackStatus,
    rawFrameStatus: frameStatus,
    refreshing,
    refreshDecodedOverlay,
    clearFrameCache: () => frameCacheRef.current.clear(),
  };
}
