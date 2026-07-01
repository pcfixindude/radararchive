import { describe, expect, it } from 'vitest';
import {
  applyRangeEndSelection,
  applyRangeStartSelection,
  formatRangePosition,
  isTimeInRange,
  resolveReplayRange,
} from './replayRange';

const times = ['t1', 't2', 't3', 't4', 't5'];

describe('resolveReplayRange', () => {
  it('normalizes out-of-order start and end', () => {
    const range = resolveReplayRange('t4', 't2', times);
    expect(range).toEqual({
      start: 't2',
      end: 't4',
      startIndex: 1,
      endIndex: 3,
      orderAdjusted: true,
    });
  });

  it('returns null when start or end missing', () => {
    expect(resolveReplayRange('t1', null, times)).toBeNull();
    expect(resolveReplayRange(null, 't3', times)).toBeNull();
  });
});

describe('applyRangeStartSelection', () => {
  it('keeps order when selected start is before existing end', () => {
    const result = applyRangeStartSelection('t4', 't2', times);
    expect(result).toEqual({
      start: 't2',
      end: 't4',
      notice: null,
    });
  });

  it('adjusts order when new start is after end', () => {
    const result = applyRangeStartSelection('t2', 't4', times);
    expect(result.start).toBe('t2');
    expect(result.end).toBe('t4');
    expect(result.notice).toContain('adjusted');
  });
});

describe('applyRangeEndSelection', () => {
  it('adjusts order when new end is before start', () => {
    const result = applyRangeEndSelection('t4', 't2', times);
    expect(result.start).toBe('t2');
    expect(result.end).toBe('t4');
    expect(result.notice).toContain('adjusted');
  });
});

describe('isTimeInRange', () => {
  it('detects frames inside and outside range', () => {
    const range = resolveReplayRange('t2', 't4', times)!;
    expect(isTimeInRange('t3', range, times)).toBe(true);
    expect(isTimeInRange('t1', range, times)).toBe(false);
    expect(isTimeInRange('t5', range, times)).toBe(false);
  });
});

describe('formatRangePosition', () => {
  it('labels position inside range', () => {
    const range = resolveReplayRange('t2', 't4', times)!;
    expect(formatRangePosition('t3', range, times)).toBe('frame 2 of 3 in range');
  });

  it('labels outside range', () => {
    const range = resolveReplayRange('t2', 't4', times)!;
    expect(formatRangePosition('t1', range, times)).toContain('outside range');
  });
});
