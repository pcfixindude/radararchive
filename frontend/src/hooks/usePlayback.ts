import { useCallback, useEffect, useRef, useState } from 'react';
import {
  advancePlaybackIndex,
  stepBackwardIndex,
  stepForwardIndex,
} from './loopPlayback';
import type { ResolvedReplayRange } from './replayRange';

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
  range: ResolvedReplayRange | null = null,
  loopRange = false,
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
      const currentIndex = indexRef.current;
      const result = advancePlaybackIndex(currentIndex, times.length, range, loopRange);
      onSelect(times[result.nextIndex] ?? selectedTime);
      if (result.pause) {
        setPlaying(false);
      }
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [playing, times, speed, onSelect, range, loopRange, selectedTime]);

  useEffect(() => {
    if (times.length === 0) {
      setPlaying(false);
    }
  }, [times.length]);

  const stepBackward = useCallback(() => {
    const index = Math.max(0, times.indexOf(selectedTime));
    const nextIndex = stepBackwardIndex(index, times.length, range, loopRange);
    onSelect(times[nextIndex] ?? selectedTime);
  }, [onSelect, selectedTime, times, range, loopRange]);

  const stepForward = useCallback(() => {
    const index = Math.max(0, times.indexOf(selectedTime));
    const nextIndex = stepForwardIndex(index, times.length, range, loopRange);
    onSelect(times[nextIndex] ?? selectedTime);
  }, [onSelect, selectedTime, times, range, loopRange]);

  const jumpToLatest = useCallback(() => {
    if (range) {
      onSelect(range.end);
      return;
    }
    onSelect(times[times.length - 1] ?? '');
  }, [onSelect, times, range]);

  const jumpToRangeStart = useCallback(() => {
    if (range) {
      onSelect(range.start);
      return;
    }
    onSelect(times[0] ?? '');
  }, [onSelect, times, range]);

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
    jumpToRangeStart,
    setPlaying,
  };
}
