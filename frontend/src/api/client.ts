const API_BASE = 'http://127.0.0.1:8000';

export type Layer = {
  id: string;
  name: string;
  type: string;
  available: boolean;
  source?: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchLayers(): Promise<Layer[]> {
  return getJson<Layer[]>('/api/layers');
}

export function fetchTimes(layer: string): Promise<string[]> {
  return getJson<string[]>(`/api/times?layer=${encodeURIComponent(layer)}`);
}

export function fetchLatest(layer: string): Promise<{ layer: string; timestamp: string | null }> {
  return getJson(`/api/latest?layer=${encodeURIComponent(layer)}`);
}
