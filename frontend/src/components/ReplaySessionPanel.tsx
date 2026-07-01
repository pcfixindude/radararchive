import type { ReplaySessionSummary } from './replaySessionSummary';
import { sessionReadinessClass } from './replaySessionSummary';
import { primarySetupCommand, setupChecklistClass } from './localReplayReady';
import type { LocalReplayReadyStatus } from './localReplayReady';
import KeyboardShortcutsHelp from './KeyboardShortcutsHelp';

export default function ReplaySessionPanel({
  summary,
  setupStatus = null,
  setupLoading = false,
  setupError = '',
  onRefreshSetup,
}: {
  summary: ReplaySessionSummary;
  setupStatus?: LocalReplayReadyStatus | null;
  setupLoading?: boolean;
  setupError?: string;
  onRefreshSetup?: () => void;
}) {
  const setupCommand = primarySetupCommand(setupStatus);

  return (
    <section className="panel replay-session-panel" aria-label="Replay session">
      <div className="replay-session-header">
        <h2>Replay session</h2>
        <span className={`session-readiness-badge ${sessionReadinessClass(summary.readiness)}`}>
          {summary.readinessLabel}
        </span>
      </div>
      <p className="replay-session-meta">
        Frame: <code>{summary.selectedTime || '—'}</code> · {summary.playbackLabel}
      </p>
      <div className="local-replay-setup">
        <div className="local-replay-setup-header">
          <h3>Local replay setup</h3>
          {onRefreshSetup ? (
            <button type="button" className="local-replay-setup-refresh" onClick={onRefreshSetup}>
              Refresh
            </button>
          ) : null}
        </div>
        {setupLoading ? <p className="replay-session-meta">Checking setup status…</p> : null}
        {setupError ? <p className="replay-session-next">{setupError}</p> : null}
        {setupStatus ? (
          <>
            <p className={`replay-session-meta local-replay-setup-status${setupStatus.ready ? ' local-replay-setup-status--ready' : ''}`}>
              {setupStatus.ready_label} · {setupStatus.frame_count} frame(s) assessed
            </p>
            <ul className="replay-session-checklist local-replay-setup-checklist">
              {setupStatus.checklist.map((item) => (
                <li key={item.id} className={setupChecklistClass(item.status)}>
                  <strong>{item.label}:</strong> {item.message}
                </li>
              ))}
            </ul>
            {setupCommand ? (
              <p className="replay-session-next">
                Setup next: <code>{setupCommand}</code>
              </p>
            ) : null}
            <p className="replay-session-hints local-replay-setup-hint">
              Dry-run: <code>make local-replay-ready</code> · bounded local warm/decode:{' '}
              <code>{setupStatus.suggested_run_command}</code>
            </p>
          </>
        ) : null}
      </div>
      <ul className="replay-session-checklist">
        <li className={summary.hasDecodedOverlay ? 'session-ok' : 'session-warn'}>
          Decoded overlay: {summary.hasDecodedOverlay ? 'yes' : 'no'}
        </li>
        <li className={summary.cacheStateLabel === 'cached' ? 'session-ok' : 'session-warn'}>
          Frame cache: <code>{summary.cacheStateLabel ?? 'unknown'}</code>
        </li>
        <li className={summary.frameQualityStatus === 'ok' ? 'session-ok' : 'session-warn'}>
          Quality: <code>{summary.frameQualityStatus ?? 'unavailable'}</code>
        </li>
        <li className={summary.hasValidBounds ? 'session-ok' : 'session-warn'}>
          Overlay bounds: {summary.hasValidBounds ? 'valid' : 'missing'}
        </li>
      </ul>
      {summary.nextCommand ? (
        <p className="replay-session-next">
          Run next: <code>{summary.nextCommand}</code>
        </p>
      ) : (
        <p className="replay-session-next replay-session-next--ready">No action required — use playback controls.</p>
      )}
      {summary.hints.length ? (
        <ul className="replay-session-hints">
          {summary.hints.map((hint) => (
            <li key={hint}>{hint}</li>
          ))}
        </ul>
      ) : null}
      <KeyboardShortcutsHelp />
    </section>
  );
}
