import { describe, expect, it } from 'vitest';
import {
  formatQualityCheckSummary,
  pickPrimaryFrameDetail,
  readinessSummaryLabel,
  selectInspectTimestamp,
} from './frameDetail';

describe('frameDetail helpers', () => {
  it('labels readiness summaries', () => {
    expect(readinessSummaryLabel('ready')).toBe('Ready for replay');
    expect(readinessSummaryLabel('cold')).toBe('Cold — warm/decode needed');
    expect(readinessSummaryLabel('unknown')).toBe('Unknown');
  });

  it('selects inspect timestamp', () => {
    expect(selectInspectTimestamp('2026-06-28T13:00:00Z', '2026-06-28T13:26:38Z')).toBe(
      '2026-06-28T13:26:38Z',
    );
  });

  it('picks primary frame from report', () => {
    const report = {
      frame_count: 1,
      ready_count: 1,
      partial_count: 0,
      cold_count: 0,
      missing_count: 0,
      failed_count: 0,
      frames: [
        {
          timestamp: '2026-06-28T13:00:00Z',
          valid: true,
          cache_state: 'ready',
          cache_ready: true,
          decode_ready: true,
          readiness_summary: 'ready',
          path_hints: { preview_available: true },
          frame_quality: { status: 'ok', checks: [] },
          suggested_commands: ['make decode-retry'],
        },
      ],
    };
    expect(pickPrimaryFrameDetail(report)?.timestamp).toBe('2026-06-28T13:00:00Z');
    expect(pickPrimaryFrameDetail(null)).toBeNull();
  });

  it('summarizes quality checks', () => {
    expect(
      formatQualityCheckSummary([
        { name: 'artifacts', status: 'error', message: 'missing' },
        { name: 'grid', status: 'warning', message: 'flat' },
      ]),
    ).toBe('1 error(s), 1 warning(s)');
  });
});
