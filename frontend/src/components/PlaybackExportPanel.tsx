import {
  copyClipManifest,
  downloadClipManifest,
  formatClipSummary,
} from './playbackExport';
import type { PlaybackExportState } from './playbackExport';

export default function PlaybackExportPanel({
  disabled = false,
  hasCompleteRange,
  rangeLabel,
  exportState,
}: {
  disabled?: boolean;
  hasCompleteRange: boolean;
  rangeLabel: string | null;
  exportState: PlaybackExportState;
}) {
  const { manifest, loading, error, copyNotice, exportClip, clearExport, markCopied } = exportState;

  const handleCopy = async () => {
    if (!manifest) {
      return;
    }
    try {
      await copyClipManifest(manifest);
      markCopied();
    } catch {
      markCopied('Copy failed — use Download instead.');
    }
  };

  const handleDownload = () => {
    if (!manifest) {
      return;
    }
    downloadClipManifest(manifest);
  };

  return (
    <div className="playback-export" aria-label="Playback clip export">
      <div className="playback-export-header">
        <h3>Export clip</h3>
        <button
          type="button"
          className="playback-export-action"
          disabled={disabled || !hasCompleteRange || loading}
          onClick={() => void exportClip()}
        >
          {loading ? 'Exporting…' : 'Export clip'}
        </button>
      </div>
      <p className="playback-export-intro">
        Save a local clip manifest for the active replay range — frame list, cache/decode status, and
        preview paths. Status only; no ingest or decode work.
      </p>
      {!hasCompleteRange ? (
        <p className="playback-export-meta playback-export-meta--empty">
          Set a complete start/end range to export a clip.
        </p>
      ) : null}
      {hasCompleteRange && rangeLabel ? (
        <p className="playback-export-meta">
          Range: <code>{rangeLabel}</code>
        </p>
      ) : null}
      {error ? <p className="playback-export-error">{error}</p> : null}
      {manifest ? (
        <div className="playback-export-summary">
          <p className="playback-export-meta">
            <strong>{manifest.clip_id}</strong> — {formatClipSummary(manifest)}
          </p>
          <p className="playback-export-meta">
            Exported {manifest.exported_at}
            {manifest.loop_suggested ? ' · loop range' : ''}
            {manifest.range_order_adjusted ? ' · order adjusted' : ''}
          </p>
          <div className="playback-export-buttons">
            <button type="button" className="playback-export-action" onClick={() => void handleCopy()}>
              Copy JSON
            </button>
            <button type="button" className="playback-export-action" onClick={handleDownload}>
              Download JSON
            </button>
            <button type="button" className="playback-export-action playback-export-action--muted" onClick={clearExport}>
              Clear
            </button>
          </div>
          {copyNotice ? (
            <p className="playback-export-notice" role="status">
              {copyNotice}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
