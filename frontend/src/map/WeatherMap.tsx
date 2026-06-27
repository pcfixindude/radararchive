import { useEffect, useState } from 'react';
import { tileUrl, tilesAvailable } from '../api/client';

export default function WeatherMap({
  selectedTime,
  selectedLayer,
  loading,
}: {
  selectedTime: string;
  selectedLayer: string;
  loading: boolean;
}) {
  const [tilesReady, setTilesReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function checkTiles() {
      if (!selectedTime || loading) {
        setTilesReady(false);
        return;
      }
      const ready = await tilesAvailable(selectedLayer, selectedTime);
      if (!cancelled) {
        setTilesReady(ready);
      }
    }

    checkTiles();
    return () => {
      cancelled = true;
    };
  }, [selectedLayer, selectedTime, loading]);

  const previewUrl =
    selectedTime && tilesReady ? `${tileUrl(selectedLayer, selectedTime)}?t=${encodeURIComponent(selectedTime)}` : '';

  return (
    <section className="map-placeholder" aria-label="Map placeholder">
      <div className="map-preview-wrap">
        {previewUrl ? (
          <img
            className="tile-preview"
            src={previewUrl}
            alt="Placeholder radar tile (not real MRMS imagery)"
          />
        ) : null}
        <div className="map-preview-caption">
          <h2>Map Placeholder</h2>
          <p>Layer: {selectedLayer}</p>
          <p>Time: {loading ? 'loading...' : selectedTime || 'no timestamps'}</p>
          <p>
            Tiles:{' '}
            {loading
              ? 'checking...'
              : tilesReady
                ? 'placeholder tiles available (stub PNG)'
                : 'not available — run make process-once'}
          </p>
          <p>Stub/demo pipeline only. Not real radar imagery.</p>
        </div>
      </div>
    </section>
  );
}
