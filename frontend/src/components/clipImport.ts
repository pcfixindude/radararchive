import type { PlaybackExportManifest } from './playbackExport';

import type { ClipRemediationPlan } from './clipRemediation';

export const CLIP_EXPORT_KIND = 'playback_clip_manifest';

export type ClipImportReadinessSummary = {
  frame_count: number;
  cache_ready_count: number;
  decode_ready_count: number;
  missing_count: number;
  cold_count: number;
  failed_count: number;
  stub_count: number;
  partial_count: number;
  ready_count: number;
  problem_count: number;
  truncated: boolean;
};

export type ClipImportProblemFrame = {
  timestamp: string;
  readiness_summary: string;
  cache_state: string;
  decode_ready: boolean;
  sync_message?: string | null;
};

export type ClipImportReport = {
  valid: boolean;
  import_status: string;
  errors: string[];
  warnings: string[];
  manifest: PlaybackExportManifest | null;
  readiness_summary: ClipImportReadinessSummary;
  problem_frames: ClipImportProblemFrame[];
  suggested_commands: string[];
  remediation_plan: ClipRemediationPlan;
  assessed_at?: string;
  verified_mrms: boolean;
  local_dev_only: boolean;
  prototype: boolean;
  status_only: boolean;
  does_not_run_ingest: boolean;
  does_not_run_decode: boolean;
};

export type ClipImportState = {
  rawInput: string;
  report: ClipImportReport | null;
  loading: boolean;
  error: string;
  applyNotice: string;
  setRawInput: (value: string) => void;
  validateImport: () => Promise<ClipImportReport | null>;
  loadFromFile: (file: File) => Promise<void>;
  clearImport: () => void;
  buildApply: () => ClipImportApplyPayload | null;
  markApplied: (message?: string) => void;
};

/** Same bound as playback export (`MAX_CLIP_FRAMES` in backend). */
export const MAX_CLIP_FRAMES = 200;

export type ClipImportApplyMode = 'frame_list' | 'range_only';

export type ClipImportApplyPayload = {
  rangeStart: string;
  rangeEnd: string;
  loopSuggested: boolean;
  frameTimestamps: string[];
  applyMode: ClipImportApplyMode;
  frameListTruncated: boolean;
};

export function parseClipManifestJson(raw: string): { manifest: unknown; error: string | null } {
  const trimmed = raw.trim();
  if (!trimmed) {
    return { manifest: null, error: 'Paste clip JSON or choose a file from Export clip.' };
  }
  try {
    return { manifest: JSON.parse(trimmed) as unknown, error: null };
  } catch {
    return { manifest: null, error: 'Invalid JSON — check the pasted or uploaded clip manifest.' };
  }
}

export function validateClipManifestShape(manifest: unknown): string | null {
  if (!manifest || typeof manifest !== 'object') {
    return 'Manifest must be a JSON object.';
  }
  const record = manifest as Record<string, unknown>;
  if (record.export_kind !== CLIP_EXPORT_KIND) {
    return `export_kind must be "${CLIP_EXPORT_KIND}".`;
  }
  if (record.verified_mrms === true) {
    return 'Manifest claims verified_mrms=true — rejected for local prototype import.';
  }
  if (!record.range_start || !record.range_end) {
    return 'range_start and range_end are required.';
  }
  return null;
}

export function formatImportSummary(report: ClipImportReport): string {
  const summary = report.readiness_summary;
  const cacheLabel =
    summary.cache_ready_count === summary.frame_count
      ? 'all cached'
      : `${summary.cache_ready_count}/${summary.frame_count} cached`;
  const decodeLabel =
    summary.decode_ready_count === summary.frame_count
      ? 'all decoded'
      : `${summary.decode_ready_count}/${summary.frame_count} decoded`;
  return `${summary.frame_count} frames · ${cacheLabel} · ${decodeLabel} · ${summary.problem_count} need attention`;
}

export function extractApplyFrameTimestamps(manifest: PlaybackExportManifest): {
  frameTimestamps: string[];
  frameListTruncated: boolean;
} {
  const seen = new Set<string>();
  const frameTimestamps: string[] = [];
  for (const frame of manifest.frames) {
    const ts = frame.timestamp?.trim();
    if (!ts || seen.has(ts)) {
      continue;
    }
    seen.add(ts);
    frameTimestamps.push(ts);
  }

  const frameListTruncated = frameTimestamps.length > MAX_CLIP_FRAMES;
  return {
    frameTimestamps: frameListTruncated
      ? frameTimestamps.slice(0, MAX_CLIP_FRAMES)
      : frameTimestamps,
    frameListTruncated,
  };
}

export function buildApplyPayload(report: ClipImportReport): ClipImportApplyPayload | null {
  if (!report.valid || !report.manifest) {
    return null;
  }
  const { frameTimestamps, frameListTruncated } = extractApplyFrameTimestamps(report.manifest);
  return {
    rangeStart: report.manifest.range_start,
    rangeEnd: report.manifest.range_end,
    loopSuggested: report.manifest.loop_suggested,
    frameTimestamps,
    applyMode: frameTimestamps.length > 0 ? 'frame_list' : 'range_only',
    frameListTruncated,
  };
}

export function formatApplyPreview(payload: ClipImportApplyPayload): string {
  if (payload.applyMode === 'frame_list') {
    const truncatedNote = payload.frameListTruncated ? ' (bounded to export limit)' : '';
    return `Will restore ${payload.frameTimestamps.length} frames from clip sequence${truncatedNote}`;
  }
  return 'Will restore range endpoints only — no frame list in manifest';
}

export function buildApplyNotice(payload: ClipImportApplyPayload): string {
  const loopNote = payload.loopSuggested ? ' and loop suggestion' : '';
  if (payload.applyMode === 'frame_list') {
    return `Clip range${loopNote} and ${payload.frameTimestamps.length}-frame sequence applied to replay.`;
  }
  return `Clip range${loopNote} applied to replay (range endpoints only).`;
}

export function importStatusLabel(status: string): string {
  switch (status) {
    case 'ready':
      return 'All frames ready';
    case 'partial':
      return 'Some frames need attention';
    case 'empty':
      return 'No frames in clip';
    case 'invalid':
    default:
      return 'Invalid manifest';
  }
}

export function problemFrameLabel(frame: ClipImportProblemFrame): string {
  return `${frame.readiness_summary} · ${frame.cache_state}${frame.decode_ready ? ' · decoded' : ''}`;
}
