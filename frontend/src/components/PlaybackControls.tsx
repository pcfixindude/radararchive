export default function PlaybackControls({
  times,
  selectedTime,
  onSelect,
  disabled = false,
}: {
  times: string[];
  selectedTime: string;
  onSelect: (time: string) => void;
  disabled?: boolean;
}) {
  const index = times.indexOf(selectedTime);
  return (
    <section className="panel controls">
      <button disabled={disabled} onClick={() => onSelect(times[Math.max(0, index - 1)] ?? selectedTime)}>
        Back
      </button>
      <button disabled={disabled} onClick={() => onSelect(times[Math.min(times.length - 1, index + 1)] ?? selectedTime)}>
        Forward
      </button>
      <button disabled={disabled} onClick={() => onSelect(times[times.length - 1] ?? '')}>
        Latest
      </button>
    </section>
  );
}
