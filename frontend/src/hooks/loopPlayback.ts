import type { ResolvedReplayRange } from './replayRange';

export type PlaybackRangeBounds = {
  startIndex: number;
  endIndex: number;
};

export function playbackBounds(
  timesLength: number,
  range: ResolvedReplayRange | null,
): PlaybackRangeBounds {
  if (range) {
    return { startIndex: range.startIndex, endIndex: range.endIndex };
  }
  return { startIndex: 0, endIndex: Math.max(0, timesLength - 1) };
}

export type AdvancePlaybackResult = {
  nextIndex: number;
  pause: boolean;
  wrapped: boolean;
};

export function advancePlaybackIndex(
  currentIndex: number,
  timesLength: number,
  range: ResolvedReplayRange | null,
  loopRange: boolean,
): AdvancePlaybackResult {
  const { startIndex, endIndex } = playbackBounds(timesLength, range);
  const nextIndex = currentIndex + 1;

  if (nextIndex > endIndex) {
    if (range && loopRange) {
      return { nextIndex: startIndex, pause: false, wrapped: true };
    }
    if (range) {
      return { nextIndex: endIndex, pause: true, wrapped: false };
    }
    if (timesLength === 0) {
      return { nextIndex: 0, pause: true, wrapped: false };
    }
    return { nextIndex: 0, pause: false, wrapped: true };
  }

  return { nextIndex, pause: false, wrapped: false };
}

export function stepForwardIndex(
  currentIndex: number,
  timesLength: number,
  range: ResolvedReplayRange | null,
  loopRange: boolean,
): number {
  const { startIndex, endIndex } = playbackBounds(timesLength, range);

  if (currentIndex < endIndex) {
    return currentIndex + 1;
  }
  if (range && loopRange && currentIndex === endIndex) {
    return startIndex;
  }
  if (!range && currentIndex < timesLength - 1) {
    return currentIndex + 1;
  }
  return currentIndex;
}

export function stepBackwardIndex(
  currentIndex: number,
  timesLength: number,
  range: ResolvedReplayRange | null,
  loopRange: boolean,
): number {
  const { startIndex, endIndex } = playbackBounds(timesLength, range);

  if (currentIndex > startIndex) {
    return currentIndex - 1;
  }
  if (range && loopRange && currentIndex === startIndex) {
    return endIndex;
  }
  if (!range && currentIndex > 0) {
    return currentIndex - 1;
  }
  return currentIndex;
}

export function playbackStatusWithRange(
  playing: boolean,
  loopActive: boolean,
  hasRange: boolean,
  inRange: boolean | null,
): string {
  if (playing && loopActive) {
    return 'Playing — looping range';
  }
  if (playing && hasRange) {
    return 'Playing — range (stops at end)';
  }
  if (playing) {
    return 'Playing';
  }
  if (hasRange && inRange === false) {
    return 'Paused — frame outside range';
  }
  if (loopActive) {
    return 'Paused — loop range on';
  }
  if (hasRange) {
    return 'Paused — range set';
  }
  return 'Paused';
}
