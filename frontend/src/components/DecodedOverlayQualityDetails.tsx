import type { FrameQualityStatus } from '../api/client';
import { qualityStatusLabel } from './frameQualityDisplay';

function qualityStatusClass(status?: string): string {
  switch (status) {
    case 'ok':
      return 'frame-quality--ok';
    case 'warning':
      return 'frame-quality--warning';
    case 'error':
      return 'frame-quality--error';
    default:
      return 'frame-quality--unavailable';
  }
}

function qualityCheckClass(status: string): string {
  return `frame-quality-check--${status}`;
}

export default function DecodedOverlayQualityDetails({
  frameQuality,
}: {
  frameQuality: FrameQualityStatus;
}) {
  return (
    <div className="frame-quality-panel" aria-label="Frame quality checks">
      <p className={`frame-quality-summary ${qualityStatusClass(frameQuality.status)}`}>
        Frame quality: <code>{qualityStatusLabel(frameQuality.status)}</code>
        {frameQuality.diagnostic_only ? ' (diagnostic)' : ''}
      </p>
      {frameQuality.measured?.manifest_width != null && frameQuality.measured?.manifest_height != null ? (
        <p className="decoded-overlay-meta">
          Grid:{' '}
          <code>
            {String(frameQuality.measured.manifest_width)}×{String(frameQuality.measured.manifest_height)}
          </code>
          {frameQuality.measured.manifest_value_min != null ? (
            <>
              {' '}
              min/max{' '}
              <code>
                {String(frameQuality.measured.manifest_value_min)} /{' '}
                {String(frameQuality.measured.manifest_value_max)}
              </code>
            </>
          ) : null}
        </p>
      ) : null}
      <ul className="frame-quality-checks">
        {frameQuality.checks.map((check) => (
          <li key={check.name} className={qualityCheckClass(check.status)}>
            <code>{check.name}</code>: {check.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
