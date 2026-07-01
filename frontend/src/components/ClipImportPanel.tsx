import type { ClipImportHookState } from '../hooks/useClipImport';
import {
  buildApplyPayload,
  formatApplyPreview,
  formatImportSummary,
  importStatusLabel,
  problemFrameLabel,
} from './clipImport';
import {
  formatRemediationGroupSummary,
  hasRemediationCommands,
  remediationPlanStatusLabel,
} from './clipRemediation';
import CommandLine from './validation/CommandLine';

export type { ClipImportApplyPayload } from './clipImport';

export default function ClipImportPanel({
  disabled = false,
  clipImport,
  inspectTimestamp,
  onInspectFrame,
  onApply,
}: {
  disabled?: boolean;
  clipImport: ClipImportHookState;
  inspectTimestamp?: string;
  onInspectFrame?: (timestamp: string) => void;
  onApply: () => void;
}) {
  const {
    rawInput,
    report,
    loading,
    error,
    applyNotice,
    setRawInput,
    validateImport,
    loadFromFile,
    clearImport,
  } = clipImport;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      void loadFromFile(file);
    }
    event.target.value = '';
  };

  const canApply = Boolean(report?.valid && report.manifest);
  const applyPayload = report?.valid && report.manifest ? buildApplyPayload(report) : null;
  const applyPreview = applyPayload ? formatApplyPreview(applyPayload) : null;

  return (
    <div className="clip-import" aria-label="Playback clip import">
      <div className="clip-import-header">
        <h3>Import clip</h3>
        <button
          type="button"
          className="clip-import-action"
          disabled={disabled || !rawInput.trim() || loading}
          onClick={() => void validateImport()}
        >
          {loading ? 'Validating…' : 'Validate import'}
        </button>
      </div>
      <p className="clip-import-intro">
        Load a saved clip manifest from Export clip — restore frame sequence, range, loop suggestion,
        and readiness. Status only; no ingest or decode work.
      </p>
      <label className="clip-import-field">
        <span>Clip JSON</span>
        <textarea
          className="clip-import-textarea"
          rows={4}
          disabled={disabled}
          value={rawInput}
          placeholder='Paste playback clip JSON or use "Choose file" below'
          onChange={(event) => setRawInput(event.target.value)}
        />
      </label>
      <div className="clip-import-buttons">
        <label className="clip-import-file-label">
          <span className="clip-import-action">Choose file</span>
          <input
            type="file"
            accept="application/json,.json"
            disabled={disabled}
            className="clip-import-file-input"
            onChange={handleFileChange}
          />
        </label>
        <button
          type="button"
          className="clip-import-action clip-import-action--muted"
          disabled={disabled || (!rawInput && !report)}
          onClick={clearImport}
        >
          Clear
        </button>
      </div>
      {error ? <p className="clip-import-error">{error}</p> : null}
      {report ? (
        <div className="clip-import-summary">
          <p className="clip-import-meta">
            <strong>{importStatusLabel(report.import_status)}</strong>
            {report.manifest ? (
              <>
                {' '}
                — <code>{report.manifest.clip_id}</code>
              </>
            ) : null}
          </p>
          {report.valid && report.manifest ? (
            <>
              <p className="clip-import-meta">{formatImportSummary(report)}</p>
              <p className="clip-import-meta">
                Range: <code>{report.manifest.range_start}</code> →{' '}
                <code>{report.manifest.range_end}</code>
                {report.manifest.loop_suggested ? ' · loop suggested' : ''}
              </p>
              {report.warnings.length > 0 ? (
                <ul className="clip-import-warnings">
                  {report.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              ) : null}
              {applyPreview ? (
                <p className="clip-import-meta clip-import-apply-preview">{applyPreview}</p>
              ) : null}
              <div className="clip-import-buttons">
                <button
                  type="button"
                  className="clip-import-action clip-import-action--apply"
                  disabled={disabled || !canApply}
                  onClick={onApply}
                >
                  Apply to replay
                </button>
              </div>
              {applyNotice ? (
                <p className="clip-import-notice" role="status">
                  {applyNotice}
                </p>
              ) : null}
              {report.remediation_plan ? (
                <div className="clip-import-remediation-plan">
                  <h4>Remediation plan</h4>
                  <p className="clip-import-meta">
                    <strong>{remediationPlanStatusLabel(report.remediation_plan.plan_status)}</strong>
                    {' — '}
                    {formatRemediationGroupSummary(report.remediation_plan.group_summary)}
                    {report.remediation_plan.truncated ? ' · bounded to plan limit' : ''}
                  </p>
                  {report.remediation_plan.problem_groups.length > 0 ? (
                    <ul className="clip-import-remediation-groups">
                      {report.remediation_plan.problem_groups.map((group) => (
                        <li key={group.readiness_type}>
                          <strong>{group.label}:</strong> {group.count}
                          {group.truncated ? ` (${group.assessed_count} in plan)` : ''}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <p className="clip-import-remediation-note">
                    Commands are not auto-run — copy and paste into your terminal manually.
                  </p>
                  {hasRemediationCommands(report.remediation_plan) ? (
                    <>
                      <CommandLine
                        command={report.remediation_plan.command_block}
                        label="Copy-ready command checklist"
                        manualCopy
                      />
                      <ol className="clip-import-remediation-steps">
                        {report.remediation_plan.commands.map((step) => (
                          <li key={step.step}>
                            <span className="clip-import-remediation-step-label">
                              Step {step.step}: {step.label}
                            </span>
                            <code>{step.command}</code>
                          </li>
                        ))}
                      </ol>
                    </>
                  ) : (
                    <p className="clip-import-meta">{report.remediation_plan.operator_note}</p>
                  )}
                </div>
              ) : null}
              {report.problem_frames.length > 0 && onInspectFrame ? (
                <div className="clip-import-problems">
                  <h4>Problem frames ({report.problem_frames.length})</h4>
                  <ul>
                    {report.problem_frames.map((frame) => (
                      <li key={frame.timestamp}>
                        <button
                          type="button"
                          className={`clip-import-problem-frame${frame.timestamp === inspectTimestamp ? ' clip-import-problem-frame--inspecting' : ''}`}
                          disabled={disabled}
                          onClick={() => onInspectFrame(frame.timestamp)}
                        >
                          <code>{frame.timestamp}</code>
                          <span>{problemFrameLabel(frame)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {report.manifest.frames.length > 0 && onInspectFrame ? (
                <div className="clip-import-frames">
                  <h4>Clip frames</h4>
                  <ul>
                    {report.manifest.frames.map((frame) => (
                      <li key={frame.timestamp}>
                        <button
                          type="button"
                          className={`clip-import-frame${frame.timestamp === inspectTimestamp ? ' clip-import-frame--inspecting' : ''}`}
                          disabled={disabled}
                          onClick={() => onInspectFrame(frame.timestamp)}
                        >
                          <code>{frame.timestamp}</code>
                          <span>{frame.cache_state}</span>
                          <span>{frame.decode_ready ? 'decoded' : 'not decoded'}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </>
          ) : (
            <ul className="clip-import-errors">
              {report.errors.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
