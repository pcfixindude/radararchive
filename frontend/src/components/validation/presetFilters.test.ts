import { describe, expect, it } from 'vitest';
import {
  countVisiblePresets,
  filterVisiblePresetGroups,
  presetMatchesFilters,
} from './presetFilters';
import type {
  OperatorWorkflowPresetCompact,
  OperatorWorkflowPresetGroupCompact,
} from '../../api/client';

const presetsById: Record<string, OperatorWorkflowPresetCompact> = {
  'quick-status-check': {
    preset_id: 'quick-status-check',
    title: 'Quick status check',
    when_to_use: 'When ok/watch',
    command: 'make operator-review-status',
    recommended: true,
    group_id: 'status-checks',
    verified_mrms: false,
    local_workflow_only: true,
    does_not_clear_alerts: true,
    does_not_enable_production: true,
  },
  'full-local-proof-review': {
    preset_id: 'full-local-proof-review',
    title: 'Full local proof review',
    when_to_use: 'After validation',
    command: 'make scheduled-proof-bundle',
    recommended: false,
    group_id: 'full-review',
    verified_mrms: false,
    local_workflow_only: true,
    does_not_clear_alerts: true,
    does_not_enable_production: true,
  },
};

const groups: OperatorWorkflowPresetGroupCompact[] = [
  {
    group_id: 'status-checks',
    group_title: 'Status checks',
    presets: [{ preset_id: 'quick-status-check', title: 'Quick status check', recommended: true }],
  },
  {
    group_id: 'full-review',
    group_title: 'Full proof review',
    presets: [
      { preset_id: 'full-local-proof-review', title: 'Full local proof review', recommended: false },
    ],
  },
];

describe('presetMatchesFilters', () => {
  it('shows all presets in all mode', () => {
    expect(presetMatchesFilters(presetsById['full-local-proof-review'], 'all')).toBe(true);
  });

  it('shows only recommended presets in recommended mode', () => {
    expect(presetMatchesFilters(presetsById['quick-status-check'], 'recommended')).toBe(true);
    expect(presetMatchesFilters(presetsById['full-local-proof-review'], 'recommended')).toBe(false);
  });
});

describe('filterVisiblePresetGroups', () => {
  it('filters to recommended only', () => {
    const visible = filterVisiblePresetGroups(groups, presetsById, 'recommended', 'all');
    expect(visible).toHaveLength(1);
    expect(visible[0]?.group_id).toBe('status-checks');
    expect(countVisiblePresets(visible)).toBe(1);
  });

  it('filters by group', () => {
    const visible = filterVisiblePresetGroups(groups, presetsById, 'all', 'full-review');
    expect(visible).toHaveLength(1);
    expect(visible[0]?.group_id).toBe('full-review');
  });

  it('hides empty groups after recommended filter', () => {
    const onlyFullReview = [
      {
        group_id: 'full-review',
        group_title: 'Full proof review',
        presets: [
          {
            preset_id: 'full-local-proof-review',
            title: 'Full local proof review',
            recommended: false,
          },
        ],
      },
    ];
    const visible = filterVisiblePresetGroups(onlyFullReview, presetsById, 'recommended', 'all');
    expect(visible).toHaveLength(0);
  });
});
