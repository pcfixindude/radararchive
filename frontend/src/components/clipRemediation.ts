export type ClipRemediationProblemGroup = {
  readiness_type: string;
  label: string;
  count: number;
  assessed_count: number;
  truncated: boolean;
  timestamps: string[];
};

export type ClipRemediationGroupSummary = {
  total_problem_count: number;
  assessed_count: number;
  cold_count: number;
  missing_count: number;
  failed_count: number;
  stub_count: number;
  partial_count: number;
  invalid_count: number;
};

export type ClipRemediationCommandStep = {
  step: number;
  category: string;
  label: string;
  command: string;
  frame_count?: number | null;
  note?: string | null;
};

export type ClipRemediationPlan = {
  clip_id?: string | null;
  valid: boolean;
  plan_status: string;
  problem_groups: ClipRemediationProblemGroup[];
  group_summary: ClipRemediationGroupSummary;
  commands: ClipRemediationCommandStep[];
  command_block: string;
  operator_note: string;
  bounded_frame_limit: number;
  truncated: boolean;
  assessed_at?: string;
  verified_mrms: boolean;
  local_dev_only: boolean;
  prototype: boolean;
  status_only: boolean;
  does_not_run_ingest: boolean;
  does_not_run_decode: boolean;
  does_not_run_real_downloads: boolean;
  commands_not_auto_run: boolean;
};

export function remediationPlanStatusLabel(status: string): string {
  switch (status) {
    case 'ready':
      return 'Remediation plan ready';
    case 'empty':
      return 'No remediation needed';
    case 'invalid':
    default:
      return 'Invalid import — fix manifest first';
  }
}

export function formatRemediationGroupSummary(summary: ClipRemediationGroupSummary): string {
  const parts: string[] = [];
  if (summary.cold_count > 0) {
    parts.push(`${summary.cold_count} cold`);
  }
  if (summary.missing_count > 0) {
    parts.push(`${summary.missing_count} missing`);
  }
  if (summary.failed_count > 0) {
    parts.push(`${summary.failed_count} failed`);
  }
  if (summary.stub_count > 0) {
    parts.push(`${summary.stub_count} stub`);
  }
  if (summary.partial_count > 0) {
    parts.push(`${summary.partial_count} partial`);
  }
  if (summary.invalid_count > 0) {
    parts.push(`${summary.invalid_count} invalid`);
  }
  if (!parts.length) {
    return 'No problem frames';
  }
  const bounded =
    summary.assessed_count < summary.total_problem_count
      ? ` · ${summary.assessed_count}/${summary.total_problem_count} assessed for commands`
      : '';
  return `${parts.join(' · ')}${bounded}`;
}

export function hasRemediationCommands(plan: ClipRemediationPlan | null | undefined): boolean {
  return Boolean(plan && plan.plan_status === 'ready' && plan.commands.length > 0);
}
