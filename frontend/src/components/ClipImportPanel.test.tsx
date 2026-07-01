import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ClipImportPanel from './ClipImportPanel';
import { CLIP_EXPORT_KIND, type ClipImportReport } from './clipImport';
import type { ClipImportHookState } from '../hooks/useClipImport';
import type { PlaybackExportManifest } from './playbackExport';

const sampleManifest: PlaybackExportManifest = {
  clip_id: 'clip_test',
  export_kind: CLIP_EXPORT_KIND,
  layer_id: 'mrms_reflectivity',
  range_start: '2026-06-28T13:00:00Z',
  range_end: '2026-06-28T13:26:38Z',
  range_order_adjusted: false,
  loop_suggested: true,
  frame_count: 2,
  cache_ready_count: 2,
  decode_ready_count: 2,
  missing_cache_count: 0,
  cold_count: 0,
  failed_count: 0,
  frames: [
    {
      timestamp: '2026-06-28T13:00:00Z',
      index: 0,
      cache_state: 'ready',
      cache_ready: true,
      decode_ready: true,
      preview_paths: [],
      preview_path_count: 0,
    },
    {
      timestamp: '2026-06-28T13:26:38Z',
      index: 1,
      cache_state: 'ready',
      cache_ready: true,
      decode_ready: true,
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
  import_status: 'ready',
  errors: [],
  warnings: [],
  manifest: sampleManifest,
  readiness_summary: {
    frame_count: 2,
    cache_ready_count: 2,
    decode_ready_count: 2,
    missing_count: 0,
    cold_count: 0,
    failed_count: 0,
    stub_count: 0,
    partial_count: 0,
    ready_count: 2,
    problem_count: 0,
    truncated: false,
  },
  problem_frames: [],
  suggested_commands: [],
  remediation_plan: {
    valid: true,
    plan_status: 'empty',
    clip_id: 'clip_test',
    problem_groups: [],
    group_summary: {
      total_problem_count: 0,
      assessed_count: 0,
      cold_count: 0,
      missing_count: 0,
      failed_count: 0,
      stub_count: 0,
      partial_count: 0,
      invalid_count: 0,
    },
    commands: [],
    command_block: '',
    operator_note: 'No remediation needed.',
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

function buildClipImportState(report: ClipImportReport | null): ClipImportHookState {
  return {
    rawInput: report ? JSON.stringify(report.manifest) : '',
    report,
    loading: false,
    error: '',
    applyNotice: '',
    setRawInput: () => undefined,
    validateImport: async () => report,
    loadFromFile: async () => undefined,
    clearImport: () => undefined,
    buildApply: () => null,
    markApplied: () => undefined,
  };
}

describe('ClipImportPanel apply preview', () => {
  it('shows frame list restore preview when manifest includes frames', () => {
    render(
      <ClipImportPanel
        clipImport={buildClipImportState(sampleReport)}
        onApply={() => undefined}
      />,
    );
    expect(screen.getByText('Will restore 2 frames from clip sequence')).toBeTruthy();
  });

  it('shows range-only preview when manifest has no frame list', () => {
    const reportWithoutFrames: ClipImportReport = {
      ...sampleReport,
      manifest: { ...sampleManifest, frames: [], frame_count: 0 },
    };
    render(
      <ClipImportPanel
        clipImport={buildClipImportState(reportWithoutFrames)}
        onApply={() => undefined}
      />,
    );
    expect(
      screen.getByText('Will restore range endpoints only — no frame list in manifest'),
    ).toBeTruthy();
  });
});
