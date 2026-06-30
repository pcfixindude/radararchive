import { PLAYBACK_SPEEDS } from '../hooks/usePlayback';
import { playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';
import type { PlaybackCacheStatus } from '../api/client';

export default function PlaybackControls({
  times,
  selectedTime,
  disabled = false,
  playing,
  speed,
  playbackFrameStatus = 'idle',
  cacheStatus = null,
  onTogglePlay,
  onStepBackward,
  onStepForward,
  onJumpLatest,
  onSpeedChange,
}: {
  times: string[];
  selectedTime: string;
  disabled?: boolean;
  playing: boolean;
  speed: number;
  playbackFrameStatus?: PlaybackFrameStatus;
  cacheStatus?: PlaybackCacheStatus | null;
  onTogglePlay: () => void;
  onStepBackward: () => void;
  onStepForward: () => void;
  onJumpLatest: () => void;
  onSpeedChange: (speed: number) => void;
}) {
  const index = times.indexOf(selectedTime);

  return (
    <section className="panel playback-panel">
      <h2>Playback</h2>
      <div className="controls playback-buttons">
        <button type="button" disabled={disabled} onClick={onStepBackward} aria-label="Step backward">
          ◀
        </button>
        <button type="button" disabled={disabled} onClick={onTogglePlay} aria-label={playing ? 'Pause' : 'Play'}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button type="button" disabled={disabled} onClick={onStepForward} aria-label="Step forward">
          ▶
        </button>
        <button type="button" disabled={disabled} onClick={onJumpLatest}>
          Latest
        </button>
      </div>
      <label className="speed-label">
        Speed
        <select
          value={speed}
          disabled={disabled}
          onChange={(event) => onSpeedChange(Number(event.target.value))}
        >
          {PLAYBACK_SPEEDS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <p className="playback-meta">
        Frame {times.length === 0 ? 0 : index + 1} of {times.length}
      </p>
      <p className={`playback-meta playback-status playback-status--${playbackFrameStatus}`}>
        Overlay: {playbackStatusLabel(playbackFrameStatus)}
      </p>
      {cacheStatus ? (
        <p className="playback-meta">
          Cache: <code>{cacheStatus.warmed_count} ready</code> / {cacheStatus.frame_count}
          {cacheStatus.failed_count ? (
            <>, <code>{cacheStatus.failed_count} failed</code></>
          ) : null}
          {cacheStatus.missing_count ? (
            <>, <code>{cacheStatus.missing_count} missing</code></>
          ) : null}
        </p>
      ) : null}
      {!cacheStatus?.playback_ready && cacheStatus?.next_commands?.[0] ? (
        <p className="playback-meta playback-hint">
          Warm cache: <code>{cacheStatus.next_commands[0]}</code>
        </p>
      ) : null}
    </section>
  );
}
