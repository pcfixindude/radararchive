import { describe, expect, it } from 'vitest';
import {
  advancePlaybackIndex,
  playbackStatusWithRange,
  stepBackwardIndex,
  stepForwardIndex,
} from './loopPlayback';
import { resolveReplayRange } from './replayRange';

const times = ['a', 'b', 'c', 'd', 'e'];

describe('advancePlaybackIndex', () => {
  it('wraps full timeline when no range is set', () => {
    const result = advancePlaybackIndex(4, times.length, null, false);
    expect(result).toEqual({ nextIndex: 0, pause: false, wrapped: true });
  });

  it('loops inside range when loop range is on', () => {
    const range = resolveReplayRange('b', 'd', times)!;
    const result = advancePlaybackIndex(3, times.length, range, true);
    expect(result).toEqual({ nextIndex: 1, pause: false, wrapped: true });
  });

  it('pauses at range end when loop is off', () => {
    const range = resolveReplayRange('b', 'd', times)!;
    const result = advancePlaybackIndex(3, times.length, range, false);
    expect(result).toEqual({ nextIndex: 3, pause: true, wrapped: false });
  });
});

describe('stepForwardIndex', () => {
  it('wraps at range end when loop is on', () => {
    const range = resolveReplayRange('b', 'd', times)!;
    expect(stepForwardIndex(3, times.length, range, true)).toBe(1);
  });

  it('stays at range end when loop is off', () => {
    const range = resolveReplayRange('b', 'd', times)!;
    expect(stepForwardIndex(3, times.length, range, false)).toBe(3);
  });
});

describe('stepBackwardIndex', () => {
  it('wraps at range start when loop is on', () => {
    const range = resolveReplayRange('b', 'd', times)!;
    expect(stepBackwardIndex(1, times.length, range, true)).toBe(3);
  });
});

describe('playbackStatusWithRange', () => {
  it('describes looping playback', () => {
    expect(playbackStatusWithRange(true, true, true, true)).toBe('Playing — looping range');
  });

  it('warns when paused outside range', () => {
    expect(playbackStatusWithRange(false, false, true, false)).toBe('Paused — frame outside range');
  });
});
