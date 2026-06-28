import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  fetchProofReviewData,
  fetchValidationLatest,
  submitSignoff,
  type MrmsProofHistory,
  type MrmsProofRegressionHistory,
  type MrmsSignoffsList,
  type ValidationSummary,
} from '../api/client';

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
  const [showProofReview, setShowProofReview] = useState(false);
  const [detailsJson, setDetailsJson] = useState<string | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [proofHistory, setProofHistory] = useState<MrmsProofHistory | null>(null);
  const [regressionHistory, setRegressionHistory] = useState<MrmsProofRegressionHistory | null>(null);
  const [signoffsList, setSignoffsList] = useState<MrmsSignoffsList | null>(null);
  const [proofReviewLoading, setProofReviewLoading] = useState(false);
  const [signoffOperator, setSignoffOperator] = useState('');
  const [signoffNotes, setSignoffNotes] = useState('');
  const [signoffLimitations, setSignoffLimitations] = useState('');
  const [signoffAcceptedLimitations, setSignoffAcceptedLimitations] = useState(false);
  const [signoffSubmitting, setSignoffSubmitting] = useState(false);
  const [signoffMessage, setSignoffMessage] = useState<string | null>(null);
  const [signoffError, setSignoffError] = useState<string | null>(null);

  const loadProofReview = useCallback(async () => {
    setProofReviewLoading(true);
    try {
      const data = await fetchProofReviewData();
      setProofHistory(data.proofHistory);
      setRegressionHistory(data.regressionHistory);
      setSignoffsList(data.signoffs);
    } finally {
      setProofReviewLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProofReview();
  }, [loadProofReview]);

  async function handleRefresh() {
    if (onRefresh) {
      await onRefresh();
    }
    await loadProofReview();
  }

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

  async function handleSignoffSubmit(event: FormEvent) {
    event.preventDefault();
    setSignoffMessage(null);
    setSignoffError(null);
    const limitationsText = signoffAcceptedLimitations
      ? signoffLimitations.trim() || 'Accepted known prototype limitations (local sign-off only).'
      : signoffLimitations.trim();
    setSignoffSubmitting(true);
    const result = await submitSignoff({
      operator_initials: signoffOperator.trim() || undefined,
      operator_notes: signoffNotes.trim() || undefined,
      accepted_limitations: limitationsText || undefined,
    });
    setSignoffSubmitting(false);
    if (!result.ok) {
      setSignoffError(result.error);
      return;
    }
    setSignoffMessage('Local sign-off recorded — does not verify MRMS or enable production rendering.');
    setSignoffOperator('');
    setSignoffNotes('');
    setSignoffLimitations('');
    setSignoffAcceptedLimitations(false);
    await loadProofReview();
    if (onRefresh) {
      await onRefresh();
    }
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
  const mrmsProof = summary.mrms_proof ?? null;
  const proofCounts = mrmsProof?.criteria_counts;
  const proofRegression = summary.mrms_proof_regression ?? null;
  const signoffSummary = summary.mrms_signoff ?? null;
  const proofBundle = summary.mrms_proof_bundle ?? null;
  const proofBundleDiff = summary.mrms_proof_bundle_diff ?? null;
  const operatorHandoff = summary.operator_handoff ?? null;
  const runbookReferences = summary.runbook_references ?? [];
  const scheduledProofStep = scheduled?.proof_step ?? null;
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
            <button type="button" className="validation-refresh" onClick={() => void handleRefresh()} disabled={refreshing || proofReviewLoading}>
              {refreshing || proofReviewLoading ? 'Refreshing…' : 'Refresh'}
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
      {mrmsProof ? (
        <>
          <p className="validation-warn">
            Proof report draft — not verified MRMS; operator review required.
          </p>
          <p className="validation-meta">
            Proof status: {mrmsProof.overall_status ?? 'not_started'} — frames evaluated{' '}
            {mrmsProof.frame_count ?? 0}
            {mrmsProof.generated_at ? ` (${formatTimestamp(mrmsProof.generated_at)})` : ''}
          </p>
          {proofCounts ? (
            <p className="validation-meta">
              Criteria — passed {proofCounts.passed ?? 0}, failed {proofCounts.failed ?? 0}, warning{' '}
              {proofCounts.warning ?? 0}, skipped {proofCounts.skipped ?? 0}
            </p>
          ) : null}
          <p className="validation-meta">verified_mrms: {yesNo(mrmsProof.verified_mrms ?? false)}</p>
        </>
      ) : (
        <p className="validation-meta">No proof report yet — run make mrms-proof-report.</p>
      )}
      {proofRegression ? (
        <>
          <p className={proofRegression.regression_detected ? 'validation-warn' : 'validation-meta'}>
            Proof regression: {proofRegression.regression_status ?? 'inconclusive'}
            {proofRegression.regression_detected ? ' — operator attention needed' : ''}
          </p>
          <p className="validation-meta">
            Regression findings: {proofRegression.regression_count ?? 0}
            {proofRegression.checked_at ? ` (${formatTimestamp(proofRegression.checked_at)})` : ''}
          </p>
        </>
      ) : null}
      {signoffSummary ? (
        <p className="validation-meta">
          Local sign-off only ({signoffSummary.signoff_count ?? 0} recorded) — latest{' '}
          {formatTimestamp(signoffSummary.latest_signoff_at)} — does not enable production rendering — not verified
          MRMS
          {signoffSummary.proof_regression_still_active
            ? ' — proof regression still active after sign-off'
            : ''}
        </p>
      ) : null}
      {validationAlert?.proof_regression_still_active ? (
        <p className="validation-warn">
          Proof regression remains active after sign-off — evidence must improve before alert clears.
        </p>
      ) : null}
      <section className="validation-proof-bundle">
        <p className="validation-meta">Proof bundle (local evidence only — does not verify MRMS)</p>
        {proofBundle?.available ? (
          <p className="validation-meta">
            Latest bundle {formatTimestamp(proofBundle.created_at)} — {proofBundle.file_count ?? 0} files
            {proofBundle.zip_path ? ` — ${proofBundle.zip_path}` : ''}
            {proofBundle.bundle_folder ? ` (folder: ${proofBundle.bundle_folder})` : ''}
          </p>
        ) : (
          <p className="validation-meta">No proof bundle yet — run make mrms-proof-bundle.</p>
        )}
        <p className="validation-meta">
          Export does not enable production rendering — verified_mrms: {yesNo(summary.verified_mrms)}
        </p>
      </section>
      <section className="validation-proof-bundle-diff">
        <p className="validation-meta">Proof bundle diff / handoff (local review only — does not verify MRMS)</p>
        {proofBundleDiff?.available ? (
          <p className="validation-meta">
            Diff status: {proofBundleDiff.overall_diff_status ?? 'unknown'} — evidence changes{' '}
            {proofBundleDiff.evidence_changes_count ?? 0}
            {proofBundleDiff.checked_at ? ` (${formatTimestamp(proofBundleDiff.checked_at)})` : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No diff report yet — run make mrms-proof-bundle twice, then make mrms-proof-bundle-diff.
          </p>
        )}
        {operatorHandoff?.available ? (
          <p className="validation-meta">
            Handoff checklist {formatTimestamp(operatorHandoff.created_at)}
            {operatorHandoff.markdown_path ? ` — ${operatorHandoff.markdown_path}` : ''}
          </p>
        ) : (
          <p className="validation-meta">No handoff checklist yet — run make mrms-operator-handoff.</p>
        )}
        <p className="validation-meta">
          Diff/handoff does not enable production rendering — verified_mrms: {yesNo(summary.verified_mrms)}
        </p>
      </section>
      {runbookReferences.length > 0 ? (
        <section className="validation-runbook-links">
          <p className="validation-meta">Operator runbook references (repo docs):</p>
          <ul className="validation-history-list">
            {runbookReferences.map((ref) => (
              <li key={ref.path} className="validation-meta">
                {ref.title} — <code>{ref.path}</code>
                {ref.anchor ? `#${ref.anchor}` : ''}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className="validation-header-actions" style={{ marginTop: '0.5rem' }}>
        <button
          type="button"
          className="validation-refresh"
          onClick={() => setShowProofReview((value) => !value)}
        >
          {showProofReview ? 'Hide proof review' : 'Show proof review'}
        </button>
      </div>
      {showProofReview ? (
        <section className="validation-proof-review">
          <p className="validation-warn">Proof review draft — not verified MRMS; local sign-off only.</p>
          <p className="validation-meta">
            Proof history ({proofHistory?.count ?? 0} saved) — latest{' '}
            {formatTimestamp(proofHistory?.latest?.generated_at)}
          </p>
          {(proofHistory?.entries ?? []).length > 0 ? (
            <ul className="validation-history-list">
              {proofHistory?.entries.map((entry, index) => (
                <li key={`${entry.generated_at ?? 'proof'}-${index}`} className="validation-meta">
                  {formatTimestamp(entry.generated_at)} — {entry.overall_status} — frames {entry.frame_count}
                  {entry.criteria_counts
                    ? ` (p${entry.criteria_counts.passed}/f${entry.criteria_counts.failed}/w${entry.criteria_counts.warning})`
                    : ''}
                </li>
              ))}
            </ul>
          ) : (
            <p className="validation-meta">No proof history — run make mrms-proof-report.</p>
          )}
          <p className="validation-meta">
            Regression history ({regressionHistory?.count ?? 0} saved)
          </p>
          {(regressionHistory?.entries ?? []).length > 0 ? (
            <ul className="validation-history-list">
              {regressionHistory?.entries.map((entry, index) => (
                <li key={`${entry.checked_at ?? 'reg'}-${index}`} className="validation-meta">
                  {formatTimestamp(entry.checked_at)} — {entry.summary}
                  {entry.regression_detected ? ' (attention)' : ''}
                </li>
              ))}
            </ul>
          ) : (
            <p className="validation-meta">No regression history — run make mrms-proof-regression.</p>
          )}
          <p className="validation-meta">
            Local sign-offs ({signoffsList?.count ?? 0}) — does not enable production rendering
          </p>
          {(signoffsList?.entries ?? []).length > 0 ? (
            <ul className="validation-history-list">
              {signoffsList?.entries.map((entry, index) => (
                <li key={`${entry.signoff_id ?? 'signoff'}-${index}`} className="validation-meta">
                  {formatTimestamp(entry.created_at)} — {entry.operator ?? '—'}
                  {entry.proof_report_timestamp
                    ? ` (proof ${formatTimestamp(entry.proof_report_timestamp)})`
                    : ''}
                  {entry.accepted_limitations ? `: ${entry.accepted_limitations}` : ''}
                </li>
              ))}
            </ul>
          ) : (
            <p className="validation-meta">No sign-offs — run make mrms-signoff (local only).</p>
          )}
          <form className="validation-signoff-form" onSubmit={(event) => void handleSignoffSubmit(event)}>
            <p className="validation-warn">
              Dev sign-off form — local sign-off only; does not verify MRMS; does not enable production rendering.
            </p>
            <label className="validation-meta">
              Operator initials or name
              <input
                type="text"
                value={signoffOperator}
                onChange={(event) => setSignoffOperator(event.target.value)}
                autoComplete="name"
              />
            </label>
            <label className="validation-meta">
              Notes
              <textarea value={signoffNotes} onChange={(event) => setSignoffNotes(event.target.value)} rows={2} />
            </label>
            <label className="validation-meta">
              <input
                type="checkbox"
                checked={signoffAcceptedLimitations}
                onChange={(event) => setSignoffAcceptedLimitations(event.target.checked)}
              />{' '}
              I accept known prototype limitations (local review only)
            </label>
            <label className="validation-meta">
              Accepted limitations (optional text)
              <input
                type="text"
                value={signoffLimitations}
                onChange={(event) => setSignoffLimitations(event.target.value)}
              />
            </label>
            <button type="submit" className="validation-refresh" disabled={signoffSubmitting}>
              {signoffSubmitting ? 'Submitting…' : 'Submit local sign-off'}
            </button>
            {signoffMessage ? <p className="validation-meta">{signoffMessage}</p> : null}
            {signoffError ? <p className="validation-warn">{signoffError}</p> : null}
          </form>
        </section>
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
      {scheduledProofStep?.proof_requested || scheduledProofStep?.ran ? (
        <p className="validation-meta">
          Scheduled proof step: {scheduledProofStep.ran ? scheduledProofStep.status ?? '—' : 'not run'}
          {scheduledProofStep.elapsed_seconds != null
            ? ` (${scheduledProofStep.elapsed_seconds.toFixed(2)}s)`
            : ''}
          {scheduledProofStep.proof_regression_status
            ? ` — regression ${scheduledProofStep.proof_regression_status}`
            : ''}
          {scheduledProofStep.proof_regression_detected ? ' (regression detected)' : ''}
        </p>
      ) : null}
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
