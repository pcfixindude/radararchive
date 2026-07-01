export type ResolvedReplayRange = {
  start: string;
  end: string;
  startIndex: number;
  endIndex: number;
  orderAdjusted: boolean;
};

export function resolveReplayRange(
  rangeStart: string | null,
  rangeEnd: string | null,
  times: string[],
): ResolvedReplayRange | null {
  if (!rangeStart || !rangeEnd || times.length === 0) {
    return null;
  }

  let startIndex = times.indexOf(rangeStart);
  let endIndex = times.indexOf(rangeEnd);
  if (startIndex === -1 || endIndex === -1) {
    return null;
  }

  let orderAdjusted = false;
  if (startIndex > endIndex) {
    [startIndex, endIndex] = [endIndex, startIndex];
    orderAdjusted = true;
  }

  return {
    start: times[startIndex],
    end: times[endIndex],
    startIndex,
    endIndex,
    orderAdjusted,
  };
}

export function isTimeInRange(time: string, range: ResolvedReplayRange, times: string[]): boolean {
  const index = times.indexOf(time);
  if (index === -1) {
    return false;
  }
  return index >= range.startIndex && index <= range.endIndex;
}

export function formatRangeEndpoints(start: string, end: string): string {
  return `${start} → ${end}`;
}

export function formatRangePosition(
  selectedTime: string,
  range: ResolvedReplayRange,
  times: string[],
): string {
  const index = times.indexOf(selectedTime);
  const rangeLength = range.endIndex - range.startIndex + 1;
  if (index === -1) {
    return 'unknown frame';
  }
  if (index < range.startIndex || index > range.endIndex) {
    return `outside range (${rangeLength} frames in segment)`;
  }
  const position = index - range.startIndex + 1;
  return `frame ${position} of ${rangeLength} in range`;
}

export function rangeSelectionNotice(
  rangeStart: string | null,
  rangeEnd: string | null,
  resolved: ResolvedReplayRange | null,
): string | null {
  if (rangeStart && !rangeEnd) {
    return 'Set an end frame to complete the range.';
  }
  if (!rangeStart && rangeEnd) {
    return 'Set a start frame to complete the range.';
  }
  if (resolved?.orderAdjusted) {
    return 'Range order adjusted — start is now before end.';
  }
  return null;
}

export function applyRangeEndSelection(
  rangeStart: string | null,
  selectedTime: string,
  times: string[],
): { start: string | null; end: string | null; notice: string | null } {
  if (!selectedTime) {
    return { start: rangeStart, end: null, notice: null };
  }
  if (rangeStart) {
    const startIdx = times.indexOf(rangeStart);
    const selectedIdx = times.indexOf(selectedTime);
    if (startIdx !== -1 && selectedIdx !== -1 && selectedIdx < startIdx) {
      return {
        start: selectedTime,
        end: rangeStart,
        notice: 'Range order adjusted — start is now before end.',
      };
    }
  }
  return { start: rangeStart, end: selectedTime, notice: null };
}

export function applyRangeStartSelection(
  rangeEnd: string | null,
  selectedTime: string,
  times: string[],
): { start: string | null; end: string | null; notice: string | null } {
  if (!selectedTime) {
    return { start: null, end: rangeEnd, notice: null };
  }
  if (rangeEnd) {
    const endIdx = times.indexOf(rangeEnd);
    const selectedIdx = times.indexOf(selectedTime);
    if (endIdx !== -1 && selectedIdx !== -1 && selectedIdx > endIdx) {
      return {
        start: rangeEnd,
        end: selectedTime,
        notice: 'Range order adjusted — start is now before end.',
      };
    }
  }
  return { start: selectedTime, end: rangeEnd, notice: null };
}
