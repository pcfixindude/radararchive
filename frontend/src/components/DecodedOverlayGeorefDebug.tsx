import type { DecodedOverlayInfo } from '../api/client';

export default function DecodedOverlayGeorefDebug({ overlay }: { overlay: DecodedOverlayInfo }) {
  return (
    <>
      {overlay.georef_mode ? (
        <p className="decoded-overlay-meta">
          Georef: <code>{overlay.georef_quality ?? overlay.georef_mode}</code>
          {overlay.geo_accurate ? ' (geo-accurate)' : ' (prototype placement)'}
        </p>
      ) : null}
      {overlay.bounds_source ? (
        <p className="decoded-overlay-meta">
          Bounds source: <code>{overlay.bounds_source}</code>
        </p>
      ) : null}
      {overlay.bounds?.length === 4 ? (
        <p className="decoded-overlay-meta">
          Bounds:{' '}
          <code>{overlay.bounds.map((value) => value.toFixed(2)).join(', ')}</code>
        </p>
      ) : null}
      {!overlay.geo_accurate ? (
        <p className="decoded-overlay-warn">Prototype georef — not verified MRMS alignment.</p>
      ) : null}
      {overlay.georef_notes?.map((note) => (
        <p key={note} className="decoded-overlay-meta decoded-overlay-georef-note">
          {note}
        </p>
      ))}
    </>
  );
}
