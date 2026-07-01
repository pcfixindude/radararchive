import { describe, expect, it } from 'vitest';
import type { DecodedOverlayInfo } from '../api/client';
import {
  hasValidOverlayBounds,
  overlayReadyForMap,
  selectedFrameSummary,
  suggestNextCommand,
} from './replayDisplay';

const matchedOverlay: DecodedOverlayInfo = {
  available: true,
  artifact_available: true,
  overlay_visible: true,
  overlay_status: 'decoded_prototype',
  sync_status: 'matched',
  bounds: [-100, 30, -90, 40],
  georef_mode: 'rasterio_wgs84_affine',
  geo_accurate: false,
  labels: [],
  refresh_commands: [],
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

describe('hasValidOverlayBounds', () => {
  it('accepts valid west/south/east/north', () => {
    expect(hasValidOverlayBounds([-100, 30, -90, 40])).toBe(true);
  });

  it('rejects invalid ordering', () => {
    expect(hasValidOverlayBounds([-90, 30, -100, 40])).toBe(false);
  });
});

describe('selectedFrameSummary', () => {
  it('describes ready matched frame', () => {
    expect(selectedFrameSummary(matchedOverlay, '2026-06-28T13:26:38Z', 'ready')).toContain('ready');
  });

  it('describes missing local file', () => {
    expect(
      selectedFrameSummary(
        { ...matchedOverlay, sync_status: 'no_local_candidate', overlay_visible: false },
        '2026-06-28T13:26:38Z',
      ),
    ).toContain('No local MRMS');
  });
});

describe('suggestNextCommand', () => {
  it('suggests ingest when no local candidate', () => {
    expect(
      suggestNextCommand(
        { ...matchedOverlay, sync_status: 'no_local_candidate', artifact_available: false },
        null,
      ),
    ).toContain('mrms-ingest-window');
  });

  it('suggests warm cache when cold', () => {
    expect(
      suggestNextCommand(matchedOverlay, {
        frames: [],
        frame_count: 8,
        warmed_count: 2,
        missing_count: 0,
        cold_count: 6,
        failed_count: 0,
        stub_count: 0,
        playback_ready: false,
        cache_warm_available: true,
        next_commands: ['make mrms-warm-frame-cache'],
      }),
    ).toBe('make mrms-warm-frame-cache');
  });
});

describe('overlayReadyForMap', () => {
  it('is true for matched overlay with bounds', () => {
    expect(overlayReadyForMap(matchedOverlay)).toBe(true);
  });

  it('is false when overlay hidden', () => {
    expect(overlayReadyForMap({ ...matchedOverlay, overlay_visible: false })).toBe(false);
  });
});
