import { useEffect, useMemo, useState } from 'react';
import {
  checkBackendHealth,
  DEFAULT_DEMO_PLAN,
  fetchAccessCurrent,
  fetchLayers,
  fetchTimes,
  fetchTilesConfig,
  type AccessCurrentInfo,
  type DemoPlan,
} from './api/client';
import type { Layer } from './api/client';
import WeatherMap from './map/WeatherMap';
import LayerPanel from './components/LayerPanel';
import TimeSlider from './components/TimeSlider';
import PlaybackControls from './components/PlaybackControls';
import RadarOpacityControl from './components/RadarOpacityControl';
import TimestampDisplay from './components/TimestampDisplay';
import PlanSelector from './components/PlanSelector';
import { usePlayback } from './hooks/usePlayback';
import { DEFAULT_LAYER } from './map/layers';

type LoadState = 'loading' | 'ready' | 'backend_down' | 'error';

export default function App() {
  const [layers, setLayers] = useState<Layer[]>([]);
  const [times, setTimes] = useState<string[]>([]);
  const [processedTimes, setProcessedTimes] = useState<string[]>([]);
  const [selectedLayer, setSelectedLayer] = useState(DEFAULT_LAYER);
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<DemoPlan>(DEFAULT_DEMO_PLAN);
  const [accessInfo, setAccessInfo] = useState<AccessCurrentInfo | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [error, setError] = useState('');
  const [radarOpacity, setRadarOpacity] = useState(0.65);
  const [tileModeLabel, setTileModeLabel] = useState('Placeholder');

  function resolveTileModeLabel(config: Awaited<ReturnType<typeof fetchTilesConfig>>): string {
    if (!config) {
      return 'Placeholder';
    }
    if (config.enable_production_radar_tiles) {
      return 'Production prototype (when built + catalog gate open)';
    }
    if (config.enable_decoded_tiles) {
      return 'Decoded prototype (when artifacts exist)';
    }
    return 'Placeholder';
  }

  const selectedLayerMeta = useMemo(
    () => layers.find((layer) => layer.id === selectedLayer),
    [layers, selectedLayer],
  );

  const playbackTimes = processedTimes.length > 0 ? processedTimes : times;

  const {
    playing,
    speed,
    setSpeed,
    togglePlay,
    stepBackward,
    stepForward,
    jumpToLatest,
    setPlaying,
  } = usePlayback(playbackTimes, selectedTime, setSelectedTime);

  useEffect(() => {
    let cancelled = false;

    async function loadLayers() {
      setLoadState('loading');
      const healthy = await checkBackendHealth();
      if (!healthy) {
        if (!cancelled) {
          setLoadState('backend_down');
          setError('Backend unavailable. Start it with make backend.');
        }
        return;
      }

      try {
        const nextLayers = await fetchLayers(selectedPlan);
        if (!cancelled) {
          setLayers(nextLayers);
          setError('');
        }
      } catch (err) {
        if (!cancelled) {
          setLoadState('error');
          setError(err instanceof Error ? err.message : 'Failed to load layers');
        }
      }
    }

    loadLayers();
    return () => {
      cancelled = true;
    };
  }, [selectedPlan]);

  useEffect(() => {
    let cancelled = false;

    async function loadAccessInfo() {
      try {
        const info = await fetchAccessCurrent(selectedPlan);
        if (!cancelled) {
          setAccessInfo(info);
        }
      } catch {
        if (!cancelled) {
          setAccessInfo(null);
        }
      }
    }

    loadAccessInfo();
    return () => {
      cancelled = true;
    };
  }, [selectedPlan]);

  useEffect(() => {
    let cancelled = false;

    async function loadTileMode() {
      const config = await fetchTilesConfig();
      if (cancelled || !config) {
        return;
      }
      setTileModeLabel(resolveTileModeLabel(config));
    }

    loadTileMode();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadTimes() {
      if (loadState === 'backend_down') {
        return;
      }

      setLoadState('loading');
      try {
        const [nextTimes, nextProcessed] = await Promise.all([
          fetchTimes(selectedLayer, selectedPlan),
          fetchTimes(selectedLayer, selectedPlan, true),
        ]);
        if (!cancelled) {
          setTimes(nextTimes);
          setProcessedTimes(nextProcessed);
          const preferred = nextProcessed[nextProcessed.length - 1] ?? nextTimes[nextTimes.length - 1] ?? '';
          setSelectedTime(preferred);
          setLoadState('ready');
          setError('');
          setPlaying(false);
        }
      } catch (err) {
        if (!cancelled) {
          setTimes([]);
          setProcessedTimes([]);
          setSelectedTime('');
          setLoadState('error');
          setError(err instanceof Error ? err.message : 'Failed to load timestamps');
        }
      }
    }

    loadTimes();
    return () => {
      cancelled = true;
    };
  }, [selectedLayer, selectedPlan, setPlaying]);

  const controlsDisabled = loadState !== 'ready' || times.length === 0;
  const noProcessedTiles = loadState === 'ready' && times.length > 0 && processedTimes.length === 0;
  const selectedNotProcessed =
    loadState === 'ready' && Boolean(selectedTime) && processedTimes.length > 0 && !processedTimes.includes(selectedTime);
  const selectedOutsidePlan =
    loadState === 'ready' && Boolean(selectedTime) && times.length > 0 && !times.includes(selectedTime);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>RadarArchive</h1>
        <p className="demo-banner">
          Tile mode: {tileModeLabel} — not verified real MRMS. Production prototype uses geo warping
          experiments only; default map tiles remain placeholders.
        </p>
      </header>
      <main className="app-main">
        <WeatherMap
          selectedTime={selectedTime}
          selectedLayer={selectedLayer}
          selectedPlan={selectedPlan}
          layerMeta={selectedLayerMeta}
          loading={loadState === 'loading'}
          backendDown={loadState === 'backend_down'}
          noProcessedTiles={noProcessedTiles}
          selectedNotProcessed={selectedNotProcessed}
          selectedOutsidePlan={selectedOutsidePlan}
          accessInfo={accessInfo}
          opacity={radarOpacity}
        />
        <aside className="app-controls">
          {loadState === 'backend_down' ? (
            <p className="error-banner">Backend unavailable. Run <code>make backend</code>.</p>
          ) : null}
          {error && loadState !== 'backend_down' ? <p className="error-banner">{error}</p> : null}
          {noProcessedTiles ? (
            <p className="warn-banner">No processed tiles yet. Run <code>make process-once</code>.</p>
          ) : null}
          {selectedOutsidePlan ? (
            <p className="warn-banner">
              Selected timestamp is outside your {selectedPlan} plan limit. Choose an allowed frame or upgrade plan.
            </p>
          ) : null}
          {selectedNotProcessed ? (
            <p className="warn-banner">Selected timestamp is not processed yet. Choose a processed frame or run process-once.</p>
          ) : null}
          <PlanSelector plan={selectedPlan} accessInfo={accessInfo} onChange={setSelectedPlan} />
          <LayerPanel layers={layers} selectedLayer={selectedLayer} onSelect={setSelectedLayer} />
          <TimestampDisplay
            timestamp={selectedTime}
            processedCount={processedTimes.length}
            totalCount={times.length}
          />
          <TimeSlider
            times={times}
            selectedTime={selectedTime}
            onSelect={(time) => {
              setPlaying(false);
              setSelectedTime(time);
            }}
            disabled={controlsDisabled}
          />
          <PlaybackControls
            times={playbackTimes}
            selectedTime={selectedTime}
            disabled={controlsDisabled || playbackTimes.length === 0}
            playing={playing}
            speed={speed}
            onTogglePlay={togglePlay}
            onStepBackward={() => {
              setPlaying(false);
              stepBackward();
            }}
            onStepForward={() => {
              setPlaying(false);
              stepForward();
            }}
            onJumpLatest={() => {
              setPlaying(false);
              jumpToLatest();
            }}
            onSpeedChange={setSpeed}
          />
          <RadarOpacityControl
            opacity={radarOpacity}
            onChange={setRadarOpacity}
            disabled={controlsDisabled || noProcessedTiles}
          />
        </aside>
      </main>
      <footer>
        Powered by public NOAA/NWS data. Not affiliated with or endorsed by NOAA or the National Weather Service.
      </footer>
    </div>
  );
}
