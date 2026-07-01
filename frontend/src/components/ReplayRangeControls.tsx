import type { ReplayRangeState } from '../hooks/useReplayRange';
import PlaybackExportPanel from './PlaybackExportPanel';
import type { PlaybackExportState } from './playbackExport';

export type { PlaybackExportState } from './playbackExport';

export default function ReplayRangeControls({
  disabled = false,
  range,
  exportState,
  inspectTimestamp,
  onInspectFrame,
}: {
  disabled?: boolean;
  range: ReplayRangeState;
  exportState: PlaybackExportState;
  inspectTimestamp?: string;
  onInspectFrame?: (timestamp: string) => void;
}) {
  const loopDisabled = disabled || !range.hasCompleteRange;

  return (
    <section className="panel replay-range-panel" aria-label="Playback range">
      <h2>Range & loop</h2>
      <div className="controls replay-range-buttons">
        <button type="button" disabled={disabled} onClick={range.setStartFromSelected}>
          Set start
        </button>
        <button type="button" disabled={disabled} onClick={range.setEndFromSelected}>
          Set end
        </button>
        <button
          type="button"
          disabled={loopDisabled}
          className={range.loopActive ? 'replay-range-loop--active' : undefined}
          onClick={range.toggleLoopRange}
          aria-pressed={range.loopActive}
        >
          {range.loopActive ? 'Loop range on' : 'Loop range'}
        </button>
        <button
          type="button"
          disabled={disabled || (!range.rangeStart && !range.rangeEnd)}
          onClick={range.clearRange}
        >
          Clear range
        </button>
      </div>
      {range.rangeLabel ? (
        <p className="replay-range-meta">
          Range: <code>{range.rangeLabel}</code>
        </p>
      ) : (
        <p className="replay-range-meta replay-range-meta--empty">
          No range selected — use Set start / Set end on the current frame.
        </p>
      )}
      {range.hasCompleteRange && range.positionLabel ? (
        <p className={`replay-range-meta replay-range-position${range.selectedInRange === false ? ' replay-range-position--outside' : ''}`}>
          Position: {range.positionLabel}
          {range.selectedInRange === false ? ' (outside range)' : ''}
        </p>
      ) : null}
      {range.loopActive ? (
        <p className="replay-range-meta replay-range-loop-status">Loop active — playback wraps inside range.</p>
      ) : range.loopRange && !range.hasCompleteRange ? (
        <p className="replay-range-meta replay-range-loop-status replay-range-loop-status--warn">
          Loop needs a complete start/end range.
        </p>
      ) : null}
      {range.rangeNotice ? (
        <p className="replay-range-notice" role="status">
          {range.rangeNotice}
        </p>
      ) : null}
      <PlaybackExportPanel
        disabled={disabled}
        hasCompleteRange={range.hasCompleteRange}
        rangeLabel={range.rangeLabel}
        exportState={exportState}
        inspectTimestamp={inspectTimestamp}
        onInspectFrame={onInspectFrame}
      />
    </section>
  );
}
