import { describe, expect, it } from 'vitest';
import {
  buildClipDownloadFilename,
  formatClipSummary,
  type PlaybackExportManifest,
} from './playbackExport';

const sampleManifest: PlaybackExportManifest = {
  clip_id: 'clip_20260628T130000Z_20260628T132638Z',
  export_kind: 'playback_clip_manifest',
  layer_id: 'mrms_reflectivity',
  range_start: '2026-06-28T13:00:00Z',
  range_end: '2026-06-28T13:26:38Z',
  range_order_adjusted: false,
  loop_suggested: true,
  frame_count: 3,
  cache_ready_count: 2,
  decode_ready_count: 1,
  missing_cache_count: 0,
  cold_count: 1,
  failed_count: 0,
  frames: [],
  exported_at: '2026-06-28T14:00:00Z',
  status: 'ready',
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

describe('formatClipSummary', () => {
  it('summarizes frame and readiness counts', () => {
    expect(formatClipSummary(sampleManifest)).toBe('3 frames · 2/3 cached · 1/3 decoded');
  });

  it('uses all-ready labels when every frame is ready', () => {
    const allReady = {
      ...sampleManifest,
      cache_ready_count: 3,
      decode_ready_count: 3,
    };
    expect(formatClipSummary(allReady)).toBe('3 frames · all cached · all decoded');
  });
});

describe('buildClipDownloadFilename', () => {
  it('builds a stable filename from range endpoints', () => {
    expect(buildClipDownloadFilename(sampleManifest)).toBe(
      'playback-clip_20260628T130000Z_20260628T132638Z.json',
    );
  });
});
