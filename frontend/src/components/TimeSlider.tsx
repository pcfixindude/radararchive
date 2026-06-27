export default function TimeSlider({
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
  const index = Math.max(0, times.indexOf(selectedTime));
  return (
    <section className="panel">
      <h2>Time</h2>
      <input
        type="range"
        min="0"
        max={Math.max(0, times.length - 1)}
        value={index}
        disabled={disabled}
        onChange={(event) => onSelect(times[Number(event.target.value)] ?? '')}
      />
      <p>{selectedTime || 'No timestamps loaded'}</p>
    </section>
  );
}
