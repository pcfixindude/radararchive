import type { FrameQualityCheckItem } from '../api/client';
import { qualityStatusLabel } from './frameQualityDisplay';

export type FrameQualityPathHints = {
  cache_dir?: string | null;
  manifest_path?: string | null;
  manifest_present?: boolean;
  decode_output_dir?: string | null;
  raw_path?: string | null;
  preview_paths?: string[];
  preview_available?: boolean;
  preview_path_count?: number;
  tile_root?: string | null;
};

export type FrameQualityDetail = {
  timestamp: string;
  valid: boolean;
  cache_state: string;
  cache_ready: boolean;
  decode_ready: boolean;
  decode_status?: string | null;
  frame_status?: string | null;
  readiness_summary: string;
  sync_message?: string | null;
  path_hints: FrameQualityPathHints;
  frame_quality: {
    status: string;
    checks: FrameQualityCheckItem[];
    measured?: Record<string, unknown>;
    diagnostic_only?: boolean;
  };
  suggested_commands: string[];
};

export type FrameQualityReport = {
  frame_count: number;
  ready_count: number;
  partial_count: number;
  cold_count: number;
  missing_count: number;
  failed_count: number;
  frames: FrameQualityDetail[];
};

export function readinessSummaryLabel(summary: string): string {
  switch (summary) {
    case 'ready':
      return 'Ready for replay';
    case 'partial':
      return 'Partially ready';
    case 'cold':
      return 'Cold — warm/decode needed';
    case 'missing':
      return 'Missing raw MRMS';
    case 'failed':
      return 'Decode/warm failed';
    case 'stub':
      return 'Stub input only';
    default:
      return 'Unknown';
  }
}

export function readinessSummaryClass(summary: string): string {
  return `frame-detail-readiness--${summary || 'invalid'}`;
}

export function formatPathHint(path: string | null | undefined): string {
  if (!path) {
    return '—';
  }
  return path;
}

export function selectInspectTimestamp(current: string, next: string): string {
  return next || current;
}

export function pickPrimaryFrameDetail(report: FrameQualityReport | null): FrameQualityDetail | null {
  if (!report || report.frames.length === 0) {
    return null;
  }
  return report.frames[0] ?? null;
}

export function formatQualityCheckSummary(checks: FrameQualityCheckItem[]): string {
  const errors = checks.filter((check) => check.status === 'error').length;
  const warnings = checks.filter((check) => check.status === 'warning').length;
  if (errors > 0) {
    return `${errors} error(s), ${warnings} warning(s)`;
  }
  if (warnings > 0) {
    return `${warnings} warning(s)`;
  }
  return qualityStatusLabel(checks.length > 0 ? 'ok' : 'unavailable');
}
