import { describe, expect, it } from 'vitest';
import {
  formatRemediationGroupSummary,
  hasRemediationCommands,
  remediationPlanStatusLabel,
  type ClipRemediationPlan,
} from './clipRemediation';

const samplePlan: ClipRemediationPlan = {
  valid: true,
  plan_status: 'ready',
  clip_id: 'clip_test',
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
      command: 'make mrms-warm-frame-cache ARGS="--start 2026-06-28T13:26:38Z --end 2026-06-28T13:26:38Z --limit 8"',
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
};

describe('remediationPlanStatusLabel', () => {
  it('maps plan status codes', () => {
    expect(remediationPlanStatusLabel('ready')).toBe('Remediation plan ready');
    expect(remediationPlanStatusLabel('empty')).toBe('No remediation needed');
    expect(remediationPlanStatusLabel('invalid')).toBe('Invalid import — fix manifest first');
  });
});

describe('formatRemediationGroupSummary', () => {
  it('summarizes cold/missing/failed counts', () => {
    expect(formatRemediationGroupSummary(samplePlan.group_summary)).toBe('1 cold');
  });

  it('shows bounded assessment when truncated', () => {
    expect(
      formatRemediationGroupSummary({
        ...samplePlan.group_summary,
        total_problem_count: 5,
        assessed_count: 3,
        cold_count: 3,
        missing_count: 2,
      }),
    ).toBe('3 cold · 2 missing · 3/5 assessed for commands');
  });
});

describe('hasRemediationCommands', () => {
  it('returns true when plan has commands', () => {
    expect(hasRemediationCommands(samplePlan)).toBe(true);
  });

  it('returns false for empty plan', () => {
    expect(hasRemediationCommands({ ...samplePlan, plan_status: 'empty', commands: [] })).toBe(
      false,
    );
  });
});
