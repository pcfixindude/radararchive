import type { DecodedOverlayInfo } from '../api/client';
import { playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';

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
  onRefresh,
  refreshing,
}: {
  overlay: DecodedOverlayInfo | null;
  selectedTime: string;
  playbackFrameStatus?: PlaybackFrameStatus;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const status = overlay?.overlay_status ?? 'missing';
  const syncStatus = overlay?.sync_status ?? 'no_selection';

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
      {overlay?.sync_message ? <p className="decoded-overlay-warn">{overlay.sync_message}</p> : null}
      {overlay?.stale_hint && overlay.sync_status !== 'mismatch' && overlay.sync_status !== 'matched' ? (
        <p className="decoded-overlay-warn">{overlay.stale_hint}</p>
      ) : null}
      {overlay?.sync_status === 'no_local_candidate' ? (
        <p className="decoded-overlay-hint">
          No local MRMS file for this timestamp. Try <code>MRMS_SOURCE_MODE=real make download-mrms</code> then Refresh.
        </p>
      ) : null}
      {!overlay?.artifact_available ? (
        <p className="decoded-overlay-hint">
          Run <code>make decode-retry</code> or <code>make mrms-local-render-pipeline</code>, then Refresh.
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
