import { describe, expect, it } from 'vitest';
import {
  formatIngestWindowLabel,
  ingestWindowQueryFromState,
  INGEST_WINDOW_PRESETS,
} from './ingestWindow';

describe('ingestWindowQueryFromState', () => {
  it('builds query for last 3 hours preset', () => {
    const query = ingestWindowQueryFromState({
      preset: 'last_3h',
      limit: 8,
      warmCache: false,
      customStart: '',
      customEnd: '',
      replayStart: null,
      replayEnd: null,
    });
    expect(query.get('preset')).toBe('last_3h');
    expect(query.get('limit')).toBe('8');
    expect(query.get('warm_cache')).toBe('false');
  });

  it('includes custom start/end for custom preset', () => {
    const query = ingestWindowQueryFromState({
      preset: 'custom',
      limit: 12,
      warmCache: true,
      customStart: '2026-06-28T12:00:00Z',
      customEnd: '2026-06-28T14:00:00Z',
      replayStart: null,
      replayEnd: null,
    });
    expect(query.get('start')).toBe('2026-06-28T12:00:00Z');
    expect(query.get('end')).toBe('2026-06-28T14:00:00Z');
    expect(query.get('warm_cache')).toBe('true');
  });

  it('maps replay range preset', () => {
    const query = ingestWindowQueryFromState({
      preset: 'replay_range',
      limit: 8,
      warmCache: false,
      customStart: '',
      customEnd: '',
      replayStart: '2026-06-28T13:00:00Z',
      replayEnd: '2026-06-28T13:20:00Z',
    });
    expect(query.get('replay_start')).toBe('2026-06-28T13:00:00Z');
    expect(query.get('replay_end')).toBe('2026-06-28T13:20:00Z');
  });
});

describe('formatIngestWindowLabel', () => {
  it('labels known presets', () => {
    expect(formatIngestWindowLabel('last_1h')).toBe(INGEST_WINDOW_PRESETS.last_1h);
  });
});
