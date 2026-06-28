export type DemoPlan = 'free' | 'basic' | 'pro' | 'business';

export const DEMO_PLANS: { id: DemoPlan; label: string }[] = [
  { id: 'free', label: 'Free' },
  { id: 'basic', label: 'Basic' },
  { id: 'pro', label: 'Pro' },
  { id: 'business', label: 'Business' },
];

export const DEFAULT_DEMO_PLAN: DemoPlan = 'pro';

export type AccessPlanInfo = {
  id: string;
  name: string;
  history_days: number | null;
};

export type AccessCurrentInfo = {
  plan: string;
  name: string;
  history_days: number | null;
  history_limit_label: string;
  reference_latest: string | null;
  demo_mode: boolean;
  upgrade_message: string;
};

const API_BASE = 'http://127.0.0.1:8000';

export type Layer = {
  id: string;
  name: string;
  type: string;
  available: boolean;
  source?: string;
  bounds?: [number, number, number, number] | null;
  minzoom?: number | null;
  maxzoom?: number | null;
  tile_support?: boolean;
  placeholder?: boolean;
};

function planParams(plan: DemoPlan): URLSearchParams {
  return new URLSearchParams({ plan });
}

function planHeaders(plan: DemoPlan): HeadersInit {
  return { 'X-Demo-Plan': plan };
}

