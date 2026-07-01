import { describe, expect, it } from 'vitest';
import {
  buildApplyNotice,
  buildApplyPayload,
  CLIP_EXPORT_KIND,
  extractApplyFrameTimestamps,
  formatApplyPreview,
  formatImportSummary,
  importStatusLabel,
  MAX_CLIP_FRAMES,
  parseClipManifestJson,
  problemFrameLabel,
  validateClipManifestShape,
  type ClipImportReport,
} from './clipImport';
import type { PlaybackExportManifest } from './playbackExport';

const sampleManifest: PlaybackExportManifest = {
  clip_id: 'clip_20260628T130000Z_20260628T132638Z',
  export_kind: CLIP_EXPORT_KIND,
  layer_id: 'mrms_reflectivity',
  range_start: '2026-06-28T13:00:00Z',
  range_end: '2026-06-28T13:26:38Z',
  range_order_adjusted: false,
  loop_suggested: true,
  frame_count: 2,
  cache_ready_count: 1,
  decode_ready_count: 0,
  missing_cache_count: 0,
  cold_count: 1,
  failed_count: 0,
  frames: [
    {
      timestamp: '2026-06-28T13:00:00Z',
      index: 0,
      cache_state: 'ready',
      cache_ready: true,
      decode_ready: false,
      preview_paths: [],
      preview_path_count: 0,
    },
    {
      timestamp: '2026-06-28T13:26:38Z',
      index: 1,
      cache_state: 'cold_no_manifest',
      cache_ready: false,
      decode_ready: false,
      preview_paths: [],
      preview_path_count: 0,
    },
  ],
  exported_at: '2026-06-28T14:00:00Z',
  status: 'ready',
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

const sampleReport: ClipImportReport = {
  valid: true,
  import_status: 'partial',
  errors: [],
  warnings: ['Readiness counts are refreshed against current local cache/decode state.'],
  manifest: sampleManifest,
  readiness_summary: {
    frame_count: 2,
    cache_ready_count: 1,
    decode_ready_count: 0,
    missing_count: 0,
    cold_count: 1,
    failed_count: 0,
    stub_count: 0,
    partial_count: 1,
    ready_count: 0,
    problem_count: 1,
    truncated: false,
  },
  problem_frames: [
    {
      timestamp: '2026-06-28T13:26:38Z',
      readiness_summary: 'cold',
      cache_state: 'cold_no_manifest',
      decode_ready: false,
      sync_message: 'Local raw present but cache not warmed.',
    },
  ],
  suggested_commands: ['make mrms-warm-frame-cache ARGS="--timestamp 2026-06-28T13:26:38Z"'],
  remediation_plan: {
    valid: true,
    plan_status: 'ready',
    clip_id: 'clip_20260628T130000Z_20260628T132638Z',
    problem_groups: [
      {
        readiness_type: 'cold',
        label: 'Cold cache',
        count: 1,
        assessed_count: 1,
        truncated: false,
        timestamps: ['2026-06-28T13:26:38Z'],
      },
    ],
    group_summary: {
      total_problem_count: 1,
      assessed_count: 1,
      cold_count: 1,
      missing_count: 0,
      failed_count: 0,
      stub_count: 0,
      partial_count: 0,
      invalid_count: 0,
    },
    commands: [
      {
        step: 1,
        category: 'warm',
        label: 'Warm cold frame cache for clip',
        command:
          'make mrms-warm-frame-cache ARGS="--start 2026-06-28T13:26:38Z --end 2026-06-28T13:26:38Z --limit 8"',
      },
    ],
    command_block: '# Clip remediation plan\nmake mrms-warm-frame-cache',
    operator_note: 'Copy commands manually.',
    bounded_frame_limit: 8,
    truncated: false,
    verified_mrms: false,
    local_dev_only: true,
    prototype: true,
    status_only: true,
    does_not_run_ingest: true,
    does_not_run_decode: true,
    does_not_run_real_downloads: true,
    commands_not_auto_run: true,
  },
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  status_only: true,
  does_not_run_ingest: true,
  does_not_run_decode: true,
};

describe('parseClipManifestJson', () => {
  it('parses valid JSON', () => {
    const result = parseClipManifestJson(JSON.stringify(sampleManifest));
    expect(result.error).toBeNull();
    expect(result.manifest).toEqual(sampleManifest);
  });

  it('rejects empty input', () => {
    const result = parseClipManifestJson('   ');
    expect(result.manifest).toBeNull();
    expect(result.error).toContain('Paste clip JSON');
  });

  it('rejects invalid JSON', () => {
    const result = parseClipManifestJson('{not json');
    expect(result.manifest).toBeNull();
    expect(result.error).toContain('Invalid JSON');
  });
});

describe('validateClipManifestShape', () => {
  it('accepts exported clip manifest', () => {
    expect(validateClipManifestShape(sampleManifest)).toBeNull();
  });

  it('rejects wrong export_kind', () => {
    expect(validateClipManifestShape({ ...sampleManifest, export_kind: 'other' })).toContain(
      'export_kind',
    );
  });

  it('rejects verified_mrms claim', () => {
    expect(validateClipManifestShape({ ...sampleManifest, verified_mrms: true })).toContain(
      'verified_mrms',
    );
  });
});

describe('formatImportSummary', () => {
  it('summarizes readiness counts', () => {
    expect(formatImportSummary(sampleReport)).toBe(
      '2 frames · 1/2 cached · 0/2 decoded · 1 need attention',
    );
  });
});

describe('extractApplyFrameTimestamps', () => {
  it('returns ordered unique timestamps from manifest frames', () => {
    const result = extractApplyFrameTimestamps(sampleManifest);
    expect(result.frameTimestamps).toEqual([
      '2026-06-28T13:00:00Z',
      '2026-06-28T13:26:38Z',
    ]);
    expect(result.frameListTruncated).toBe(false);
  });

  it('bounds frame list to export maximum', () => {
    const frames = Array.from({ length: MAX_CLIP_FRAMES + 5 }, (_, index) => ({
      timestamp: `2026-06-28T${String(Math.floor(index / 60)).padStart(2, '0')}:${String(index % 60).padStart(2, '0')}:00Z`,
      index,
      cache_state: 'ready',
      cache_ready: true,
      decode_ready: false,
      preview_paths: [],
      preview_path_count: 0,
    }));
    const result = extractApplyFrameTimestamps({ ...sampleManifest, frames });
    expect(result.frameTimestamps).toHaveLength(MAX_CLIP_FRAMES);
    expect(result.frameListTruncated).toBe(true);
  });
});

describe('buildApplyPayload', () => {
  it('returns range, loop, and frame list from valid report', () => {
    expect(buildApplyPayload(sampleReport)).toEqual({
      rangeStart: '2026-06-28T13:00:00Z',
      rangeEnd: '2026-06-28T13:26:38Z',
      loopSuggested: true,
      frameTimestamps: ['2026-06-28T13:00:00Z', '2026-06-28T13:26:38Z'],
      applyMode: 'frame_list',
      frameListTruncated: false,
    });
  });

  it('falls back to range-only when manifest has no frames', () => {
    const reportWithoutFrames: ClipImportReport = {
      ...sampleReport,
      manifest: { ...sampleManifest, frames: [], frame_count: 0 },
    };
    expect(buildApplyPayload(reportWithoutFrames)).toEqual({
      rangeStart: '2026-06-28T13:00:00Z',
      rangeEnd: '2026-06-28T13:26:38Z',
      loopSuggested: true,
      frameTimestamps: [],
      applyMode: 'range_only',
      frameListTruncated: false,
    });
  });

  it('returns null for invalid report', () => {
    expect(buildApplyPayload({ ...sampleReport, valid: false, manifest: null })).toBeNull();
  });
});

describe('formatApplyPreview', () => {
  it('shows frame count when manifest includes frame list', () => {
    const payload = buildApplyPayload(sampleReport);
    expect(payload).not.toBeNull();
    expect(formatApplyPreview(payload!)).toBe('Will restore 2 frames from clip sequence');
  });

  it('shows range-only fallback when no frame list', () => {
    const payload = buildApplyPayload({
      ...sampleReport,
      manifest: { ...sampleManifest, frames: [], frame_count: 0 },
    });
    expect(payload).not.toBeNull();
    expect(formatApplyPreview(payload!)).toBe(
      'Will restore range endpoints only — no frame list in manifest',
    );
  });
});

describe('buildApplyNotice', () => {
  it('mentions frame sequence when frame list is applied', () => {
    const payload = buildApplyPayload(sampleReport);
    expect(payload).not.toBeNull();
    expect(buildApplyNotice(payload!)).toBe(
      'Clip range and loop suggestion and 2-frame sequence applied to replay.',
    );
  });
});

describe('importStatusLabel', () => {
  it('maps import status codes', () => {
    expect(importStatusLabel('ready')).toBe('All frames ready');
    expect(importStatusLabel('partial')).toBe('Some frames need attention');
    expect(importStatusLabel('invalid')).toBe('Invalid manifest');
  });
});

describe('problemFrameLabel', () => {
  it('formats problem frame summary', () => {
    expect(problemFrameLabel(sampleReport.problem_frames[0])).toBe(
      'cold · cold_no_manifest',
    );
  });
});
