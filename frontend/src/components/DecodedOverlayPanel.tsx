import type { DecodedOverlayInfo } from '../api/client';

function statusClass(status: string): string {
  if (status === 'decoded_prototype') {
    return 'decoded-overlay-badge--decoded';
  }
  if (status === 'missing') {
    return 'decoded-overlay-badge--missing';
  }
  return 'decoded-overlay-badge--placeholder';
}

export default function DecodedOverlayPanel({
  overlay,
  onRefresh,
  refreshing,
}: {
  overlay: DecodedOverlayInfo | null;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const status = overlay?.overlay_status ?? 'missing';
  const available = overlay?.available ?? false;

  return (
    <section className="decoded-overlay-panel" aria-label="Decoded preview overlay">
      <div className="decoded-overlay-header">
        <h2>Local decoded preview</h2>
        <button type="button" className="decoded-overlay-refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <p className={`decoded-overlay-badge ${statusClass(status)}`}>
        {available ? status.replace(/_/g, ' ') : 'missing'}
      </p>
      <ul className="decoded-overlay-labels">
        {(overlay?.labels ?? ['Local dev prototype', 'NOT verified MRMS']).map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
      {overlay?.georef_mode ? (
        <p className="decoded-overlay-meta">
          Georef: <code>{overlay.georef_mode}</code>
          {overlay.geo_accurate ? ' (geo-accurate)' : ' (prototype placement)'}
        </p>
      ) : null}
      {overlay?.ran_at ? (
        <p className="decoded-overlay-meta">
          Pipeline ran: <code>{overlay.ran_at}</code>
        </p>
      ) : null}
      {overlay?.stale_hint ? <p className="decoded-overlay-warn">{overlay.stale_hint}</p> : null}
      {!available ? (
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