async function getJson<T>(path: string, plan: DemoPlan): Promise<T> {
  const separator = path.includes('?') ? '&' : '?';
  const response = await fetch(`${API_BASE}${path}${separator}${planParams(plan).toString()}`, {
    headers: planHeaders(plan),
  });
  if (!response.ok) {
    throw new Error(`API ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export function fetchLayers(plan: DemoPlan = DEFAULT_DEMO_PLAN): Promise<Layer[]> {
  return getJson<Layer[]>('/api/layers', plan);
}

export function fetchTimes(layer: string, plan: DemoPlan = DEFAULT_DEMO_PLAN, processedOnly = false): Promise<string[]> {
  const params = new URLSearchParams({ layer, plan });
  if (processedOnly) {
    params.set('processed_only', 'true');
  }
  return getJson<string[]>(`/api/times?${params.toString()}`, plan);
}

export function fetchLatest(layer: string, plan: DemoPlan = DEFAULT_DEMO_PLAN) {
  return getJson<{ layer: string; timestamp: string | null }>(
    `/api/latest?layer=${encodeURIComponent(layer)}`,
    plan,
  );
}

export function fetchAccessPlans(): Promise<AccessPlanInfo[]> {
  return fetch(`${API_BASE}/api/access/plans`).then((response) => {
    if (!response.ok) {
      throw new Error('Failed to load access plans');
    }
    return response.json();
  });
}

export function fetchAccessCurrent(plan: DemoPlan): Promise<AccessCurrentInfo> {
  return getJson<AccessCurrentInfo>(`/api/access/current?plan=${encodeURIComponent(plan)}`, plan);
}

export type TilesConfigInfo = {
  enable_decoded_tiles: boolean;
  enable_production_radar_tiles: boolean;
  default_mode: string;
  decoded_mode: string;
  production_mode: string;
  production_rendering: boolean;
  production_rendering_enabled: boolean;
  note: string;
};

export async function fetchTilesConfig(): Promise<TilesConfigInfo | null> {
  try {
    const response = await fetch(`${API_BASE}/tiles/config`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<TilesConfigInfo>;
  } catch {
    return null;
  }
}

export type RenderJobInfo = {
  id: number;
  status: string;
  progress_current: number;
  progress_total: number;
  tiles_written: number;
  prototype: boolean;
  verified_mrms: boolean;
};

export type RenderQueueSummary = {
  queued: number;
  running: number;
  succeeded: number;
  failed: number;
  canceled: number;
  total_tiles_written: number;
  total_output_bytes: number;
  prototype: boolean;
  verified_mrms: boolean;
};

export type ValidationTileCacheSummary = {
  tiles_written: number;
  tiles_skipped: number;
  output_bytes: number;
  job_id?: number | null;
  job_status?: string | null;
};

export type ValidationCompact = {
  validated_at?: string | null;
  source_mode?: string | null;
  batch?: boolean;
  requested_frame_count?: number | null;
  effective_frame_count?: number | null;
  discovered_count: number;
  downloaded_count: number;
  inspected_count: number;
  decoded_count: number;
  render_jobs_enqueued: number;
  worker_jobs_processed: number;
  tiles_planned?: number;
  tiles_written?: number;
  tiles_skipped?: number;
  output_bytes?: number;
  elapsed_seconds?: number | null;
  decoder_available: boolean;
  tile_cache: ValidationTileCacheSummary;
  warnings: string[];
  errors: string[];
  verified_mrms: boolean;
  prototype: boolean;
};

export type BenchmarkCompact = {
  benchmarked_at?: string | null;
  source_mode?: string | null;
  stage_timings: { stage: string; elapsed_seconds: number }[];
  min_zoom?: number | null;
  max_zoom?: number | null;
  tiles_planned: number;
  tiles_written: number;
  tiles_skipped: number;
  output_bytes: number;
  tile_build_elapsed_seconds: number;
  decoder_used?: string | null;
  warnings: string[];
  errors: string[];
  verified_mrms: boolean;
  prototype: boolean;
};

export type QueueBenchmarkJobCompact = {
  timestamp?: string | null;
  radar_file_id?: number | null;
  job_id?: number | null;
  status?: string | null;
  decode_status?: string | null;
  min_zoom?: number | null;
  max_zoom?: number | null;
  tiles_planned?: number;
  tiles_written: number;
  tiles_skipped: number;
  output_bytes: number;
  elapsed_seconds?: number | null;
  warnings?: string[];
  errors?: string[];
};

export type QueueBenchmarkCompact = {
  benchmarked_at?: string | null;
  source_mode?: string | null;
  effective_count?: number | null;
  min_zoom?: number | null;
  max_zoom?: number | null;
  dry_run: boolean;
  jobs_enqueued: number;
  jobs_processed: number;
  jobs_succeeded: number;
  jobs_failed: number;
  total_tiles_written: number;
  total_tiles_skipped: number;
  total_output_bytes: number;
  total_elapsed_seconds?: number | null;
  job_summaries: QueueBenchmarkJobCompact[];
  warnings: string[];
  errors: string[];
  verified_mrms: boolean;
  prototype: boolean;
};

export type ValidationHistoryEntry = {
  validated_at?: string | null;
  source_mode?: string | null;
  batch?: boolean;
  requested_frame_count?: number | null;
  effective_frame_count?: number | null;
  discovered_count: number;
  downloaded_count: number;
  decoded_count: number;
  elapsed_seconds?: number | null;
  verified_mrms: boolean;
  prototype: boolean;
};

export type FrameTileMetricsCompact = {
  timestamp?: string | null;
  radar_file_id?: number | null;
  decode_status?: string | null;
  render_job_id?: number | null;
  min_zoom?: number | null;
  max_zoom?: number | null;
  tiles_planned: number;
  tiles_written: number;
  tiles_skipped: number;
  output_bytes: number;
  elapsed_seconds?: number | null;
  warnings?: string[];
  errors?: string[];
};

export type ScheduledValidationStepCompact = {
  name?: string | null;
  status?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  elapsed_seconds?: number | null;
  summary?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
};

export type ValidationFailureCompact = {
  logged_at?: string | null;
  phase?: string | null;
  step?: string | null;
  source_mode?: string | null;
  command_context?: string | null;
  error_message?: string | null;
  warnings?: string[];
  verified_mrms: boolean;
  prototype: boolean;
};

export type ScheduledProofStepCompact = {
  ran: boolean;
  proof_requested: boolean;
  status?: string | null;
  elapsed_seconds?: number | null;
  proof_regression_status?: string | null;
  proof_regression_detected: boolean;
  verified_mrms: boolean;
  prototype: boolean;
};

export type ScheduledValidationCompact = {
  ran_at?: string | null;
  source_mode?: string | null;
  success: boolean;
  exit_code: number;
  effective_count?: number | null;
  min_zoom?: number | null;
  max_zoom?: number | null;
  elapsed_seconds?: number | null;
  steps_ok: number;
  steps_failed: number;
  steps?: ScheduledValidationStepCompact[];
  batch_decoded_count: number;
  queue_jobs_succeeded: number;
  queue_jobs_failed: number;
  warnings: string[];
  errors: string[];
  proof_step?: ScheduledProofStepCompact | null;
  verified_mrms: boolean;
  prototype: boolean;
};

export type ScheduledProofBundleCompact = {
  bundle_exported: boolean;
  bundle_id?: string | null;
  bundle_created_at?: string | null;
  diff_ran: boolean;
  diff_status?: string | null;
  evidence_changes_count: number;
  operator_attention_needed: boolean;
  handoff_requested?: boolean;
  handoff_generated?: boolean;
  handoff_path?: string | null;
  handoff_reason?: string | null;
  diff_status_that_triggered_handoff?: string | null;
  verified_mrms: boolean;
  local_evidence_monitoring_only: boolean;
  prototype: boolean;
};

export type ValidationAlertCompact = {
  status: string;
  latest_run_at?: string | null;
  updated_at?: string | null;
  failure_count: number;
  warning_count: number;
  operator_attention_needed: boolean;
  suggested_next_action?: string | null;
  grouped_failure_causes?: GroupedFailureCauseCompact[];
  proof_regression_detected?: boolean;
  proof_regression_count?: number;
  proof_regression_still_active?: boolean;
  proof_regression_reviewed?: boolean;
  latest_signoff_at?: string | null;
  latest_signoff_operator?: string | null;
  proof_bundle_diff_status?: string | null;
  proof_bundle_diff_attention?: boolean;
  latest_proof_bundle_id?: string | null;
  latest_proof_bundle_created_at?: string | null;
  proof_bundle_diff_alert_history_count?: number;
  latest_proof_bundle_diff_alert_at?: string | null;
  latest_proof_bundle_diff_alert_status?: string | null;
  proof_bundle_diff_alert_trend?: string | null;
  diff_acknowledgment_count?: number;
  latest_diff_acknowledgment_at?: string | null;
  latest_diff_acknowledgment_operator?: string | null;
  diff_alert_acknowledged_but_still_active?: boolean;
  proof_bundle_diff_escalation_level?: string | null;
  proof_bundle_diff_escalation_stale_ack?: boolean;
  proof_bundle_diff_escalation_reason?: string | null;
  proof_bundle_diff_escalation_suggested_next_action?: string | null;
  proof_bundle_diff_escalation_guidance_items?: OperatorGuidanceItem[];
  proof_bundle_diff_escalation_history_count?: number;
  latest_proof_bundle_diff_escalation_snapshot_at?: string | null;
  urgent_stdout_notice_triggered?: boolean;
  urgent_stdout_notice_at?: string | null;
  operator_guidance?: OperatorGuidanceItem[];
  verified_mrms: boolean;
  prototype: boolean;
};

export type OperatorGuidanceItem = {
  title: string;
  path: string;
  anchor?: string;
  section_label?: string;
  cause: string;
  suggested_action?: string;
  verified_mrms: boolean;
  local_guidance_only: boolean;
  prototype: boolean;
};

export type ProofBundleDiffAlertEntry = {
  created_at?: string | null;
  diff_status?: string | null;
  operator_attention_needed: boolean;
  evidence_changes_count: number;
  bundle_id?: string | null;
  baseline_bundle_id?: string | null;
  suggested_next_action?: string | null;
  guidance_cause?: string | null;
  verified_mrms: boolean;
  local_history_only: boolean;
  prototype: boolean;
};

export type ProofBundleDiffAlertCompact = {
  available: boolean;
  count: number;
  created_at?: string | null;
  diff_status?: string | null;
  operator_attention_needed?: boolean;
  evidence_changes_count?: number;
  bundle_id?: string | null;
  baseline_bundle_id?: string | null;
  suggested_next_action?: string | null;
  guidance_cause?: string | null;
  verified_mrms: boolean;
  local_history_only: boolean;
  prototype: boolean;
};

export type ProofBundleDiffAlertTrendCompact = {
  available: boolean;
  latest_status?: string | null;
  latest_at?: string | null;
  last_worsened_at?: string | null;
  last_mixed_at?: string | null;
  last_improved_at?: string | null;
  last_unchanged_at?: string | null;
  current_attention_streak: number;
  current_non_attention_streak: number;
  recent_worsened_count: number;
  recent_mixed_count: number;
  recent_improved_count: number;
  recent_unchanged_count: number;
  trend: string;
  window_size?: number;
  history_count?: number;
  suggested_next_action?: string | null;
  verified_mrms: boolean;
  local_trend_only: boolean;
  prototype: boolean;
};

export type ProofBundleDiffAcknowledgmentCompact = {
  available: boolean;
  count: number;
  acknowledgment_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  note?: string | null;
  related_diff_status?: string | null;
  acknowledged_attention?: boolean;
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationCompact = {
  available: boolean;
  escalation_level: string;
  reason: string;
  latest_diff_status?: string | null;
  current_attention_streak: number;
  acknowledgment_status: string;
  latest_acknowledgment_at?: string | null;
  latest_acknowledgment_operator?: string | null;
  stale_acknowledgment: boolean;
  suggested_next_action: string;
  guidance_items?: OperatorGuidanceItem[];
  trend?: string | null;
  verified_mrms: boolean;
  local_escalation_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationHistoryEntry = {
  created_at?: string | null;
  escalation_level: string;
  reason?: string;
  latest_diff_status?: string | null;
  current_attention_streak?: number;
  acknowledgment_status?: string;
  stale_acknowledgment?: boolean;
  suggested_next_action?: string;
  guidance_item_count?: number;
  source?: string | null;
  verified_mrms: boolean;
  local_history_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationHistoryCompact = {
  available: boolean;
  count: number;
  max_entries?: number;
  latest_snapshot_at?: string | null;
  latest_escalation_level?: string | null;
  recent?: ProofBundleDiffEscalationHistoryEntry[];
  urgent_stdout_notice_triggered?: boolean;
  urgent_stdout_notice_at?: string | null;
  urgent_stdout_local_only?: boolean;
  verified_mrms: boolean;
  local_history_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationMetricsCompact = {
  available: boolean;
  total_snapshots: number;
  urgent_count: number;
  attention_count: number;
  watch_count: number;
  none_count: number;
  latest_level: string;
  latest_at?: string | null;
  first_urgent_at?: string | null;
  last_urgent_at?: string | null;
  longest_urgent_streak: number;
  longest_attention_or_urgent_streak: number;
  current_urgent_streak: number;
  current_attention_or_urgent_streak: number;
  acknowledgment_status?: string | null;
  stale_acknowledgment_count: number;
  verified_mrms: boolean;
  local_metrics_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationDigestCompact = {
  available: boolean;
  generated_at?: string | null;
  markdown_path?: string | null;
  json_path?: string | null;
  latest_escalation_level?: string | null;
  snapshot_count?: number;
  urgent_count?: number;
  attention_count?: number;
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationDigestHistoryEntry = {
  created_at?: string | null;
  digest_path?: string | null;
  metadata_path?: string | null;
  latest_escalation_level?: string | null;
  latest_diff_status?: string | null;
  current_attention_or_urgent_streak?: number;
  urgent_count?: number;
  attention_count?: number;
  stale_acknowledgment_count?: number;
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationDigestHistoryCompact = {
  available: boolean;
  count: number;
  max_entries: number;
  latest?: ProofBundleDiffEscalationDigestHistoryEntry | null;
  recent?: ProofBundleDiffEscalationDigestHistoryEntry[];
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type ProofBundleDiffEscalationDigestDiffCompact = {
  available: boolean;
  overall_digest_diff_status?: string | null;
  checked_at?: string | null;
  history_count?: number;
  changes?: Record<string, unknown> | null;
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type DigestRegenerationHintCompact = {
  digest_regeneration_recommended: boolean;
  reason?: string | null;
  suggested_command?: string | null;
  latest_escalation_level?: string | null;
  current_attention_or_urgent_streak?: number;
  latest_digest_at?: string | null;
  latest_escalation_snapshot_at?: string | null;
  latest_digest_diff_status?: string | null;
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type OpenAttentionGuidanceItem = {
  title: string;
  path: string;
  anchor?: string;
  section_label?: string;
  cause: string;
  attention_item?: string;
  suggested_action?: string;
  verified_mrms: boolean;
  local_guidance_only: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionComparisonCompact = {
  available: boolean;
  overall_review_diff_status?: string | null;
  compared_at?: string | null;
  latest_created_at?: string | null;
  baseline_created_at?: string | null;
  latest_operator?: string | null;
  baseline_operator?: string | null;
  open_attention_count_change?: { baseline?: number; latest?: number } | null;
  checklist_reviewed_count_change?: { baseline?: number; latest?: number } | null;
  checklist_not_reviewed_count_change?: { baseline?: number; latest?: number } | null;
  improvements?: string[];
  regressions?: string[];
  history_count?: number;
  verified_mrms: boolean;
  local_comparison_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionSummaryCompact = {
  available: boolean;
  session_count: number;
  latest_created_at?: string | null;
  latest_operator?: string | null;
  latest_escalation_level?: string | null;
  open_attention_count: number;
  open_attention_guidance?: OpenAttentionGuidanceItem[];
  comparison?: MrmsReviewSessionComparisonCompact | null;
  verified_mrms: boolean;
  local_review_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionExportCompact = {
  available: boolean;
  created_at?: string | null;
  export_path?: string | null;
  metadata_path?: string | null;
  session_id?: string | null;
  operator?: string | null;
  comparison_status?: string | null;
  open_attention_count: number;
  history_count?: number;
  verified_mrms: boolean;
  local_export_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type ReviewExportRegenerationHintCompact = {
  review_export_regeneration_recommended: boolean;
  reason?: string | null;
  suggested_command?: string | null;
  latest_export_at?: string | null;
  latest_session_at?: string | null;
  latest_comparison_at?: string | null;
  digest_regeneration_recommended?: boolean;
  digest_regeneration_reason?: string | null;
  verified_mrms: boolean;
  local_export_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  session_notes?: string;
  checklist_items_reviewed?: string[];
  accepted_limitations?: boolean;
  accepted_limitations_text?: string;
};

export type MrmsReviewSessionCreateResponse = {
  verified_mrms: boolean;
  local_review_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  production_enabled: boolean;
  review_session: Record<string, unknown>;
};

export type ProofBundleDiffAcknowledgmentCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  note: string;
};

export type ProofBundleDiffAcknowledgmentCreateResponse = {
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  production_enabled: boolean;
  diff_alert_still_active: boolean;
  acknowledgment: Record<string, unknown>;
};

export type GroupedFailureCauseCompact = {
  step: string;
  cause: string;
  message?: string;
  normalized_message?: string;
  count: number;
  latest_logged_at?: string | null;
};

export type MrmsProofCriteriaCounts = {
  passed: number;
  failed: number;
  warning: number;
  skipped: number;
  unknown: number;
};

export type MrmsProofCompact = {
  generated_at?: string | null;
  overall_status: string;
  source_mode?: string | null;
  frame_count: number;
  criteria_counts?: MrmsProofCriteriaCounts;
  operator_review_required: boolean;
  proof_only: boolean;
  verified_mrms: boolean;
  prototype: boolean;
};

export type MrmsProofRegressionCompact = {
  checked_at?: string | null;
  regression_status: string;
  regression_detected: boolean;
  regression_count: number;
  current_overall_status?: string | null;
  previous_overall_status?: string | null;
  verified_mrms: boolean;
  prototype: boolean;
};

export type MrmsSignoffSummaryCompact = {
  signoff_count: number;
  latest_signoff_at?: string | null;
  latest_operator?: string | null;
  proof_regression_still_active?: boolean;
  proof_regression_reviewed?: boolean;
  verified_mrms: boolean;
  local_signoff_only: boolean;
  does_not_set_verified_mrms: boolean;
  does_not_enable_production?: boolean;
  prototype: boolean;
};

export type MrmsSignoffCreateRequest = {
  operator_name?: string | null;
  operator_initials?: string | null;
  operator_notes?: string | null;
  accepted_limitations?: string | null;
  proof_report_timestamp?: string | null;
  frame_count_reviewed?: number | null;
};

export type MrmsSignoffCreateResponse = {
  prototype: boolean;
  verified_mrms: boolean;
  local_signoff_only: boolean;
  does_not_enable_production: boolean;
  production_enabled: boolean;
  proof_regression_still_active: boolean;
  signoff: Record<string, unknown>;
  alert: ValidationAlertCompact | null;
};

export type MrmsProofBundleCompact = {
  available: boolean;
  bundle_id?: string | null;
  created_at?: string | null;
  bundle_folder?: string | null;
  zip_path?: string | null;
  file_count: number;
  files_missing_count?: number;
  bundle_count?: number;
  include_history?: boolean;
  verified_mrms: boolean;
  local_bundle_only: boolean;
  proof_only: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type MrmsProofBundleDiffCompact = {
  available: boolean;
  diff_id?: string | null;
  checked_at?: string | null;
  overall_diff_status: string;
  evidence_changes_count: number;
  has_baseline?: boolean;
  verified_mrms: boolean;
  local_diff_only: boolean;
  proof_only: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type ScheduledDigestCompact = {
  digest_requested: boolean;
  digest_generated: boolean;
  digest_path?: string | null;
  digest_metadata_path?: string | null;
  digest_reason?: string | null;
  digest_elapsed_seconds?: number | null;
  verified_mrms: boolean;
  local_digest_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications: boolean;
  prototype: boolean;
};

export type ScheduledReviewExportCompact = {
  review_export_requested: boolean;
  review_export_generated: boolean;
  review_export_path?: string | null;
  review_export_metadata_path?: string | null;
  review_export_reason?: string | null;
  review_export_elapsed_seconds?: number | null;
  verified_mrms: boolean;
  local_export_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications: boolean;
  prototype: boolean;
};

export type OperatorHandoffCompact = {
  available: boolean;
  created_at?: string | null;
  markdown_path?: string | null;
  json_path?: string | null;
  question_count: number;
  diff_status?: string | null;
  auto_generated?: boolean;
  trigger_reason?: string | null;
  handoff_requested?: boolean;
  handoff_generated?: boolean;
  handoff_reason?: string | null;
  scheduled_handoff_path?: string | null;
  diff_status_that_triggered_handoff?: string | null;
  include_escalation_review?: boolean;
  digest_path?: string | null;
  digest_metadata_path?: string | null;
  acknowledgment_status?: string | null;
  stale_acknowledgment?: boolean | null;
  escalation_level?: string | null;
  review_checklist_count?: number;
  verified_mrms: boolean;
  local_handoff_only: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type RunbookReference = {
  title: string;
  path: string;
  anchor?: string;
};

export type MrmsProofHistoryEntry = {
  generated_at?: string | null;
  overall_status: string;
  source_mode?: string | null;
  frame_count: number;
  criteria_counts?: MrmsProofCriteriaCounts;
  operator_review_required: boolean;
  verified_mrms: boolean;
};

export type MrmsProofHistory = {
  prototype: boolean;
  verified_mrms: boolean;
  count: number;
  max_entries: number;
  latest: MrmsProofCompact | null;
  entries: MrmsProofHistoryEntry[];
};

export type MrmsProofRegressionHistoryEntry = {
  checked_at?: string | null;
  regression_status: string;
  regression_detected: boolean;
  regression_count: number;
  summary: string;
  verified_mrms: boolean;
};

export type MrmsProofRegressionHistory = {
  prototype: boolean;
  verified_mrms: boolean;
  count: number;
  max_entries: number;
  latest: MrmsProofRegressionCompact | null;
  entries: MrmsProofRegressionHistoryEntry[];
};

export type MrmsSignoffItem = {
  signoff_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  operator_name?: string | null;
  operator_initials?: string | null;
  proof_report_timestamp?: string | null;
  accepted_limitations?: string | null;
  verified_mrms: boolean;
  does_not_set_verified_mrms: boolean;
  local_signoff_only: boolean;
};

export type MrmsSignoffsList = {
  prototype: boolean;
  verified_mrms: boolean;
  local_signoff_only: boolean;
  does_not_set_verified_mrms: boolean;
  count: number;
  entries: MrmsSignoffItem[];
};

export type ValidationLatest = {
  prototype: boolean;
  verified_mrms: boolean;
  production_rendering_enabled: boolean;
  validation: Record<string, unknown> | null;
  benchmark: Record<string, unknown> | null;
  queue_benchmark: Record<string, unknown> | null;
  scheduled_validation: Record<string, unknown> | null;
  validation_alert: Record<string, unknown> | null;
  mrms_proof: Record<string, unknown> | null;
  mrms_proof_regression: Record<string, unknown> | null;
  mrms_signoffs: Record<string, unknown>[];
};

export type ValidationSummary = {
  prototype: boolean;
  verified_mrms: boolean;
  production_rendering_enabled: boolean;
  placeholder_default: boolean;
  decoder_available: boolean;
  decoder_summary: string;
  stale_running_job_seconds: number;
  validation_available: boolean;
  validation: ValidationCompact | null;
  benchmark_available: boolean;
  benchmark: BenchmarkCompact | null;
  queue_benchmark_available?: boolean;
  queue_benchmark?: QueueBenchmarkCompact | null;
  render_queue: RenderQueueSummary;
  validation_history_count: number;
  validation_history?: ValidationHistoryEntry[];
  queue_benchmark_history_count?: number;
  scheduled_validation_available?: boolean;
  scheduled_validation?: ScheduledValidationCompact | null;
  scheduled_proof_bundle?: ScheduledProofBundleCompact | null;
  scheduled_digest?: ScheduledDigestCompact | null;
  scheduled_review_export?: ScheduledReviewExportCompact | null;
  validation_failures_count?: number;
  validation_failures_recent?: ValidationFailureCompact[];
  validation_alert?: ValidationAlertCompact | null;
  grouped_failure_causes?: GroupedFailureCauseCompact[];
  mrms_proof?: MrmsProofCompact | null;
  mrms_proof_available?: boolean;
  mrms_proof_regression?: MrmsProofRegressionCompact | null;
  mrms_proof_regression_available?: boolean;
  mrms_signoff?: MrmsSignoffSummaryCompact | null;
  mrms_proof_bundle?: MrmsProofBundleCompact | null;
  mrms_proof_bundle_diff?: MrmsProofBundleDiffCompact | null;
  operator_handoff?: OperatorHandoffCompact | null;
  operator_guidance?: OperatorGuidanceItem[];
  proof_bundle_diff_alert?: ProofBundleDiffAlertCompact | null;
  proof_bundle_diff_alert_history?: ProofBundleDiffAlertEntry[];
  proof_bundle_diff_alert_trend?: ProofBundleDiffAlertTrendCompact | null;
  proof_bundle_diff_acknowledgment?: ProofBundleDiffAcknowledgmentCompact | null;
  proof_bundle_diff_escalation?: ProofBundleDiffEscalationCompact | null;
  proof_bundle_diff_escalation_history?: ProofBundleDiffEscalationHistoryCompact | null;
  proof_bundle_diff_escalation_metrics?: ProofBundleDiffEscalationMetricsCompact | null;
  proof_bundle_diff_escalation_digest?: ProofBundleDiffEscalationDigestCompact | null;
  proof_bundle_diff_escalation_digest_history?: ProofBundleDiffEscalationDigestHistoryCompact | null;
  proof_bundle_diff_escalation_digest_diff?: ProofBundleDiffEscalationDigestDiffCompact | null;
  digest_regeneration_hint?: DigestRegenerationHintCompact | null;
  mrms_review_session?: MrmsReviewSessionSummaryCompact | null;
  mrms_review_session_export?: MrmsReviewSessionExportCompact | null;
  review_export_regeneration_hint?: ReviewExportRegenerationHintCompact | null;
  runbook_references?: RunbookReference[];
  frame_summaries?: FrameTileMetricsCompact[];
  catalog: CatalogStatus;
};

export type CatalogStatus = {
  product_id: string;
  total_frames: number;
  mrms_discovered_frames: number;
  download_status: Record<string, number>;
  processed_status: Record<string, number>;
  render_status: Record<string, number>;
  latest_timestamp: string | null;
  earliest_timestamp: string | null;
  latest_downloaded_timestamp: string | null;
  prototype: boolean;
  verified_mrms: boolean;
};

export async function fetchRenderJobs(limit = 3): Promise<RenderJobInfo[]> {
  try {
    const response = await fetch(`${API_BASE}/api/render/jobs?limit=${limit}`);
    if (!response.ok) {
      return [];
    }
    return response.json() as Promise<RenderJobInfo[]>;
  } catch {
    return [];
  }
}

export async function fetchRenderQueueSummary(): Promise<RenderQueueSummary | null> {
  try {
    const response = await fetch(`${API_BASE}/api/render/jobs/summary`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<RenderQueueSummary>;
  } catch {
    return null;
  }
}

export async function fetchValidationSummary(): Promise<ValidationSummary | null> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/summary`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<ValidationSummary>;
  } catch {
    return null;
  }
}

export async function fetchValidationLatest(): Promise<ValidationLatest | null> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/latest`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<ValidationLatest>;
  } catch {
    return null;
  }
}

export async function fetchProofHistory(): Promise<MrmsProofHistory | null> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/proof/history`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<MrmsProofHistory>;
  } catch {
    return null;
  }
}

