import { useEffect, useState } from 'react';
import {
  DEFAULT_INGEST_WINDOW_STATE,
  formatIngestWindowLabel,
  fromDatetimeLocalValue,
  ingestWindowQueryFromState,
  INGEST_WINDOW_PRESETS,
  toDatetimeLocalValue,
  type IngestWindowFormState,
  type IngestWindowPlan,
  type IngestWindowPreset,
} from './ingestWindow';
import { fetchIngestWindowPlan } from '../api/client';

export default function IngestWindowPanel({
  disabled = false,
  replayRangeStart = null,
  replayRangeEnd = null,
}: {
  disabled?: boolean;
  replayRangeStart?: string | null;
  replayRangeEnd?: string | null;
}) {
  const [form, setForm] = useState<IngestWindowFormState>(DEFAULT_INGEST_WINDOW_STATE);
  const [plan, setPlan] = useState<IngestWindowPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      replayStart: replayRangeStart,
      replayEnd: replayRangeEnd,
    }));
  }, [replayRangeStart, replayRangeEnd]);

  useEffect(() => {
    let cancelled = false;

    async function loadPlan() {
      setLoading(true);
      setError('');
      try {
        const nextPlan = await fetchIngestWindowPlan(ingestWindowQueryFromState(form));
        if (!cancelled) {
          setPlan(nextPlan);
        }
      } catch (err) {
        if (!cancelled) {
          setPlan(null);
          setError(err instanceof Error ? err.message : 'Failed to load ingest plan');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPlan();
    return () => {
      cancelled = true;
    };
  }, [form]);

  const updateForm = (patch: Partial<IngestWindowFormState>) => {
    setForm((current) => ({ ...current, ...patch }));
    setCopied(false);
  };

  const applyReplayRangePreset = () => {
    if (!replayRangeStart || !replayRangeEnd) {
      return;
    }
    updateForm({
      preset: 'replay_range',
      replayStart: replayRangeStart,
      replayEnd: replayRangeEnd,
    });
  };

  const copyCommand = async () => {
    const command = plan?.bulk_ingest_command;
    if (!command) {
      return;
    }
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="panel ingest-window-panel" aria-label="Ingest window">
      <h2>Load frames</h2>
      <p className="ingest-window-intro">
        Plan a bounded real MRMS ingest window. Downloads do not start automatically — copy and run the command in your terminal with explicit <code>--real</code>.
      </p>
      <label className="ingest-window-field">
        Preset
        <select
          value={form.preset}
          disabled={disabled}
          onChange={(event) => updateForm({ preset: event.target.value as IngestWindowPreset })}
        >
          {Object.entries(INGEST_WINDOW_PRESETS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {form.preset === 'custom' ? (
        <div className="ingest-window-custom">
          <label className="ingest-window-field">
            Start (UTC)
            <input
              type="datetime-local"
              disabled={disabled}
              value={toDatetimeLocalValue(form.customStart)}
              onChange={(event) =>
                updateForm({ customStart: fromDatetimeLocalValue(event.target.value) })
              }
            />
          </label>
          <label className="ingest-window-field">
            End (UTC)
            <input
              type="datetime-local"
              disabled={disabled}
              value={toDatetimeLocalValue(form.customEnd)}
              onChange={(event) =>
                updateForm({ customEnd: fromDatetimeLocalValue(event.target.value) })
              }
            />
          </label>
        </div>
      ) : null}
      <label className="ingest-window-field">
        Limit
        <input
          type="number"
          min={1}
          max={20}
          disabled={disabled}
          value={form.limit}
          onChange={(event) => updateForm({ limit: Number(event.target.value) || 8 })}
        />
      </label>
      <label className="ingest-window-checkbox">
        <input
          type="checkbox"
          disabled={disabled}
          checked={form.warmCache}
          onChange={(event) => updateForm({ warmCache: event.target.checked })}
        />
        Include <code>--warm-cache</code> in generated command
      </label>
      <div className="ingest-window-actions">
        <button
          type="button"
          disabled={disabled || !replayRangeStart || !replayRangeEnd}
          onClick={applyReplayRangePreset}
        >
          Use replay range
        </button>
      </div>
      {loading ? <p className="ingest-window-meta">Building ingest plan…</p> : null}
      {error ? <p className="ingest-window-error">{error}</p> : null}
      {plan ? (
        <>
          <p className="ingest-window-meta">
            Window: <code>{formatIngestWindowLabel(plan.preset)}</code>
            {plan.start_time && plan.end_time ? (
              <>
                {' '}
                · <code>{plan.start_time}</code> → <code>{plan.end_time}</code>
              </>
            ) : null}
          </p>
          {plan.estimated_frames_in_window ? (
            <p className="ingest-window-meta">
              Estimated frames in window: ~{plan.estimated_frames_in_window} (capped at limit {plan.limit})
            </p>
          ) : null}
          {plan.warnings.map((warning) => (
            <p key={warning} className="ingest-window-warning" role="status">
              {warning}
            </p>
          ))}
          {plan.bulk_ingest_command ? (
            <div className="ingest-window-command">
              <p className="ingest-window-command-label">Run in terminal:</p>
              <code>{plan.bulk_ingest_command}</code>
              <button type="button" disabled={disabled} onClick={copyCommand}>
                {copied ? 'Copied' : 'Copy command'}
              </button>
            </div>
          ) : null}
          <p className="ingest-window-meta">
            Guided dry-run: <code>{plan.guided_command}</code>
          </p>
          {plan.next_commands.length ? (
            <ul className="ingest-window-next">
              {plan.next_commands.map((command) => (
                <li key={command}>
                  <code>{command}</code>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
