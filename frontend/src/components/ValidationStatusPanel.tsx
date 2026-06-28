import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  fetchProofReviewData,
  fetchValidationLatest,
  submitSignoff,
  submitDiffAcknowledgment,
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
  const [showDiffAlertTimeline, setShowDiffAlertTimeline] = useState(false);
  const [showDiffAlertTrend, setShowDiffAlertTrend] = useState(false);
  const [showDiffEscalation, setShowDiffEscalation] = useState(false);
  const [showDiffEscalationHistory, setShowDiffEscalationHistory] = useState(false);
  const [showDiffEscalationMetrics, setShowDiffEscalationMetrics] = useState(false);
  const [showDigestHistory, setShowDigestHistory] = useState(false);
  const [ackOperator, setAckOperator] = useState('');
  const [ackNote, setAckNote] = useState('');
  const [ackSubmitting, setAckSubmitting] = useState(false);
  const [ackMessage, setAckMessage] = useState<string | null>(null);
  const [ackError, setAckError] = useState<string | null>(null);
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

  async function handleAckSubmit(event: FormEvent) {
    event.preventDefault();
    setAckMessage(null);
    setAckError(null);
    setAckSubmitting(true);
    const result = await submitDiffAcknowledgment({
      operator_initials: ackOperator.trim() || undefined,
      note: ackNote.trim(),
    });
    setAckSubmitting(false);
    if (!result.ok) {
      setAckError(result.error);
      return;
    }
    setAckMessage(
      result.data.diff_alert_still_active
        ? 'Acknowledgment recorded — diff alert may still be active (does not clear alerts).'
        : 'Acknowledgment recorded (local only — does not verify MRMS).',
    );
    setAckNote('');
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
  const scheduledProofBundle = summary.scheduled_proof_bundle ?? null;
  const scheduledDigest = summary.scheduled_digest ?? null;
  const proofBundle = summary.mrms_proof_bundle ?? null;
  const proofBundleDiff = summary.mrms_proof_bundle_diff ?? null;
  const operatorHandoff = summary.operator_handoff ?? null;
  const operatorGuidance =
    summary.operator_guidance ?? validationAlert?.operator_guidance ?? [];
  const diffAlertTimeline = summary.proof_bundle_diff_alert_history ?? [];
  const diffAlertLatest = summary.proof_bundle_diff_alert ?? null;
  const diffAlertTrend = summary.proof_bundle_diff_alert_trend ?? null;
  const diffAck = summary.proof_bundle_diff_acknowledgment ?? null;
  const diffEscalation = summary.proof_bundle_diff_escalation ?? null;
  const diffEscalationHistory = summary.proof_bundle_diff_escalation_history ?? null;
  const diffEscalationMetrics = summary.proof_bundle_diff_escalation_metrics ?? null;
  const diffEscalationDigest = summary.proof_bundle_diff_escalation_digest ?? null;
  const digestHistory = summary.proof_bundle_diff_escalation_digest_history ?? null;
  const digestDiff = summary.proof_bundle_diff_escalation_digest_diff ?? null;
  const digestRegenerationHint = summary.digest_regeneration_hint ?? null;
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
          {validationAlert.operator_attention_needed && operatorGuidance.length > 0 ? (
            <section className="validation-operator-guidance">
              <p className="validation-warn">
                Operator guidance (local review only — does not verify MRMS; does not enable production
                rendering)
              </p>
              <ul className="validation-history-list">
                {operatorGuidance.map((item, index) => (
                  <li key={`${item.cause}-${index}`} className="validation-meta">
                    {item.title} — <code>{item.path}</code>
                    {item.section_label ? ` — section: ${item.section_label}` : ''}
                    {item.anchor ? ` (anchor: ${item.anchor})` : ''}
                    {item.suggested_action ? ` — ${item.suggested_action}` : ''}
                  </li>
                ))}
              </ul>
            </section>
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
      <section className="validation-scheduled-proof-bundle">
        <p className="validation-meta">
          Scheduled proof bundle monitoring (local evidence only — does not verify MRMS)
        </p>
        {scheduledProofBundle ? (
          <>
            <p className="validation-meta">
              Bundle exported: {scheduledProofBundle.bundle_exported ? 'yes' : 'no'}
              {scheduledProofBundle.bundle_created_at
                ? ` — ${formatTimestamp(scheduledProofBundle.bundle_created_at)}`
                : ''}
              {scheduledProofBundle.bundle_id ? ` (id ${scheduledProofBundle.bundle_id.slice(0, 8)}…)` : ''}
            </p>
            <p className="validation-meta">
              Diff ran: {scheduledProofBundle.diff_ran ? 'yes' : 'no'}
              {scheduledProofBundle.diff_status ? ` — status ${scheduledProofBundle.diff_status}` : ''}
              {scheduledProofBundle.evidence_changes_count != null
                ? ` — changes ${scheduledProofBundle.evidence_changes_count}`
                : ''}
            </p>
            {scheduledProofBundle.operator_attention_needed || validationAlert?.proof_bundle_diff_attention ? (
              <p className="validation-warn">
                Proof bundle diff requires operator attention — does not enable production rendering
              </p>
            ) : null}
            {scheduledProofBundle.handoff_requested ? (
              <p className="validation-meta">
                Scheduled handoff: {scheduledProofBundle.handoff_generated ? 'generated' : 'skipped'}
                {scheduledProofBundle.handoff_reason ? ` — ${scheduledProofBundle.handoff_reason}` : ''}
                {scheduledProofBundle.handoff_path ? ` — ${scheduledProofBundle.handoff_path}` : ''}
              </p>
            ) : null}
            {scheduledProofBundle.handoff_requested ? (
              <p className="validation-meta">
                Local operator handoff only — does not verify MRMS — does not enable production rendering
              </p>
            ) : null}
            {scheduledDigest?.digest_requested ? (
              <>
                <p className="validation-meta">
                  Scheduled digest: {scheduledDigest.digest_generated ? 'generated' : 'skipped'}
                  {scheduledDigest.digest_reason ? ` — ${scheduledDigest.digest_reason}` : ''}
                  {scheduledDigest.digest_path ? ` — ${scheduledDigest.digest_path}` : ''}
                  {scheduledDigest.digest_elapsed_seconds != null
                    ? ` (${scheduledDigest.digest_elapsed_seconds.toFixed(2)}s)`
                    : ''}
                </p>
                <p className="validation-meta">
                  Local digest only — does not notify externally — does not verify MRMS — does not
                  enable production rendering — does not clear alerts
                </p>
              </>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No scheduled proof bundle status — run make scheduled-proof-bundle.
          </p>
        )}
        <p className="validation-meta">verified_mrms: {yesNo(summary.verified_mrms)}</p>
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
            {operatorHandoff.auto_generated ? ' (auto-generated)' : ''}
            {operatorHandoff.include_escalation_review
              ? ` — review checklist (${operatorHandoff.review_checklist_count ?? 0} items)`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">No handoff checklist yet — run make mrms-operator-handoff.</p>
        )}
        {operatorHandoff?.include_escalation_review ? (
          <>
            {operatorHandoff.acknowledgment_status ? (
              <p className="validation-meta">
                Acknowledgment: {operatorHandoff.acknowledgment_status}
                {operatorHandoff.stale_acknowledgment ? ' (stale)' : ' (current)'}
              </p>
            ) : (
              <p className="validation-meta">Acknowledgment: missing</p>
            )}
            {operatorHandoff.digest_path ? (
              <p className="validation-meta">Checklist digest path: {operatorHandoff.digest_path}</p>
            ) : null}
          </>
        ) : null}
        {operatorHandoff?.handoff_requested ? (
          <p className="validation-meta">
            Latest scheduled handoff: {operatorHandoff.handoff_generated ? 'generated' : 'skipped'}
            {operatorHandoff.handoff_reason ? ` — ${operatorHandoff.handoff_reason}` : ''}
            {operatorHandoff.scheduled_handoff_path
              ? ` — ${operatorHandoff.scheduled_handoff_path}`
              : ''}
          </p>
        ) : null}
        <p className="validation-meta">
          Local operator handoff only — does not verify MRMS — does not enable production rendering
        </p>
        <p className="validation-meta">
          Diff/handoff does not enable production rendering — verified_mrms: {yesNo(summary.verified_mrms)}
        </p>
      </section>
      <section className="validation-diff-alert-history">
        <div className="validation-header-actions">
          <p className="validation-meta">
            Proof bundle diff alert timeline (local evidence monitoring only — does not verify MRMS)
          </p>
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDiffAlertTimeline((value) => !value)}
          >
            {showDiffAlertTimeline ? 'Hide timeline' : 'Show timeline'}
          </button>
        </div>
        {diffAlertLatest?.available || validationAlert?.latest_proof_bundle_diff_alert_at ? (
          <p className="validation-meta">
            Latest alert status:{' '}
            {diffAlertLatest?.diff_status ??
              validationAlert?.latest_proof_bundle_diff_alert_status ??
              '—'}
            {diffAlertLatest?.created_at || validationAlert?.latest_proof_bundle_diff_alert_at
              ? ` (${formatTimestamp(
                  diffAlertLatest?.created_at ?? validationAlert?.latest_proof_bundle_diff_alert_at,
                )})`
              : ''}
            {diffAlertLatest?.operator_attention_needed ? ' — attention needed' : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No diff alert history yet — run make mrms-proof-bundle-diff or make scheduled-proof-bundle.
          </p>
        )}
        {validationAlert?.proof_bundle_diff_alert_history_count != null ? (
          <p className="validation-meta">
            Timeline entries: {validationAlert.proof_bundle_diff_alert_history_count}
          </p>
        ) : null}
        <p className="validation-meta">
          Does not enable production rendering — verified_mrms: {yesNo(summary.verified_mrms)}
        </p>
        {showDiffAlertTimeline && diffAlertTimeline.length > 0 ? (
          <ul className="validation-history-list">
            {diffAlertTimeline.map((entry, index) => (
              <li
                key={`${entry.created_at ?? 'diff-alert'}-${entry.diff_status}-${index}`}
                className={entry.operator_attention_needed ? 'validation-warn' : 'validation-meta'}
              >
                {formatTimestamp(entry.created_at)} — {entry.diff_status ?? 'unknown'}
                {entry.evidence_changes_count != null
                  ? ` — changes ${entry.evidence_changes_count}`
                  : ''}
                {entry.operator_attention_needed ? ' — attention needed' : ''}
                {entry.suggested_next_action ? ` — ${entry.suggested_next_action}` : ''}
              </li>
            ))}
          </ul>
        ) : showDiffAlertTimeline ? (
          <p className="validation-meta">No timeline entries in summary — run make proof-bundle-diff-alert-history.</p>
        ) : null}
      </section>
      <section className="validation-diff-escalation">
        <div className="validation-header-actions">
          <p className="validation-meta">
            Diff alert escalation (local operator guidance only — does not verify MRMS; does not enable
            production rendering; does not clear alerts)
          </p>
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDiffEscalation((value) => !value)}
          >
            {showDiffEscalation ? 'Hide escalation' : 'Show escalation'}
          </button>
        </div>
        {diffEscalation?.available ||
        validationAlert?.proof_bundle_diff_escalation_level ||
        (diffEscalation?.escalation_level && diffEscalation.escalation_level !== 'none') ? (
          <p
            className={
              diffEscalation?.escalation_level === 'urgent' ||
              validationAlert?.proof_bundle_diff_escalation_level === 'urgent'
                ? 'validation-warn'
                : 'validation-meta'
            }
          >
            Escalation:{' '}
            {diffEscalation?.escalation_level ??
              validationAlert?.proof_bundle_diff_escalation_level ??
              'none'}
            {diffEscalation?.reason || validationAlert?.proof_bundle_diff_escalation_reason
              ? ` — ${diffEscalation?.reason ?? validationAlert?.proof_bundle_diff_escalation_reason}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No escalation hints — run make proof-bundle-diff-escalation after diff alert history.
          </p>
        )}
        {(diffEscalation?.stale_acknowledgment ||
          validationAlert?.proof_bundle_diff_escalation_stale_ack) && (
          <p className="validation-warn">
            Stale acknowledgment — latest ack predates or does not cover current attention streak
          </p>
        )}
        {showDiffEscalation ? (
          <>
            {diffEscalation?.suggested_next_action ||
            validationAlert?.proof_bundle_diff_escalation_suggested_next_action ? (
              <p className="validation-meta">
                Suggested:{' '}
                {diffEscalation?.suggested_next_action ??
                  validationAlert?.proof_bundle_diff_escalation_suggested_next_action}
              </p>
            ) : null}
            {(diffEscalation?.guidance_items ??
              validationAlert?.proof_bundle_diff_escalation_guidance_items ??
              []
            ).length > 0 ? (
              <ul className="validation-history-list">
                {(diffEscalation?.guidance_items ??
                  validationAlert?.proof_bundle_diff_escalation_guidance_items ??
                  []
                ).map((item, index) => (
                  <li key={`${item.cause}-${index}`} className="validation-meta">
                    {item.title}
                    {item.section_label ? ` — ${item.section_label}` : ''}
                    {item.path ? ` — ${item.path}` : ''}
                    {item.anchor ? ` (anchor: ${item.anchor})` : ''}
                  </li>
                ))}
              </ul>
            ) : null}
            <p className="validation-meta">
              verified_mrms: {yesNo(summary.verified_mrms)} — local escalation only — does not clear
              alerts
            </p>
          </>
        ) : null}
      </section>
      <section className="validation-diff-escalation-history">
        <div className="validation-header-actions">
          <p className="validation-meta">
            Escalation history (local monitoring only — terminal stdout notices are local only; no
            external notifications; does not verify MRMS; does not clear alerts)
          </p>
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDiffEscalationHistory((value) => !value)}
          >
            {showDiffEscalationHistory ? 'Hide history' : 'Show history'}
          </button>
        </div>
        {diffEscalationHistory?.available ||
        (validationAlert?.proof_bundle_diff_escalation_history_count ?? 0) > 0 ? (
          <p className="validation-meta">
            Snapshots: {diffEscalationHistory?.count ?? validationAlert?.proof_bundle_diff_escalation_history_count ?? 0}
            {diffEscalationHistory?.latest_snapshot_at ||
            validationAlert?.latest_proof_bundle_diff_escalation_snapshot_at
              ? ` — latest ${formatTimestamp(
                  diffEscalationHistory?.latest_snapshot_at ??
                    validationAlert?.latest_proof_bundle_diff_escalation_snapshot_at
                )}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No escalation history — run make proof-bundle-diff-escalation or scheduled-proof-bundle.
          </p>
        )}
        {(diffEscalationHistory?.urgent_stdout_notice_triggered ||
          validationAlert?.urgent_stdout_notice_triggered) && (
          <p className="validation-warn">
            Urgent stdout notice triggered{' '}
            {formatTimestamp(
              diffEscalationHistory?.urgent_stdout_notice_at ??
                validationAlert?.urgent_stdout_notice_at
            )}{' '}
            — local terminal only; does not verify MRMS
          </p>
        )}
        {showDiffEscalationHistory && (diffEscalationHistory?.recent ?? []).length > 0 ? (
          <ul className="validation-history-list">
            {(diffEscalationHistory?.recent ?? []).map((entry, index) => (
              <li
                key={`${entry.created_at ?? 'escalation'}-${entry.escalation_level}-${index}`}
                className={entry.escalation_level === 'urgent' ? 'validation-warn' : 'validation-meta'}
              >
                {formatTimestamp(entry.created_at)} — {entry.escalation_level ?? 'none'}
                {entry.latest_diff_status ? ` (${entry.latest_diff_status})` : ''}
                {entry.stale_acknowledgment ? ' — stale ack' : ''}
              </li>
            ))}
          </ul>
        ) : showDiffEscalationHistory ? (
          <p className="validation-meta">No recent escalation snapshots in summary.</p>
        ) : null}
      </section>
      <section className="validation-diff-escalation-metrics">
        <div className="validation-header-actions">
          <p className="validation-meta">
            Escalation metrics (local digest only — does not verify MRMS; does not enable production
            rendering; does not clear alerts; no external notifications)
          </p>
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDiffEscalationMetrics((value) => !value)}
          >
            {showDiffEscalationMetrics ? 'Hide metrics' : 'Show metrics'}
          </button>
        </div>
        {diffEscalationMetrics?.available || (diffEscalationMetrics?.total_snapshots ?? 0) > 0 ? (
          <p className="validation-meta">
            Snapshots {diffEscalationMetrics?.total_snapshots ?? 0} — urgent{' '}
            {diffEscalationMetrics?.urgent_count ?? 0}, attention{' '}
            {diffEscalationMetrics?.attention_count ?? 0}, watch {diffEscalationMetrics?.watch_count ?? 0}
          </p>
        ) : (
          <p className="validation-meta">
            No escalation metrics — run make proof-bundle-diff-escalation-metrics after history exists.
          </p>
        )}
        {diffEscalationDigest?.available ? (
          <p className="validation-meta">
            Latest digest {formatTimestamp(diffEscalationDigest.generated_at)} —{' '}
            {diffEscalationDigest.markdown_path ?? '—'} (local digest only — does not notify externally)
          </p>
        ) : (
          <p className="validation-meta">
            No digest exported — run make proof-bundle-diff-escalation-digest.
          </p>
        )}
        {digestHistory?.available || (digestHistory?.count ?? 0) > 0 ? (
          <p className="validation-meta">
            Digest history: {digestHistory?.count ?? 0} export(s)
            {digestHistory?.latest?.created_at
              ? ` — latest ${formatTimestamp(digestHistory.latest.created_at)}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No digest history — export a digest with make proof-bundle-diff-escalation-digest.
          </p>
        )}
        {digestDiff?.available ? (
          <p className="validation-meta">
            Digest diff: {digestDiff.overall_digest_diff_status ?? 'unknown'}
            {digestDiff.checked_at ? ` (${formatTimestamp(digestDiff.checked_at)})` : ''}
          </p>
        ) : (
          <p className="validation-meta">No digest diff yet — export digest twice to compare.</p>
        )}
        {digestRegenerationHint ? (
          <p
            className={
              digestRegenerationHint.digest_regeneration_recommended
                ? 'validation-warn'
                : 'validation-meta'
            }
          >
            Digest regeneration recommended:{' '}
            {digestRegenerationHint.digest_regeneration_recommended ? 'yes' : 'no'}
            {digestRegenerationHint.reason ? ` — ${digestRegenerationHint.reason}` : ''}
            {digestRegenerationHint.suggested_command
              ? ` — run ${digestRegenerationHint.suggested_command}`
              : ''}
          </p>
        ) : null}
        <p className="validation-meta">
          Local digest only — does not notify externally — does not verify MRMS — does not enable
          production rendering — does not clear alerts
        </p>
        <div className="validation-header-actions">
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDigestHistory((value) => !value)}
          >
            {showDigestHistory ? 'Hide digest history' : 'Show digest history'}
          </button>
        </div>
        {showDigestHistory && (digestHistory?.recent ?? []).length > 0 ? (
          <ul className="validation-history-list">
            {(digestHistory?.recent ?? []).map((entry, index) => (
              <li key={`${entry.created_at ?? 'digest'}-${index}`} className="validation-meta">
                {formatTimestamp(entry.created_at)} — {entry.latest_escalation_level ?? '—'}
                {entry.latest_diff_status ? ` (${entry.latest_diff_status})` : ''}
                {entry.digest_path ? ` — ${entry.digest_path}` : ''}
              </li>
            ))}
          </ul>
        ) : showDigestHistory ? (
          <p className="validation-meta">No recent digest exports in summary.</p>
        ) : null}
        {showDiffEscalationMetrics && diffEscalationMetrics ? (
          <>
            <p className="validation-meta">
              Current urgent streak {diffEscalationMetrics.current_urgent_streak} — current
              attention/urgent streak {diffEscalationMetrics.current_attention_or_urgent_streak}
            </p>
            <p className="validation-meta">
              Longest urgent streak {diffEscalationMetrics.longest_urgent_streak} — longest
              attention/urgent streak {diffEscalationMetrics.longest_attention_or_urgent_streak}
            </p>
            <p className="validation-meta">
              Stale acknowledgment snapshots {diffEscalationMetrics.stale_acknowledgment_count} —
              verified_mrms: {yesNo(summary.verified_mrms)}
            </p>
          </>
        ) : null}
      </section>
      <section className="validation-diff-alert-trend">
        <div className="validation-header-actions">
          <p className="validation-meta">
            Diff alert trend (local evidence monitoring only — does not verify MRMS)
          </p>
          <button
            type="button"
            className="validation-refresh"
            onClick={() => setShowDiffAlertTrend((value) => !value)}
          >
            {showDiffAlertTrend ? 'Hide trend' : 'Show trend'}
          </button>
        </div>
        {diffAlertTrend?.available || validationAlert?.proof_bundle_diff_alert_trend ? (
          <p className="validation-meta">
            Trend: {diffAlertTrend?.trend ?? validationAlert?.proof_bundle_diff_alert_trend ?? 'no_data'}
            {diffAlertTrend?.latest_status ? ` — latest ${diffAlertTrend.latest_status}` : ''}
            {diffAlertTrend?.current_attention_streak
              ? ` — attention streak ${diffAlertTrend.current_attention_streak}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">No trend data — run make proof-bundle-diff-alert-trend after diff history.</p>
        )}
        {showDiffAlertTrend && diffAlertTrend ? (
          <>
            <p className="validation-meta">
              Last worsened: {formatTimestamp(diffAlertTrend.last_worsened_at)} — last mixed:{' '}
              {formatTimestamp(diffAlertTrend.last_mixed_at)} — last improved:{' '}
              {formatTimestamp(diffAlertTrend.last_improved_at)}
            </p>
            <p className="validation-meta">
              Recent counts — worsened {diffAlertTrend.recent_worsened_count}, mixed{' '}
              {diffAlertTrend.recent_mixed_count}, improved {diffAlertTrend.recent_improved_count},
              unchanged {diffAlertTrend.recent_unchanged_count}
            </p>
            {diffAlertTrend.suggested_next_action ? (
              <p className="validation-meta">Suggested: {diffAlertTrend.suggested_next_action}</p>
            ) : null}
          </>
        ) : null}
        {diffAck?.available || (validationAlert?.diff_acknowledgment_count ?? 0) > 0 ? (
          <p className="validation-meta">
            Latest acknowledgment {formatTimestamp(diffAck?.created_at ?? validationAlert?.latest_diff_acknowledgment_at)}{' '}
            — {diffAck?.operator ?? validationAlert?.latest_diff_acknowledgment_operator ?? '—'} (
            {validationAlert?.diff_acknowledgment_count ?? diffAck?.count ?? 0} total)
          </p>
        ) : (
          <p className="validation-meta">No diff alert acknowledgments recorded yet.</p>
        )}
        {validationAlert?.diff_alert_acknowledged_but_still_active ? (
          <p className="validation-warn">
            Acknowledged but diff alert still active — acknowledgment does not clear alerts or verify MRMS
          </p>
        ) : null}
        <p className="validation-meta">
          Local acknowledgment only — does not enable production rendering — verified_mrms:{' '}
          {yesNo(summary.verified_mrms)}
        </p>
        <form className="validation-ack-form" onSubmit={(event) => void handleAckSubmit(event)}>
          <p className="validation-warn">
            Dev acknowledgment form — local only; does not clear alerts or verify MRMS.
          </p>
          <label className="validation-meta">
            Operator initials or name
            <input
              type="text"
              value={ackOperator}
              onChange={(event) => setAckOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label className="validation-meta">
            Note (required)
            <textarea value={ackNote} onChange={(event) => setAckNote(event.target.value)} rows={2} />
          </label>
          <button type="submit" className="validation-refresh" disabled={ackSubmitting}>
            {ackSubmitting ? 'Submitting…' : 'Submit local acknowledgment'}
          </button>
          {ackMessage ? <p className="validation-meta">{ackMessage}</p> : null}
          {ackError ? <p className="validation-warn">{ackError}</p> : null}
        </form>
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
