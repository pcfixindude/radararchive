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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
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

export function fetchLayers(): Promise<Layer[]> {
  return getJson<Layer[]>('/api/layers');
}

export function fetchTimes(layer: string, processedOnly = false): Promise<string[]> {
  const params = new URLSearchParams({ layer });
  if (processedOnly) {
    params.set('processed_only', 'true');
  }
  return getJson<string[]>(`/api/times?${params.toString()}`);
}

export function fetchLatest(layer: string): Promise<{ layer: string; timestamp: string | null }> {
  return getJson(`/api/latest?layer=${encodeURIComponent(layer)}`);
}

export function tileUrl(layer: string, timestamp: string, z = 0, x = 0, y = 0): string {
  const encoded = encodeURIComponent(timestamp);
  return `${API_BASE}/tiles/${encodeURIComponent(layer)}/${encoded}/${z}/${x}/${y}.png`;
}

/** MapLibre raster template with {z}/{x}/{y} placeholders. */
export function tileUrlTemplate(layer: string, timestamp: string): string {
  const encoded = encodeURIComponent(timestamp);
  return `${API_BASE}/tiles/${encodeURIComponent(layer)}/${encoded}/{z}/{x}/{y}.png`;
}

export async function tilesAvailable(layer: string, timestamp: string): Promise<boolean> {
  if (!timestamp) {
    return false;
  }
  try {
    const response = await fetch(tileUrl(layer, timestamp), { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
}
