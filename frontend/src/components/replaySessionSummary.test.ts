import { describe, expect, it } from 'vitest';
import type { DecodedOverlayInfo } from '../api/client';
import { buildReplaySessionSummary } from './replaySessionSummary';

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
  frame_quality: { status: 'ok', checks: [], diagnostic_only: true },
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

describe('buildReplaySessionSummary', () => {
  it('marks session ready when overlay and cache are warm', () => {
    const summary = buildReplaySessionSummary({
      loadState: 'ready',
      selectedTime: '2026-06-28T13:26:38Z',
      overlay: matchedOverlay,
      cacheStatus: {
        frames: [{ timestamp: '2026-06-28T13:26:38Z', cache_state: 'ready' }],
        frame_count: 8,
        warmed_count: 8,
        missing_count: 0,
        cold_count: 0,
        failed_count: 0,
        stub_count: 0,
        playback_ready: true,
        cache_warm_available: true,
        next_commands: [],
      },
      playbackFrameStatus: 'frame_ready',
      playing: false,
      frameCount: 8,
    });
    expect(summary.readiness).toBe('ready');
    expect(summary.hasDecodedOverlay).toBe(true);
    expect(summary.hasValidBounds).toBe(true);
    expect(summary.nextCommand).toBeNull();
  });

  it('suggests ingest when no frames', () => {
    const summary = buildReplaySessionSummary({
      loadState: 'ready',
      selectedTime: '',
      overlay: null,
      cacheStatus: null,
      playbackFrameStatus: 'idle',
      playing: false,
      frameCount: 0,
    });
    expect(summary.nextCommand).toContain('mrms-ingest-window');
  });

  it('suggests backend when API is down', () => {
    const summary = buildReplaySessionSummary({
      loadState: 'backend_down',
      selectedTime: '2026-06-28T13:26:38Z',
      overlay: null,
      cacheStatus: null,
      playbackFrameStatus: 'idle',
      playing: false,
      frameCount: 0,
    });
    expect(summary.readiness).toBe('backend_down');
    expect(summary.nextCommand).toBe('make backend');
  });

  it('suggests warm cache when cold', () => {
    const summary = buildReplaySessionSummary({
      loadState: 'ready',
      selectedTime: '2026-06-28T13:26:38Z',
      overlay: matchedOverlay,
      cacheStatus: {
        frames: [{ timestamp: '2026-06-28T13:26:38Z', cache_state: 'cold_decodable' }],
        frame_count: 8,
        warmed_count: 2,
        missing_count: 0,
        cold_count: 6,
        failed_count: 0,
        stub_count: 0,
        playback_ready: false,
        cache_warm_available: true,
        next_commands: ['make mrms-warm-frame-cache'],
      },
      playbackFrameStatus: 'frame_ready',
      playing: false,
      frameCount: 8,
    });
    expect(summary.nextCommand).toBe('make mrms-warm-frame-cache');
    expect(summary.hints.some((hint) => hint.includes('cold'))).toBe(true);
  });
});
