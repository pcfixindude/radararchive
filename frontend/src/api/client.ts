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
