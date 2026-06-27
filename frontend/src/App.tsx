import { useEffect, useState } from 'react';
import { fetchLayers, fetchTimes } from './api/client';
import type { Layer } from './api/client';
import WeatherMap from './map/WeatherMap';
import LayerPanel from './components/LayerPanel';
import TimeSlider from './components/TimeSlider';
import PlaybackControls from './components/PlaybackControls';
import RadarOpacityControl from './components/RadarOpacityControl';
import { DEFAULT_LAYER } from './map/layers';

export default function App() {
  const [layers, setLayers] = useState<Layer[]>([]);
  const [times, setTimes] = useState<string[]>([]);
  const [selectedLayer, setSelectedLayer] = useState(DEFAULT_LAYER);
  const [selectedTime, setSelectedTime] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [radarOpacity, setRadarOpacity] = useState(0.65);

  useEffect(() => {
    let cancelled = false;

    async function loadLayers() {
      try {
        const nextLayers = await fetchLayers();
        if (!cancelled) {
          setLayers(nextLayers);
          setError('');
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load layers');
        }
      }
    }

    loadLayers();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadTimes() {
      setLoading(true);
      try {
        const nextTimes = await fetchTimes(selectedLayer);
        if (!cancelled) {
          setTimes(nextTimes);
          setSelectedTime(nextTimes[nextTimes.length - 1] ?? '');
          setError('');
        }
      } catch (err) {
        if (!cancelled) {
          setTimes([]);
          setSelectedTime('');
          setError(err instanceof Error ? err.message : 'Failed to load timestamps');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadTimes();
    return () => {
      cancelled = true;
    };
  }, [selectedLayer]);

  return (
    <div className="app-shell">
      <header>
        <h1>RadarArchive</h1>
        <p>Historical weather replay app</p>
        <p className="demo-banner">Placeholder tiles on MapLibre — not real NOAA/MRMS radar imagery.</p>
      </header>
      <main>
        <WeatherMap
          selectedTime={selectedTime}
          selectedLayer={selectedLayer}
          layerAvailable={layers.find((layer) => layer.id === selectedLayer)?.available ?? false}
          loading={loading}
          opacity={radarOpacity}
        />
        <aside>
          {error ? <p className="error-banner">{error}</p> : null}
          <LayerPanel layers={layers} selectedLayer={selectedLayer} onSelect={setSelectedLayer} />
          <RadarOpacityControl
            opacity={radarOpacity}
            onChange={setRadarOpacity}
            disabled={loading || times.length === 0}
          />
          <TimeSlider times={times} selectedTime={selectedTime} onSelect={setSelectedTime} disabled={loading || times.length === 0} />
          <PlaybackControls times={times} selectedTime={selectedTime} onSelect={setSelectedTime} disabled={loading || times.length === 0} />
        </aside>
      </main>
      <footer>
        Powered by public NOAA/NWS data. Not affiliated with or endorsed by NOAA or the National Weather Service.
      </footer>
    </div>
  );
}
