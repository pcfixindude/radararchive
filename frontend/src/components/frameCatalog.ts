import type { FrameCacheState } from '../hooks/framePlayback';
import { cacheStateLabel } from '../hooks/framePlayback';

export type FrameCatalogItem = {
  timestamp: string;
  cache_state: FrameCacheState | string;
  cache_ready: boolean;
  decode_ready: boolean;
  decode_status?: string | null;
};

export type FrameCatalogStatus = {
  layer_id: string;
  frame_count: number;
  cache_ready_count: number;
  decode_ready_count: number;
  missing_count: number;
  cold_count: number;
  failed_count: number;
  window_source: string;
  frames: FrameCatalogItem[];
  playback_ready: boolean;
};

export function filterFrameCatalog(
  frames: FrameCatalogItem[],
  filterText: string,
): FrameCatalogItem[] {
  const query = filterText.trim().toLowerCase();
  if (!query) {
    return frames;
  }
  return frames.filter((frame) => frame.timestamp.toLowerCase().includes(query));
}

export function frameReadinessLabel(frame: FrameCatalogItem): string {
  const cache = cacheStateLabel(frame.cache_state);
  const decode = frame.decode_ready ? 'decode ok' : 'decode missing';
  return `${cache} · ${decode}`;
}

export function frameReadinessClass(frame: FrameCatalogItem): string {
  if (frame.cache_ready && frame.decode_ready) {
    return 'frame-catalog-row--ready';
  }
  if (frame.cache_state === 'failed') {
    return 'frame-catalog-row--failed';
  }
  if (frame.cache_state === 'missing_raw') {
    return 'frame-catalog-row--missing';
  }
  return 'frame-catalog-row--partial';
}

export function formatFrameTimestamp(timestamp: string): string {
  if (!timestamp) {
    return '—';
  }
  const parsed = Date.parse(timestamp);
  if (Number.isNaN(parsed)) {
    return timestamp;
  }
  return new Date(parsed).toISOString().replace('T', ' ').replace('.000Z', ' UTC');
}
