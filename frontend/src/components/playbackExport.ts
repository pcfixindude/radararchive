export type PlaybackExportFrame = {
  timestamp: string;
  index: number;
  cache_state: string;
  cache_ready: boolean;
  decode_ready: boolean;
  decode_status?: string | null;
  preview_paths: string[];
  preview_path_count: number;
};

export type PlaybackExportManifest = {
  clip_id: string;
  export_kind: string;
  layer_id: string;
  range_start: string;
  range_end: string;
  range_order_adjusted: boolean;
  loop_suggested: boolean;
  frame_count: number;
  cache_ready_count: number;
  decode_ready_count: number;
  missing_cache_count: number;
  cold_count: number;
  failed_count: number;
  frames: PlaybackExportFrame[];
  exported_at: string;
  status: string;
  verified_mrms: boolean;
  local_dev_only: boolean;
  prototype: boolean;
  production_tile_serving: boolean;
};

export type PlaybackExportState = {
  manifest: PlaybackExportManifest | null;
  loading: boolean;
  error: string;
  copyNotice: string;
  exportClip: () => Promise<void>;
  clearExport: () => void;
  markCopied: (message?: string) => void;
};

export function formatClipSummary(manifest: PlaybackExportManifest): string {
  const decodeLabel =
    manifest.decode_ready_count === manifest.frame_count
      ? 'all decoded'
      : `${manifest.decode_ready_count}/${manifest.frame_count} decoded`;
  const cacheLabel =
    manifest.cache_ready_count === manifest.frame_count
      ? 'all cached'
      : `${manifest.cache_ready_count}/${manifest.frame_count} cached`;
  return `${manifest.frame_count} frames · ${cacheLabel} · ${decodeLabel}`;
}

export function buildClipDownloadFilename(manifest: PlaybackExportManifest): string {
  const startToken = manifest.range_start.replace(/[:.-]/g, '');
  const endToken = manifest.range_end.replace(/[:.-]/g, '');
  return `playback-clip_${startToken}_${endToken}.json`;
}

export function downloadClipManifest(manifest: PlaybackExportManifest): void {
  const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = buildClipDownloadFilename(manifest);
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function copyClipManifest(manifest: PlaybackExportManifest): Promise<void> {
  await navigator.clipboard.writeText(JSON.stringify(manifest, null, 2));
}
