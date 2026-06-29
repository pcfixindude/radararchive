import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import {
  fetchProofReviewData,
  fetchValidationLatest,
  submitSignoff,
  submitReviewSession,
  submitVisualReviewSampleSet,
  submitVisualReviewSampleAnnotation,
  refreshVisualReviewSampleReadiness,
  refreshRenderCandidatePreflight,
  refreshRenderCandidateDryRunPlan,
  refreshRenderCandidateScaffold,
  refreshRenderCandidateSandbox,
  exportRenderCandidateSandbox,
  importRenderCandidateSandbox,
  refreshRenderCandidateSandboxComparisonHistory,
  refreshRenderCandidateSandboxComparisonTrendHint,
  submitSandboxComparisonReviewAcknowledgment,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatus,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusHistory,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory,
  refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint,
  submitTrendHintReviewAcknowledgment,
  submitAckStatusTrendReviewAckStatusTrendReviewAcknowledgment,
  submitAckStatusTrendReviewAcknowledgment,
  submitDiffAcknowledgment,
  type MrmsProofHistory,
  type MrmsProofRegressionHistory,
  type MrmsSignoffsList,
  type ValidationSummary,
} from '../api/client';
import CollapsibleSection from './validation/CollapsibleSection';
import CommandLine from './validation/CommandLine';
import {
  countVisiblePresets,
  filterVisiblePresetGroups,
  type PresetFilterMode,
} from './validation/presetFilters';
import SafetyNote from './validation/SafetyNote';
import StatusBadge from './validation/StatusBadge';
import { formatTimestamp, yesNo } from './validation/format';

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
  const [ackOperator, setAckOperator] = useState('');
  const [ackNote, setAckNote] = useState('');
  const [ackSubmitting, setAckSubmitting] = useState(false);
  const [ackMessage, setAckMessage] = useState<string | null>(null);
  const [ackError, setAckError] = useState<string | null>(null);
  const [signoffError, setSignoffError] = useState<string | null>(null);
  const [reviewSessionOperator, setReviewSessionOperator] = useState('');
  const [reviewSessionNotes, setReviewSessionNotes] = useState('');
  const [reviewSessionAcceptedLimitations, setReviewSessionAcceptedLimitations] = useState(false);
  const [reviewSessionExportAfterCreate, setReviewSessionExportAfterCreate] = useState(false);
  const [presetFilterMode, setPresetFilterMode] = useState<PresetFilterMode>('all');
  const [presetGroupFilter, setPresetGroupFilter] = useState('all');
  const [reviewSessionSubmitting, setReviewSessionSubmitting] = useState(false);
  const [reviewSessionMessage, setReviewSessionMessage] = useState<string | null>(null);
  const [reviewSessionError, setReviewSessionError] = useState<string | null>(null);
  const [sampleSetSubmitting, setSampleSetSubmitting] = useState(false);
  const [sampleSetMessage, setSampleSetMessage] = useState<string | null>(null);
  const [sampleSetError, setSampleSetError] = useState<string | null>(null);
  const [annotationDrafts, setAnnotationDrafts] = useState<
    Record<string, { status: string; notes: string; reviewer: string }>
  >({});
  const [annotationSavingKey, setAnnotationSavingKey] = useState<string | null>(null);
  const [annotationMessage, setAnnotationMessage] = useState<string | null>(null);
  const [annotationError, setAnnotationError] = useState<string | null>(null);
  const [readinessRefreshing, setReadinessRefreshing] = useState(false);
  const [readinessMessage, setReadinessMessage] = useState<string | null>(null);
  const [preflightRefreshing, setPreflightRefreshing] = useState(false);
  const [preflightMessage, setPreflightMessage] = useState<string | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [dryRunPlanRefreshing, setDryRunPlanRefreshing] = useState(false);
  const [dryRunPlanMessage, setDryRunPlanMessage] = useState<string | null>(null);
  const [dryRunPlanError, setDryRunPlanError] = useState<string | null>(null);
  const [scaffoldRefreshing, setScaffoldRefreshing] = useState(false);
  const [scaffoldMessage, setScaffoldMessage] = useState<string | null>(null);
  const [scaffoldError, setScaffoldError] = useState<string | null>(null);
  const [sandboxRefreshing, setSandboxRefreshing] = useState(false);
  const [sandboxMessage, setSandboxMessage] = useState<string | null>(null);
  const [sandboxError, setSandboxError] = useState<string | null>(null);
  const [importExportExporting, setImportExportExporting] = useState(false);
  const [importExportImporting, setImportExportImporting] = useState(false);
  const [importExportMessage, setImportExportMessage] = useState<string | null>(null);
  const [importExportError, setImportExportError] = useState<string | null>(null);
  const [comparisonHistoryRefreshing, setComparisonHistoryRefreshing] = useState(false);
  const [comparisonHistoryMessage, setComparisonHistoryMessage] = useState<string | null>(null);
  const [comparisonHistoryError, setComparisonHistoryError] = useState<string | null>(null);
  const [trendHintRefreshing, setTrendHintRefreshing] = useState(false);
  const [trendHintMessage, setTrendHintMessage] = useState<string | null>(null);
  const [trendHintError, setTrendHintError] = useState<string | null>(null);
  const [comparisonReviewAckOperator, setComparisonReviewAckOperator] = useState('');
  const [comparisonReviewAckNote, setComparisonReviewAckNote] = useState('');
  const [comparisonReviewAckTrendReview, setComparisonReviewAckTrendReview] = useState(false);
  const [comparisonReviewAckSubmitting, setComparisonReviewAckSubmitting] = useState(false);
  const [comparisonReviewAckMessage, setComparisonReviewAckMessage] = useState<string | null>(null);
  const [comparisonReviewAckError, setComparisonReviewAckError] = useState<string | null>(null);
  const [ackStatusRefreshing, setAckStatusRefreshing] = useState(false);
  const [ackStatusMessage, setAckStatusMessage] = useState<string | null>(null);
  const [ackStatusError, setAckStatusError] = useState<string | null>(null);
  const [ackStatusHistoryRefreshing, setAckStatusHistoryRefreshing] = useState(false);
  const [ackStatusHistoryMessage, setAckStatusHistoryMessage] = useState<string | null>(null);
  const [ackStatusHistoryError, setAckStatusHistoryError] = useState<string | null>(null);
  const [ackStatusTrendHintRefreshing, setAckStatusTrendHintRefreshing] = useState(false);
  const [ackStatusTrendHintMessage, setAckStatusTrendHintMessage] = useState<string | null>(null);
  const [ackStatusTrendHintError, setAckStatusTrendHintError] = useState<string | null>(null);
  const [ackStatusTrendReviewAckOperator, setAckStatusTrendReviewAckOperator] = useState('');
  const [ackStatusTrendReviewAckNote, setAckStatusTrendReviewAckNote] = useState('');
  const [ackStatusTrendReviewAckTrendReview, setAckStatusTrendReviewAckTrendReview] = useState(false);
  const [ackStatusTrendReviewAckSubmitting, setAckStatusTrendReviewAckSubmitting] = useState(false);
  const [ackStatusTrendReviewAckMessage, setAckStatusTrendReviewAckMessage] = useState<string | null>(null);
  const [ackStatusTrendReviewAckError, setAckStatusTrendReviewAckError] = useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusRefreshing, setAckStatusTrendReviewAckStatusRefreshing] = useState(false);
  const [ackStatusTrendReviewAckStatusMessage, setAckStatusTrendReviewAckStatusMessage] = useState<string | null>(
    null,
  );
  const [ackStatusTrendReviewAckStatusError, setAckStatusTrendReviewAckStatusError] = useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusHistoryRefreshing, setAckStatusTrendReviewAckStatusHistoryRefreshing] =
    useState(false);
  const [ackStatusTrendReviewAckStatusHistoryMessage, setAckStatusTrendReviewAckStatusHistoryMessage] = useState<
    string | null
  >(null);
  const [ackStatusTrendReviewAckStatusHistoryError, setAckStatusTrendReviewAckStatusHistoryError] = useState<
    string | null
  >(null);
  const [
    ackStatusTrendReviewAckStatusTrendHintRefreshing,
    setAckStatusTrendReviewAckStatusTrendHintRefreshing,
  ] = useState(false);
  const [ackStatusTrendReviewAckStatusTrendHintMessage, setAckStatusTrendReviewAckStatusTrendHintMessage] =
    useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusTrendHintError, setAckStatusTrendReviewAckStatusTrendHintError] =
    useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusTrendReviewAckOperator, setAckStatusTrendReviewAckStatusTrendReviewAckOperator] =
    useState('');
  const [ackStatusTrendReviewAckStatusTrendReviewAckNote, setAckStatusTrendReviewAckStatusTrendReviewAckNote] =
    useState('');
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckTrendReview,
    setAckStatusTrendReviewAckStatusTrendReviewAckTrendReview,
  ] = useState(false);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckSubmitting,
    setAckStatusTrendReviewAckStatusTrendReviewAckSubmitting,
  ] = useState(false);
  const [ackStatusTrendReviewAckStatusTrendReviewAckMessage, setAckStatusTrendReviewAckStatusTrendReviewAckMessage] =
    useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusTrendReviewAckError, setAckStatusTrendReviewAckStatusTrendReviewAckError] =
    useState<string | null>(null);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing,
  ] = useState(false);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusMessage,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusMessage,
  ] = useState<string | null>(null);
  const [ackStatusTrendReviewAckStatusTrendReviewAckStatusError, setAckStatusTrendReviewAckStatusTrendReviewAckStatusError] =
    useState<string | null>(null);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing,
  ] = useState(false);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage,
  ] = useState<string | null>(null);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError,
  ] = useState<string | null>(null);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing,
  ] = useState(false);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage,
  ] = useState<string | null>(null);
  const [
    ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError,
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError,
  ] = useState<string | null>(null);
  const [trendHintReviewAckOperator, setTrendHintReviewAckOperator] = useState('');
  const [trendHintReviewAckNote, setTrendHintReviewAckNote] = useState('');
  const [trendHintReviewAckTrendReview, setTrendHintReviewAckTrendReview] = useState(false);
  const [trendHintReviewAckSubmitting, setTrendHintReviewAckSubmitting] = useState(false);
  const [trendHintReviewAckMessage, setTrendHintReviewAckMessage] = useState<string | null>(null);
  const [trendHintReviewAckError, setTrendHintReviewAckError] = useState<string | null>(null);

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

  useEffect(() => {
    const summaries = summary?.mrms_visual_review_sample_readiness?.entry_summaries ?? [];
    if (summaries.length === 0) {
      return;
    }
    setAnnotationDrafts((previous) => {
      const next = { ...previous };
      for (const entry of summaries) {
        const key = entry.sample_key ?? '';
        if (!key || next[key]) {
          continue;
        }
        next[key] = {
          status: entry.status ?? 'unreviewed',
          notes: entry.operator_notes ?? '',
          reviewer: entry.reviewer_label ?? '',
        };
      }
      return next;
    });
  }, [summary?.mrms_visual_review_sample_readiness?.entry_summaries]);

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

  async function openDetails() {
    if (detailsJson) {
      setShowDetails(true);
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

  async function handleReviewSessionSubmit(event: FormEvent) {
    event.preventDefault();
    setReviewSessionMessage(null);
    setReviewSessionError(null);
    setReviewSessionSubmitting(true);
    const result = await submitReviewSession({
      operator_initials: reviewSessionOperator.trim() || undefined,
      session_notes: reviewSessionNotes.trim() || undefined,
      accepted_limitations: reviewSessionAcceptedLimitations,
      accepted_limitations_text: reviewSessionAcceptedLimitations
        ? 'Accepted known prototype limitations (local review session only).'
        : undefined,
      export_after_create: reviewSessionExportAfterCreate,
    });
    setReviewSessionSubmitting(false);
    if (!result.ok) {
      setReviewSessionError(result.error);
      return;
    }
    let message =
      'Local review session recorded — does not verify MRMS, clear alerts, or enable production rendering.';
    if (result.data.export_after_create_requested) {
      if (result.data.export_generated) {
        message += ` Markdown export written to ${result.data.export_path ?? '—'}.`;
      } else if (result.data.export_error) {
        message += ` Export after create failed: ${result.data.export_error}`;
      }
    }
    setReviewSessionMessage(message);
    setReviewSessionOperator('');
    setReviewSessionNotes('');
    setReviewSessionAcceptedLimitations(false);
    setReviewSessionExportAfterCreate(false);
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleSampleSetGenerate() {
    setSampleSetMessage(null);
    setSampleSetError(null);
    setSampleSetSubmitting(true);
    const result = await submitVisualReviewSampleSet({
      selection_mode: 'recommended',
      limit: 5,
    });
    setSampleSetSubmitting(false);
    if (!result.ok) {
      setSampleSetError(result.error);
      return;
    }
    setSampleSetMessage(
      `Local sample set saved (${result.data.sample_set.entry_count ?? 0} entries) — does not verify MRMS or enable production rendering.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleSampleAnnotationSave(sampleKey: string) {
    const draft = annotationDrafts[sampleKey];
    if (!draft) {
      return;
    }
    setAnnotationMessage(null);
    setAnnotationError(null);
    setAnnotationSavingKey(sampleKey);
    const result = await submitVisualReviewSampleAnnotation({
      sample_key: sampleKey,
      status: draft.status,
      operator_notes: draft.notes.trim() || null,
      reviewer_label: draft.reviewer.trim() || null,
    });
    setAnnotationSavingKey(null);
    if (!result.ok) {
      setAnnotationError(result.error);
      return;
    }
    setAnnotationMessage(
      `Annotation saved for ${sampleKey} — local advisory only; does not verify MRMS.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleReadinessRefresh() {
    setReadinessMessage(null);
    setReadinessRefreshing(true);
    const result = await refreshVisualReviewSampleReadiness();
    setReadinessRefreshing(false);
    if (!result.ok) {
      setAnnotationError(result.error);
      return;
    }
    setReadinessMessage('Readiness summary refreshed — candidate_ready is not production authorization.');
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handlePreflightRefresh() {
    setPreflightMessage(null);
    setPreflightError(null);
    setPreflightRefreshing(true);
    const result = await refreshRenderCandidatePreflight();
    setPreflightRefreshing(false);
    if (!result.ok) {
      setPreflightError(result.error);
      return;
    }
    setPreflightMessage(
      `Preflight report refreshed (${result.data.compact.preflight_level ?? '—'}) — local advisory only; does not authorize production use.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleDryRunPlanRefresh() {
    setDryRunPlanMessage(null);
    setDryRunPlanError(null);
    setDryRunPlanRefreshing(true);
    const result = await refreshRenderCandidateDryRunPlan();
    setDryRunPlanRefreshing(false);
    if (!result.ok) {
      setDryRunPlanError(result.error);
      return;
    }
    setDryRunPlanMessage(
      `Dry-run plan refreshed (${result.data.compact.plan_status ?? '—'}) — local advisory only; does not download/decode/render.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleScaffoldRefresh() {
    setScaffoldMessage(null);
    setScaffoldError(null);
    setScaffoldRefreshing(true);
    const result = await refreshRenderCandidateScaffold();
    setScaffoldRefreshing(false);
    if (!result.ok) {
      setScaffoldError(result.error);
      return;
    }
    setScaffoldMessage(
      `Scaffold refreshed (${result.data.compact.scaffold_status ?? '—'}) — disabled-by-default local scaffold; no side effects.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleSandboxRefresh() {
    setSandboxMessage(null);
    setSandboxError(null);
    setSandboxRefreshing(true);
    const result = await refreshRenderCandidateSandbox();
    setSandboxRefreshing(false);
    if (!result.ok) {
      setSandboxError(result.error);
      return;
    }
    setSandboxMessage(
      `Sandbox refreshed (${result.data.compact.sandbox_status ?? '—'}) — local-only; cleanup report-only by default.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleImportExportExport() {
    setImportExportMessage(null);
    setImportExportError(null);
    setImportExportExporting(true);
    const result = await exportRenderCandidateSandbox();
    setImportExportExporting(false);
    if (!result.ok) {
      setImportExportError(result.error);
      return;
    }
    setImportExportMessage(
      `Export generated (${result.data.compact.import_export_status ?? '—'}) — metadata/report-only.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleImportExportImport() {
    setImportExportMessage(null);
    setImportExportError(null);
    setImportExportImporting(true);
    const result = await importRenderCandidateSandbox();
    setImportExportImporting(false);
    if (!result.ok) {
      setImportExportError(result.error);
      return;
    }
    setImportExportMessage(
      `Import validated (${result.data.compact.import_export_status ?? '—'}) — metadata/report-only.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleComparisonHistoryRefresh() {
    setComparisonHistoryMessage(null);
    setComparisonHistoryError(null);
    setComparisonHistoryRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonHistory();
    setComparisonHistoryRefreshing(false);
    if (!result.ok) {
      setComparisonHistoryError(result.error);
      return;
    }
    setComparisonHistoryMessage(
      `Comparison history refreshed (${result.data.compact.history_status ?? '—'}) — ${result.data.compact.history_count ?? 0} entries.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleTrendHintRefresh() {
    setTrendHintMessage(null);
    setTrendHintError(null);
    setTrendHintRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonTrendHint();
    setTrendHintRefreshing(false);
    if (!result.ok) {
      setTrendHintError(result.error);
      return;
    }
    setTrendHintMessage(
      `Trend hint refreshed (${result.data.compact.hint_status ?? '—'}) — trend ${result.data.compact.trend ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleComparisonReviewAckSubmit(event: FormEvent) {
    event.preventDefault();
    setComparisonReviewAckMessage(null);
    setComparisonReviewAckError(null);
    setComparisonReviewAckSubmitting(true);
    const result = await submitSandboxComparisonReviewAcknowledgment({
      operator_initials: comparisonReviewAckOperator.trim() || undefined,
      note: comparisonReviewAckNote.trim(),
      acknowledged_trend_review: comparisonReviewAckTrendReview || undefined,
    });
    setComparisonReviewAckSubmitting(false);
    if (!result.ok) {
      setComparisonReviewAckError(result.error);
      return;
    }
    setComparisonReviewAckMessage(
      result.data.trend_review_still_recommended
        ? 'Acknowledgment recorded — trend review may still be recommended (does not clear alerts).'
        : 'Acknowledgment recorded (local only — does not verify MRMS).',
    );
    setComparisonReviewAckNote('');
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusRefresh() {
    setAckStatusMessage(null);
    setAckStatusError(null);
    setAckStatusRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonAcknowledgmentStatus();
    setAckStatusRefreshing(false);
    if (!result.ok) {
      setAckStatusError(result.error);
      return;
    }
    setAckStatusMessage(
      `Acknowledgment status refreshed (${result.data.compact.rollup_status ?? '—'}) — ${result.data.compact.acknowledgment_status ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusHistoryRefresh() {
    setAckStatusHistoryMessage(null);
    setAckStatusHistoryError(null);
    setAckStatusHistoryRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusHistory();
    setAckStatusHistoryRefreshing(false);
    if (!result.ok) {
      setAckStatusHistoryError(result.error);
      return;
    }
    setAckStatusHistoryMessage(
      `Status history refreshed — ${result.data.compact.history_count ?? 0} entries, latest coverage ${result.data.compact.latest_coverage_change ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendHintRefresh() {
    setAckStatusTrendHintMessage(null);
    setAckStatusTrendHintError(null);
    setAckStatusTrendHintRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint();
    setAckStatusTrendHintRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendHintError(result.error);
      return;
    }
    setAckStatusTrendHintMessage(
      `Status trend hint refreshed (${result.data.compact.hint_status ?? '—'}) — trend ${result.data.compact.trend ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckSubmit(event: FormEvent) {
    event.preventDefault();
    setAckStatusTrendReviewAckMessage(null);
    setAckStatusTrendReviewAckError(null);
    setAckStatusTrendReviewAckSubmitting(true);
    const result = await submitAckStatusTrendReviewAcknowledgment({
      operator_initials: ackStatusTrendReviewAckOperator.trim() || undefined,
      note: ackStatusTrendReviewAckNote.trim(),
      acknowledged_trend_review: ackStatusTrendReviewAckTrendReview || undefined,
    });
    setAckStatusTrendReviewAckSubmitting(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckError(result.error);
      return;
    }
    setAckStatusTrendReviewAckMessage(
      result.data.trend_review_still_recommended
        ? 'Acknowledgment recorded — status trend review may still be recommended (does not clear alerts).'
        : 'Acknowledgment recorded (local only — does not verify MRMS).',
    );
    setAckStatusTrendReviewAckNote('');
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusRefresh() {
    setAckStatusTrendReviewAckStatusMessage(null);
    setAckStatusTrendReviewAckStatusError(null);
    setAckStatusTrendReviewAckStatusRefreshing(true);
    const result = await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus();
    setAckStatusTrendReviewAckStatusRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusMessage(
      `Status trend review acknowledgment status refreshed (${result.data.compact.rollup_status ?? '—'}) — ${result.data.compact.acknowledgment_status ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusHistoryRefresh() {
    setAckStatusTrendReviewAckStatusHistoryMessage(null);
    setAckStatusTrendReviewAckStatusHistoryError(null);
    setAckStatusTrendReviewAckStatusHistoryRefreshing(true);
    const result =
      await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory();
    setAckStatusTrendReviewAckStatusHistoryRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusHistoryError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusHistoryMessage(
      `Status trend review acknowledgment status history refreshed — ${result.data.compact.history_count ?? 0} entries.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusTrendHintRefresh() {
    setAckStatusTrendReviewAckStatusTrendHintMessage(null);
    setAckStatusTrendReviewAckStatusTrendHintError(null);
    setAckStatusTrendReviewAckStatusTrendHintRefreshing(true);
    const result =
      await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint();
    setAckStatusTrendReviewAckStatusTrendHintRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusTrendHintError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusTrendHintMessage(
      `Status trend review acknowledgment status trend hint refreshed (${result.data.compact.hint_status ?? '—'}) — trend ${result.data.compact.trend ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusTrendReviewAckSubmit(event: FormEvent) {
    event.preventDefault();
    setAckStatusTrendReviewAckStatusTrendReviewAckMessage(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckError(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckSubmitting(true);
    const result = await submitAckStatusTrendReviewAckStatusTrendReviewAcknowledgment({
      operator_initials: ackStatusTrendReviewAckStatusTrendReviewAckOperator.trim() || undefined,
      note: ackStatusTrendReviewAckStatusTrendReviewAckNote.trim(),
      acknowledged_trend_review: ackStatusTrendReviewAckStatusTrendReviewAckTrendReview || undefined,
    });
    setAckStatusTrendReviewAckStatusTrendReviewAckSubmitting(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusTrendReviewAckError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusTrendReviewAckMessage(
      result.data.trend_review_still_recommended
        ? 'Acknowledgment recorded — status trend review may still be recommended (does not clear alerts).'
        : 'Acknowledgment recorded (local only — does not verify MRMS).',
    );
    setAckStatusTrendReviewAckStatusTrendReviewAckNote('');
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusTrendReviewAckStatusRefresh() {
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusMessage(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusError(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing(true);
    const result =
      await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus();
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusTrendReviewAckStatusError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusMessage(
      `Trend review acknowledgment status refreshed (${result.data.compact.rollup_status ?? '—'}) — ${result.data.compact.acknowledgment_status ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefresh() {
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing(true);
    const result =
      await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory();
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage(
      `Trend review acknowledgment status history refreshed — ${result.data.compact.history_count ?? 0} entries.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefresh() {
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError(null);
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing(true);
    const result =
      await refreshRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint();
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing(false);
    if (!result.ok) {
      setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError(result.error);
      return;
    }
    setAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage(
      `Trend review acknowledgment status trend hint refreshed (${result.data.compact.hint_status ?? '—'}) — trend ${result.data.compact.trend ?? '—'}.`,
    );
    if (onRefresh) {
      await onRefresh();
    }
  }

  async function handleTrendHintReviewAckSubmit(event: FormEvent) {
    event.preventDefault();
    setTrendHintReviewAckMessage(null);
    setTrendHintReviewAckError(null);
    setTrendHintReviewAckSubmitting(true);
    const result = await submitTrendHintReviewAcknowledgment({
      operator_initials: trendHintReviewAckOperator.trim() || undefined,
      note: trendHintReviewAckNote.trim(),
      acknowledged_trend_review: trendHintReviewAckTrendReview || undefined,
    });
    setTrendHintReviewAckSubmitting(false);
    if (!result.ok) {
      setTrendHintReviewAckError(result.error);
      return;
    }
    setTrendHintReviewAckMessage(
      result.data.trend_review_still_recommended
        ? 'Acknowledgment recorded — trend review may still be recommended (does not clear alerts).'
        : 'Acknowledgment recorded (local only — does not verify MRMS).',
    );
    setTrendHintReviewAckNote('');
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
  const scheduledReviewExport = summary.scheduled_review_export ?? null;
  const scheduledVisualReview = summary.scheduled_visual_review ?? null;
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
  const reviewSessionSummary = summary.mrms_review_session ?? null;
  const reviewSessionComparison = reviewSessionSummary?.comparison ?? null;
  const openAttentionGuidance = reviewSessionSummary?.open_attention_guidance ?? [];
  const reviewSessionExport = summary.mrms_review_session_export ?? null;
  const reviewSessionExportDiff = summary.mrms_review_session_export_diff ?? null;
  const reviewSessionExportDiffTrend = summary.mrms_review_session_export_diff_trend ?? null;
  const reviewSessionExportDiffTrendHint = summary.mrms_review_session_export_diff_trend_hint ?? null;
  const reviewSessionExportDiffHistory = summary.mrms_review_session_export_diff_history ?? null;
  const reviewExportRegenerationHint = summary.review_export_regeneration_hint ?? null;
  const operatorReviewStatus = summary.operator_review_status ?? null;
  const operatorWorkflowPresets = summary.operator_workflow_presets ?? null;
  const mrmsVisualReview = summary.mrms_visual_review ?? null;
  const mrmsVisualReviewComparison = summary.mrms_visual_review_comparison ?? null;
  const mrmsVisualReviewHint = summary.mrms_visual_review_hint ?? null;
  const mrmsVisualReviewSampleSet = summary.mrms_visual_review_sample_set ?? null;
  const mrmsVisualReviewSampleReadiness = summary.mrms_visual_review_sample_readiness ?? null;
  const mrmsRenderCandidatePreflight = summary.mrms_render_candidate_preflight ?? null;
  const mrmsRenderCandidateDryRunPlan = summary.mrms_render_candidate_dry_run_plan ?? null;
  const mrmsRenderCandidateScaffold = summary.mrms_render_candidate_scaffold ?? null;
  const mrmsRenderCandidateSandbox = summary.mrms_render_candidate_sandbox ?? null;
  const mrmsRenderCandidateSandboxImportExport =
    summary.mrms_render_candidate_sandbox_import_export ?? null;
  const mrmsRenderCandidateSandboxComparisonHistory =
    summary.mrms_render_candidate_sandbox_comparison_history ?? null;
  const mrmsRenderCandidateSandboxComparisonTrendHint =
    summary.mrms_render_candidate_sandbox_comparison_trend_hint ?? null;
  const mrmsRenderCandidateSandboxComparisonReviewAcknowledgment =
    summary.mrms_render_candidate_sandbox_comparison_review_acknowledgment ?? null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status ?? null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history ?? null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint ?? null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history ??
    null;
  const mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint =
    summary.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint ??
    null;
  const trendHintReviewAck =
    summary.mrms_render_candidate_trend_hint_review_acknowledgment ?? null;
  const workflowPresetById = Object.fromEntries(
    (operatorWorkflowPresets?.presets ?? []).map((preset) => [preset.preset_id, preset]),
  );
  const workflowPresetGroups = operatorWorkflowPresets?.operator_workflow_preset_groups ?? [];
  const visibleWorkflowPresetGroups = useMemo(
    () => filterVisiblePresetGroups(workflowPresetGroups, workflowPresetById, presetFilterMode, presetGroupFilter),
    [workflowPresetGroups, workflowPresetById, presetFilterMode, presetGroupFilter],
  );
  const visibleWorkflowPresetCount = useMemo(
    () => countVisiblePresets(visibleWorkflowPresetGroups),
    [visibleWorkflowPresetGroups],
  );
  const scheduledOperatorStatus = summary.scheduled_operator_status ?? null;
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
      {operatorReviewStatus ? (
        <section className="validation-operator-review-status">
          <h3>Operator Review Status</h3>
          <p className="validation-meta">
            Status: <StatusBadge level={operatorReviewStatus.status_level} />
            {operatorReviewStatus.status_reason ? ` — ${operatorReviewStatus.status_reason}` : ''}
          </p>
          {operatorReviewStatus.top_recommended_action ? (
            <p className="validation-meta">
              Top recommended action: {operatorReviewStatus.top_recommended_action}
            </p>
          ) : null}
          <CommandLine command={operatorReviewStatus.top_suggested_command} />
          {operatorReviewStatus.top_guidance_item ? (
            <p className="validation-meta">
              Top guidance: {operatorReviewStatus.top_guidance_item.title}
              {operatorReviewStatus.runbook_path ? (
                <>
                  {' '}
                  — <code>{operatorReviewStatus.runbook_path}</code>
                </>
              ) : null}
              {operatorReviewStatus.runbook_section
                ? ` — section: ${operatorReviewStatus.runbook_section}`
                : ''}
            </p>
          ) : null}
          {operatorReviewStatus.suggested_action ? (
            <p className="validation-meta">
              Suggested action: {operatorReviewStatus.suggested_action}
            </p>
          ) : null}
          <p className="validation-meta">
            Review session recommended: {yesNo(operatorReviewStatus.review_session_recommended ?? false)} —
            review export recommended: {yesNo(operatorReviewStatus.review_export_recommended ?? false)} —
            digest regeneration recommended:{' '}
            {yesNo(operatorReviewStatus.digest_regeneration_recommended ?? false)} —
            visual review regeneration recommended:{' '}
            {yesNo(operatorReviewStatus.visual_review_regeneration_recommended ?? false)}
          </p>
          {operatorReviewStatus.visual_review_hint_reason ? (
            <p className="validation-meta">
              Visual review reason: {operatorReviewStatus.visual_review_hint_reason}
            </p>
          ) : null}
          <p className="validation-meta">
            Evidence trend: {operatorReviewStatus.evidence_trend ?? 'unknown'}
            {operatorReviewStatus.latest_export_diff_status
              ? ` — latest export diff: ${operatorReviewStatus.latest_export_diff_status}`
              : ''}
            {operatorReviewStatus.latest_visual_review_comparison_status
              ? ` — visual review comparison: ${operatorReviewStatus.latest_visual_review_comparison_status}`
              : ''}
          </p>
          <p className="validation-meta">
            Latest review session: {formatTimestamp(operatorReviewStatus.latest_review_session_at)} —
            latest export: {formatTimestamp(operatorReviewStatus.latest_review_export_at)} —
            latest digest: {formatTimestamp(operatorReviewStatus.latest_digest_at)}
            {operatorReviewStatus.latest_visual_review_at
              ? ` — latest visual review: ${formatTimestamp(operatorReviewStatus.latest_visual_review_at)}`
              : ''}
          </p>
          {operatorReviewStatus.latest_visual_review_path ? (
            <p className="validation-meta">
              Visual review path: <code>{operatorReviewStatus.latest_visual_review_path}</code>
              {operatorReviewStatus.visual_review_artifact_count != null
                ? ` — artifacts: ${operatorReviewStatus.visual_review_artifact_count}`
                : ''}
              {operatorReviewStatus.visual_review_missing_artifact_count != null
                ? ` — missing: ${operatorReviewStatus.visual_review_missing_artifact_count}`
                : ''}
            </p>
          ) : null}
          {operatorReviewStatus.latest_visual_review_markdown_path ? (
            <p className="validation-meta">
              Visual review Markdown:{' '}
              <code>{operatorReviewStatus.latest_visual_review_markdown_path}</code>
            </p>
          ) : null}
          {operatorReviewStatus.scheduled_visual_review?.visual_review_requested ? (
            <p className="validation-meta">
              Scheduled visual review:{' '}
              {operatorReviewStatus.scheduled_visual_review.visual_review_generated
                ? 'generated'
                : 'skipped'}
              {operatorReviewStatus.scheduled_visual_review.visual_review_reason
                ? ` — ${operatorReviewStatus.scheduled_visual_review.visual_review_reason}`
                : ''}
            </p>
          ) : null}
          <SafetyNote />
        </section>
      ) : null}
      {operatorWorkflowPresets?.presets && operatorWorkflowPresets.presets.length > 0 ? (
        <CollapsibleSection
          title="Operator Workflow Presets"
          className="validation-operator-workflow-presets"
          summary={
            <p className="validation-meta">
              {operatorWorkflowPresets.recommended_count ?? 0} recommended — local workflow guidance only
            </p>
          }
        >
          <p className="validation-meta">
            Presets are grouped by workflow category — advisory only. Use Copy to paste commands into
            your terminal; the UI does not execute them.
          </p>
          <div className="validation-workflow-preset-filters">
            <fieldset className="validation-workflow-preset-filter-fieldset">
              <legend className="validation-meta">Show presets</legend>
              <label className="validation-workflow-preset-filter-option">
                <input
                  type="radio"
                  name="workflow-preset-filter"
                  checked={presetFilterMode === 'all'}
                  onChange={() => setPresetFilterMode('all')}
                />
                Show all presets
              </label>
              <label className="validation-workflow-preset-filter-option">
                <input
                  type="radio"
                  name="workflow-preset-filter"
                  checked={presetFilterMode === 'recommended'}
                  onChange={() => setPresetFilterMode('recommended')}
                />
                Show recommended only
              </label>
            </fieldset>
            {workflowPresetGroups.length > 1 ? (
              <label className="validation-workflow-preset-group-filter">
                <span className="validation-meta">Group</span>
                <select
                  value={presetGroupFilter}
                  onChange={(event) => setPresetGroupFilter(event.target.value)}
                  aria-label="Filter presets by group"
                >
                  <option value="all">All groups</option>
                  {workflowPresetGroups.map((group) => (
                    <option key={group.group_id} value={group.group_id}>
                      {group.group_title ?? group.group_id}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <p className="validation-meta validation-workflow-preset-visible-count">
              Showing {visibleWorkflowPresetCount} of {operatorWorkflowPresets.preset_count ?? 0}{' '}
              preset{operatorWorkflowPresets.preset_count === 1 ? '' : 's'}
            </p>
          </div>
          {visibleWorkflowPresetCount === 0 ? (
            <p className="validation-meta">No presets match the current filters.</p>
          ) : null}
          {visibleWorkflowPresetGroups.map((group) => (
            <section key={group.group_id} className="validation-workflow-preset-group">
              <h4 className="validation-workflow-preset-group-title">
                {group.group_title ?? group.group_id}
                {group.recommended_count ? ` — ${group.recommended_count} recommended` : ''}
              </h4>
              <ul className="validation-history-list validation-workflow-preset-list">
                {(group.presets ?? []).map((entry) => {
                  const preset = workflowPresetById[entry.preset_id];
                  if (!preset) {
                    return null;
                  }
                  return (
                    <li
                      key={preset.preset_id}
                      className={
                        preset.recommended
                          ? 'validation-workflow-preset-recommended'
                          : 'validation-meta'
                      }
                    >
                      {preset.short_reason ? (
                        <p className="validation-meta">
                          <strong>{preset.short_reason}</strong>
                        </p>
                      ) : null}
                      <p className="validation-meta">
                        <strong>{preset.title}</strong> — recommended:{' '}
                        {yesNo(preset.recommended ?? false)}
                        {preset.recommendation_reason ? ` (${preset.recommendation_reason})` : ''}
                        {preset.recommended_priority != null
                          ? ` — priority ${preset.recommended_priority}`
                          : ''}
                      </p>
                      <p className="validation-meta">{preset.when_to_use}</p>
                      {preset.suggested_action ? (
                        <p className="validation-meta">Suggested action: {preset.suggested_action}</p>
                      ) : null}
                      {preset.runbook_path ? (
                        <p className="validation-meta">
                          Runbook: <code>{preset.runbook_path}</code>
                          {preset.runbook_section ? ` — ${preset.runbook_section}` : ''}
                          {preset.runbook_anchor ? ` (#${preset.runbook_anchor})` : ''}
                        </p>
                      ) : null}
                      <CommandLine command={preset.command} label="Exact command" manualCopy />
                      {(preset.expected_outputs?.length ?? 0) > 0 ? (
                        <p className="validation-meta">
                          Expected outputs: {preset.expected_outputs?.join('; ')}
                        </p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
          <SafetyNote />
        </CollapsibleSection>
      ) : null}
      <CollapsibleSection
        title="MRMS Visual Review"
        className="validation-visual-review"
        summary={
          <p className="validation-meta">
            {mrmsVisualReview?.available
              ? `Latest ${formatTimestamp(mrmsVisualReview.created_at)} — ${mrmsVisualReview.artifact_count ?? 0} artifacts, ${mrmsVisualReview.missing_artifact_count ?? 0} missing`
              : 'No visual review yet — run make mrms-visual-review'}
          </p>
        }
      >
        <p className="validation-meta">
          Local visual review only — inspects existing tile/render artifacts on disk. Does not verify
          MRMS, clear alerts, enable production rendering, or download/decode new MRMS data.
        </p>
        {mrmsVisualReviewComparison?.available ? (
          <p className="validation-meta">
            Comparison status: {mrmsVisualReviewComparison.overall_visual_review_diff_status ?? '—'}
            {mrmsVisualReviewComparison.compared_at
              ? ` — compared ${formatTimestamp(mrmsVisualReviewComparison.compared_at)}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            Comparison: no baseline yet — run <code>make mrms-visual-review-compare</code> after two
            visual reviews.
          </p>
        )}
        {mrmsVisualReviewComparison?.artifact_count_change ? (
          <p className="validation-meta">
            Artifact count change: {mrmsVisualReviewComparison.artifact_count_change.baseline ?? '—'}{' '}
            → {mrmsVisualReviewComparison.artifact_count_change.latest ?? '—'}
          </p>
        ) : null}
        {mrmsVisualReviewComparison?.missing_artifact_count_change ? (
          <p className="validation-meta">
            Missing artifact count change:{' '}
            {mrmsVisualReviewComparison.missing_artifact_count_change.baseline ?? '—'} →{' '}
            {mrmsVisualReviewComparison.missing_artifact_count_change.latest ?? '—'}
          </p>
        ) : null}
        {((mrmsVisualReviewComparison?.tile_modes_added?.length ?? 0) > 0 ||
          (mrmsVisualReviewComparison?.tile_modes_removed?.length ?? 0) > 0) ? (
          <p className="validation-meta">
            Tile modes added:{' '}
            {(mrmsVisualReviewComparison?.tile_modes_added ?? []).join(', ') || '—'} — removed:{' '}
            {(mrmsVisualReviewComparison?.tile_modes_removed ?? []).join(', ') || '—'}
          </p>
        ) : null}
        <p className="validation-meta">
          Regenerate visual review recommended:{' '}
          {yesNo(mrmsVisualReviewHint?.visual_review_regeneration_recommended ?? false)}
          {mrmsVisualReviewHint?.reason ? ` — ${mrmsVisualReviewHint.reason}` : ''}
        </p>
        {mrmsVisualReviewHint?.latest_relevant_evidence_at ? (
          <p className="validation-meta">
            Latest relevant evidence:{' '}
            {formatTimestamp(mrmsVisualReviewHint.latest_relevant_evidence_at)}
          </p>
        ) : null}
        {mrmsVisualReview?.available ? (
          <>
            <p className="validation-meta">
              Latest review: {formatTimestamp(mrmsVisualReview.created_at)}
            </p>
            <p className="validation-meta">
              JSON: <code>{mrmsVisualReview.json_path}</code>
            </p>
            <p className="validation-meta">
              Markdown: <code>{mrmsVisualReview.markdown_path}</code>
            </p>
            <p className="validation-meta">
              Layers inspected: {(mrmsVisualReview.layers_inspected ?? []).join(', ') || '—'} —{' '}
              timestamps: {mrmsVisualReview.timestamp_count ?? 0}
            </p>
            <p className="validation-meta">
              Artifacts found: {mrmsVisualReview.artifact_count ?? 0} — missing warnings:{' '}
              {mrmsVisualReview.missing_artifact_count ?? 0}
            </p>
            <p className="validation-meta">
              Tile modes: {(mrmsVisualReview.tile_modes_found ?? []).join(', ') || '—'}
            </p>
            {mrmsVisualReview.history_count != null && mrmsVisualReview.history_count > 0 ? (
              <p className="validation-meta">
                History entries: {mrmsVisualReview.history_count} (max 25)
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Generate a local manifest with <code>make mrms-visual-review</code> to inspect placeholder,
            decoded prototype, and production-gated tile evidence.
          </p>
        )}
        <CollapsibleSection
          title="Visual review sample set (drilldown)"
          className="validation-visual-review-sample-set"
          summary={
            <p className="validation-meta">
              {mrmsVisualReviewSampleSet?.available
                ? `${mrmsVisualReviewSampleSet.entry_count ?? 0} selected — ${mrmsVisualReviewSampleSet.selection_mode ?? '—'}`
                : 'No sample set yet — generate a recommended subset for manual inspection'}
            </p>
          }
        >
          <p className="validation-meta">
            Local-only visual review sample set. Does not verify MRMS, clear alerts, enable production
            rendering, or create production tiles.
          </p>
          {mrmsVisualReviewSampleSet?.available ? (
            <>
              <p className="validation-meta">
                Created: {formatTimestamp(mrmsVisualReviewSampleSet.created_at)}
              </p>
              <p className="validation-meta">
                Entries: {mrmsVisualReviewSampleSet.entry_count ?? 0} — mode:{' '}
                {mrmsVisualReviewSampleSet.selection_mode ?? '—'}
              </p>
              <p className="validation-meta">
                Source visual review:{' '}
                {formatTimestamp(mrmsVisualReviewSampleSet.source_visual_review_at)}
              </p>
              <p className="validation-meta">
                JSON: <code>{mrmsVisualReviewSampleSet.json_path}</code>
              </p>
              <p className="validation-meta">
                Markdown: <code>{mrmsVisualReviewSampleSet.markdown_path}</code>
              </p>
              {mrmsVisualReviewSampleSet.context?.visual_review_regeneration_recommended ? (
                <p className="validation-meta">
                  Visual review regeneration recommended —{' '}
                  {mrmsVisualReviewSampleSet.context.visual_review_hint_reason ?? 'stale evidence'}
                </p>
              ) : null}
              {mrmsVisualReviewSampleSet.context?.latest_visual_review_comparison_status ? (
                <p className="validation-meta">
                  Comparison status:{' '}
                  {mrmsVisualReviewSampleSet.context.latest_visual_review_comparison_status}
                </p>
              ) : null}
            </>
          ) : (
            <p className="validation-meta">
              Build a small recommended sample from the latest visual review manifest for closer manual
              inspection.
            </p>
          )}
          <button
            type="button"
            className="validation-refresh"
            onClick={() => void handleSampleSetGenerate()}
            disabled={sampleSetSubmitting || !mrmsVisualReview?.available}
          >
            {sampleSetSubmitting ? 'Generating…' : 'Generate recommended sample set (local only)'}
          </button>
          {sampleSetMessage ? <p className="validation-meta">{sampleSetMessage}</p> : null}
          {sampleSetError ? <p className="validation-warn">{sampleSetError}</p> : null}
          {mrmsVisualReviewSampleSet?.available ? (
            <>
              <p className="validation-warn">
                Local-only advisory review. Does not verify MRMS, enable production rendering, create
                production tiles, or clear alerts. Candidate readiness is not production authorization.
              </p>
              {mrmsVisualReviewSampleReadiness ? (
                <>
                  <p className="validation-meta">
                    Advisory readiness: {mrmsVisualReviewSampleReadiness.readiness_level ?? '—'} —{' '}
                    {mrmsVisualReviewSampleReadiness.readiness_reason ?? '—'}
                  </p>
                  <p className="validation-meta">
                    Reviewed {mrmsVisualReviewSampleReadiness.reviewed_samples ?? 0} /{' '}
                    {mrmsVisualReviewSampleReadiness.total_selected_samples ?? 0} — acceptable:{' '}
                    {mrmsVisualReviewSampleReadiness.acceptable_count ?? 0}, questionable:{' '}
                    {mrmsVisualReviewSampleReadiness.questionable_count ?? 0}, rejected:{' '}
                    {mrmsVisualReviewSampleReadiness.rejected_count ?? 0}
                  </p>
                  <p className="validation-meta">
                    Missing artifact samples:{' '}
                    {mrmsVisualReviewSampleReadiness.missing_artifact_samples ?? 0} — stale:{' '}
                    {mrmsVisualReviewSampleReadiness.stale_samples ?? 0} — needs follow-up:{' '}
                    {mrmsVisualReviewSampleReadiness.needs_followup_samples ?? 0}
                  </p>
                  {mrmsVisualReviewSampleReadiness.markdown_path ? (
                    <p className="validation-meta">
                      Readiness Markdown:{' '}
                      <code>{mrmsVisualReviewSampleReadiness.markdown_path}</code>
                    </p>
                  ) : null}
                  {mrmsVisualReviewSampleReadiness.annotations_path ? (
                    <p className="validation-meta">
                      Annotations JSON:{' '}
                      <code>{mrmsVisualReviewSampleReadiness.annotations_path}</code>
                    </p>
                  ) : null}
                </>
              ) : null}
              {(mrmsVisualReviewSampleReadiness?.entry_summaries ?? []).map((entry) => {
                const sampleKey = entry.sample_key ?? '';
                const draft = annotationDrafts[sampleKey] ?? {
                  status: entry.status ?? 'unreviewed',
                  notes: entry.operator_notes ?? '',
                  reviewer: entry.reviewer_label ?? '',
                };
                return (
                  <div key={sampleKey} className="validation-meta validation-sample-entry">
                    <p>
                      <strong>{formatTimestamp(entry.timestamp)}</strong> — {entry.tile_mode ?? '—'} —{' '}
                      <code>{entry.primary_artifact_path ?? '—'}</code>
                    </p>
                    <p>
                      Sample key: <code>{sampleKey}</code>
                      {(entry.issue_tags ?? []).length > 0
                        ? ` — tags: ${(entry.issue_tags ?? []).join(', ')}`
                        : ''}
                    </p>
                    <label className="validation-meta">
                      Status
                      <select
                        value={draft.status}
                        onChange={(event) =>
                          setAnnotationDrafts((previous) => ({
                            ...previous,
                            [sampleKey]: { ...draft, status: event.target.value },
                          }))
                        }
                      >
                        <option value="unreviewed">unreviewed</option>
                        <option value="acceptable">acceptable</option>
                        <option value="questionable">questionable</option>
                        <option value="rejected">rejected</option>
                      </select>
                    </label>
                    <label className="validation-meta">
                      Operator notes
                      <textarea
                        value={draft.notes}
                        onChange={(event) =>
                          setAnnotationDrafts((previous) => ({
                            ...previous,
                            [sampleKey]: { ...draft, notes: event.target.value },
                          }))
                        }
                        rows={2}
                      />
                    </label>
                    <label className="validation-meta">
                      Reviewer label
                      <input
                        type="text"
                        value={draft.reviewer}
                        onChange={(event) =>
                          setAnnotationDrafts((previous) => ({
                            ...previous,
                            [sampleKey]: { ...draft, reviewer: event.target.value },
                          }))
                        }
                      />
                    </label>
                    <button
                      type="button"
                      className="validation-refresh"
                      onClick={() => void handleSampleAnnotationSave(sampleKey)}
                      disabled={annotationSavingKey === sampleKey}
                    >
                      {annotationSavingKey === sampleKey ? 'Saving…' : 'Save local annotation'}
                    </button>
                  </div>
                );
              })}
              <button
                type="button"
                className="validation-refresh"
                onClick={() => void handleReadinessRefresh()}
                disabled={readinessRefreshing}
              >
                {readinessRefreshing ? 'Refreshing…' : 'Refresh readiness summary (local only)'}
              </button>
              {annotationMessage ? <p className="validation-meta">{annotationMessage}</p> : null}
              {readinessMessage ? <p className="validation-meta">{readinessMessage}</p> : null}
              {annotationError ? <p className="validation-warn">{annotationError}</p> : null}
              <CommandLine
                command={
                  mrmsVisualReviewSampleReadiness?.suggested_command ??
                  'make mrms-visual-review-readiness --refresh'
                }
                label="Suggested readiness command"
                manualCopy
              />
            </>
          ) : null}
          <CommandLine
            command={
              mrmsVisualReviewSampleSet?.suggested_command ?? 'make mrms-visual-review-sample-set'
            }
            label="Suggested sample-set command"
            manualCopy
          />
          <SafetyNote />
        </CollapsibleSection>
        <CommandLine
          command={
            mrmsVisualReviewHint?.suggested_command ??
            mrmsVisualReview?.suggested_next_command ??
            'make mrms-visual-review'
          }
          label="Suggested command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate preflight"
        className="validation-render-candidate-preflight"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidatePreflight?.preflight_level
              ? `Advisory ${mrmsRenderCandidatePreflight.preflight_level} — ${mrmsRenderCandidatePreflight.blocking_items?.length ?? 0} blocking, ${mrmsRenderCandidatePreflight.warnings?.length ?? 0} warnings`
              : 'No preflight report yet — run make mrms-render-candidate-preflight --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local advisory preflight only. Does not verify MRMS, enable production rendering, create
          production tiles, clear alerts, or authorize production use.{' '}
          <code>candidate_preflight_ready</code> is not production authorization.
        </p>
        {mrmsRenderCandidatePreflight ? (
          <>
            <p className="validation-meta">
              Preflight level: {mrmsRenderCandidatePreflight.preflight_level ?? '—'} — reason:{' '}
              {mrmsRenderCandidatePreflight.preflight_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Evidence found — visual review:{' '}
              {yesNo(mrmsRenderCandidatePreflight.evidence_found?.visual_review ?? false)} — sample set:{' '}
              {yesNo(mrmsRenderCandidatePreflight.evidence_found?.sample_set ?? false)} — sample
              readiness: {yesNo(mrmsRenderCandidatePreflight.evidence_found?.sample_readiness ?? false)}{' '}
              — required docs: {yesNo(mrmsRenderCandidatePreflight.evidence_found?.required_docs ?? false)}
            </p>
            {(mrmsRenderCandidatePreflight.blocking_items ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blocking items</strong>
                <ul>
                  {(mrmsRenderCandidatePreflight.blocking_items ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blocking items: none</p>
            )}
            {(mrmsRenderCandidatePreflight.warnings ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Warnings</strong>
                <ul>
                  {(mrmsRenderCandidatePreflight.warnings ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Warnings: none</p>
            )}
            {mrmsRenderCandidatePreflight.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidatePreflight.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidatePreflight.markdown_path ? (
              <p className="validation-meta">
                Markdown: <code>{mrmsRenderCandidatePreflight.markdown_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Generate a local preflight report after visual review, sample-set selection, and sample
            readiness scoring are in place.
          </p>
        )}
        <button
          type="button"
          className="validation-refresh"
          onClick={() => void handlePreflightRefresh()}
          disabled={preflightRefreshing}
        >
          {preflightRefreshing ? 'Refreshing…' : 'Refresh preflight report (local only)'}
        </button>
        {preflightMessage ? <p className="validation-meta">{preflightMessage}</p> : null}
        {preflightError ? <p className="validation-warn">{preflightError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidatePreflight?.suggested_command ??
            'make mrms-render-candidate-preflight --refresh'
          }
          label="Suggested preflight command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate dry-run plan"
        className="validation-render-candidate-dry-run-plan"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateDryRunPlan?.plan_status
              ? `Advisory ${mrmsRenderCandidateDryRunPlan.plan_status} — ${mrmsRenderCandidateDryRunPlan.blocking_items?.length ?? 0} blocking`
              : 'No dry-run plan yet — run make mrms-render-candidate-dry-run-plan --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local advisory dry-run plan only. Does not verify MRMS, enable production rendering,
          download/decode/render by default, create production tiles, clear alerts, or authorize
          production use. Listed operator commands are for a future gated attempt — not run now.
        </p>
        {mrmsRenderCandidateDryRunPlan ? (
          <>
            <p className="validation-meta">
              Plan status: {mrmsRenderCandidateDryRunPlan.plan_status ?? '—'} — reason:{' '}
              {mrmsRenderCandidateDryRunPlan.plan_reason ?? '—'}
            </p>
            {(mrmsRenderCandidateDryRunPlan.blocking_items ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateDryRunPlan.blocking_items ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blockers: none</p>
            )}
            {(mrmsRenderCandidateDryRunPlan.warnings ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Warnings</strong>
                <ul>
                  {(mrmsRenderCandidateDryRunPlan.warnings ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateDryRunPlan.prerequisites ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Prerequisites</strong>
                <ul>
                  {(mrmsRenderCandidateDryRunPlan.prerequisites ?? []).slice(0, 5).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateDryRunPlan.stop_conditions ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Stop conditions</strong>
                <ul>
                  {(mrmsRenderCandidateDryRunPlan.stop_conditions ?? []).slice(0, 5).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateDryRunPlan.expected_artifacts ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Expected outputs</strong>
                <ul>
                  {(mrmsRenderCandidateDryRunPlan.expected_artifacts ?? []).slice(0, 6).map((item) => (
                    <li key={item.path}>
                      <code>{item.path}</code> — {item.description}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateDryRunPlan.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidateDryRunPlan.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateDryRunPlan.markdown_path ? (
              <p className="validation-meta">
                Markdown: <code>{mrmsRenderCandidateDryRunPlan.markdown_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateDryRunPlan.next_phase_recommendation ? (
              <p className="validation-meta">
                Next phase: {mrmsRenderCandidateDryRunPlan.next_phase_recommendation}
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Generate a local dry-run plan after preflight and sample readiness evidence are in place.
          </p>
        )}
        <button
          type="button"
          className="validation-refresh"
          onClick={() => void handleDryRunPlanRefresh()}
          disabled={dryRunPlanRefreshing}
        >
          {dryRunPlanRefreshing ? 'Refreshing…' : 'Refresh dry-run plan (local only)'}
        </button>
        {dryRunPlanMessage ? <p className="validation-meta">{dryRunPlanMessage}</p> : null}
        {dryRunPlanError ? <p className="validation-warn">{dryRunPlanError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateDryRunPlan?.suggested_command ??
            'make mrms-render-candidate-dry-run-plan --refresh'
          }
          label="Suggested dry-run plan command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate command scaffold"
        className="validation-render-candidate-scaffold"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateScaffold?.scaffold_status
              ? `Advisory ${mrmsRenderCandidateScaffold.scaffold_status} — ${mrmsRenderCandidateScaffold.blocking_items?.length ?? 0} blocking`
              : 'No scaffold report yet — run make mrms-render-candidate-scaffold --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          This is a disabled-by-default local scaffold. It does not verify MRMS, enable production
          rendering, download/decode/render by default, create or serve production tiles, clear
          alerts, or authorize production use. Future candidate commands listed below are not executed
          by default.
        </p>
        {mrmsRenderCandidateScaffold ? (
          <>
            <p className="validation-meta">
              Scaffold status: {mrmsRenderCandidateScaffold.scaffold_status ?? '—'} — reason:{' '}
              {mrmsRenderCandidateScaffold.scaffold_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Dry-run/no-op mode: {mrmsRenderCandidateScaffold.dry_run_mode ? 'yes' : 'no'} — execute
              performed: {mrmsRenderCandidateScaffold.execute_performed ? 'yes' : 'no'}
            </p>
            {(mrmsRenderCandidateScaffold.blocking_items ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateScaffold.blocking_items ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blockers: none</p>
            )}
            {(mrmsRenderCandidateScaffold.warnings ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Warnings</strong>
                <ul>
                  {(mrmsRenderCandidateScaffold.warnings ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateScaffold.safety_gates ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Safety gates</strong>
                <ul>
                  {(mrmsRenderCandidateScaffold.safety_gates ?? []).slice(0, 8).map((gate) => (
                    <li key={gate.id ?? gate.message}>
                      {gate.id ?? 'gate'}: {gate.passed ? 'passed' : 'failed'} — {gate.message}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateScaffold.future_candidate_commands ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Future candidate commands (not executed by default)</strong>
                <ul>
                  {(mrmsRenderCandidateScaffold.future_candidate_commands ?? []).map((item) => (
                    <li key={item.command}>
                      <code>{item.command}</code> — executed_by_scaffold={item.executed_by_scaffold}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateScaffold.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidateScaffold.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateScaffold.markdown_path ? (
              <p className="validation-meta">
                Markdown: <code>{mrmsRenderCandidateScaffold.markdown_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateScaffold.next_phase_recommendation ? (
              <p className="validation-meta">
                Next phase: {mrmsRenderCandidateScaffold.next_phase_recommendation}
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No scaffold report yet. Run{' '}
            <code>make mrms-render-candidate-scaffold --refresh</code> after preflight and dry-run
            plan are ready.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={scaffoldRefreshing}
          onClick={() => void handleScaffoldRefresh()}
        >
          {scaffoldRefreshing ? 'Refreshing scaffold…' : 'Refresh scaffold report (local only)'}
        </button>
        {scaffoldMessage ? <p className="validation-meta">{scaffoldMessage}</p> : null}
        {scaffoldError ? <p className="validation-warn">{scaffoldError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateScaffold?.suggested_command ??
            'make mrms-render-candidate-scaffold --refresh'
          }
          label="Suggested scaffold command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox"
        className="validation-render-candidate-sandbox"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandbox?.sandbox_status
              ? `Advisory ${mrmsRenderCandidateSandbox.sandbox_status} — ${mrmsRenderCandidateSandbox.blocking_items?.length ?? 0} blocking`
              : 'No sandbox report yet — run make mrms-render-candidate-sandbox --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          This is a local candidate artifact sandbox only. It does not verify MRMS, enable production
          rendering, download/decode/render by default, create or serve production tiles, clear alerts,
          or authorize production use. Cleanup is report-only unless explicitly confirmed.
        </p>
        {mrmsRenderCandidateSandbox ? (
          <>
            <p className="validation-meta">
              Sandbox status: {mrmsRenderCandidateSandbox.sandbox_status ?? '—'} — reason:{' '}
              {mrmsRenderCandidateSandbox.sandbox_reason ?? '—'}
            </p>
            {mrmsRenderCandidateSandbox.sandbox_root ? (
              <p className="validation-meta">
                Sandbox root: <code>{mrmsRenderCandidateSandbox.sandbox_root}</code>
              </p>
            ) : null}
            <p className="validation-meta">
              Isolated from production tile serving:{' '}
              {mrmsRenderCandidateSandbox.isolation_status ? 'yes' : 'no'} — cleanup mode:{' '}
              {mrmsRenderCandidateSandbox.cleanup_mode ?? 'report_only'} — delete performed:{' '}
              {mrmsRenderCandidateSandbox.delete_performed ? 'yes' : 'no'}
            </p>
            {(mrmsRenderCandidateSandbox.expected_subdirectories ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Expected subdirectories</strong>
                <ul>
                  {(mrmsRenderCandidateSandbox.expected_subdirectories ?? []).map((name) => (
                    <li key={name}>
                      <code>{name}/</code> —{' '}
                      {(mrmsRenderCandidateSandbox.existing_subdirectories ?? []).includes(name)
                        ? 'present'
                        : 'missing'}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandbox.blocking_items ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateSandbox.blocking_items ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blockers: none</p>
            )}
            {(mrmsRenderCandidateSandbox.warnings ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Warnings</strong>
                <ul>
                  {(mrmsRenderCandidateSandbox.warnings ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandbox.safety_gates ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Safety gates</strong>
                <ul>
                  {(mrmsRenderCandidateSandbox.safety_gates ?? []).slice(0, 8).map((gate) => (
                    <li key={gate.id ?? gate.message}>
                      {gate.id ?? 'gate'}: {gate.passed ? 'passed' : 'failed'} — {gate.message}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandbox.cleanup_candidates ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Cleanup candidates (report-only)</strong>
                <ul>
                  {(mrmsRenderCandidateSandbox.cleanup_candidates ?? []).map((item) => (
                    <li key={item.path}>
                      <code>{item.path}</code> — {item.category} ({item.file_count} files)
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandbox.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidateSandbox.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandbox.markdown_path ? (
              <p className="validation-meta">
                Markdown: <code>{mrmsRenderCandidateSandbox.markdown_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandbox.next_phase_recommendation ? (
              <p className="validation-meta">
                Next phase: {mrmsRenderCandidateSandbox.next_phase_recommendation}
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No sandbox report yet. Run <code>make mrms-render-candidate-sandbox --refresh</code> to
            create the local layout and advisory report.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={sandboxRefreshing}
          onClick={() => void handleSandboxRefresh()}
        >
          {sandboxRefreshing ? 'Refreshing sandbox…' : 'Refresh sandbox report (local only)'}
        </button>
        {sandboxMessage ? <p className="validation-meta">{sandboxMessage}</p> : null}
        {sandboxError ? <p className="validation-warn">{sandboxError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandbox?.suggested_command ??
            'make mrms-render-candidate-sandbox --refresh'
          }
          label="Suggested sandbox command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox import/export"
        className="validation-render-candidate-sandbox-import-export"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxImportExport?.import_export_status
              ? `Advisory ${mrmsRenderCandidateSandboxImportExport.import_export_status} — schema ${mrmsRenderCandidateSandboxImportExport.schema_version ?? '—'}`
              : 'No import/export report yet — run make mrms-render-candidate-sandbox-export'}
          </p>
        }
      >
        <p className="validation-warn">
          This is local manifest import/export only. It does not verify MRMS, enable production
          rendering, download/decode/render, create or serve production tiles, clear alerts, or
          authorize production use. Imports are metadata/report-only.
        </p>
        {mrmsRenderCandidateSandboxImportExport ? (
          <>
            <p className="validation-meta">
              Status: {mrmsRenderCandidateSandboxImportExport.import_export_status ?? '—'} — reason:{' '}
              {mrmsRenderCandidateSandboxImportExport.import_export_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Schema version: {mrmsRenderCandidateSandboxImportExport.schema_version ?? '—'} — binary
              artifacts included:{' '}
              {mrmsRenderCandidateSandboxImportExport.binary_artifacts_included ? 'yes' : 'no'}
            </p>
            {(mrmsRenderCandidateSandboxImportExport.included_reports ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Included reports</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxImportExport.included_reports ?? []).map((item) => (
                    <li key={`${item.path}-${item.kind}`}>
                      <code>{item.path}</code> — {item.kind}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandboxImportExport.missing_inputs ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Missing inputs</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxImportExport.missing_inputs ?? []).map((item) => (
                    <li key={item}>
                      <code>{item}</code>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandboxImportExport.blockers ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxImportExport.blockers ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blockers: none</p>
            )}
            {(mrmsRenderCandidateSandboxImportExport.warnings ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Warnings</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxImportExport.warnings ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxImportExport.latest_export_json_path ? (
              <p className="validation-meta">
                Latest export JSON:{' '}
                <code>{mrmsRenderCandidateSandboxImportExport.latest_export_json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxImportExport.latest_import_json_path ? (
              <p className="validation-meta">
                Latest import JSON:{' '}
                <code>{mrmsRenderCandidateSandboxImportExport.latest_import_json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxImportExport.comparison?.changed_sandbox_status != null ? (
              <p className="validation-meta">
                Comparison changed sandbox status:{' '}
                {mrmsRenderCandidateSandboxImportExport.comparison.changed_sandbox_status ? 'yes' : 'no'}
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxImportExport.status_json_path ? (
              <p className="validation-meta">
                Status JSON: <code>{mrmsRenderCandidateSandboxImportExport.status_json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxImportExport.status_markdown_path ? (
              <p className="validation-meta">
                Status Markdown:{' '}
                <code>{mrmsRenderCandidateSandboxImportExport.status_markdown_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No import/export report yet. Run{' '}
            <code>make mrms-render-candidate-sandbox-export</code> to archive local sandbox metadata.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={importExportExporting}
          onClick={() => void handleImportExportExport()}
        >
          {importExportExporting ? 'Exporting…' : 'Export sandbox manifest (local only)'}
        </button>
        <button
          type="button"
          className="validation-action"
          disabled={importExportImporting}
          onClick={() => void handleImportExportImport()}
        >
          {importExportImporting ? 'Importing…' : 'Import latest export (validate only)'}
        </button>
        {importExportMessage ? <p className="validation-meta">{importExportMessage}</p> : null}
        {importExportError ? <p className="validation-warn">{importExportError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxImportExport?.suggested_import_export_command ??
            'make mrms-render-candidate-sandbox-import-export'
          }
          label="Suggested import/export command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison history"
        className="validation-render-candidate-sandbox-comparison-history"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonHistory?.history_status
              ? `Advisory ${mrmsRenderCandidateSandboxComparisonHistory.history_status} — ${mrmsRenderCandidateSandboxComparisonHistory.history_count ?? 0} entries`
              : 'No comparison history yet — run make mrms-render-candidate-sandbox-import-export'}
          </p>
        }
      >
        <p className="validation-warn">
          This is local manifest import/export comparison history only. It does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use. Imports are metadata/report-only.
        </p>
        {mrmsRenderCandidateSandboxComparisonHistory ? (
          <>
            <p className="validation-meta">
              History status: {mrmsRenderCandidateSandboxComparisonHistory.history_status ?? '—'} —
              reason: {mrmsRenderCandidateSandboxComparisonHistory.history_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Schema version: {mrmsRenderCandidateSandboxComparisonHistory.schema_version ?? '—'} —
              latest comparison: {mrmsRenderCandidateSandboxComparisonHistory.latest_comparison_type ?? '—'}{' '}
              ({mrmsRenderCandidateSandboxComparisonHistory.latest_comparison_status ?? '—'})
            </p>
            {(mrmsRenderCandidateSandboxComparisonHistory.recent_entries ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recent entries</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxComparisonHistory.recent_entries ?? []).map((item) => (
                    <li key={`${item.recorded_at}-${item.comparison_type}`}>
                      {item.recorded_at} — {item.comparison_type} ({item.comparison_status})
                      {item.changed_sandbox_status ? ' — sandbox status changed' : ''}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonHistory.blockers ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxComparisonHistory.blockers ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="validation-meta">Blockers: none</p>
            )}
            {mrmsRenderCandidateSandboxComparisonHistory.json_path ? (
              <p className="validation-meta">
                History JSON: <code>{mrmsRenderCandidateSandboxComparisonHistory.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonHistory.markdown_path ? (
              <p className="validation-meta">
                History Markdown:{' '}
                <code>{mrmsRenderCandidateSandboxComparisonHistory.markdown_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No comparison history yet. Run import/export workflow to record advisory comparisons.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={comparisonHistoryRefreshing}
          onClick={() => void handleComparisonHistoryRefresh()}
        >
          {comparisonHistoryRefreshing
            ? 'Refreshing comparison history…'
            : 'Refresh comparison history report (local only)'}
        </button>
        {comparisonHistoryMessage ? <p className="validation-meta">{comparisonHistoryMessage}</p> : null}
        {comparisonHistoryError ? <p className="validation-warn">{comparisonHistoryError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonHistory?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-history --refresh'
          }
          label="Suggested comparison history command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison trend hints"
        className="validation-render-candidate-sandbox-comparison-trend-hint"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonTrendHint?.trend
              ? `Advisory ${mrmsRenderCandidateSandboxComparisonTrendHint.hint_status ?? '—'} — trend ${mrmsRenderCandidateSandboxComparisonTrendHint.trend}`
              : 'No trend hint yet — run make mrms-render-candidate-sandbox-comparison-trend-hint --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          This is local manifest import/export comparison trend hints only. It does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use. Imports are metadata/report-only.
        </p>
        {mrmsRenderCandidateSandboxComparisonTrendHint ? (
          <>
            <p className="validation-meta">
              Hint status: {mrmsRenderCandidateSandboxComparisonTrendHint.hint_status ?? '—'} — reason:{' '}
              {mrmsRenderCandidateSandboxComparisonTrendHint.hint_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Trend: {mrmsRenderCandidateSandboxComparisonTrendHint.trend ?? '—'} — review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonTrendHint.trend_review_recommended ? 'yes' : 'no'} —
              changed streak: {mrmsRenderCandidateSandboxComparisonTrendHint.current_changed_streak ?? 0}
            </p>
            {mrmsRenderCandidateSandboxComparisonTrendHint.suggested_action ? (
              <p className="validation-meta">
                Suggested action: {mrmsRenderCandidateSandboxComparisonTrendHint.suggested_action}
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonTrendHint.recurring_signals ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recurring signals</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxComparisonTrendHint.recurring_signals ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonTrendHint.blockers ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxComparisonTrendHint.blockers ?? []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonTrendHint.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidateSandboxComparisonTrendHint.json_path}</code>
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonTrendHint.markdown_path ? (
              <p className="validation-meta">
                Markdown: <code>{mrmsRenderCandidateSandboxComparisonTrendHint.markdown_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No trend hint yet. Seed comparison history first, then run{' '}
            <code>make mrms-render-candidate-sandbox-comparison-trend-hint --refresh</code>.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={trendHintRefreshing}
          onClick={() => void handleTrendHintRefresh()}
        >
          {trendHintRefreshing ? 'Refreshing trend hint…' : 'Refresh trend hint report (local only)'}
        </button>
        {trendHintMessage ? <p className="validation-meta">{trendHintMessage}</p> : null}
        {trendHintError ? <p className="validation-warn">{trendHintError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonTrendHint?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-trend-hint --refresh'
          }
          label="Suggested trend hint command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison review acknowledgment"
        className="validation-render-candidate-sandbox-comparison-review-acknowledgment"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment?.available
              ? `Latest ack ${formatTimestamp(mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.created_at)} — ${mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.operator ?? '—'}`
              : 'No comparison review acknowledgment yet — record local review below'}
          </p>
        }
      >
        <p className="validation-warn">
          Local acknowledgment of reviewed sandbox comparison trend hints only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment?.available ? (
          <>
            <p className="validation-meta">
              Count: {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.count ?? 0} — related
              trend: {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.related_trend ?? '—'} —
              hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.related_hint_status ?? '—'}
            </p>
            {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.note ? (
              <p className="validation-meta">
                Latest note: {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.note}
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonReviewAcknowledgment.trend_review_still_recommended ? (
              <p className="validation-warn">
                Trend review still recommended — acknowledgment does not clear alerts or change trend
                hints.
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh trend hints first, then record acknowledgment after local review.
          </p>
        )}
        <form className="validation-form" onSubmit={(event) => void handleComparisonReviewAckSubmit(event)}>
          <label>
            Operator initials
            <input
              type="text"
              value={comparisonReviewAckOperator}
              onChange={(event) => setComparisonReviewAckOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label>
            Note (required)
            <textarea
              value={comparisonReviewAckNote}
              onChange={(event) => setComparisonReviewAckNote(event.target.value)}
              rows={2}
              required
            />
          </label>
          <label className="validation-checkbox">
            <input
              type="checkbox"
              checked={comparisonReviewAckTrendReview}
              onChange={(event) => setComparisonReviewAckTrendReview(event.target.checked)}
            />
            Acknowledged current trend review recommendation (local only)
          </label>
          <button type="submit" className="validation-action" disabled={comparisonReviewAckSubmitting}>
            {comparisonReviewAckSubmitting
              ? 'Recording acknowledgment…'
              : 'Record comparison review acknowledgment (local only)'}
          </button>
        </form>
        {comparisonReviewAckMessage ? (
          <p className="validation-meta">{comparisonReviewAckMessage}</p>
        ) : null}
        {comparisonReviewAckError ? <p className="validation-warn">{comparisonReviewAckError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonReviewAcknowledgment?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-review-acknowledgment --operator OP --note "Reviewed locally"'
          }
          label="Suggested review acknowledgment command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus?.rollup_status
              ? `Rollup ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.rollup_status} — ack ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.acknowledgment_status ?? '—'}`
              : 'No acknowledgment status yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local rollup linking trend hints to review acknowledgments only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus ? (
          <>
            <p className="validation-meta">
              Rollup status: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.rollup_status ?? '—'} —
              acknowledgment status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.acknowledgment_status ?? '—'} —
              reason: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.status_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Trend: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.trend ?? '—'} — hint
              status: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.hint_status ?? '—'} —
              review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.trend_review_recommended
                ? 'yes'
                : 'no'}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.stale_acknowledgment ? (
              <p className="validation-warn">
                Stale acknowledgment — trend hint changed since latest review acknowledgment.
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.suggested_action}
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.blockers ?? []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.blockers ?? []).map(
                    (item) => (
                      <li key={item}>{item}</li>
                    ),
                  )}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.json_path ? (
              <p className="validation-meta">
                JSON: <code>{mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus.json_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh trend hints and record acknowledgments first, then run{' '}
            <code>make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh</code>.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusRefreshing}
          onClick={() => void handleAckStatusRefresh()}
        >
          {ackStatusRefreshing
            ? 'Refreshing acknowledgment status…'
            : 'Refresh acknowledgment status rollup (local only)'}
        </button>
        {ackStatusMessage ? <p className="validation-meta">{ackStatusMessage}</p> : null}
        {ackStatusError ? <p className="validation-warn">{ackStatusError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatus?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh'
          }
          label="Suggested acknowledgment status command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status history"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-history"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory?.available
              ? `${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.history_count ?? 0} entries — latest coverage ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.latest_coverage_change ?? '—'}`
              : 'No acknowledgment status history yet — refresh acknowledgment status first'}
          </p>
        }
      >
        <p className="validation-warn">
          Local bounded history of acknowledgment status rollups only. Does not verify MRMS, enable
          production rendering, download/decode/render, create or serve production tiles, clear alerts,
          or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory?.available ? (
          <>
            <p className="validation-meta">
              Latest rollup:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.latest_rollup_status ??
                '—'}{' '}
              — acknowledgment:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.latest_acknowledgment_status ??
                '—'}
            </p>
            <p className="validation-meta">
              Latest coverage change:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.latest_coverage_change ??
                '—'}{' '}
              — recorded:{' '}
              {formatTimestamp(
                mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.latest_recorded_at,
              )}
            </p>
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.recent_entries ?? [])
              .length > 0 ? (
              <div className="validation-meta">
                <strong>Recent entries</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.recent_entries ??
                    []
                  ).map((item) => (
                    <li key={`${item.recorded_at}-${item.rollup_status}`}>
                      {item.recorded_at} — rollup {item.rollup_status} (ack {item.acknowledgment_status}
                      ) — coverage {item.coverage_change}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>{mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory.json_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Run{' '}
            <code>make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh</code>{' '}
            to seed history entries.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusHistoryRefreshing}
          onClick={() => void handleAckStatusHistoryRefresh()}
        >
          {ackStatusHistoryRefreshing
            ? 'Refreshing status history…'
            : 'Refresh acknowledgment status history report (local only)'}
        </button>
        {ackStatusHistoryMessage ? <p className="validation-meta">{ackStatusHistoryMessage}</p> : null}
        {ackStatusHistoryError ? <p className="validation-warn">{ackStatusHistoryError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistory?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history --refresh'
          }
          label="Suggested acknowledgment status history command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend hints"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint?.trend
              ? `Advisory ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.hint_status ?? '—'} — trend ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.trend}`
              : 'No status trend hint yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local advisory trend hints from acknowledgment status history only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint ? (
          <>
            <p className="validation-meta">
              Hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.hint_status ?? '—'} —
              reason: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.hint_reason ?? '—'}
            </p>
            <p className="validation-meta">
              Trend: {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.trend ?? '—'} —
              review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.trend_review_recommended
                ? 'yes'
                : 'no'}{' '}
              — needs-ack streak:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.current_needs_ack_streak ??
                0}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.suggested_action}
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.recurring_signals ?? [])
              .length > 0 ? (
              <div className="validation-meta">
                <strong>Recurring signals</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.recurring_signals ??
                    []
                  ).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>{mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint.json_path}</code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Seed acknowledgment status history first, then run{' '}
            <code>make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh</code>.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendHintRefreshing}
          onClick={() => void handleAckStatusTrendHintRefresh()}
        >
          {ackStatusTrendHintRefreshing
            ? 'Refreshing status trend hint…'
            : 'Refresh status trend hint report (local only)'}
        </button>
        {ackStatusTrendHintMessage ? <p className="validation-meta">{ackStatusTrendHintMessage}</p> : null}
        {ackStatusTrendHintError ? <p className="validation-warn">{ackStatusTrendHintError}</p> : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHint?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh'
          }
          label="Suggested status trend hint command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment?.available
              ? `Latest ack ${formatTimestamp(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.created_at)} — ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.operator ?? '—'}`
              : 'No status trend review acknowledgment yet — record local review below'}
          </p>
        }
      >
        <p className="validation-warn">
          Local acknowledgment of reviewed acknowledgment status trend hints only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment?.available ? (
          <>
            <p className="validation-meta">
              Count:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.count ?? 0}{' '}
              — related trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.related_trend ??
                '—'}{' '}
              — hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.related_hint_status ??
                '—'}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.note ? (
              <p className="validation-meta">
                Latest note:{' '}
                {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.note}
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment.trend_review_still_recommended ? (
              <p className="validation-warn">
                Status trend review still recommended — acknowledgment does not clear alerts or change
                trend hints.
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh status trend hints first, then record acknowledgment after local review.
          </p>
        )}
        <form
          className="validation-form"
          onSubmit={(event) => void handleAckStatusTrendReviewAckSubmit(event)}
        >
          <label>
            Operator initials
            <input
              type="text"
              value={ackStatusTrendReviewAckOperator}
              onChange={(event) => setAckStatusTrendReviewAckOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label>
            Note (required)
            <textarea
              value={ackStatusTrendReviewAckNote}
              onChange={(event) => setAckStatusTrendReviewAckNote(event.target.value)}
              rows={2}
              required
            />
          </label>
          <label className="validation-checkbox">
            <input
              type="checkbox"
              checked={ackStatusTrendReviewAckTrendReview}
              onChange={(event) => setAckStatusTrendReviewAckTrendReview(event.target.checked)}
            />
            Acknowledged current status trend review recommendation (local only)
          </label>
          <button type="submit" className="validation-action" disabled={ackStatusTrendReviewAckSubmitting}>
            {ackStatusTrendReviewAckSubmitting
              ? 'Recording acknowledgment…'
              : 'Record status trend review acknowledgment (local only)'}
          </button>
        </form>
        {ackStatusTrendReviewAckMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgment?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"'
          }
          label="Suggested status trend review acknowledgment command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus?.rollup_status
              ? `Rollup ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.rollup_status} — ack ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.acknowledgment_status ?? '—'}`
              : 'No status trend review acknowledgment status yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local rollup linking status trend hints to trend review acknowledgments only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear
          alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus ? (
          <>
            <p className="validation-meta">
              Rollup status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.rollup_status ??
                '—'}{' '}
              — acknowledgment status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.acknowledgment_status ??
                '—'}{' '}
              — reason:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.status_reason ??
                '—'}
            </p>
            <p className="validation-meta">
              Trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.trend ?? '—'}{' '}
              — hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.hint_status ??
                '—'}{' '}
              — review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.trend_review_recommended
                ? 'yes'
                : 'no'}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.stale_acknowledgment ? (
              <p className="validation-warn">
                Stale acknowledgment — status trend hint changed since latest trend review acknowledgment.
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {
                  mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.suggested_action
                }
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.blockers ??
              []).length > 0 ? (
              <div className="validation-meta">
                <strong>Blockers</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.blockers ??
                    []
                  ).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh status trend hints and record trend review acknowledgments first, then run{' '}
            <code>
              make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status
              --refresh
            </code>
            .
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusRefresh()}
        >
          {ackStatusTrendReviewAckStatusRefreshing
            ? 'Refreshing status trend review acknowledgment status…'
            : 'Refresh status trend review acknowledgment status rollup (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatus?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status --refresh'
          }
          label="Suggested status trend review acknowledgment status command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status history"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.available
              ? `${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.history_count ?? 0} entries — latest coverage ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_coverage_change ?? '—'}`
              : 'No status trend review acknowledgment status history yet — refresh status rollup first'}
          </p>
        }
      >
        <p className="validation-warn">
          Local bounded history of status trend review acknowledgment status rollups only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear alerts,
          or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.available ? (
          <>
            <p className="validation-meta">
              Latest rollup:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_rollup_status ??
                '—'}{' '}
              — acknowledgment:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_acknowledgment_status ??
                '—'}
            </p>
            <p className="validation-meta">
              Latest coverage change:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_coverage_change ??
                '—'}{' '}
              — recorded:{' '}
              {formatTimestamp(
                mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_recorded_at,
              )}
            </p>
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.recent_entries ??
              []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recent entries</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.recent_entries ??
                    []
                  ).map((item) => (
                    <li key={`${item.recorded_at}-${item.rollup_status}`}>
                      {item.recorded_at} — rollup {item.rollup_status} (ack {item.acknowledgment_status}
                      ) — coverage {item.coverage_change}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Run{' '}
            <code>
              make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status
              --refresh
            </code>{' '}
            to seed history entries.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusHistoryRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusHistoryRefresh()}
        >
          {ackStatusTrendReviewAckStatusHistoryRefreshing
            ? 'Refreshing status history…'
            : 'Refresh status trend review acknowledgment status history report (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusHistoryMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusHistoryMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusHistoryError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusHistoryError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history --refresh'
          }
          label="Suggested status trend review acknowledgment status history command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint?.trend
              ? `Advisory ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_status ?? '—'} — trend ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend}`
              : 'No status trend review acknowledgment status trend hint yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local advisory trend hints from trend review acknowledgment status history only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear alerts,
          or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint ? (
          <>
            <p className="validation-meta">
              Hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_status ??
                '—'}{' '}
              — reason:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_reason ??
                '—'}
            </p>
            <p className="validation-meta">
              Trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend ??
                '—'}{' '}
              — review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend_review_recommended
                ? 'yes'
                : 'no'}{' '}
              — needs-ack streak:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.current_needs_ack_streak ??
                0}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {
                  mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.suggested_action
                }
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.recurring_signals ??
              []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recurring signals</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.recurring_signals ??
                    []
                  ).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Seed trend review acknowledgment status history first, then run{' '}
            <code>
              make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint
              --refresh
            </code>
            .
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusTrendHintRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusTrendHintRefresh()}
        >
          {ackStatusTrendReviewAckStatusTrendHintRefreshing
            ? 'Refreshing status trend hint…'
            : 'Refresh status trend review acknowledgment status trend hint report (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusTrendHintMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusTrendHintMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusTrendHintError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusTrendHintError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh'
          }
          label="Suggested status trend review acknowledgment status trend hint command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment?.available
              ? `Latest ack ${formatTimestamp(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.created_at)} — ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.operator ?? '—'}`
              : 'No status trend review acknowledgment status trend review acknowledgment yet — record local review below'}
          </p>
        }
      >
        <p className="validation-warn">
          Local acknowledgment of reviewed trend review acknowledgment status trend hints only. Does not
          verify MRMS, enable production rendering, download/decode/render, create or serve production
          tiles, clear alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment?.available ? (
          <>
            <p className="validation-meta">
              Count:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.count ??
                0}{' '}
              — related trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.related_trend ??
                '—'}{' '}
              — hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.related_hint_status ??
                '—'}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.note ? (
              <p className="validation-meta">
                Latest note:{' '}
                {
                  mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.note
                }
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment.trend_review_still_recommended ? (
              <p className="validation-warn">
                Status trend review still recommended — acknowledgment does not clear alerts or change
                trend hints.
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh status trend review acknowledgment status trend hints first, then record acknowledgment
            after local review.
          </p>
        )}
        <form
          className="validation-form"
          onSubmit={(event) => void handleAckStatusTrendReviewAckStatusTrendReviewAckSubmit(event)}
        >
          <label>
            Operator initials
            <input
              type="text"
              value={ackStatusTrendReviewAckStatusTrendReviewAckOperator}
              onChange={(event) => setAckStatusTrendReviewAckStatusTrendReviewAckOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label>
            Note (required)
            <textarea
              value={ackStatusTrendReviewAckStatusTrendReviewAckNote}
              onChange={(event) => setAckStatusTrendReviewAckStatusTrendReviewAckNote(event.target.value)}
              rows={2}
              required
            />
          </label>
          <label className="validation-checkbox">
            <input
              type="checkbox"
              checked={ackStatusTrendReviewAckStatusTrendReviewAckTrendReview}
              onChange={(event) =>
                setAckStatusTrendReviewAckStatusTrendReviewAckTrendReview(event.target.checked)
              }
            />
            Acknowledged current status trend review recommendation (local only)
          </label>
          <button
            type="submit"
            className="validation-action"
            disabled={ackStatusTrendReviewAckStatusTrendReviewAckSubmitting}
          >
            {ackStatusTrendReviewAckStatusTrendReviewAckSubmitting
              ? 'Recording acknowledgment…'
              : 'Record status trend review acknowledgment status trend review acknowledgment (local only)'}
          </button>
        </form>
        {ackStatusTrendReviewAckStatusTrendReviewAckMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusTrendReviewAckMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusTrendReviewAckError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusTrendReviewAckError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgment?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"'
          }
          label="Suggested status trend review acknowledgment status trend review acknowledgment command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus?.rollup_status
              ? `Rollup ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.rollup_status} — ack ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.acknowledgment_status ?? '—'}`
              : 'No trend review acknowledgment status yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local rollup linking trend review acknowledgment status trend hints to trend review acknowledgments only.
          Does not verify MRMS, enable production rendering, download/decode/render, create or serve production
          tiles, clear alerts, or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus ? (
          <>
            <p className="validation-meta">
              Rollup status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.rollup_status ??
                '—'}{' '}
              — acknowledgment status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.acknowledgment_status ??
                '—'}{' '}
              — reason:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.status_reason ??
                '—'}
            </p>
            <p className="validation-meta">
              Trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.trend ??
                '—'}{' '}
              — hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.hint_status ??
                '—'}{' '}
              — review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.trend_review_recommended
                ? 'yes'
                : 'no'}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.stale_acknowledgment ? (
              <p className="validation-warn">
                Stale acknowledgment — re-review updated trend hints and record a fresh acknowledgment.
              </p>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {
                  mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.suggested_action
                }
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.blockers ??
              []).length > 0 ? (
              <div className="validation-warn">
                <strong>Blockers</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.blockers ??
                    []
                  ).map((blocker) => (
                    <li key={blocker}>{blocker}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh trend review acknowledgment status trend hints and record trend review acknowledgments first,
            then run{' '}
            <code>
              make
              mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status
              --refresh
            </code>
            .
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusTrendReviewAckStatusRefresh()}
        >
          {ackStatusTrendReviewAckStatusTrendReviewAckStatusRefreshing
            ? 'Refreshing trend review acknowledgment status…'
            : 'Refresh trend review acknowledgment status rollup (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusTrendReviewAckStatusMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusTrendReviewAckStatusError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatus?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status --refresh'
          }
          label="Suggested trend review acknowledgment status command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status history"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-history"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.available
              ? `${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.history_count ?? 0} entries — latest coverage ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_coverage_change ?? '—'}`
              : 'No trend review acknowledgment status history yet — refresh status rollup first'}
          </p>
        }
      >
        <p className="validation-warn">
          Local bounded history of trend review acknowledgment status rollups only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear alerts,
          or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.available ? (
          <>
            <p className="validation-meta">
              Latest rollup:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_rollup_status ??
                '—'}{' '}
              — acknowledgment:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_acknowledgment_status ??
                '—'}
            </p>
            <p className="validation-meta">
              Latest coverage change:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_coverage_change ??
                '—'}{' '}
              — recorded:{' '}
              {formatTimestamp(
                mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.latest_recorded_at,
              )}
            </p>
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.recent_entries ??
              []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recent entries</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.recent_entries ??
                    []
                  ).map((item) => (
                    <li key={`${item.recorded_at}-${item.rollup_status}`}>
                      {item.recorded_at} — rollup {item.rollup_status} (ack {item.acknowledgment_status}
                      ) — coverage {item.coverage_change}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Run{' '}
            <code>
              make
              mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status
              --refresh
            </code>{' '}
            to seed history entries.
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefresh()}
        >
          {ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryRefreshing
            ? 'Refreshing status history…'
            : 'Refresh trend review acknowledgment status history report (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusTrendReviewAckStatusHistoryError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistory?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-history --refresh'
          }
          label="Suggested trend review acknowledgment status history command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status trend hints"
        className="validation-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint"
        summary={
          <p className="validation-meta">
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint?.trend
              ? `Advisory ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_status ?? '—'} — trend ${mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend}`
              : 'No trend review acknowledgment status trend hint yet — run make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh'}
          </p>
        }
      >
        <p className="validation-warn">
          Local advisory trend hints from trend review acknowledgment status history only. Does not verify MRMS,
          enable production rendering, download/decode/render, create or serve production tiles, clear alerts,
          or authorize production use.
        </p>
        {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint ? (
          <>
            <p className="validation-meta">
              Hint status:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_status ??
                '—'}{' '}
              — reason:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.hint_reason ??
                '—'}
            </p>
            <p className="validation-meta">
              Trend:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend ??
                '—'}{' '}
              — review recommended:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.trend_review_recommended
                ? 'yes'
                : 'no'}{' '}
              — needs-ack streak:{' '}
              {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.current_needs_ack_streak ??
                0}
            </p>
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.suggested_action ? (
              <p className="validation-meta">
                Suggested action:{' '}
                {
                  mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.suggested_action
                }
              </p>
            ) : null}
            {(mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.recurring_signals ??
              []).length > 0 ? (
              <div className="validation-meta">
                <strong>Recurring signals</strong>
                <ul>
                  {(
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.recurring_signals ??
                    []
                  ).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.json_path ? (
              <p className="validation-meta">
                JSON:{' '}
                <code>
                  {
                    mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint.json_path
                  }
                </code>
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Seed trend review acknowledgment status history first, then run{' '}
            <code>
              make
              mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint
              --refresh
            </code>
            .
          </p>
        )}
        <button
          type="button"
          className="validation-action"
          disabled={ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing}
          onClick={() => void handleAckStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefresh()}
        >
          {ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintRefreshing
            ? 'Refreshing trend hint…'
            : 'Refresh trend review acknowledgment status trend hint report (local only)'}
        </button>
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage ? (
          <p className="validation-meta">{ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintMessage}</p>
        ) : null}
        {ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError ? (
          <p className="validation-warn">{ackStatusTrendReviewAckStatusTrendReviewAckStatusTrendHintError}</p>
        ) : null}
        <CommandLine
          command={
            mrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHint?.suggested_command ??
            'make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh'
          }
          label="Suggested trend review acknowledgment status trend hint command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="Candidate trend-hint review acknowledgments"
        className="validation-render-candidate-trend-hint-review-acknowledgment"
        summary={
          <p className="validation-meta">
            {trendHintReviewAck?.available
              ? `Latest ack ${formatTimestamp(trendHintReviewAck.created_at)} — ${trendHintReviewAck.operator ?? '—'}`
              : 'No candidate trend-hint review acknowledgment yet — record local review below'}
          </p>
        }
      >
        <p className="validation-warn">
          Local acknowledgment of reviewed candidate trend hints only. Does not verify MRMS, enable
          production rendering, download/decode/render, create or serve production tiles, clear alerts, or
          authorize production use.
        </p>
        {trendHintReviewAck?.available ? (
          <>
            <p className="validation-meta">
              Count: {trendHintReviewAck.count ?? 0} — related trend: {trendHintReviewAck.related_trend ?? '—'}{' '}
              — hint status: {trendHintReviewAck.related_hint_status ?? '—'}
            </p>
            {trendHintReviewAck.note ? (
              <p className="validation-meta">Latest note: {trendHintReviewAck.note}</p>
            ) : null}
            {trendHintReviewAck.trend_review_still_recommended ? (
              <p className="validation-warn">
                Trend review still recommended — acknowledgment does not clear alerts or change trend hints.
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            Refresh candidate trend hints first, then record acknowledgment after local review.
          </p>
        )}
        <form className="validation-form" onSubmit={(event) => void handleTrendHintReviewAckSubmit(event)}>
          <label>
            Operator initials
            <input
              type="text"
              value={trendHintReviewAckOperator}
              onChange={(event) => setTrendHintReviewAckOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label>
            Note (required)
            <textarea
              value={trendHintReviewAckNote}
              onChange={(event) => setTrendHintReviewAckNote(event.target.value)}
              rows={2}
              required
            />
          </label>
          <label className="validation-checkbox">
            <input
              type="checkbox"
              checked={trendHintReviewAckTrendReview}
              onChange={(event) => setTrendHintReviewAckTrendReview(event.target.checked)}
            />
            Acknowledged current trend review recommendation (local only)
          </label>
          <button type="submit" className="validation-action" disabled={trendHintReviewAckSubmitting}>
            {trendHintReviewAckSubmitting
              ? 'Recording acknowledgment…'
              : 'Record candidate trend-hint review acknowledgment (local only)'}
          </button>
        </form>
        {trendHintReviewAckMessage ? (
          <p className="validation-meta">{trendHintReviewAckMessage}</p>
        ) : null}
        {trendHintReviewAckError ? <p className="validation-warn">{trendHintReviewAckError}</p> : null}
        <CommandLine
          command={
            trendHintReviewAck?.suggested_command ??
            'make mrms-render-candidate-trend-hint-review-acknowledgment --operator OP --note "Reviewed locally"'
          }
          label="Suggested candidate trend-hint review acknowledgment command"
          manualCopy
        />
        <SafetyNote />
      </CollapsibleSection>
      <CollapsibleSection
        title="Scheduled validation & operator status"
        className="validation-scheduled-summary"
        summary={
          <>
            {scheduled ? (
              <p className="validation-meta">
                Latest run {formatTimestamp(scheduled.ran_at)}:{' '}
                {scheduled.success ? 'success' : 'failed'} (exit {scheduled.exit_code})
                {scheduled.elapsed_seconds != null
                  ? ` — ${scheduled.elapsed_seconds.toFixed(1)}s`
                  : ''}
              </p>
            ) : (
              <p className="validation-meta">No scheduled validation — run make scheduled-validation.</p>
            )}
            {scheduledOperatorStatus?.operator_status_requested ? (
              <p className="validation-meta">
                Operator status:{' '}
                <StatusBadge level={scheduledOperatorStatus.operator_status_level} />
                {scheduledOperatorStatus.operator_status_reason
                  ? ` — ${scheduledOperatorStatus.operator_status_reason}`
                  : ''}
                {scheduledOperatorStatus.operator_status_top_suggested_command ? (
                  <>
                    {' '}
                    — <code>{scheduledOperatorStatus.operator_status_top_suggested_command}</code>
                  </>
                ) : null}
              </p>
            ) : null}
          </>
        }
      >
        {scheduledProofStep?.proof_requested || scheduledProofStep?.ran ? (
          <p className="validation-meta">
            Scheduled proof step: {scheduledProofStep.ran ? scheduledProofStep.status ?? '—' : 'not run'}
            {scheduledProofStep.elapsed_seconds != null
              ? ` (${scheduledProofStep.elapsed_seconds.toFixed(2)}s)`
              : ''}
          </p>
        ) : null}
        {scheduledProofBundle ? (
          <>
            <p className="validation-meta">
              Bundle exported: {yesNo(scheduledProofBundle.bundle_exported ?? false)}
              {scheduledProofBundle.bundle_created_at
                ? ` — ${formatTimestamp(scheduledProofBundle.bundle_created_at)}`
                : ''}
            </p>
            <p className="validation-meta">
              Diff: {scheduledProofBundle.diff_status ?? '—'} — changes{' '}
              {scheduledProofBundle.evidence_changes_count ?? 0}
            </p>
          </>
        ) : null}
        {scheduledDigest?.digest_requested ? (
          <p className="validation-meta">
            Digest: {scheduledDigest.digest_generated ? 'generated' : 'skipped'}
            {scheduledDigest.digest_reason ? ` — ${scheduledDigest.digest_reason}` : ''}
          </p>
        ) : null}
        {scheduledReviewExport?.review_export_requested ? (
          <p className="validation-meta">
            Review export: {scheduledReviewExport.review_export_generated ? 'generated' : 'skipped'}
            {scheduledReviewExport.review_export_reason
              ? ` — ${scheduledReviewExport.review_export_reason}`
              : ''}
          </p>
        ) : null}
        {scheduledVisualReview?.visual_review_requested ? (
          <>
            <p className="validation-meta">
              Visual review:{' '}
              {scheduledVisualReview.visual_review_generated ? 'generated' : 'skipped'}
              {scheduledVisualReview.visual_review_reason
                ? ` — ${scheduledVisualReview.visual_review_reason}`
                : ''}
              {scheduledVisualReview.visual_review_elapsed_seconds != null
                ? ` (${scheduledVisualReview.visual_review_elapsed_seconds.toFixed(2)}s)`
                : ''}
            </p>
            {scheduledVisualReview.visual_review_path ? (
              <p className="validation-meta">
                Visual review JSON: <code>{scheduledVisualReview.visual_review_path}</code>
              </p>
            ) : null}
            {scheduledVisualReview.visual_review_markdown_path ? (
              <p className="validation-meta">
                Visual review Markdown:{' '}
                <code>{scheduledVisualReview.visual_review_markdown_path}</code>
              </p>
            ) : null}
            {scheduledVisualReview.visual_review_error ? (
              <p className="validation-meta">
                Visual review error: {scheduledVisualReview.visual_review_error}
              </p>
            ) : null}
          </>
        ) : null}
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Validation alerts"
        className="validation-alerts-section"
        summary={
          validationAlert ? (
            <p
              className={
                validationAlert.operator_attention_needed ? 'validation-warn' : 'validation-meta'
              }
            >
              Alert {validationAlert.status ?? 'ok'} — attention{' '}
              {validationAlert.operator_attention_needed ? 'needed' : 'not needed'} — updated{' '}
              {formatTimestamp(validationAlert.updated_at)}
            </p>
          ) : (
            <p className="validation-meta">No validation alert data.</p>
          )
        }
      >
        {validationAlert ? (
          <>
            <p
              className={
                validationAlert.operator_attention_needed ? 'validation-warn' : 'validation-meta'
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
              Alert counts: {validationAlert.failure_count ?? 0} failures,{' '}
              {validationAlert.warning_count ?? 0} warnings
            </p>
            {validationAlert.suggested_next_action ? (
              <p className="validation-meta">
                Suggested next action: {validationAlert.suggested_next_action}
              </p>
            ) : null}
            {validationAlert.operator_attention_needed && operatorGuidance.length > 0 ? (
              <section className="validation-operator-guidance">
                <SafetyNote />
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
        ) : (
          <p className="validation-meta">No validation alert — run make validation-alerts.</p>
        )}
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Proof report & regression"
        className="validation-proof-report-section"
        summary={
          <p className="validation-meta">
            Proof: {mrmsProof?.overall_status ?? 'not_started'}
            {proofRegression?.regression_detected ? ' — regression detected' : ''}
            {mrmsProof?.generated_at ? ` — ${formatTimestamp(mrmsProof.generated_at)}` : ''}
          </p>
        }
      >
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Proof bundle"
        className="validation-proof-bundle-section"
        summary={
          <p className="validation-meta">
            {proofBundle?.available
              ? `Latest ${formatTimestamp(proofBundle.created_at)} — ${proofBundle.file_count ?? 0} files`
              : 'No proof bundle — run make mrms-proof-bundle'}
          </p>
        }
      >
        {proofBundle?.available ? (
          <p className="validation-meta">
            {proofBundle.zip_path ? `ZIP: ${proofBundle.zip_path}` : ''}
            {proofBundle.bundle_folder ? ` — folder: ${proofBundle.bundle_folder}` : ''}
          </p>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Proof bundle diff & handoff"
        className="validation-proof-bundle-diff-section"
        summary={
          <p className="validation-meta">
            Diff: {proofBundleDiff?.overall_diff_status ?? 'none'}
            {proofBundleDiff?.checked_at ? ` — ${formatTimestamp(proofBundleDiff.checked_at)}` : ''}
            {operatorHandoff?.available ? ' — handoff available' : ''}
          </p>
        }
      >
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
        <SafetyNote variant="meta" />
      </section>
      </CollapsibleSection>
      <CollapsibleSection
        title="Proof bundle diff alert history"
        className="validation-diff-alert-history"
        summary={
          <p className="validation-meta">
            Latest:{' '}
            {diffAlertLatest?.diff_status ??
              validationAlert?.latest_proof_bundle_diff_alert_status ??
              '—'}
            {validationAlert?.proof_bundle_diff_alert_history_count != null
              ? ` — ${validationAlert.proof_bundle_diff_alert_history_count} entries`
              : ''}
          </p>
        }
      >
        {diffAlertTimeline.length > 0 ? (
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
              </li>
            ))}
          </ul>
        ) : (
          <p className="validation-meta">No timeline entries — run make proof-bundle-diff-alert-history.</p>
        )}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Diff alert escalation"
        className="validation-diff-escalation"
        summary={
          <p className="validation-meta">
            Escalation:{' '}
            <StatusBadge
              level={
                diffEscalation?.escalation_level ??
                validationAlert?.proof_bundle_diff_escalation_level ??
                'none'
              }
            />
          </p>
        }
      >
        {(diffEscalation?.stale_acknowledgment ||
          validationAlert?.proof_bundle_diff_escalation_stale_ack) && (
          <p className="validation-warn">
            Stale acknowledgment — latest ack predates or does not cover current attention streak
          </p>
        )}
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
              </li>
            ))}
          </ul>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Escalation history"
        className="validation-diff-escalation-history"
        summary={
          <p className="validation-meta">
            Snapshots:{' '}
            {diffEscalationHistory?.count ??
              validationAlert?.proof_bundle_diff_escalation_history_count ??
              0}
          </p>
        }
      >
        {(diffEscalationHistory?.recent ?? []).length > 0 ? (
          <ul className="validation-history-list">
            {(diffEscalationHistory?.recent ?? []).map((entry, index) => (
              <li
                key={`${entry.created_at ?? 'escalation'}-${entry.escalation_level}-${index}`}
                className={entry.escalation_level === 'urgent' ? 'validation-warn' : 'validation-meta'}
              >
                {formatTimestamp(entry.created_at)} — {entry.escalation_level ?? 'none'}
                {entry.latest_diff_status ? ` (${entry.latest_diff_status})` : ''}
              </li>
            ))}
          </ul>
        ) : (
          <p className="validation-meta">No recent escalation snapshots in summary.</p>
        )}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Digest, metrics & regeneration"
        className="validation-diff-escalation-metrics"
        summary={
          <p className="validation-meta">
            Digest regeneration:{' '}
            {yesNo(digestRegenerationHint?.digest_regeneration_recommended ?? false)}
            {digestRegenerationHint?.suggested_command ? (
              <>
                {' '}
                — <code>{digestRegenerationHint.suggested_command}</code>
              </>
            ) : null}
          </p>
        }
      >
        {diffEscalationMetrics?.available || (diffEscalationMetrics?.total_snapshots ?? 0) > 0 ? (
          <p className="validation-meta">
            Snapshots {diffEscalationMetrics?.total_snapshots ?? 0} — urgent{' '}
            {diffEscalationMetrics?.urgent_count ?? 0}, attention{' '}
            {diffEscalationMetrics?.attention_count ?? 0}
          </p>
        ) : null}
        {diffEscalationDigest?.available ? (
          <p className="validation-meta">
            Latest digest {formatTimestamp(diffEscalationDigest.generated_at)} —{' '}
            {diffEscalationDigest.markdown_path ?? '—'}
          </p>
        ) : null}
        {digestDiff?.available ? (
          <p className="validation-meta">
            Digest diff: {digestDiff.overall_digest_diff_status ?? 'unknown'}
          </p>
        ) : null}
        {digestRegenerationHint ? (
          <CommandLine command={digestRegenerationHint.suggested_command} />
        ) : null}
        {(digestHistory?.recent ?? []).length > 0 ? (
          <ul className="validation-history-list">
            {(digestHistory?.recent ?? []).map((entry, index) => (
              <li key={`${entry.created_at ?? 'digest'}-${index}`} className="validation-meta">
                {formatTimestamp(entry.created_at)} — {entry.latest_escalation_level ?? '—'}
              </li>
            ))}
          </ul>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review sessions"
        className="validation-review-session"
        summary={
          <p className="validation-meta">
            {reviewSessionSummary?.available
              ? `Latest ${formatTimestamp(reviewSessionSummary.latest_created_at)} — ${reviewSessionSummary.latest_operator ?? '—'} — attention ${reviewSessionSummary.open_attention_count ?? 0}`
              : 'No review sessions — run make mrms-review-session'}
          </p>
        }
      >
        {reviewSessionSummary?.available ? (
          <p className="validation-meta">
            Latest session {formatTimestamp(reviewSessionSummary.latest_created_at)} —{' '}
            {reviewSessionSummary.latest_operator ?? '—'} — escalation{' '}
            {reviewSessionSummary.latest_escalation_level ?? '—'} — open attention{' '}
            {reviewSessionSummary.open_attention_count ?? 0}
          </p>
        ) : (
          <p className="validation-meta">
            No review sessions — run make mrms-review-session (local only).
          </p>
        )}
        <form className="validation-signoff-form" onSubmit={(event) => void handleReviewSessionSubmit(event)}>
          <p className="validation-warn">Review session form — local only; does not verify MRMS.</p>
          <label className="validation-meta">
            Operator initials or name
            <input
              type="text"
              value={reviewSessionOperator}
              onChange={(event) => setReviewSessionOperator(event.target.value)}
              autoComplete="name"
            />
          </label>
          <label className="validation-meta">
            Session notes
            <textarea
              value={reviewSessionNotes}
              onChange={(event) => setReviewSessionNotes(event.target.value)}
              rows={2}
            />
          </label>
          <label className="validation-meta">
            <input
              type="checkbox"
              checked={reviewSessionAcceptedLimitations}
              onChange={(event) => setReviewSessionAcceptedLimitations(event.target.checked)}
            />{' '}
            I accept this review session does not verify MRMS (required)
          </label>
          <label className="validation-meta">
            <input
              type="checkbox"
              checked={reviewSessionExportAfterCreate}
              onChange={(event) => setReviewSessionExportAfterCreate(event.target.checked)}
            />{' '}
            Export Markdown after creating this session
          </label>
          <button type="submit" className="validation-refresh" disabled={reviewSessionSubmitting}>
            {reviewSessionSubmitting ? 'Submitting…' : 'Submit local review session'}
          </button>
          {reviewSessionMessage ? <p className="validation-meta">{reviewSessionMessage}</p> : null}
          {reviewSessionError ? <p className="validation-warn">{reviewSessionError}</p> : null}
        </form>
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review session comparison"
        className="validation-review-session-compare"
        summary={
          <p className="validation-meta">
            {reviewSessionComparison?.available
              ? `${reviewSessionComparison.overall_review_diff_status ?? 'unknown'} — attention ${reviewSessionComparison.open_attention_count_change?.latest ?? reviewSessionSummary?.open_attention_count ?? '—'}`
              : 'No comparison — run make mrms-review-session-compare'}
          </p>
        }
      >
        {reviewSessionComparison?.available ? (
          <>
            <p className="validation-meta">
              Session comparison: {reviewSessionComparison.overall_review_diff_status ?? 'unknown'}
              {reviewSessionComparison.compared_at
                ? ` (${formatTimestamp(reviewSessionComparison.compared_at)})`
                : ''}
            </p>
            <p className="validation-meta">
              Baseline {formatTimestamp(reviewSessionComparison.baseline_created_at)} —{' '}
              {reviewSessionComparison.baseline_operator ?? '—'} → latest{' '}
              {formatTimestamp(reviewSessionComparison.latest_created_at)} —{' '}
              {reviewSessionComparison.latest_operator ?? '—'}
            </p>
            {reviewSessionComparison.open_attention_count_change ? (
              <p className="validation-meta">
                Open attention count: baseline{' '}
                {reviewSessionComparison.open_attention_count_change.baseline ?? '—'} → latest{' '}
                {reviewSessionComparison.open_attention_count_change.latest ?? '—'}
              </p>
            ) : null}
            {reviewSessionComparison.checklist_reviewed_count_change ? (
              <p className="validation-meta">
                Checklist reviewed: baseline{' '}
                {reviewSessionComparison.checklist_reviewed_count_change.baseline ?? '—'} → latest{' '}
                {reviewSessionComparison.checklist_reviewed_count_change.latest ?? '—'}
              </p>
            ) : null}
            {reviewSessionComparison.checklist_not_reviewed_count_change ? (
              <p className="validation-meta">
                Checklist not reviewed: baseline{' '}
                {reviewSessionComparison.checklist_not_reviewed_count_change.baseline ?? '—'} → latest{' '}
                {reviewSessionComparison.checklist_not_reviewed_count_change.latest ?? '—'}
              </p>
            ) : null}
            {(reviewSessionComparison.improvements?.length ?? 0) > 0 ? (
              <p className="validation-meta">
                Improvements: {reviewSessionComparison.improvements?.join(', ')}
              </p>
            ) : null}
            {(reviewSessionComparison.regressions?.length ?? 0) > 0 ? (
              <p className="validation-warn">
                Regressions: {reviewSessionComparison.regressions?.join(', ')}
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No session comparison yet — run make mrms-review-session-compare after two sessions.
          </p>
        )}
        {openAttentionGuidance.length > 0 ? (
          <section className="validation-open-attention-guidance">
            <p className="validation-warn">
              Open attention runbook guidance (local review only — does not verify MRMS)
            </p>
            <ul className="validation-history-list">
              {openAttentionGuidance.map((item, index) => (
                <li key={`${item.cause}-${index}`} className="validation-meta">
                  {item.title} — <code>{item.path}</code>
                  {item.suggested_action ? ` — ${item.suggested_action}` : ''}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review session export"
        className="validation-review-session-export"
        summary={
          <p className="validation-meta">
            {reviewSessionExport?.available
              ? `${formatTimestamp(reviewSessionExport.created_at)} — ${reviewSessionExport.comparison_status ?? '—'}`
              : 'No export — run make mrms-review-session-export'}
            {reviewExportRegenerationHint?.review_export_regeneration_recommended
              ? ' — regeneration recommended'
              : ''}
          </p>
        }
      >
        {reviewSessionExport?.available ? (
          <p className="validation-meta">
            Latest export {formatTimestamp(reviewSessionExport.created_at)} —{' '}
            <code>{reviewSessionExport.export_path ?? '—'}</code> — comparison{' '}
            {reviewSessionExport.comparison_status ?? '—'} — open attention{' '}
            {reviewSessionExport.open_attention_count ?? 0}
          </p>
        ) : (
          <p className="validation-meta">
            No review session export — run make mrms-review-session-export (local only).
          </p>
        )}
        {reviewExportRegenerationHint ? (
          <>
            <p
              className={
                reviewExportRegenerationHint.review_export_regeneration_recommended
                  ? 'validation-warn'
                  : 'validation-meta'
              }
            >
              Review export regeneration recommended:{' '}
              {yesNo(reviewExportRegenerationHint.review_export_regeneration_recommended ?? false)}
              {reviewExportRegenerationHint.reason ? ` — ${reviewExportRegenerationHint.reason}` : ''}
            </p>
            <CommandLine command={reviewExportRegenerationHint.suggested_command} />
          </>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review export diff"
        className="validation-review-export-diff"
        summary={
          <p className="validation-meta">
            {reviewSessionExportDiff?.available
              ? `${reviewSessionExportDiff.overall_export_diff_status ?? 'unknown'} — session changed ${reviewSessionExportDiff.session_changed ? 'yes' : 'no'}`
              : 'No export diff — run make mrms-review-session-export twice'}
          </p>
        }
      >
        {reviewSessionExportDiff?.available ? (
          <>
            <p className="validation-meta">
              Export diff: {reviewSessionExportDiff.overall_export_diff_status ?? 'unknown'}
              {reviewSessionExportDiff.compared_at
                ? ` (${formatTimestamp(reviewSessionExportDiff.compared_at)})`
                : ''}
            </p>
            {(reviewSessionExportDiff.regressions?.length ?? 0) > 0 ? (
              <p className="validation-warn">
                Export diff regressions: {reviewSessionExportDiff.regressions?.join(', ')}
              </p>
            ) : null}
          </>
        ) : (
          <p className="validation-meta">
            No review export diff — run make mrms-review-session-export twice or use export-after-create.
          </p>
        )}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review export diff history"
        className="validation-review-export-diff-history"
        summary={
          <p className="validation-meta">
            {reviewSessionExportDiffHistory?.available
              ? `${reviewSessionExportDiffHistory.count ?? 0} entries — latest ${reviewSessionExportDiffHistory.latest_status ?? '—'}`
              : 'No export diff history'}
          </p>
        }
      >
        {(reviewSessionExportDiffHistory?.recent ?? []).length > 0 ? (
          <ul className="validation-history-list">
            {(reviewSessionExportDiffHistory?.recent ?? []).map((entry, index) => (
              <li
                key={`${entry.created_at ?? 'export-diff'}-${index}`}
                className="validation-meta"
              >
                {formatTimestamp(entry.created_at)} — {entry.overall_export_diff_status ?? '—'}
              </li>
            ))}
          </ul>
        ) : (
          <p className="validation-meta">
            No export diff history — run make mrms-review-session-export-diff-history (local only).
          </p>
        )}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Review export diff trend & hint"
        className="validation-review-export-diff-trend"
        summary={
          <p className="validation-meta">
            {reviewSessionExportDiffTrend?.available
              ? `Trend ${reviewSessionExportDiffTrend.trend ?? 'no_data'}`
              : 'No export diff trend'}
            {reviewSessionExportDiffTrendHint?.review_trend_regeneration_recommended
              ? ' — regeneration recommended'
              : ''}
          </p>
        }
      >
        {reviewSessionExportDiffTrend?.available ? (
          <p className="validation-meta">
            Export diff trend: {reviewSessionExportDiffTrend.trend ?? 'no_data'}
            {reviewSessionExportDiffTrend.latest_at
              ? ` (${formatTimestamp(reviewSessionExportDiffTrend.latest_at)})`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No export diff trend — run make mrms-review-session-export-diff-trend after multiple exports.
          </p>
        )}
        {reviewSessionExportDiffTrendHint ? (
          <>
            <p className="validation-meta">
              Trend regeneration recommended:{' '}
              {yesNo(reviewSessionExportDiffTrendHint.review_trend_regeneration_recommended ?? false)}
            </p>
            <CommandLine command={reviewSessionExportDiffTrendHint.suggested_command} />
          </>
        ) : null}
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Diff alert trend & acknowledgment"
        className="validation-diff-alert-trend"
        summary={
          <p className="validation-meta">
            Trend: {diffAlertTrend?.trend ?? validationAlert?.proof_bundle_diff_alert_trend ?? 'no_data'}
          </p>
        }
      >
        {diffAlertTrend?.available || validationAlert?.proof_bundle_diff_alert_trend ? (
          <p className="validation-meta">
            Trend: {diffAlertTrend?.trend ?? validationAlert?.proof_bundle_diff_alert_trend ?? 'no_data'}
            {diffAlertTrend?.latest_status ? ` — latest ${diffAlertTrend.latest_status}` : ''}
            {diffAlertTrend?.current_attention_streak
              ? ` — attention streak ${diffAlertTrend.current_attention_streak}`
              : ''}
          </p>
        ) : (
          <p className="validation-meta">
            No trend data — run make proof-bundle-diff-alert-trend after diff history.
          </p>
        )}
        {diffAlertTrend ? (
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
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
      <CollapsibleSection
        title="Proof review & sign-off"
        className="validation-proof-review"
        summary={
          <p className="validation-meta">
            Proof history {proofHistory?.count ?? 0} — sign-offs {signoffsList?.count ?? 0}
            {proofReviewLoading ? ' (loading…)' : ''}
          </p>
        }
      >
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Validation pipeline"
        className="validation-pipeline-summary"
        summary={
          <p className="validation-meta">
            Catalog {catalog.total_frames} frames — queue {queue.queued} queued / {queue.running} running —
            production {summary.production_rendering_enabled ? 'enabled' : 'disabled'}
          </p>
        }
      >
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
        <SafetyNote variant="meta" />
      </CollapsibleSection>
      <CollapsibleSection
        title="Raw JSON drilldown"
        className="validation-raw-json"
        expanded={showDetails}
        onExpandedChange={(next) => {
          if (!next) {
            setShowDetails(false);
            return;
          }
          void openDetails();
        }}
        summary={
          <p className="validation-meta">
            {detailsLoading
              ? 'Loading…'
              : detailsJson
                ? 'Loaded validation latest payload'
                : 'Collapsed — expand or use header Show details'}
          </p>
        }
      >
      {showDetails && detailsJson ? (
        <pre className="validation-details-json">{detailsJson}</pre>
      ) : (
        <p className="validation-meta">
          Use the header <strong>Show details</strong> button to fetch and display the latest validation JSON.
        </p>
      )}
      </CollapsibleSection>
    </section>
  );
}
