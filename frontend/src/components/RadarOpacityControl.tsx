export default function RadarOpacityControl({
  opacity,
  onChange,
  disabled = false,
}: {
  opacity: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <section className="panel">
      <h2>Radar Opacity</h2>
      <input
        type="range"
        min="0"
        max="100"
        value={Math.round(opacity * 100)}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value) / 100)}
      />
      <p>{Math.round(opacity * 100)}%</p>
    </section>
  );
}
