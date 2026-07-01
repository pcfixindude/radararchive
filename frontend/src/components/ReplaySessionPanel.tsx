import type { ReplaySessionSummary } from './replaySessionSummary';
import { sessionReadinessClass } from './replaySessionSummary';
import KeyboardShortcutsHelp from './KeyboardShortcutsHelp';

export default function ReplaySessionPanel({ summary }: { summary: ReplaySessionSummary }) {
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
