import type {
  OperatorWorkflowPresetCompact,
  OperatorWorkflowPresetGroupCompact,
} from '../../api/client';

export type PresetFilterMode = 'all' | 'recommended';

export function presetMatchesFilters(
  preset: OperatorWorkflowPresetCompact | undefined,
  mode: PresetFilterMode,
): boolean {
  if (!preset) {
    return false;
  }
  if (mode === 'recommended') {
    return Boolean(preset.recommended);
  }
  return true;
}

export function filterVisiblePresetGroups(
  groups: OperatorWorkflowPresetGroupCompact[],
  presetsById: Record<string, OperatorWorkflowPresetCompact>,
  mode: PresetFilterMode,
  groupFilter: string,
): OperatorWorkflowPresetGroupCompact[] {
  return groups
    .map((group) => {
      if (groupFilter !== 'all' && group.group_id !== groupFilter) {
        return null;
      }
      const visiblePresets = (group.presets ?? []).filter((entry) =>
        presetMatchesFilters(presetsById[entry.preset_id], mode),
      );
      if (visiblePresets.length === 0) {
        return null;
      }
      return {
        ...group,
        presets: visiblePresets,
        preset_count: visiblePresets.length,
        recommended_count: visiblePresets.filter((entry) =>
          Boolean(presetsById[entry.preset_id]?.recommended),
        ).length,
      };
    })
    .filter((group): group is OperatorWorkflowPresetGroupCompact => group !== null);
}

export function countVisiblePresets(groups: OperatorWorkflowPresetGroupCompact[]): number {
  return groups.reduce((total, group) => total + (group.presets?.length ?? 0), 0);
}