export async function fetchProofRegressionHistory(): Promise<MrmsProofRegressionHistory | null> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/proof-regression/history`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<MrmsProofRegressionHistory>;
  } catch {
    return null;
  }
}

export async function fetchSignoffsList(): Promise<MrmsSignoffsList | null> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/signoffs`);
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<MrmsSignoffsList>;
  } catch {
    return null;
  }
}

export async function submitDiffAcknowledgment(
  payload: ProofBundleDiffAcknowledgmentCreateRequest,
): Promise<
  { ok: true; data: ProofBundleDiffAcknowledgmentCreateResponse } | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/proof-bundle-diff-acknowledgments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let error = `Acknowledgment failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) {
          error = body.detail;
        }
      } catch {
        // keep default error
      }
      return { ok: false, error };
    }
    const data = (await response.json()) as ProofBundleDiffAcknowledgmentCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Acknowledgment request failed' };
  }
}

export async function submitReviewSession(
  payload: MrmsReviewSessionCreateRequest,
): Promise<{ ok: true; data: MrmsReviewSessionCreateResponse } | { ok: false; error: string }> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/review-sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let error = `Review session failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) {
          error = body.detail;
        }
      } catch {
        // keep default error
      }
      return { ok: false, error };
    }
    const data = (await response.json()) as MrmsReviewSessionCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Review session request failed' };
  }
}

