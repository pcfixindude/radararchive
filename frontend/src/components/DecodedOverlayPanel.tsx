import type { DecodedOverlayInfo, PlaybackCacheStatus } from '../api/client';
import { cacheStateLabel, playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';
import DecodedOverlayGeorefDebug from './DecodedOverlayGeorefDebug';
import DecodedOverlayQualityDetails from './DecodedOverlayQualityDetails';
import { selectedFrameSummary, suggestNextCommand } from './replayDisplay';

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
  showGeorefDebug = false,
  showFrameQualityDetails = false,
  onRefresh,
  refreshing,
}: {
  overlay: DecodedOverlayInfo | null;
  selectedTime: string;
  playbackFrameStatus?: PlaybackFrameStatus;
  cacheStatus?: PlaybackCacheStatus | null;
  showGeorefDebug?: boolean;
  showFrameQualityDetails?: boolean;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const status = overlay?.overlay_status ?? 'missing';
  const syncStatus = overlay?.sync_status ?? 'no_selection';
  const selectedCacheState = cacheStatus?.frames.find((frame) => frame.timestamp === selectedTime)?.cache_state;
  const frameQuality = overlay?.frame_quality;
  const nextCommand = suggestNextCommand(overlay, cacheStatus);
  const frameSummary = selectedFrameSummary(overlay, selectedTime, selectedCacheState);

  return (
    <section className="decoded-overlay-panel" aria-label="Decoded preview overlay">
      <div className="decoded-overlay-header">
        <h2>Local decoded preview</h2>
        <button type="button" className="decoded-overlay-refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <p className="selected-frame-summary">{frameSummary}</p>
      {nextCommand ? (
        <p className="decoded-overlay-hint">
          Next: <code>{nextCommand}</code>
        </p>
      ) : null}
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
      {selectedCacheState ? (
        <p className="decoded-overlay-meta">
          This frame cache: <code>{cacheStateLabel(selectedCacheState)}</code>
          {!cacheStatus?.playback_ready ? ' — cold window' : ' — warm window'}
        </p>
      ) : null}
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
      {cacheStatus && !cacheStatus.playback_ready ? (
        <p className="decoded-overlay-meta">
          Playback cache: <code>{cacheStatus.warmed_count} ready</code> / {cacheStatus.frame_count}
        </p>
      ) : null}
      {overlay?.frame_status ? (
        <p className="decoded-overlay-meta">
          Frame: <code>{overlay.frame_status.replace(/_/g, ' ')}</code>
        </p>
      ) : null}
      <p className="decoded-overlay-meta">
        Tile mode: <code>{overlay?.tile_mode ?? 'single_image'}</code>
        {overlay?.tile_count ? ` (${overlay.tile_count} tiles)` : ''}
      </p>
      {showGeorefDebug && overlay ? <DecodedOverlayGeorefDebug overlay={overlay} /> : null}
      {showFrameQualityDetails && frameQuality ? (
        <DecodedOverlayQualityDetails frameQuality={frameQuality} />
      ) : frameQuality ? (
        <p className={`frame-quality-summary frame-quality--${frameQuality.status}`}>
          Quality: <code>{frameQuality.status}</code> — enable details in Map & overlay
        </p>
      ) : null}
      {overlay?.sync_message ? <p className="decoded-overlay-warn">{overlay.sync_message}</p> : null}
      {overlay?.stale_hint && overlay.sync_status !== 'mismatch' && overlay.sync_status !== 'matched' ? (
        <p className="decoded-overlay-warn">{overlay.stale_hint}</p>
      ) : null}
      {overlay?.sync_status === 'no_local_candidate' ? (
        <p className="decoded-overlay-hint">
          Download frames with{' '}
          <code>make mrms-bulk-local-ingest ARGS=&apos;--real --limit 8&apos;</code>
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
