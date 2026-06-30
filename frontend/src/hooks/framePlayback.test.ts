import { describe, expect, it } from 'vitest';
import {
  adjacentTimestamps,
  cacheStateLabel,
  overlayToFrameStatus,
  playbackStatusLabel,
} from '../hooks/framePlayback';
import type { DecodedOverlayInfo } from '../api/client';

const matchedOverlay: DecodedOverlayInfo = {
  available: true,
  artifact_available: true,
  overlay_visible: true,
  overlay_status: 'decoded_prototype',
  sync_status: 'matched',
  bounds: [-125, 24, -66, 50],
  georef_mode: 'prototype_bounds',
  geo_accurate: false,
  labels: [],
  refresh_commands: [],
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

describe('overlayToFrameStatus', () => {
  it('returns frame_ready for matched overlay', () => {
    expect(overlayToFrameStatus(matchedOverlay)).toBe('frame_ready');
  });

  it('returns frame_missing for no local candidate', () => {
    expect(
      overlayToFrameStatus({
        ...matchedOverlay,
        overlay_visible: false,
        sync_status: 'no_local_candidate',
      }),
    ).toBe('frame_missing');
  });
});

describe('adjacentTimestamps', () => {
  it('returns previous and next timestamps', () => {
    const times = ['a', 'b', 'c'];
    expect(adjacentTimestamps(times, 'b')).toEqual(['a', 'c']);
  });
});

describe('playbackStatusLabel', () => {
  it('labels decoding state', () => {
    expect(playbackStatusLabel('decoding')).toBe('decoding');
  });
});

describe('cacheStateLabel', () => {
  it('labels cache states for slider UI', () => {
    expect(cacheStateLabel('ready')).toBe('cached');
    expect(cacheStateLabel('cold_decodable')).toBe('cold');
    expect(cacheStateLabel('missing_raw')).toBe('no raw');
  });
});
