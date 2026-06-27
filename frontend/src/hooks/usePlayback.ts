import { useCallback, useEffect, useRef, useState } from 'react';

export const PLAYBACK_SPEEDS = [
  { label: '0.5x', value: 0.5 },
  { label: '1x', value: 1 },
  { label: '2x', value: 2 },
  { label: '4x', value: 4 },
] as const;

const BASE_INTERVAL_MS = 1000;

export function usePlayback(
  times: string[],
  selectedTime: string,
  onSelect: (time: string) => void,
) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = Math.max(0, times.indexOf(selectedTime));
  }, [selectedTime, times]);

  useEffect(() => {
    if (!playing || times.length === 0) {
      return undefined;
    }

    const intervalMs = BASE_INTERVAL_MS / speed;
    const timer = window.setInterval(() => {
      const nextIndex = indexRef.current + 1;
      if (nextIndex >= times.length) {
        onSelect(times[0]);
      } else {
        onSelect(times[nextIndex]);
      }
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [playing, times, speed, onSelect]);

  useEffect(() => {
    if (times.length === 0) {
      setPlaying(false);
    }
  }, [times.length]);

  const stepBackward = useCallback(() => {
    const index = Math.max(0, times.indexOf(selectedTime));
    onSelect(times[Math.max(0, index - 1)] ?? selectedTime);
  }, [onSelect, selectedTime, times]);

  const stepForward = useCallback(() => {
    const index = times.indexOf(selectedTime);
    onSelect(times[Math.min(times.length - 1, index + 1)] ?? selectedTime);
  }, [onSelect, selectedTime, times]);

  const jumpToLatest = useCallback(() => {
    onSelect(times[times.length - 1] ?? '');
  }, [onSelect, times]);

  const togglePlay = useCallback(() => {
    setPlaying((current) => !current);
  }, []);

  return {
    playing,
    speed,
    setSpeed,
    togglePlay,
    stepBackward,
    stepForward,
    jumpToLatest,
    setPlaying,
  };
}
