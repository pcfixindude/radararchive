import { PLAYBACK_SPEEDS } from '../hooks/usePlayback';
import { playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';

export default function PlaybackControls({
  times,
  selectedTime,
  disabled = false,
  playing,
  speed,
  playbackFrameStatus = 'idle',
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
    </section>
  );
}
