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

export type OperatorWorkflowPresetGroupEntryCompact = {
  preset_id: string;
  title: string;
  recommended?: boolean;
  recommended_priority?: number | null;
  short_reason?: string | null;
  priority?: number;
};

export type OperatorWorkflowPresetGroupCompact = {
  group_id: string;
  group_title?: string | null;
  preset_count?: number;
  recommended_count?: number;
  presets?: OperatorWorkflowPresetGroupEntryCompact[];
};

export type OperatorWorkflowPresetCompact = {
  preset_id: string;
  title: string;
  description?: string;
  when_to_use: string;
  command: string;
  expected_outputs?: string[];
  safety_notes?: string[];
  recommended?: boolean;
  recommendation_reason?: string | null;
  group_id?: string | null;
  group_title?: string | null;
  priority?: number;
  recommended_priority?: number | null;
  short_reason?: string | null;
  runbook_path?: string | null;
  runbook_section?: string | null;
  runbook_anchor?: string | null;
  suggested_action?: string | null;
  verified_mrms: boolean;
  local_workflow_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
};

export type MrmsVisualReviewCompact = {
  available?: boolean;
  created_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  layers_inspected?: string[];
  timestamp_count?: number;
  frame_count?: number;
  artifact_count?: number;
  missing_artifact_count?: number;
  tile_modes_found?: string[];
  suggested_next_command?: string | null;
  runbook_path?: string | null;
  history_count?: number;
  verified_mrms: boolean;
  local_visual_review_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
};

export type MrmsVisualReviewComparisonCompact = {
  available?: boolean;
  overall_visual_review_diff_status?: string | null;
  compared_at?: string | null;
  latest_created_at?: string | null;
  baseline_created_at?: string | null;
  artifact_count_change?: { baseline?: number; latest?: number } | null;
  missing_artifact_count_change?: { baseline?: number; latest?: number } | null;
  tile_modes_added?: string[];
  tile_modes_removed?: string[];
  history_count?: number;
  verified_mrms: boolean;
  local_visual_review_comparison_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
};

export type MrmsVisualReviewHintCompact = {
  available?: boolean;
  visual_review_regeneration_recommended?: boolean;
  reason?: string | null;
  suggested_command?: string | null;
  latest_visual_review_at?: string | null;
  latest_relevant_evidence_at?: string | null;
  stale_visual_review?: boolean;
  verified_mrms: boolean;
  local_hint_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
};

export type MrmsVisualReviewSampleSetContextCompact = {
  visual_review_regeneration_recommended?: boolean;
  visual_review_hint_reason?: string | null;
  stale_visual_review?: boolean;
  latest_visual_review_comparison_status?: string | null;
  comparison_available?: boolean;
};

export type MrmsVisualReviewSampleSetCompact = {
  available?: boolean;
  created_at?: string | null;
  selection_mode?: string | null;
  entry_count?: number;
  limit?: number;
  json_path?: string | null;
  markdown_path?: string | null;
  source_visual_review_at?: string | null;
  source_visual_review_path?: string | null;
  reason?: string | null;
  suggested_command?: string | null;
  context?: MrmsVisualReviewSampleSetContextCompact | null;
  verified_mrms: boolean;
  local_sample_set_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  no_external_notifications: boolean;
};

export type MrmsVisualReviewSampleSetCreateRequest = {
  selection_mode?: string;
  limit?: number;
  timestamps?: string[];
  notes?: string | null;
};

export type MrmsVisualReviewSampleSetCreateResponse = {
  verified_mrms: boolean;
  local_sample_set_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  sample_set: {
    entry_count?: number;
    entries?: Array<{
      timestamp?: string | null;
      layer?: string | null;
      tile_mode?: string | null;
      primary_artifact_path?: string | null;
      selection_reason?: string | null;
      missing_artifacts?: string[];
    }>;
    json_path?: string | null;
    markdown_path?: string | null;
  };
  compact: MrmsVisualReviewSampleSetCompact;
};

export type MrmsVisualReviewSampleEntrySummaryCompact = {
  sample_key?: string | null;
  timestamp?: string | null;
  layer?: string | null;
  tile_mode?: string | null;
  primary_artifact_path?: string | null;
  status?: string | null;
  operator_notes?: string | null;
  reviewed_at?: string | null;
  reviewer_label?: string | null;
  issue_tags?: string[];
  missing_artifacts?: string[];
  stale_visual_review?: boolean;
};

export type MrmsVisualReviewSampleReadinessCompact = {
  available?: boolean;
  readiness_level?: string | null;
  readiness_reason?: string | null;
  total_selected_samples?: number;
  reviewed_samples?: number;
  unreviewed_samples?: number;
  acceptable_count?: number;
  questionable_count?: number;
  rejected_count?: number;
  missing_artifact_samples?: number;
  stale_samples?: number;
  needs_followup_samples?: number;
  suspicious_visual_samples?: number;
  computed_at?: string | null;
  annotations_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  entry_summaries?: MrmsVisualReviewSampleEntrySummaryCompact[];
  verified_mrms: boolean;
  local_advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  no_external_notifications: boolean;
  candidate_ready_is_not_production_authorization: boolean;
};

