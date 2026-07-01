import { describe, expect, it } from 'vitest';
import {
  filterFrameCatalog,
  frameReadinessClass,
  frameReadinessLabel,
  type FrameCatalogItem,
} from './frameCatalog';

const sampleFrames: FrameCatalogItem[] = [
  {
    timestamp: '2026-06-28T13:26:38Z',
    cache_state: 'ready',
    cache_ready: true,
    decode_ready: true,
    decode_status: 'matched',
  },
  {
    timestamp: '2026-06-28T13:00:00Z',
    cache_state: 'cold_decodable',
    cache_ready: false,
    decode_ready: false,
    decode_status: null,
  },
  {
    timestamp: '2026-06-27T20:00:00Z',
    cache_state: 'missing_raw',
    cache_ready: false,
    decode_ready: false,
    decode_status: null,
  },
];

describe('filterFrameCatalog', () => {
  it('returns all frames when filter is empty', () => {
    expect(filterFrameCatalog(sampleFrames, '')).toHaveLength(3);
  });

  it('filters by timestamp substring', () => {
    const filtered = filterFrameCatalog(sampleFrames, '13:26');
    expect(filtered).toHaveLength(1);
    expect(filtered[0].timestamp).toBe('2026-06-28T13:26:38Z');
  });
});

describe('frameReadinessLabel', () => {
  it('shows cache and decode status', () => {
    expect(frameReadinessLabel(sampleFrames[0])).toBe('cached · decode ok');
    expect(frameReadinessLabel(sampleFrames[1])).toBe('cold · decode missing');
  });
});

describe('frameReadinessClass', () => {
  it('marks fully ready frames', () => {
    expect(frameReadinessClass(sampleFrames[0])).toBe('frame-catalog-row--ready');
  });

  it('marks missing raw frames', () => {
    expect(frameReadinessClass(sampleFrames[2])).toBe('frame-catalog-row--missing');
  });
});
