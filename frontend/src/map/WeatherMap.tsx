export default function WeatherMap({
  selectedTime,
  selectedLayer,
  loading,
}: {
  selectedTime: string;
  selectedLayer: string;
  loading: boolean;
}) {
  return (
    <section className="map-placeholder" aria-label="Map placeholder">
      <div>
        <h2>Map Placeholder</h2>
        <p>Layer: {selectedLayer}</p>
        <p>Time: {loading ? 'loading...' : selectedTime || 'no timestamps'}</p>
        <p>Phase 1 uses fake/demo catalog data. Real map tiles come in a later phase.</p>
      </div>
    </section>
  );
}