export type MrmsVisualReviewSampleBootstrapCompact = {
  available?: boolean;
  bootstrap_status?: string | null;
  visual_readiness_level?: string | null;
  visual_readiness_reason?: string | null;
  visual_blockers?: string[];
  review_readiness_level?: string | null;
  chain_readiness_level?: string | null;
  preflight_not_run?: boolean;
  preflight_attempt_status?: string | null;
  preflight_level?: string | null;
  resolution_status?: string | null;
  remaining_blockers?: string[];
  annotations_seeded?: number | null;
  sample_set_entry_count?: number | null;
  next_commands?: string[];
  next_operator_step?: string | null;
  bootstrapped_at?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_sample_bootstrap_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  candidate_ready_is_not_production_authorization: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsVisualReviewSampleAnnotationUpsertRequest = {
  sample_key: string;
  status?: string;
  operator_notes?: string | null;
  reviewer_label?: string | null;
  issue_tags?: string[];
};

export type MrmsVisualReviewSampleAnnotationUpsertResponse = {
  verified_mrms: boolean;
  local_advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  annotation: {
    sample_key?: string;
    status?: string;
    operator_notes?: string | null;
  };
  compact: MrmsVisualReviewSampleReadinessCompact;
};

export type MrmsRenderCandidatePreflightEvidenceFoundCompact = {
  visual_review?: boolean;
  sample_set?: boolean;
  sample_readiness?: boolean;
  required_docs?: boolean;
};

export type MrmsRenderCandidatePreflightCompact = {
  available?: boolean;
  preflight_level?: string | null;
  preflight_reason?: string | null;
  blocking_items?: string[];
  warnings?: string[];
  computed_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  evidence_found?: MrmsRenderCandidatePreflightEvidenceFoundCompact | null;
  verified_mrms: boolean;
  local_advisory_preflight_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  no_external_notifications: boolean;
  candidate_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidateReviewReadinessCompact = {
  available?: boolean;
  chain_readiness_level?: string | null;
  overall_readiness_level?: string | null;
  review_chain_ready?: boolean;
  preflight_blocked?: boolean;
  preflight_candidate_ready?: boolean;
  gated_preflight_still_blocked?: boolean;
  blocking_items?: string[];
  warnings?: string[];
  next_operator_step?: string | null;
  suggested_commands?: string[];
  regeneration_recommended?: boolean;
  regeneration_reason?: string | null;
  regeneration_suggested_command?: string | null;
  computed_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_readiness_summary_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidatePreflightAttemptCompact = {
  available?: boolean;
  attempt_status?: string | null;
  attempted_at?: string | null;
  readiness_level?: string | null;
  review_chain_ready?: boolean;
  gate_open?: boolean;
  preflight_not_run?: boolean;
  preflight_level?: string | null;
  preflight_reason?: string | null;
  gate_reason?: string | null;
  blocking_items?: string[];
  warnings?: string[];
  suggested_commands?: string[];
  next_operator_step?: string | null;
  json_path?: string | null;
  preflight_json_path?: string | null;
  preflight_markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_preflight_attempt_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidatePreflightBlockersCompact = {
  available?: boolean;
  resolution_status?: string | null;
  blocker_category?: string | null;
  primary_blocker?: string | null;
  remaining_blockers?: string[];
  visual_blockers?: string[];
  readiness_level?: string | null;
  visual_readiness_level?: string | null;
  visual_readiness_reason?: string | null;
  preflight_attempt_status?: string | null;
  preflight_level?: string | null;
  preflight_not_run?: boolean;
  next_commands?: string[];
  next_operator_step?: string | null;
  resolved_at?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_blocker_report_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidateTrendHintChainBootstrapCompact = {
  available?: boolean;
  bootstrap_status?: string | null;
  trend_hint_chain_ready?: boolean;
  trend_hint_blockers?: string[];
  visual_blockers?: string[];
  rollup_status?: string | null;
  digest_status?: string | null;
  chain_readiness_level?: string | null;
  overall_readiness_level?: string | null;
  preflight_not_run?: boolean;
  preflight_attempt_status?: string | null;
  preflight_level?: string | null;
  resolution_status?: string | null;
  remaining_blockers?: string[];
  next_commands?: string[];
  next_operator_step?: string | null;
  bootstrapped_at?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_chain_bootstrap_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidateDryRunPlanCompact = {
  available?: boolean;
  plan_status?: string | null;
  plan_reason?: string | null;
  blocking_items?: string[];
  warnings?: string[];
  created_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  prerequisites?: string[];
  stop_conditions?: string[];
  expected_artifacts?: Array<{ path?: string; description?: string }>;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_advisory_dry_run_plan_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_execute_candidate_steps: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateGatedDryRunReviewCompact = {
  available?: boolean;
  review_status?: string | null;
  preflight_level?: string | null;
  preflight_reason?: string | null;
  preflight_blocking_items?: string[];
  dry_run_plan_skipped?: boolean;
  dry_run_plan_status?: string | null;
  dry_run_plan_reason?: string | null;
  dry_run_plan_blocking_items?: string[];
  resolution_status?: string | null;
  remaining_blockers?: string[];
  preflight_not_run?: boolean;
  preflight_candidate_ready?: boolean;
  next_commands?: string[];
  next_operator_step?: string | null;
  reviewed_at?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_gated_dry_run_review_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_execute_candidate_steps: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  dry_run_plan_ready_is_not_production_authorization: boolean;
  gated_preflight_ready_is_not_production_authorization: boolean;
};

export type MrmsRenderCandidateScaffoldCompact = {
  available?: boolean;
  scaffold_status?: string | null;
  scaffold_reason?: string | null;
  blocking_items?: string[];
  warnings?: string[];
  dry_run_mode?: boolean;
  execute_performed?: boolean;
  created_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  safety_gates?: Array<{ id?: string; passed?: boolean; message?: string }>;
  future_candidate_commands?: Array<{
    command?: string;
    phase?: string;
    executed_by_scaffold?: string;
    requires_opt_in?: string;
  }>;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_scaffold_only: boolean;
  disabled_by_default: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_execute_by_default: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxCompact = {
  available?: boolean;
  sandbox_status?: string | null;
  sandbox_reason?: string | null;
  blocking_items?: string[];
  warnings?: string[];
  sandbox_root?: string | null;
  expected_subdirectories?: string[];
  existing_subdirectories?: string[];
  missing_subdirectories?: string[];
  cleanup_candidates?: Array<{
    path?: string;
    category?: string;
    file_count?: number;
    total_bytes?: number;
    action?: string;
    delete_requires_flag?: string;
    note?: string;
  }>;
  cleanup_mode?: string;
  delete_performed?: boolean;
  safety_gates?: Array<{ id?: string; passed?: boolean; message?: string }>;
  isolation_status?: boolean | null;
  created_at?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_sandbox_only: boolean;
  disabled_by_default: boolean;
  cleanup_report_only_by_default: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxImportExportCompact = {
  available?: boolean;
  import_export_status?: string | null;
  import_export_reason?: string | null;
  schema_version?: string | null;
  blockers?: string[];
  warnings?: string[];
  included_reports?: Array<{ path?: string; kind?: string; format?: string }>;
  missing_inputs?: string[];
  latest_export_json_path?: string | null;
  latest_export_markdown_path?: string | null;
  latest_import_json_path?: string | null;
  latest_import_markdown_path?: string | null;
  comparison?: Record<string, unknown>;
  status_json_path?: string | null;
  status_markdown_path?: string | null;
  suggested_export_command?: string | null;
  suggested_import_export_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_import_export_only: boolean;
  metadata_report_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonHistoryCompact = {
  available?: boolean;
  history_status?: string | null;
  history_reason?: string | null;
  history_count?: number;
  blockers?: string[];
  warnings?: string[];
  schema_version?: string | null;
  latest_comparison_type?: string | null;
  latest_comparison_status?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string;
    comparison_type?: string;
    comparison_status?: string;
    changed_sandbox_status?: boolean;
  }>;
  latest_import_export_status?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  latest_json_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_comparison_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonTrendHintCompact = {
  available?: boolean;
  hint_status?: string | null;
  hint_reason?: string | null;
  trend?: string | null;
  trend_review_recommended?: boolean;
  history_count?: number | null;
  changed_count?: number | null;
  unchanged_count?: number | null;
  current_changed_streak?: number | null;
  recurring_signals?: string[];
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_trend_hint_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact = {
  available?: boolean;
  count?: number;
  acknowledgment_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  operator_name?: string | null;
  operator_initials?: string | null;
  note?: string | null;
  related_trend?: string | null;
  related_hint_status?: string | null;
  related_hint_reason?: string | null;
  related_trend_review_recommended?: boolean;
  acknowledged_trend_review?: boolean;
  trend_review_still_recommended?: boolean;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  note: string;
  acknowledged_trend_review?: boolean;
};

export type MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse = {
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_authorize_production_use: boolean;
  production_enabled: boolean;
  trend_review_still_recommended: boolean;
  acknowledgment: Record<string, unknown>;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact = {
  available?: boolean;
  rollup_status?: string | null;
  acknowledgment_status?: string | null;
  status_reason?: string | null;
  stale_acknowledgment?: boolean;
  trend?: string | null;
  hint_status?: string | null;
  trend_review_recommended?: boolean;
  acknowledgment_count?: number | null;
  latest_acknowledgment_id?: string | null;
  latest_acknowledgment_created_at?: string | null;
  latest_acknowledgment_operator?: string | null;
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_rollup_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact = {
  available?: boolean;
  history_count?: number;
  latest_rollup_status?: string | null;
  latest_acknowledgment_status?: string | null;
  latest_coverage_change?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string | null;
    rollup_status?: string | null;
    acknowledgment_status?: string | null;
    coverage_change?: string | null;
    stale_acknowledgment?: boolean;
  }>;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  prototype?: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact = {
  available?: boolean;
  hint_status?: string | null;
  hint_reason?: string | null;
  trend?: string | null;
  trend_review_recommended?: boolean;
  history_count?: number | null;
  worsened_count?: number | null;
  improved_count?: number | null;
  unchanged_count?: number | null;
  current_needs_ack_streak?: number | null;
  current_stale_streak?: number | null;
  latest_rollup_status?: string | null;
  recurring_signals?: string[];
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_trend_hint_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact = {
  available?: boolean;
  count?: number;
  acknowledgment_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  operator_name?: string | null;
  operator_initials?: string | null;
  note?: string | null;
  related_trend?: string | null;
  related_hint_status?: string | null;
  related_hint_reason?: string | null;
  related_trend_review_recommended?: boolean;
  acknowledged_trend_review?: boolean;
  latest_rollup_status?: string | null;
  trend_review_still_recommended?: boolean;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  note: string;
  acknowledged_trend_review?: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse = {
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_authorize_production_use: boolean;
  production_enabled: boolean;
  trend_review_still_recommended: boolean;
  acknowledgment: Record<string, unknown>;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact = {
  available?: boolean;
  rollup_status?: string | null;
  acknowledgment_status?: string | null;
  status_reason?: string | null;
  stale_acknowledgment?: boolean;
  trend?: string | null;
  hint_status?: string | null;
  trend_review_recommended?: boolean;
  acknowledgment_count?: number | null;
  latest_acknowledgment_id?: string | null;
  latest_acknowledgment_created_at?: string | null;
  latest_acknowledgment_operator?: string | null;
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_rollup_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact = {
  available?: boolean;
  history_count?: number;
  latest_rollup_status?: string | null;
  latest_acknowledgment_status?: string | null;
  latest_coverage_change?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string | null;
    rollup_status?: string | null;
    acknowledgment_status?: string | null;
    coverage_change?: string | null;
    stale_acknowledgment?: boolean;
  }>;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
  prototype?: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact = {
  available?: boolean;
  hint_status?: string | null;
  hint_reason?: string | null;
  trend?: string | null;
  trend_review_recommended?: boolean;
  history_count?: number | null;
  worsened_count?: number | null;
  improved_count?: number | null;
  unchanged_count?: number | null;
  current_needs_ack_streak?: number | null;
  current_stale_streak?: number | null;
  latest_rollup_status?: string | null;
  recurring_signals?: string[];
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_trend_hint_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact = {
  available?: boolean;
  count?: number;
  acknowledgment_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  operator_name?: string | null;
  operator_initials?: string | null;
  note?: string | null;
  related_trend?: string | null;
  related_hint_status?: string | null;
  related_hint_reason?: string | null;
  related_trend_review_recommended?: boolean;
  acknowledged_trend_review?: boolean;
  latest_rollup_status?: string | null;
  trend_review_still_recommended?: boolean;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact = {
  available?: boolean;
  rollup_status?: string | null;
  acknowledgment_status?: string | null;
  status_reason?: string | null;
  stale_acknowledgment?: boolean;
  trend?: string | null;
  hint_status?: string | null;
  trend_review_recommended?: boolean;
  acknowledgment_count?: number | null;
  latest_acknowledgment_id?: string | null;
  latest_acknowledgment_created_at?: string | null;
  latest_acknowledgment_operator?: string | null;
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_rollup_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact = {
  available?: boolean;
  history_count?: number;
  latest_rollup_status?: string | null;
  latest_acknowledgment_status?: string | null;
  latest_coverage_change?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string | null;
    rollup_status?: string | null;
    acknowledgment_status?: string | null;
    coverage_change?: string | null;
    stale_acknowledgment?: boolean;
  }>;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact = {
  available?: boolean;
  hint_status?: string | null;
  hint_reason?: string | null;
  trend?: string | null;
  trend_review_recommended?: boolean;
  history_count?: number | null;
  worsened_count?: number | null;
  improved_count?: number | null;
  unchanged_count?: number | null;
  current_needs_ack_streak?: number | null;
  current_stale_streak?: number | null;
  latest_rollup_status?: string | null;
  recurring_signals?: string[];
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_trend_hint_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintReviewAcknowledgmentCompact = {
  available?: boolean;
  count?: number;
  acknowledgment_id?: string | null;
  created_at?: string | null;
  operator?: string | null;
  operator_name?: string | null;
  operator_initials?: string | null;
  note?: string | null;
  related_trend?: string | null;
  related_hint_status?: string | null;
  related_hint_reason?: string | null;
  related_trend_review_recommended?: boolean;
  acknowledged_trend_review?: boolean;
  latest_rollup_status?: string | null;
  trend_review_still_recommended?: boolean;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  note: string;
  acknowledged_trend_review?: boolean;
};

export type MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse = {
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_authorize_production_use: boolean;
  production_enabled: boolean;
  trend_review_still_recommended: boolean;
  acknowledgment: Record<string, unknown>;
};

export type MrmsRenderCandidateTrendHintAckStatusCompact = {
  available?: boolean;
  rollup_status?: string | null;
  acknowledgment_status?: string | null;
  status_reason?: string | null;
  stale_acknowledgment?: boolean;
  trend?: string | null;
  hint_status?: string | null;
  trend_review_recommended?: boolean;
  acknowledgment_count?: number | null;
  latest_acknowledgment_id?: string | null;
  latest_acknowledgment_created_at?: string | null;
  latest_acknowledgment_operator?: string | null;
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_rollup_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintAckStatusHistoryCompact = {
  available?: boolean;
  history_count?: number;
  latest_rollup_status?: string | null;
  latest_acknowledgment_status?: string | null;
  latest_coverage_change?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string | null;
    rollup_status?: string | null;
    acknowledgment_status?: string | null;
    coverage_change?: string | null;
    stale_acknowledgment?: boolean;
  }>;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_status_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintReviewDigestCompact = {
  available?: boolean;
  digest_status?: string | null;
  digest_reason?: string | null;
  rollup_status?: string | null;
  acknowledgment_status?: string | null;
  history_count?: number | null;
  latest_coverage_change?: string | null;
  worsened_count?: number | null;
  improved_count?: number | null;
  trend_review_recommended?: boolean;
  stale_acknowledgment?: boolean;
  blockers?: string[];
  warnings?: string[];
  suggested_action?: string | null;
  suggested_command?: string | null;
  schema_version?: string | null;
  json_path?: string | null;
  markdown_path?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_digest_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintReviewDigestHistoryCompact = {
  available?: boolean;
  history_count?: number;
  latest_digest_status?: string | null;
  latest_rollup_status?: string | null;
  latest_coverage_change?: string | null;
  latest_recorded_at?: string | null;
  recent_entries?: Array<{
    recorded_at?: string | null;
    digest_status?: string | null;
    rollup_status?: string | null;
    coverage_change?: string | null;
  }>;
  json_path?: string | null;
  markdown_path?: string | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_digest_history_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateTrendHintReviewDigestDiffCompact = {
  available?: boolean;
  diff_status?: string | null;
  checked_at?: string | null;
  history_count?: number;
  changes?: Record<string, unknown> | null;
  suggested_command?: string | null;
  next_phase_recommendation?: string | null;
  verified_mrms: boolean;
  local_digest_diff_only: boolean;
  advisory_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_download_or_decode: boolean;
  does_not_create_production_tiles: boolean;
  does_not_serve_production_tiles: boolean;
  does_not_delete_by_default: boolean;
  binary_artifacts_included: boolean;
  no_external_notifications: boolean;
  does_not_authorize_production_use: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest = {
  operator_name?: string;
  operator_initials?: string;
  note: string;
  acknowledged_trend_review?: boolean;
};

export type MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse = {
  verified_mrms: boolean;
  local_acknowledgment_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  does_not_authorize_production_use: boolean;
  production_enabled: boolean;
  trend_review_still_recommended: boolean;
  acknowledgment: Record<string, unknown>;
};

export type OperatorWorkflowPresetsCompact = {
  available?: boolean;
  recommended_count?: number;
  presets?: OperatorWorkflowPresetCompact[];
  operator_workflow_preset_groups?: OperatorWorkflowPresetGroupCompact[];
  verified_mrms: boolean;
  local_workflow_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
};

export type OperatorReviewStatusCompact = {
  available?: boolean;
  created_at?: string | null;
  status_level?: string;
  status_reason?: string | null;
  top_recommended_action?: string | null;
  top_suggested_command?: string | null;
  review_session_recommended?: boolean;
  review_export_recommended?: boolean;
  digest_regeneration_recommended?: boolean;
  visual_review_regeneration_recommended?: boolean;
  visual_review_hint_reason?: string | null;
  evidence_trend?: string;
  latest_review_session_at?: string | null;
  latest_review_export_at?: string | null;
  latest_digest_at?: string | null;
  latest_visual_review_at?: string | null;
  latest_visual_review_path?: string | null;
  latest_visual_review_json_path?: string | null;
  latest_visual_review_markdown_path?: string | null;
  latest_visual_review_comparison_status?: string | null;
  visual_review_artifact_count?: number | null;
  visual_review_missing_artifact_count?: number | null;
  scheduled_visual_review?: ScheduledVisualReviewCompact | null;
  latest_export_diff_status?: string | null;
  latest_export_diff_trend?: string | null;
  open_attention_count?: number | null;
  active_guidance_count?: number;
  guidance_items?: OperatorGuidanceItem[];
  top_guidance_item?: OperatorGuidanceItem | null;
  runbook_path?: string | null;
  runbook_section?: string | null;
  suggested_action?: string | null;
  verified_mrms: boolean;
  local_status_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type ScheduledOperatorStatusCompact = {
  operator_status_requested: boolean;
  operator_status_generated: boolean;
  operator_status_level?: string | null;
  operator_status_reason?: string | null;
  operator_status_top_recommended_action?: string | null;
  operator_status_top_suggested_command?: string | null;
  operator_status_evidence_trend?: string | null;
  operator_status_elapsed_seconds?: number | null;
  operator_status_error?: string | null;
  verified_mrms: boolean;
  local_status_only: boolean;
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
  export_after_create?: boolean;
};

export type MrmsReviewSessionCreateResponse = {
  verified_mrms: boolean;
  local_review_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  production_enabled: boolean;
  review_session: Record<string, unknown>;
  export_after_create_requested?: boolean;
  export_generated?: boolean;
  export_path?: string | null;
  export_metadata_path?: string | null;
  export_error?: string | null;
  export_compact?: MrmsReviewSessionExportCompact | null;
};

export type MrmsReviewSessionExportDiffCompact = {
  available: boolean;
  overall_export_diff_status?: string | null;
  compared_at?: string | null;
  latest_export_created_at?: string | null;
  baseline_export_created_at?: string | null;
  session_changed: boolean;
  open_attention_count_change?: { baseline?: number; latest?: number } | null;
  improvements?: string[];
  regressions?: string[];
  history_count?: number;
  verified_mrms: boolean;
  local_export_diff_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionExportDiffTrendCompact = {
  available: boolean;
  total_diffs?: number;
  latest_status?: string | null;
  latest_at?: string | null;
  last_worsened_at?: string | null;
  last_improved_at?: string | null;
  last_mixed_at?: string | null;
  last_unchanged_at?: string | null;
  worsened_count?: number;
  improved_count?: number;
  mixed_count?: number;
  unchanged_count?: number;
  no_baseline_count?: number;
  current_worsened_streak?: number;
  current_improved_streak?: number;
  current_mixed_or_worsened_streak?: number;
  longest_worsened_streak?: number;
  longest_mixed_or_worsened_streak?: number;
  trend?: string;
  window_size?: number;
  history_count?: number;
  suggested_next_action?: string | null;
  verified_mrms: boolean;
  local_trend_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionExportDiffTrendHintCompact = {
  available?: boolean;
  review_trend_regeneration_recommended: boolean;
  reason?: string | null;
  suggested_command?: string | null;
  trend?: string;
  latest_export_diff_status?: string | null;
  current_mixed_or_worsened_streak?: number;
  current_worsened_streak?: number;
  latest_review_session_id?: string | null;
  latest_export_session_id?: string | null;
  export_is_stale?: boolean;
  latest_session_at?: string | null;
  latest_export_at?: string | null;
  digest_regeneration_recommended?: boolean;
  session_summary_available?: boolean;
  verified_mrms: boolean;
  local_hint_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionExportDiffHistoryEntry = {
  created_at?: string | null;
  overall_export_diff_status?: string | null;
  latest_session_id?: string | null;
  baseline_session_id?: string | null;
  session_changed: boolean;
  open_attention_count_change?: { baseline?: number; latest?: number } | null;
  comparison_status_change?: { baseline?: string | null; latest?: string | null } | null;
  escalation_level_change?: { baseline?: string | null; latest?: string | null } | null;
  digest_regeneration_recommended_change?: { baseline?: boolean; latest?: boolean } | null;
  improvements_count?: number;
  regressions_count?: number;
  verified_mrms: boolean;
  local_export_diff_history_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  prototype: boolean;
};

export type MrmsReviewSessionExportDiffHistoryCompact = {
  available: boolean;
  count: number;
  max_entries?: number;
  latest_status?: string | null;
  latest_created_at?: string | null;
  latest?: MrmsReviewSessionExportDiffHistoryEntry | null;
  recent?: MrmsReviewSessionExportDiffHistoryEntry[];
  verified_mrms: boolean;
  local_export_diff_history_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications?: boolean;
  prototype: boolean;
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
  review_export_trend_hint?: MrmsReviewSessionExportDiffTrendHintCompact | null;
  verified_mrms: boolean;
  local_export_only: boolean;
  does_not_clear_alerts: boolean;
  does_not_enable_production: boolean;
  no_external_notifications: boolean;
  prototype: boolean;
};

export type ScheduledVisualReviewCompact = {
  visual_review_requested: boolean;
  visual_review_generated: boolean;
  visual_review_path?: string | null;
  visual_review_markdown_path?: string | null;
  visual_review_history_count?: number | null;
  visual_review_reason?: string | null;
  visual_review_elapsed_seconds?: number | null;
  visual_review_error?: string | null;
  verified_mrms: boolean;
  local_visual_review_only: boolean;
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
  scheduled_visual_review?: ScheduledVisualReviewCompact | null;
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
  mrms_review_session_export_diff?: MrmsReviewSessionExportDiffCompact | null;
  mrms_review_session_export_diff_trend?: MrmsReviewSessionExportDiffTrendCompact | null;
  mrms_review_session_export_diff_trend_hint?: MrmsReviewSessionExportDiffTrendHintCompact | null;
  mrms_review_session_export_diff_history?: MrmsReviewSessionExportDiffHistoryCompact | null;
  review_export_regeneration_hint?: ReviewExportRegenerationHintCompact | null;
  operator_review_status?: OperatorReviewStatusCompact | null;
  operator_workflow_presets?: OperatorWorkflowPresetsCompact | null;
  mrms_visual_review?: MrmsVisualReviewCompact | null;
  mrms_visual_review_comparison?: MrmsVisualReviewComparisonCompact | null;
  mrms_visual_review_hint?: MrmsVisualReviewHintCompact | null;
  mrms_visual_review_sample_set?: MrmsVisualReviewSampleSetCompact | null;
  mrms_visual_review_sample_readiness?: MrmsVisualReviewSampleReadinessCompact | null;
  mrms_visual_review_sample_bootstrap?: MrmsVisualReviewSampleBootstrapCompact | null;
  mrms_render_candidate_preflight?: MrmsRenderCandidatePreflightCompact | null;
  mrms_render_candidate_review_readiness?: MrmsRenderCandidateReviewReadinessCompact | null;
  mrms_render_candidate_preflight_attempt?: MrmsRenderCandidatePreflightAttemptCompact | null;
  mrms_render_candidate_preflight_blockers?: MrmsRenderCandidatePreflightBlockersCompact | null;
  mrms_render_candidate_trend_hint_chain_bootstrap?: MrmsRenderCandidateTrendHintChainBootstrapCompact | null;
  mrms_render_candidate_dry_run_plan?: MrmsRenderCandidateDryRunPlanCompact | null;
  mrms_render_candidate_gated_dry_run_review?: MrmsRenderCandidateGatedDryRunReviewCompact | null;
  mrms_render_candidate_scaffold?: MrmsRenderCandidateScaffoldCompact | null;
  mrms_render_candidate_sandbox?: MrmsRenderCandidateSandboxCompact | null;
  mrms_render_candidate_sandbox_import_export?: MrmsRenderCandidateSandboxImportExportCompact | null;
  mrms_render_candidate_sandbox_comparison_history?: MrmsRenderCandidateSandboxComparisonHistoryCompact | null;
  mrms_render_candidate_sandbox_comparison_trend_hint?: MrmsRenderCandidateSandboxComparisonTrendHintCompact | null;
  mrms_render_candidate_sandbox_comparison_review_acknowledgment?: MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_history?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact | null;
  mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint?: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact | null;
  mrms_render_candidate_trend_hint_review_acknowledgment?: MrmsRenderCandidateTrendHintReviewAcknowledgmentCompact | null;
  mrms_render_candidate_trend_hint_ack_status?: MrmsRenderCandidateTrendHintAckStatusCompact | null;
  mrms_render_candidate_trend_hint_ack_status_history?: MrmsRenderCandidateTrendHintAckStatusHistoryCompact | null;
  mrms_render_candidate_trend_hint_review_digest?: MrmsRenderCandidateTrendHintReviewDigestCompact | null;
  mrms_render_candidate_trend_hint_review_digest_history?: MrmsRenderCandidateTrendHintReviewDigestHistoryCompact | null;
  mrms_render_candidate_trend_hint_review_digest_diff?: MrmsRenderCandidateTrendHintReviewDigestDiffCompact | null;
  scheduled_operator_status?: ScheduledOperatorStatusCompact | null;
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

export async function submitVisualReviewSampleSet(
  payload: MrmsVisualReviewSampleSetCreateRequest = {},
): Promise<
  { ok: true; data: MrmsVisualReviewSampleSetCreateResponse } | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-visual-review/sample-set`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let error = `Visual review sample set failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) {
          error = body.detail;
        }
      } catch {
        // ignore parse errors
      }
      return { ok: false, error };
    }
    const data = (await response.json()) as MrmsVisualReviewSampleSetCreateResponse;
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function submitVisualReviewSampleAnnotation(
  payload: MrmsVisualReviewSampleAnnotationUpsertRequest,
): Promise<
  | { ok: true; data: MrmsVisualReviewSampleAnnotationUpsertResponse }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-visual-review/sample-set/annotations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let error = `Sample annotation failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) {
          error = body.detail;
        }
      } catch {
        // ignore parse errors
      }
      return { ok: false, error };
    }
    const data = (await response.json()) as MrmsVisualReviewSampleAnnotationUpsertResponse;
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshVisualReviewSampleReadiness(): Promise<
  { ok: true; data: { compact: MrmsVisualReviewSampleReadinessCompact } } | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-visual-review/sample-set/readiness`, {
      method: 'POST',
    });
    if (!response.ok) {
      return { ok: false, error: `Sample readiness refresh failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsVisualReviewSampleReadinessCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshVisualReviewSampleBootstrap(): Promise<
  | { ok: true; data: { compact: MrmsVisualReviewSampleBootstrapCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-visual-review/sample-set/bootstrap`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Visual sample set bootstrap failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsVisualReviewSampleBootstrapCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateReviewReadiness(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateReviewReadinessCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/review-readiness`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Candidate review readiness refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateReviewReadinessCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidatePreflightBlockers(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidatePreflightBlockersCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/preflight-blockers`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Preflight blocker resolution failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidatePreflightBlockersCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateTrendHintChainBootstrap(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateTrendHintChainBootstrapCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Trend-hint chain bootstrap failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateTrendHintChainBootstrapCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidatePreflightAttempt(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidatePreflightAttemptCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/preflight-attempt`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Gated preflight attempt failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidatePreflightAttemptCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidatePreflight(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidatePreflightCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-render-candidate/preflight`, {
      method: 'POST',
    });
    if (!response.ok) {
      return { ok: false, error: `Render candidate preflight refresh failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidatePreflightCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateDryRunPlan(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateDryRunPlanCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-render-candidate/dry-run-plan`, {
      method: 'POST',
    });
    if (!response.ok) {
      return { ok: false, error: `Render candidate dry-run plan refresh failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateDryRunPlanCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateGatedDryRunReview(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateGatedDryRunReviewCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/gated-dry-run-review`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Gated dry-run plan review failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateGatedDryRunReviewCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateScaffold(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateScaffoldCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-render-candidate/scaffold`, {
      method: 'POST',
    });
    if (!response.ok) {
      return { ok: false, error: `Render candidate scaffold refresh failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateScaffoldCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandbox(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/api/validation/mrms-render-candidate/sandbox`, {
      method: 'POST',
    });
    if (!response.ok) {
      return { ok: false, error: `Render candidate sandbox refresh failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateSandboxCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function exportRenderCandidateSandbox(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxImportExportCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/export`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return { ok: false, error: `Render candidate sandbox export failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateSandboxImportExportCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function importRenderCandidateSandbox(importJsonPath?: string): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxImportExportCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/import`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importJsonPath ? { import_json_path: importJsonPath } : {}),
      },
    );
    if (!response.ok) {
      return { ok: false, error: `Render candidate sandbox import failed (${response.status})` };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateSandboxImportExportCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonHistory(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxComparisonHistoryCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison history refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateSandboxComparisonHistoryCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonTrendHint(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxComparisonTrendHintCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison trend hint refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as { compact: MrmsRenderCandidateSandboxComparisonTrendHintCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function submitSandboxComparisonReviewAcknowledgment(
  payload: MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateRequest,
): Promise<
  | { ok: true; data: MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      let error = `Sandbox comparison review acknowledgment failed (${response.status})`;
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
    const data =
      (await response.json()) as MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Sandbox comparison review acknowledgment request failed' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatus(): Promise<
  | { ok: true; data: { compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact } }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison acknowledgment status refresh failed (${response.status})`,
      };
    }
    const data =
      (await response.json()) as { compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusHistory(): Promise<
  | {
      ok: true;
      data: { compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison acknowledgment status history refresh failed (${response.status})`,
      };
    }
    const data =
      (await response.json()) as {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact;
      };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint(): Promise<
  | {
      ok: true;
      data: { compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-hint`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison acknowledgment status trend hint refresh failed (${response.status})`,
      };
    }
    const data =
      (await response.json()) as {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact;
      };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function submitAckStatusTrendReviewAcknowledgment(
  payload: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
): Promise<
  | {
      ok: true;
      data: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse;
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      let error = `Status trend review acknowledgment failed (${response.status})`;
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
    const data =
      (await response.json()) as MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Status trend review acknowledgment request failed' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison status trend review acknowledgment status refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison status trend review acknowledgment status history refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-hint`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison status trend review acknowledgment status trend hint refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison trend review acknowledgment status trend hint refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function submitTrendHintReviewAcknowledgment(
  payload: MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateRequest,
): Promise<
  | {
      ok: true;
      data: MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse;
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-review-acknowledgments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      let error = `Trend-hint review acknowledgment failed (${response.status})`;
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
    const data = (await response.json()) as MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse;
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Trend-hint review acknowledgment request failed' };
  }
}

export async function refreshRenderCandidateTrendHintAckStatus(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateTrendHintAckStatusCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Candidate trend-hint acknowledgment status rollup refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateTrendHintAckStatusCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateTrendHintAckStatusHistory(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateTrendHintAckStatusHistoryCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Candidate trend-hint acknowledgment status history refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateTrendHintAckStatusHistoryCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateTrendHintReviewDigest(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateTrendHintReviewDigestCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Candidate trend-hint review digest refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateTrendHintReviewDigestCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateTrendHintReviewDigestHistory(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateTrendHintReviewDigestHistoryCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Candidate trend-hint review digest history refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateTrendHintReviewDigestHistoryCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function submitAckStatusTrendReviewAckStatusTrendReviewAcknowledgment(
  payload: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
): Promise<
  | {
      ok: true;
      data: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse;
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      let error = `Trend review acknowledgment status trend review acknowledgment failed (${response.status})`;
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
    const data =
      (await response.json()) as MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse;
    return { ok: true, data };
  } catch {
    return {
      ok: false,
      error: 'Trend review acknowledgment status trend review acknowledgment request failed',
    };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison trend review acknowledgment status rollup refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory(): Promise<
  | {
      ok: true;
      data: {
        compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact;
      };
    }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(
      `${API_BASE}/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/history`,
      { method: 'POST' },
    );
    if (!response.ok) {
      return {
        ok: false,
        error: `Render candidate sandbox comparison trend review acknowledgment status history refresh failed (${response.status})`,
      };
    }
    const data = (await response.json()) as {
      compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact;
    };
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Unknown error' };
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
