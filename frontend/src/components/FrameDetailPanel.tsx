import DecodedOverlayQualityDetails from './DecodedOverlayQualityDetails';
import {
  formatPathHint,
  formatQualityCheckSummary,
  pickPrimaryFrameDetail,
  readinessSummaryClass,
  readinessSummaryLabel,
} from './frameDetail';
import { formatFrameTimestamp } from './frameCatalog';
import type { FrameQualityReport } from '../api/client';

export default function FrameDetailPanel({
  disabled = false,
  inspectTimestamp,
  report,
  loading = false,
  error = '',
  onRefresh,
}: {
  disabled?: boolean;
  inspectTimestamp: string;
  report: FrameQualityReport | null;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
}) {
  const detail = pickPrimaryFrameDetail(report);

  return (
    <section className="panel frame-detail-panel" aria-label="Frame detail">
      <div className="frame-detail-header">
        <h2>Frame detail</h2>
        {onRefresh ? (
          <button type="button" className="frame-detail-refresh" disabled={disabled || loading} onClick={onRefresh}>
            Refresh
          </button>
        ) : null}
      </div>
      <p className="frame-detail-intro">
        Per-frame cache/decode/quality breakdown with suggested remediation commands. Status only — no
        ingest or decode work.
      </p>
      <p className="frame-detail-meta">
        Inspecting <code>{formatFrameTimestamp(inspectTimestamp)}</code>
      </p>
      {loading ? <p className="frame-detail-meta">Loading frame quality…</p> : null}
      {error ? <p className="frame-detail-error">{error}</p> : null}
      {!loading && !error && report && !detail ? (
        <p className="frame-detail-meta frame-detail-meta--empty">No quality data for this timestamp.</p>
      ) : null}
      {detail ? (
        <div className="frame-detail-body">
          <p className={`frame-detail-readiness ${readinessSummaryClass(detail.readiness_summary)}`}>
            {readinessSummaryLabel(detail.readiness_summary)}
            {detail.sync_message ? ` — ${detail.sync_message}` : ''}
          </p>
          <dl className="frame-detail-grid">
            <div>
              <dt>Cache</dt>
              <dd>
                <code>{detail.cache_state}</code>
                {detail.cache_ready ? ' · ready' : ''}
              </dd>
            </div>
            <div>
              <dt>Decode</dt>
              <dd>
                <code>{detail.decode_status ?? detail.frame_status ?? 'unknown'}</code>
                {detail.decode_ready ? ' · ready' : ''}
              </dd>
            </div>
            <div>
              <dt>Preview</dt>
              <dd>{detail.path_hints.preview_available ? 'available' : 'missing'}</dd>
            </div>
            <div>
              <dt>Quality</dt>
              <dd>
                <code>{detail.frame_quality.status}</code>
                {' · '}
                {formatQualityCheckSummary(detail.frame_quality.checks)}
              </dd>
            </div>
          </dl>
          <div className="frame-detail-paths">
            <h3>Path hints</h3>
            <ul>
              <li>
                Cache dir: <code>{formatPathHint(detail.path_hints.cache_dir)}</code>
              </li>
              <li>
                Manifest:{' '}
                <code>{formatPathHint(detail.path_hints.manifest_path ?? (detail.path_hints.manifest_present ? 'present' : null))}</code>
              </li>
              <li>
                Decode output: <code>{formatPathHint(detail.path_hints.decode_output_dir)}</code>
              </li>
              <li>
                Raw GRIB2: <code>{formatPathHint(detail.path_hints.raw_path)}</code>
              </li>
              {detail.path_hints.preview_paths && detail.path_hints.preview_paths.length > 0 ? (
                <li>
                  Preview: <code>{formatPathHint(detail.path_hints.preview_paths[0])}</code>
                </li>
              ) : null}
            </ul>
          </div>
          {detail.suggested_commands.length > 0 ? (
            <div className="frame-detail-commands">
              <h3>Suggested commands</h3>
              <ul>
                {detail.suggested_commands.map((command) => (
                  <li key={command}>
                    <code>{command}</code>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <DecodedOverlayQualityDetails frameQuality={detail.frame_quality} />
        </div>
      ) : null}
    </section>
  );
}
