import { cacheStateClass, cacheStateLabel, type FrameCacheState } from '../hooks/framePlayback';
import type { PlaybackCacheStatus } from '../api/client';

export default function TimeSlider({
  times,
  selectedTime,
  onSelect,
  disabled = false,
  cacheStatus = null,
}: {
  times: string[];
  selectedTime: string;
  onSelect: (time: string) => void;
  disabled?: boolean;
  cacheStatus?: PlaybackCacheStatus | null;
}) {
  const index = Math.max(0, times.indexOf(selectedTime));
  const stateByTime = new Map(
    (cacheStatus?.frames ?? []).map((frame) => [frame.timestamp, frame.cache_state as FrameCacheState]),
  );

  return (
    <section className="panel time-slider-panel">
      <h2>Time</h2>
      <input
        type="range"
        min="0"
        max={Math.max(0, times.length - 1)}
        value={index}
        disabled={disabled}
        onChange={(event) => onSelect(times[Number(event.target.value)] ?? '')}
      />
      {times.length > 0 ? (
        <div className="slider-cache-track" aria-label="Frame cache status">
          {times.map((time) => {
            const state = stateByTime.get(time) ?? 'missing_raw';
            const selected = time === selectedTime;
            return (
              <span
                key={time}
                className={`slider-cache-dot ${cacheStateClass(state)}${selected ? ' slider-cache-dot--selected' : ''}`}
                title={`${time}: ${cacheStateLabel(state)}`}
              />
            );
          })}
        </div>
      ) : null}
      <p>{selectedTime || 'No timestamps loaded'}</p>
      {cacheStatus ? (
        <p className="slider-cache-summary">
          Cache: {cacheStatus.warmed_count} ready, {cacheStatus.cold_count} cold,{' '}
          {cacheStatus.missing_count} missing
          {cacheStatus.failed_count ? `, ${cacheStatus.failed_count} failed` : ''}
        </p>
      ) : null}
    </section>
  );
}
