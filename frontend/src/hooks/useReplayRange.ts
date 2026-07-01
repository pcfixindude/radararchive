import { useCallback, useMemo, useState } from 'react';
import {
  applyRangeEndSelection,
  applyRangeStartSelection,
  formatRangeEndpoints,
  formatRangePosition,
  isTimeInRange,
  rangeSelectionNotice,
  resolveReplayRange,
  type ResolvedReplayRange,
} from './replayRange';

export function useReplayRange(times: string[], selectedTime: string) {
  const [rangeStart, setRangeStart] = useState<string | null>(null);
  const [rangeEnd, setRangeEnd] = useState<string | null>(null);
  const [loopRange, setLoopRange] = useState(false);
  const [operatorNotice, setOperatorNotice] = useState<string | null>(null);

  const resolvedRange = useMemo(
    () => resolveReplayRange(rangeStart, rangeEnd, times),
    [rangeStart, rangeEnd, times],
  );

  const hasCompleteRange = Boolean(resolvedRange);
  const loopActive = loopRange && hasCompleteRange;

  const rangeNotice = useMemo(() => {
    if (operatorNotice) {
      return operatorNotice;
    }
    return rangeSelectionNotice(rangeStart, rangeEnd, resolvedRange);
  }, [operatorNotice, rangeStart, rangeEnd, resolvedRange]);

  const setStartFromSelected = useCallback(() => {
    if (!selectedTime) {
      return;
    }
    const next = applyRangeStartSelection(rangeEnd, selectedTime, times);
    setRangeStart(next.start);
    setRangeEnd(next.end);
    setOperatorNotice(next.notice);
  }, [selectedTime, rangeEnd, times]);

  const setEndFromSelected = useCallback(() => {
    if (!selectedTime) {
      return;
    }
    const next = applyRangeEndSelection(rangeStart, selectedTime, times);
    setRangeStart(next.start);
    setRangeEnd(next.end);
    setOperatorNotice(next.notice);
  }, [selectedTime, rangeStart, times]);

  const clearRange = useCallback(() => {
    setRangeStart(null);
    setRangeEnd(null);
    setLoopRange(false);
    setOperatorNotice(null);
  }, []);

  const toggleLoopRange = useCallback(() => {
    if (!resolvedRange) {
      setOperatorNotice('Set a start and end frame before enabling loop.');
      return;
    }
    setLoopRange((current) => !current);
    setOperatorNotice(null);
  }, [resolvedRange]);

  const rangeLabel = resolvedRange
    ? formatRangeEndpoints(resolvedRange.start, resolvedRange.end)
    : rangeStart || rangeEnd
      ? `${rangeStart ?? '…'} → ${rangeEnd ?? '…'}`
      : null;

  const selectedInRange = resolvedRange ? isTimeInRange(selectedTime, resolvedRange, times) : null;
  const positionLabel = resolvedRange
    ? formatRangePosition(selectedTime, resolvedRange, times)
    : null;

  return {
    rangeStart,
    rangeEnd,
    resolvedRange,
    hasCompleteRange,
    loopRange,
    loopActive,
    rangeNotice,
    rangeLabel,
    selectedInRange,
    positionLabel,
    setStartFromSelected,
    setEndFromSelected,
    clearRange,
    toggleLoopRange,
    setLoopRange,
  };
}

export type ReplayRangeState = ReturnType<typeof useReplayRange>;
export type { ResolvedReplayRange };
