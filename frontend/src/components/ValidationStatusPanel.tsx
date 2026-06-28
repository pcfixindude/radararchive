import { useState } from 'react';
import { fetchValidationLatest, type ValidationSummary } from '../api/client';

function yesNo(value: boolean): string {
  return value ? 'yes' : 'no';
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  return value.replace('T', ' ').replace('Z', ' UTC');
}

export default function ValidationStatusPanel({
  summary,
  onRefresh,
  refreshing = false,
}: {
  summary: ValidationSummary | null;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const [detailsJson, setDetailsJson] = useState<string | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  async function toggleDetails() {
    if (showDetails) {
      setShowDetails(false);
      return;
    }
    setDetailsLoading(true);
    const latest = await fetchValidationLatest();
    setDetailsJson(latest ? JSON.stringify(latest, null, 2) : 'Details unavailable');
    setDetailsLoading(false);
    setShowDetails(true);
  }

  if (!summary) {
    return (
      <section className="panel validation-panel">
        <div className="validation-header">
          <h2>Dev Validation</h2>
          {onRefresh ? (
            <button type="button" className="validation-refresh" onClick={onRefresh} disabled={refreshing}>
              Refresh
            </button>
          ) : null}
        </div>
        <p className="validation-meta">Validation summary unavailable (run make validate-real-mrms).</p>
        <p className="validation-warn">Prototype only — not verified real MRMS.</p>
      </section>
    );
  }

  const validation = summary.validation;
  const benchmark = summary.benchmark;
  const queueBenchmark = summary.queue_benchmark ?? null;
  const scheduled = summary.scheduled_validation ?? null;
  const scheduledSteps = scheduled?.steps ?? [];
  const recentFailures = summary.validation_failures_recent ?? [];
  const frameSummaries = summary.frame_summaries ?? [];
  const validationAlert = summary.validation_alert ?? null;
  const groupedCauses = summary.grouped_failure_causes ?? validationAlert?.grouped_failure_causes ?? [];
  const queue = summary.render_queue;
  const catalog = summary.catalog;
  const history = summary.validation_history ?? [];

  return (
    <section className="panel validation-panel">
      <div className="validation-header">
        <h2>Dev Validation</h2>
        <div className="validation-header-actions">
          <button type="button" className="validation-refresh" onClick={toggleDetails} disabled={detailsLoading}>
            {detailsLoading ? 'Loading…' : showDetails ? 'Hide details' : 'Show details'}
          </button>
          {onRefresh ? (
            <button type="button" className="validation-refresh" onClick={onRefresh} disabled={refreshing}>
              {refreshing ? 'Refreshing…' : 'Refresh'}
            </button>
          ) : null}
        </div>
      </div>
      <p className="validation-warn">Experimental pipeline — not verified real MRMS.</p>
      {validationAlert ? (
        <>
          <p
            className={
              validationAlert.operator_attention_needed
                ? 'validation-warn'
                : 'validation-meta'
            }
          >
            Operator attention: {validationAlert.operator_attention_needed ? 'needed' : 'not needed'} — alert{' '}
            {validationAlert.status ?? 'ok'}
          </p>
          <p className="validation-meta">
            Alert updated: {formatTimestamp(validationAlert.updated_at)} — latest run{' '}
            {formatTimestamp(validationAlert.latest_run_at)}
          </p>
          <p className="validation-meta">
            Alert counts: {validationAlert.failure_count ?? 0} failures, {validationAlert.warning_count ?? 0} warnings
          </p>
          {validationAlert.suggested_next_action ? (
            <p className="validation-meta">Suggested next action: {validationAlert.suggested_next_action}</p>
          ) : null}
        </>
      ) : null}
      {groupedCauses.length > 0 ? (
        <>
          <p className="validation-meta">Grouped failure causes (prototype diagnostics):</p>
          <ul className="validation-history-list">
            {groupedCauses.map((cause, index) => (
              <li key={`${cause.step}-${cause.cause}-${index}`} className="validation-meta">
                {cause.step} — {cause.cause} ×{cause.count}
                {cause.message ? `: ${cause.message}` : ''}
                {cause.latest_logged_at ? ` (${formatTimestamp(cause.latest_logged_at)})` : ''}
              </li>
            ))}
          </ul>
        </>
      ) : null}
      <p className="validation-meta">Placeholder default: {yesNo(summary.placeholder_default)}</p>
      <p className="validation-meta">
        Production rendering: {summary.production_rendering_enabled ? 'enabled (flag on)' : 'disabled (default)'}
      </p>
      <p className="validation-meta">verified_mrms: {yesNo(summary.verified_mrms)}</p>
      <p className="validation-meta">Decoder: {summary.decoder_available ? 'available' : 'not installed'}</p>
      <p className="validation-meta">
        Catalog: {catalog.total_frames} frames ({catalog.mrms_discovered_frames} MRMS discovered)
      </p>
      <p className="validation-meta">
        Queue: queued {queue.queued}, running {queue.running}, succeeded {queue.succeeded}, failed {queue.failed}
      </p>
      {scheduled ? (
        <p className="validation-meta">
          Scheduled run ({formatTimestamp(scheduled.ran_at)}):{' '}
          {scheduled.success ? 'success' : 'failed'} (exit {scheduled.exit_code}), steps {scheduled.steps_ok}/
          {scheduled.steps_ok + scheduled.steps_failed}, decoded {scheduled.batch_decoded_count}, queue jobs{' '}
          {scheduled.queue_jobs_succeeded} ok
          {scheduled.elapsed_seconds != null ? ` (${scheduled.elapsed_seconds.toFixed(1)}s)` : ''}
        </p>
      ) : (
        <p className="validation-meta">No scheduled validation yet — run make scheduled-validation.</p>
      )}
      {scheduledSteps.length > 0 ? (
        <ul className="validation-history-list">
          {scheduledSteps.map((step, index) => (
            <li key={`${step.name ?? 'step'}-${index}`} className="validation-meta">
              {step.name ?? '—'}: {step.status ?? '—'}
              {step.elapsed_seconds != null ? ` (${step.elapsed_seconds.toFixed(2)}s)` : ''}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="validation-meta">
        Recent failures logged: {summary.validation_failures_count ?? 0}
      </p>
      {recentFailures.length > 0 ? (
        <ul className="validation-history-list">
          {recentFailures.map((failure, index) => (
            <li key={`${failure.logged_at ?? 'fail'}-${index}`} className="validation-meta">
              {formatTimestamp(failure.logged_at)} — {failure.phase ?? '—'}
              {failure.step ? `/${failure.step}` : ''}: {failure.error_message ?? 'warning'}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="validation-meta">Validation history: {summary.validation_history_count} saved</p>
      {history.length > 0 ? (
        <ul className="validation-history-list">
          {history.map((entry, index) => (
            <li key={`${entry.validated_at ?? 'entry'}-${index}`} className="validation-meta">
              {formatTimestamp(entry.validated_at)} — {entry.source_mode ?? '—'}
              {entry.batch ? ` batch ${entry.effective_frame_count ?? entry.requested_frame_count ?? '?'}` : ''}: decoded{' '}
              {entry.decoded_count}
              {entry.elapsed_seconds != null ? ` (${entry.elapsed_seconds.toFixed(1)}s)` : ''}
            </li>
          ))}
        </ul>
      ) : null}
      {validation ? (
        <>
          <p className="validation-meta">
            Last validation ({validation.source_mode ?? '—'}
            {validation.batch ? `, batch ${validation.effective_frame_count ?? validation.requested_frame_count ?? '?'}` : ''}
            ): discovered {validation.discovered_count}, downloaded {validation.downloaded_count}, decoded{' '}
            {validation.decoded_count}
          </p>
          {validation.elapsed_seconds != null ? (
            <p className="validation-meta">Elapsed: {validation.elapsed_seconds.toFixed(2)}s</p>
          ) : null}
          <p className="validation-meta">
            Jobs enqueued {validation.render_jobs_enqueued}, processed {validation.worker_jobs_processed}
          </p>
        </>
      ) : (
        <p className="validation-meta">No validation report yet — run make validate-real-mrms-batch.</p>
      )}
      {frameSummaries.length > 0 ? (
        <ul className="validation-history-list">
          {frameSummaries.map((frame, index) => (
            <li key={`${frame.timestamp ?? 'frame'}-${index}`} className="validation-meta">
              {formatTimestamp(frame.timestamp)} — {frame.decode_status ?? '—'}: planned {frame.tiles_planned}, written{' '}
              {frame.tiles_written}
              {frame.render_job_id != null ? ` (job ${frame.render_job_id})` : ''}
            </li>
          ))}
        </ul>
      ) : null}
      {benchmark ? (
        <p className="validation-meta">
          Stage benchmark: tiles {benchmark.tiles_written}/{benchmark.tiles_planned}, build{' '}
          {benchmark.tile_build_elapsed_seconds.toFixed(2)}s, zoom {benchmark.min_zoom}–{benchmark.max_zoom}
        </p>
      ) : null}
      {queueBenchmark ? (
        <>
          <p className="validation-meta">
            Queue benchmark ({formatTimestamp(queueBenchmark.benchmarked_at)}): jobs {queueBenchmark.jobs_succeeded}/
            {queueBenchmark.jobs_processed} ok, zoom {queueBenchmark.min_zoom}–{queueBenchmark.max_zoom}, tiles{' '}
            {queueBenchmark.total_tiles_written} written
            {queueBenchmark.total_elapsed_seconds != null
              ? ` (${queueBenchmark.total_elapsed_seconds.toFixed(2)}s)`
              : ''}
          </p>
          {queueBenchmark.job_summaries.length > 0 ? (
            <ul className="validation-history-list">
              {queueBenchmark.job_summaries.map((job, index) => (
                <li key={`${job.job_id ?? 'dry'}-${index}`} className="validation-meta">
                  {job.job_id != null ? `job ${job.job_id}` : 'planned'} ({formatTimestamp(job.timestamp)}):{' '}
                  {job.status ?? '—'}, {job.decode_status ?? '—'}, planned {job.tiles_planned ?? 0}, tiles{' '}
                  {job.tiles_written}
                  {job.elapsed_seconds != null ? ` (${job.elapsed_seconds.toFixed(2)}s)` : ''}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : (
        <p className="validation-meta">No queue benchmark yet — run make benchmark-render-queue.</p>
      )}
      {showDetails && detailsJson ? (
        <pre className="validation-details-json">{detailsJson}</pre>
      ) : null}
    </section>
  );
}
