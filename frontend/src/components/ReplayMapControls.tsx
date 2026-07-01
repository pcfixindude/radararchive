import {
  hasValidOverlayBounds,
  type ReplayDisplayState,
} from './replayDisplay';

export default function ReplayMapControls({
  display,
  onChange,
  overlayBounds,
  onFitToBounds,
  overlayAvailable,
}: {
  display: ReplayDisplayState;
  onChange: (patch: Partial<ReplayDisplayState>) => void;
  overlayBounds?: number[] | null;
  onFitToBounds: () => void;
  overlayAvailable: boolean;
}) {
  const canFit = overlayAvailable && hasValidOverlayBounds(overlayBounds);

  return (
    <section className="panel replay-map-controls" aria-label="Replay map controls">
      <h2>Map & overlay</h2>
      <label className="replay-toggle">
        <input
          type="checkbox"
          checked={display.showDecodedOverlay}
          onChange={(event) => onChange({ showDecodedOverlay: event.target.checked })}
          disabled={!overlayAvailable}
        />
        Show decoded overlay
      </label>
      {!overlayAvailable ? (
        <p className="replay-control-hint">No decoded overlay for the selected frame.</p>
      ) : null}
      <label className="replay-toggle">
        <input
          type="checkbox"
          checked={display.showBoundsOutline}
          onChange={(event) => onChange({ showBoundsOutline: event.target.checked })}
          disabled={!display.showDecodedOverlay || !overlayAvailable}
        />
        Show bounds outline
      </label>
      <label className="replay-toggle">
        <input
          type="checkbox"
          checked={display.showGeorefDebug}
          onChange={(event) => onChange({ showGeorefDebug: event.target.checked })}
        />
        Show georef debug in panel
      </label>
      <label className="replay-toggle">
        <input
          type="checkbox"
          checked={display.showFrameQualityDetails}
          onChange={(event) => onChange({ showFrameQualityDetails: event.target.checked })}
        />
        Show frame quality details
      </label>
      <button
        type="button"
        className="replay-fit-bounds"
        disabled={!canFit || !display.showDecodedOverlay}
        onClick={onFitToBounds}
        title={canFit ? 'Pan/zoom map to overlay bounds' : 'Needs valid overlay bounds'}
      >
        Fit map to overlay bounds
      </button>
      {!canFit ? (
        <p className="replay-control-hint">Fit disabled until a frame has valid overlay bounds.</p>
      ) : null}
    </section>
  );
}
