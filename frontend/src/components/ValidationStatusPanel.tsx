import type { ValidationSummary } from '../api/client';

function yesNo(value: boolean): string {
  return value ? 'yes' : 'no';
}

export default function ValidationStatusPanel({ summary }: { summary: ValidationSummary | null }) {
  if (!summary) {
    return (
      <section className="panel validation-panel">
        <h2>Dev Validation</h2>
        <p className="validation-meta">Validation summary unavailable (run make validate-real-mrms).</p>
        <p className="validation-warn">Prototype only — not verified real MRMS.</p>
      </section>
    );
  }

  const validation = summary.validation;
  const benchmark = summary.benchmark;
  const queue = summary.render_queue;

  return (
    <section className="panel validation-panel">
      <h2>Dev Validation</h2>
      <p className="validation-warn">Experimental pipeline — not verified real MRMS.</p>
      <p className="validation-meta">Placeholder default: {yesNo(summary.placeholder_default)}</p>
      <p className="validation-meta">
        Production rendering: {summary.production_rendering_enabled ? 'enabled (flag on)' : 'disabled (default)'}
      </p>
      <p className="validation-meta">verified_mrms: {yesNo(summary.verified_mrms)}</p>
      <p className="validation-meta">Decoder: {summary.decoder_available ? 'available' : 'not installed'}</p>
      <p className="validation-meta">
        Queue: queued {queue.queued}, running {queue.running}, failed {queue.failed}
      </p>
      {validation ? (
        <>
          <p className="validation-meta">
            Last validation ({validation.source_mode ?? '—'}): discovered {validation.discovered_count},
            downloaded {validation.downloaded_count}, decoded {validation.decoded_count}
          </p>
          <p className="validation-meta">
            Jobs enqueued {validation.render_jobs_enqueued}, processed {validation.worker_jobs_processed}
          </p>
        </>
      ) : (
        <p className="validation-meta">No validation report yet — run make validate-real-mrms.</p>
      )}
      {benchmark ? (
        <p className="validation-meta">
          Benchmark: tiles {benchmark.tiles_written}/{benchmark.tiles_planned}, build{' '}
          {benchmark.tile_build_elapsed_seconds.toFixed(2)}s, zoom {benchmark.min_zoom}–{benchmark.max_zoom}
        </p>
      ) : null}
    </section>
  );
}
