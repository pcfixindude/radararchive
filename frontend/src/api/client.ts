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
  verified_mrms: boolean;
  prototype: boolean;
};

export type ValidationLatest = {
  prototype: boolean;
  verified_mrms: boolean;
  production_rendering_enabled: boolean;
  validation: Record<string, unknown> | null;
  benchmark: Record<string, unknown> | null;
  queue_benchmark: Record<string, unknown> | null;
  scheduled_validation: Record<string, unknown> | null;
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
  validation_failures_count?: number;
  validation_failures_recent?: ValidationFailureCompact[];
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