export async function submitSignoff(
  payload: MrmsSignoffCreateRequest,
): Promise<{ ok: true; data: MrmsSignoffCreateResponse } | { ok: false; error: string }> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/signoffs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let error = `Sign-off failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) {
          error = body.detail;
        }
      } catch {
        // keep default error
      }
      return { ok: false, error };
    }
    const data = (await response.json()) as MrmsSignoffCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Sign-off request failed' };
  }
}

export async function fetchProofReviewData(): Promise<{
  proofHistory: MrmsProofHistory | null;
  regressionHistory: MrmsProofRegressionHistory | null;
  signoffs: MrmsSignoffsList | null;
}> {
  const [proofHistory, regressionHistory, signoffs] = await Promise.all([
    fetchProofHistory(),
    fetchProofRegressionHistory(),
    fetchSignoffsList(),
  ]);
  return { proofHistory, regressionHistory, signoffs };
}

export function tileUrl(layer: string, timestamp: string, plan: DemoPlan, z = 0, x = 0, y = 0): string {
  const encoded = encodeURIComponent(timestamp);
  return `${API_BASE}/tiles/${encodeURIComponent(layer)}/${encoded}/${z}/${x}/${y}.png?plan=${encodeURIComponent(plan)}`;
}

/** MapLibre raster template with {z}/{x}/{y} placeholders. */
export function tileUrlTemplate(layer: string, timestamp: string, plan: DemoPlan): string {
  const encoded = encodeURIComponent(timestamp);
  return `${API_BASE}/tiles/${encodeURIComponent(layer)}/${encoded}/{z}/{x}/{y}.png?plan=${encodeURIComponent(plan)}`;
}

export async function tilesAvailable(layer: string, timestamp: string, plan: DemoPlan): Promise<boolean> {
  if (!timestamp) {
    return false;
  }
  try {
    const response = await fetch(tileUrl(layer, timestamp, plan), {
      method: 'HEAD',
      headers: planHeaders(plan),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function tileBlockedByPlan(layer: string, timestamp: string, plan: DemoPlan): Promise<boolean> {
  try {
    const response = await fetch(tileUrl(layer, timestamp, plan), { headers: planHeaders(plan) });
    return response.status === 403;
  } catch {
    return false;
  }
}
