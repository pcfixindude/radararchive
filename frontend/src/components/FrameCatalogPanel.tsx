import { useMemo, useState, type MouseEvent } from 'react';
import {
  filterFrameCatalog,
  formatFrameTimestamp,
  frameReadinessClass,
  frameReadinessLabel,
  type FrameCatalogItem,
} from './frameCatalog';
import type { FrameCatalogStatus } from '../api/client';

export default function FrameCatalogPanel({
  disabled = false,
  catalog,
  loading = false,
  error = '',
  selectedTime,
  onSelectFrame,
  onInspectFrame,
  inspectTimestamp,
  onRefresh,
}: {
  disabled?: boolean;
  catalog: FrameCatalogStatus | null;
  loading?: boolean;
  error?: string;
  selectedTime: string;
  onSelectFrame: (timestamp: string) => void;
  onInspectFrame?: (timestamp: string) => void;
  inspectTimestamp?: string;
  onRefresh?: () => void;
}) {
  const [filterText, setFilterText] = useState('');

  const visibleFrames = useMemo(
    () => filterFrameCatalog(catalog?.frames ?? [], filterText),
    [catalog?.frames, filterText],
  );

  const handleJump = (frame: FrameCatalogItem) => {
    if (disabled) {
      return;
    }
    onSelectFrame(frame.timestamp);
  };

  const handleInspect = (frame: FrameCatalogItem, event: MouseEvent) => {
    event.stopPropagation();
    if (disabled || !onInspectFrame) {
      return;
    }
    onInspectFrame(frame.timestamp);
  };

  return (
    <section className="panel frame-catalog-panel" aria-label="Frame catalog">
      <div className="frame-catalog-header">
        <h2>Frame catalog</h2>
        {onRefresh ? (
          <button type="button" className="frame-catalog-refresh" onClick={onRefresh}>
            Refresh
          </button>
        ) : null}
      </div>
      <p className="frame-catalog-intro">
        Browse local MRMS frames with cache/decode readiness. Click a row to jump playback.
      </p>
      {loading ? <p className="frame-catalog-meta">Loading catalog…</p> : null}
      {error ? <p className="frame-catalog-error">{error}</p> : null}
      {catalog ? (
        <>
          <p className="frame-catalog-meta">
            {catalog.frame_count} frame(s) · {catalog.cache_ready_count} cached ·{' '}
            {catalog.decode_ready_count} decoded
            {catalog.missing_count ? ` · ${catalog.missing_count} missing raw` : ''}
          </p>
          <label className="frame-catalog-filter">
            <span className="frame-catalog-filter-label">Filter</span>
            <input
              type="search"
              value={filterText}
              onChange={(event) => setFilterText(event.target.value)}
              placeholder="Timestamp text…"
              disabled={disabled}
            />
          </label>
          {visibleFrames.length === 0 ? (
            <p className="frame-catalog-meta frame-catalog-meta--empty">
              {filterText ? 'No frames match filter.' : 'No local frames in catalog.'}
            </p>
          ) : (
            <ul className="frame-catalog-list">
              {visibleFrames.map((frame) => {
                const selected = frame.timestamp === selectedTime;
                const inspecting = frame.timestamp === inspectTimestamp;
                return (
                  <li key={frame.timestamp}>
                    <button
                      type="button"
                      className={`frame-catalog-row ${frameReadinessClass(frame)}${selected ? ' frame-catalog-row--selected' : ''}${inspecting ? ' frame-catalog-row--inspecting' : ''}`}
                      disabled={disabled}
                      onClick={() => handleJump(frame)}
                      aria-current={selected ? 'true' : undefined}
                    >
                      <span className="frame-catalog-time">{formatFrameTimestamp(frame.timestamp)}</span>
                      <span className="frame-catalog-status">{frameReadinessLabel(frame)}</span>
                      {onInspectFrame ? (
                        <span
                          role="button"
                          tabIndex={0}
                          className="frame-catalog-detail"
                          onClick={(event) => handleInspect(frame, event)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              handleInspect(frame, event as unknown as MouseEvent);
                            }
                          }}
                        >
                          {inspecting ? 'detail ✓' : 'detail'}
                        </span>
                      ) : null}
                      <span className="frame-catalog-jump">{selected ? 'current' : 'jump'}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      ) : null}
    </section>
  );
}
