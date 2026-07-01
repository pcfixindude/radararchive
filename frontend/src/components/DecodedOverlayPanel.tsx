import type { DecodedOverlayInfo, FrameQualityStatus, PlaybackCacheStatus } from '../api/client';
import { cacheStateLabel, playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';

function qualityStatusClass(status?: string): string {
  switch (status) {
    case 'ok':
      return 'frame-quality--ok';
    case 'warning':
      return 'frame-quality--warning';
    case 'error':
      return 'frame-quality--error';
    default:
      return 'frame-quality--unavailable';
  }
}

function qualityCheckClass(status: string): string {
  return `frame-quality-check--${status}`;
}

function statusClass(status: string): string {
  if (status === 'decoded_prototype') {
    return 'decoded-overlay-badge--decoded';
  }
  if (status === 'missing') {
    return 'decoded-overlay-badge--missing';
  }
  return 'decoded-overlay-badge--placeholder';
}

function syncClass(syncStatus?: string): string {
  if (syncStatus === 'matched') {
    return 'decoded-overlay-badge--decoded';
  }
  if (syncStatus === 'mismatch' || syncStatus === 'stale_latest_fallback') {
    return 'decoded-overlay-badge--placeholder';
  }
  if (syncStatus === 'no_local_candidate' || syncStatus === 'decode_failed') {
    return 'decoded-overlay-badge--missing';
  }
  return 'decoded-overlay-badge--missing';
}

export default function DecodedOverlayPanel({
  overlay,
  selectedTime,
  playbackFrameStatus = 'idle',
  cacheStatus = null,
  onRefresh,
  refreshing,
}: {
  overlay: DecodedOverlayInfo | null;
  selectedTime: string;
  playbackFrameStatus?: PlaybackFrameStatus;
  cacheStatus?: PlaybackCacheStatus | null;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const status = overlay?.overlay_status ?? 'missing';
  const syncStatus = overlay?.sync_status ?? 'no_selection';
  const selectedCacheState = cacheStatus?.frames.find((frame) => frame.timestamp === selectedTime)?.cache_state;
  const frameQuality: FrameQualityStatus | null | undefined = overlay?.frame_quality;

  return (
    <section className="decoded-overlay-panel" aria-label="Decoded preview overlay">
      <div className="decoded-overlay-header">
        <h2>Local decoded preview</h2>
        <button type="button" className="decoded-overlay-refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <p className={`decoded-overlay-badge ${statusClass(status)}`}>
        {status.replace(/_/g, ' ')}
      </p>
      <p className={`decoded-overlay-badge ${syncClass(syncStatus)}`}>
        sync: {syncStatus.replace(/_/g, ' ')}
      </p>
      <p className="decoded-overlay-meta">
        Playback: <code>{playbackStatusLabel(playbackFrameStatus)}</code>
        {refreshing ? ' (loading)' : ''}
      </p>
      <ul className="decoded-overlay-labels">
        {(overlay?.labels ?? ['Local dev prototype', 'NOT verified MRMS']).map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
      <p className="decoded-overlay-meta">
        Selected time: <code>{selectedTime || '—'}</code>
      </p>
      <p className="decoded-overlay-meta">
        Decoded candidate: <code>{overlay?.candidate_timestamp ?? '—'}</code>
      </p>
      {overlay?.nearest_raw_timestamp ? (
        <p className="decoded-overlay-meta">
          Nearest local raw: <code>{overlay.nearest_raw_timestamp}</code>
        </p>
      ) : null}
      {overlay?.nearest_decoded_timestamp ? (
        <p className="decoded-overlay-meta">
          Nearest decoded: <code>{overlay.nearest_decoded_timestamp}</code>
        </p>
      ) : null}
      {cacheStatus ? (
        <p className="decoded-overlay-meta">
          Window cache: <code>{cacheStatus.warmed_count} ready</code>,{' '}
          <code>{cacheStatus.cold_count} cold</code>,{' '}
          <code>{cacheStatus.missing_count} missing</code>
          {cacheStatus.cache_warm_ran_at ? (
            <> (warm {cacheStatus.cache_warm_ran_at})</>
          ) : null}
        </p>
      ) : null}
      {selectedCacheState ? (
        <p className="decoded-overlay-meta">
          Frame cache: <code>{cacheStateLabel(selectedCacheState)}</code>
        </p>
      ) : null}
      {!cacheStatus?.playback_ready && cacheStatus?.next_commands?.length ? (
        <p className="decoded-overlay-hint">
          Cold cache — run <code>{cacheStatus.next_commands[0]}</code>
        </p>
      ) : null}
      {overlay?.playback_ready || cacheStatus?.playback_ready ? (
        <p className="decoded-overlay-meta">
          Playback cache: <code>ready ({overlay?.cache_warm_matched ?? cacheStatus?.warmed_count}/{overlay?.cache_warm_considered ?? cacheStatus?.frame_count} warmed)</code>
        </p>
      ) : overlay?.cache_warm_available ? (
        <p className="decoded-overlay-meta">
          Playback cache: <code>{overlay.cache_warm_status ?? 'unknown'}</code>
          {overlay.cache_warm_matched ? ` (${overlay.cache_warm_matched} warmed)` : ''}
        </p>
      ) : null}
      {overlay?.frame_status ? (
        <p className="decoded-overlay-meta">
          Frame: <code>{overlay.frame_status.replace(/_/g, ' ')}</code>
        </p>
      ) : null}
      <p className="decoded-overlay-meta">
        Render mode: <code>{overlay?.render_mode ?? '—'}</code>
      </p>
      <p className="decoded-overlay-meta">
        Color scale: <code>{overlay?.color_scale_mode ?? '—'}</code>
      </p>
      <p className="decoded-overlay-meta">
        Tile mode: <code>{overlay?.tile_mode ?? 'single_image'}</code>
        {overlay?.tile_count ? ` (${overlay.tile_count} tiles, z≤${overlay.tile_max_z ?? 0})` : ''}
      </p>
      {overlay?.georef_mode ? (
        <p className="decoded-overlay-meta">
          Georef: <code>{overlay.georef_quality ?? overlay.georef_mode}</code>
          {overlay.geo_accurate ? ' (geo-accurate)' : ' (prototype placement)'}
        </p>
      ) : null}
      {overlay?.bounds_source ? (
        <p className="decoded-overlay-meta">
          Bounds source: <code>{overlay.bounds_source}</code>
        </p>
      ) : null}
      {overlay?.bounds?.length === 4 ? (
        <p className="decoded-overlay-meta">
          Bounds:{' '}
          <code>
            {overlay.bounds.map((value) => value.toFixed(2)).join(', ')}
          </code>
        </p>
      ) : null}
      {!overlay?.geo_accurate ? (
        <p className="decoded-overlay-warn">Prototype georef — not verified MRMS alignment.</p>
      ) : null}
      {overlay?.georef_notes?.length ? (
        <p className="decoded-overlay-meta decoded-overlay-georef-note">{overlay.georef_notes[0]}</p>
      ) : null}
      {frameQuality ? (
        <div className="frame-quality-panel" aria-label="Frame quality checks">
          <p className={`frame-quality-summary ${qualityStatusClass(frameQuality.status)}`}>
            Frame quality: <code>{frameQuality.status}</code>
            {frameQuality.diagnostic_only ? ' (diagnostic)' : ''}
          </p>
          {frameQuality.measured?.manifest_width != null && frameQuality.measured?.manifest_height != null ? (
            <p className="decoded-overlay-meta">
              Grid: <code>{String(frameQuality.measured.manifest_width)}×{String(frameQuality.measured.manifest_height)}</code>
              {frameQuality.measured.manifest_value_min != null ? (
                <> min/max <code>{String(frameQuality.measured.manifest_value_min)} / {String(frameQuality.measured.manifest_value_max)}</code></>
              ) : null}
            </p>
          ) : null}
          <ul className="frame-quality-checks">
            {frameQuality.checks.map((check) => (
              <li key={check.name} className={qualityCheckClass(check.status)}>
                <code>{check.name}</code>: {check.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {overlay?.sync_message ? <p className="decoded-overlay-warn">{overlay.sync_message}</p> : null}
      {overlay?.stale_hint && overlay.sync_status !== 'mismatch' && overlay.sync_status !== 'matched' ? (
        <p className="decoded-overlay-warn">{overlay.stale_hint}</p>
      ) : null}
      {overlay?.sync_status === 'no_local_candidate' ? (
        <p className="decoded-overlay-hint">
          No local MRMS file for this timestamp. Try{' '}
          <code>make mrms-bulk-local-ingest ARGS=&apos;--real --limit 8&apos;</code> then Refresh.
        </p>
      ) : null}
      {!overlay?.artifact_available ? (
        <p className="decoded-overlay-hint">
          Run <code>make mrms-bulk-local-ingest ARGS=&apos;--real --limit 8&apos;</code>, then{' '}
          <code>make mrms-warm-frame-cache</code>, then Refresh.
        </p>
      ) : null}
      <ul className="decoded-overlay-commands">
        {(overlay?.refresh_commands ?? ['make decode-retry']).map((cmd) => (
          <li key={cmd}>
            <code>{cmd}</code>
          </li>
        ))}
      </ul>
    </section>
  );
}
