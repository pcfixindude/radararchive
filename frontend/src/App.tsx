import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  checkBackendHealth,
  DEFAULT_DEMO_PLAN,
  fetchAccessCurrent,
  fetchLayers,
  fetchTimes,
  fetchTilesConfig,
  fetchRenderQueueSummary,
  fetchValidationSummary,
  type ValidationSummary,
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
import ValidationStatusPanel from './components/ValidationStatusPanel';
import DecodedOverlayPanel from './components/DecodedOverlayPanel';
import ReplayMapControls from './components/ReplayMapControls';
import ReplayRangeControls from './components/ReplayRangeControls';
import IngestWindowPanel from './components/IngestWindowPanel';
import ReplayBookmarksPanel from './components/ReplayBookmarksPanel';
import ReplaySessionPanel from './components/ReplaySessionPanel';
import FrameCatalogPanel from './components/FrameCatalogPanel';
import { DEFAULT_INGEST_WINDOW_STATE, type IngestWindowFormState } from './components/ingestWindow';
import { buildReplaySessionSummary } from './components/replaySessionSummary';
import { DEFAULT_REPLAY_DISPLAY, overlayReadyForMap, type ReplayDisplayState } from './components/replayDisplay';
import type { ReplayShortcutAction } from './hooks/keyboardShortcuts';
import { useReplayKeyboardShortcuts } from './hooks/useReplayKeyboardShortcuts';
import { useReplayBookmarks } from './hooks/useReplayBookmarks';
import { useLocalReplayReady } from './hooks/useLocalReplayReady';
import { useFrameCatalog } from './hooks/useFrameCatalog';
import { useReplayRange } from './hooks/useReplayRange';
import { usePlayback } from './hooks/usePlayback';
import { useFrameOverlay } from './hooks/useFrameOverlay';
import { usePlaybackCacheStatus } from './hooks/usePlaybackCacheStatus';
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
  const [renderJobHint, setRenderJobHint] = useState('');
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  const [validationRefreshing, setValidationRefreshing] = useState(false);
  const [replayDisplay, setReplayDisplay] = useState<ReplayDisplayState>(DEFAULT_REPLAY_DISPLAY);
  const [fitBoundsToken, setFitBoundsToken] = useState(0);
  const [ingestForm, setIngestForm] = useState<IngestWindowFormState>(DEFAULT_INGEST_WINDOW_STATE);

  const replayBookmarks = useReplayBookmarks();
  const localReplayReady = useLocalReplayReady(loadState === 'ready');

  const refreshValidationSummary = async () => {
    setValidationRefreshing(true);
    try {
      const summary = await fetchValidationSummary();
      setValidationSummary(summary);
    } finally {
      setValidationRefreshing(false);
    }
  };

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

  const playbackTimes = useMemo(() => {
    const merged = [...new Set([...times, ...processedTimes])].sort();
    return merged.length > 0 ? merged : [];
  }, [times, processedTimes]);

  const replayRange = useReplayRange(playbackTimes, selectedTime);

  const {
    playing,
    speed,
    setSpeed,
    togglePlay,
    stepBackward,
    stepForward,
    jumpToLatest,
    setPlaying,
  } = usePlayback(
    playbackTimes,
    selectedTime,
    setSelectedTime,
    replayRange.resolvedRange,
    replayRange.loopActive,
  );

  const {
    decodedOverlay,
    displayOverlay,
    frameStatus: playbackFrameStatus,
    refreshing: decodedOverlayRefreshing,
    refreshDecodedOverlay,
    clearFrameCache,
  } = useFrameOverlay(playbackTimes, selectedTime, playing, loadState === 'ready');

  const { cacheStatus, refetchCacheStatus } = usePlaybackCacheStatus(
    playbackTimes,
    loadState === 'ready',
  );

  const frameCatalog = useFrameCatalog(playbackTimes, loadState === 'ready');

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

    async function loadRenderJobs() {
      const summary = await fetchRenderQueueSummary();
      if (cancelled || !summary) {
        return;
      }
      setRenderJobHint(
        `Render queue (prototype): queued ${summary.queued}, running ${summary.running}, failed ${summary.failed} — not verified MRMS`,
      );
    }

    loadRenderJobs();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadValidationSummary() {
      const summary = await fetchValidationSummary();
      if (!cancelled) {
        setValidationSummary(summary);
      }
    }

    loadValidationSummary();
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
          clearFrameCache();
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
  }, [selectedLayer, selectedPlan, setPlaying, clearFrameCache]);

  const controlsDisabled = loadState !== 'ready' || times.length === 0;
  const noProcessedTiles = loadState === 'ready' && times.length > 0 && processedTimes.length === 0;
  const selectedNotProcessed =
    loadState === 'ready' && Boolean(selectedTime) && processedTimes.length > 0 && !processedTimes.includes(selectedTime);
  const selectedOutsidePlan =
    loadState === 'ready' && Boolean(selectedTime) && times.length > 0 && !times.includes(selectedTime);
  const overlayMapReady = overlayReadyForMap(displayOverlay ?? decodedOverlay);
  const canFitBounds = overlayMapReady && Boolean(replayDisplay.showDecodedOverlay);

  const sessionSummary = useMemo(
    () =>
      buildReplaySessionSummary({
        loadState,
        selectedTime,
        overlay: decodedOverlay,
        cacheStatus,
        playbackFrameStatus,
        playing,
        frameCount: playbackTimes.length,
      }),
    [
      loadState,
      selectedTime,
      decodedOverlay,
      cacheStatus,
      playbackFrameStatus,
      playing,
      playbackTimes.length,
    ],
  );

  const handleShortcutAction = useCallback(
    (action: ReplayShortcutAction) => {
      switch (action) {
        case 'togglePlay':
          if (!controlsDisabled && playbackTimes.length > 0) {
            togglePlay();
          }
          break;
        case 'stepBackward':
          setPlaying(false);
          stepBackward();
          break;
        case 'stepForward':
          setPlaying(false);
          stepForward();
          break;
        case 'toggleOverlay':
          if (overlayMapReady) {
            setReplayDisplay((current) => ({
              ...current,
              showDecodedOverlay: !current.showDecodedOverlay,
            }));
          }
          break;
        case 'toggleBounds':
          setReplayDisplay((current) => ({
            ...current,
            showBoundsOutline: !current.showBoundsOutline,
          }));
          break;
        case 'fitBounds':
          if (canFitBounds) {
            setFitBoundsToken((token) => token + 1);
          }
          break;
        case 'setRangeStart':
          if (!controlsDisabled && selectedTime) {
            replayRange.setStartFromSelected();
          }
          break;
        case 'setRangeEnd':
          if (!controlsDisabled && selectedTime) {
            replayRange.setEndFromSelected();
          }
          break;
        case 'toggleLoopRange':
          if (!controlsDisabled) {
            replayRange.toggleLoopRange();
          }
          break;
        case 'clearRange':
          if (replayRange.rangeStart || replayRange.rangeEnd) {
            replayRange.clearRange();
          }
          break;
        default:
          break;
      }
    },
    [
      controlsDisabled,
      playbackTimes.length,
      togglePlay,
      setPlaying,
      stepBackward,
      stepForward,
      overlayMapReady,
      canFitBounds,
      selectedTime,
      replayRange,
    ],
  );

  useReplayKeyboardShortcuts({
    enabled: loadState === 'ready',
    canStep: !controlsDisabled && playbackTimes.length > 0,
    canFitBounds,
    onAction: handleShortcutAction,
  });

  const handleIngestFormChange = useCallback((patch: Partial<IngestWindowFormState>) => {
    setIngestForm((current) => ({ ...current, ...patch }));
  }, []);

  const handleSaveBookmark = useCallback(
    (name: string) => {
      replayBookmarks.saveBookmark(name, {
        selectedLayer,
        selectedTime: selectedTime || null,
        rangeStart: replayRange.rangeStart,
        rangeEnd: replayRange.rangeEnd,
        loopRange: replayRange.loopRange,
        ingest: ingestForm,
      });
    },
    [
      replayBookmarks,
      selectedLayer,
      selectedTime,
      replayRange.rangeStart,
      replayRange.rangeEnd,
      replayRange.loopRange,
      ingestForm,
    ],
  );

  const handleLoadBookmark = useCallback(
    (id: string) => {
      const plan = replayBookmarks.planBookmarkRestore(id, playbackTimes);
      if (!plan) {
        return;
      }
      setSelectedLayer(plan.selectedLayer);
      replayRange.loadRangeState({
        rangeStart: plan.rangeStart,
        rangeEnd: plan.rangeEnd,
        loopRange: plan.loopRange,
      });
      setIngestForm(plan.ingest);
      if (plan.selectedTime) {
        setSelectedTime(plan.selectedTime);
      }
      setPlaying(false);
    },
    [replayBookmarks, playbackTimes, replayRange, setPlaying],
  );

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>RadarArchive</h1>
        <p className="demo-banner">
          Tile mode: {tileModeLabel} — experimental validation pipeline; not verified real MRMS.
          Production prototype uses geo warping experiments only; default map tiles remain placeholders.
        </p>
        {renderJobHint ? <p className="demo-banner subtle">{renderJobHint}</p> : null}
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
          decodedOverlay={displayOverlay}
          overlayTransitioning={decodedOverlayRefreshing && playbackFrameStatus === 'decoding'}
          playbackFrameStatus={playbackFrameStatus}
          showDecodedOverlay={replayDisplay.showDecodedOverlay}
          showBoundsOutline={replayDisplay.showBoundsOutline}
          fitBoundsToken={fitBoundsToken}
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
          <ReplaySessionPanel
            summary={sessionSummary}
            setupStatus={localReplayReady.status}
            setupLoading={localReplayReady.loading}
            setupError={localReplayReady.error}
            onRefreshSetup={localReplayReady.refresh}
          />
          <FrameCatalogPanel
            disabled={controlsDisabled}
            catalog={frameCatalog.catalog}
            loading={frameCatalog.loading}
            error={frameCatalog.error}
            selectedTime={selectedTime}
            onSelectFrame={(time) => {
              setPlaying(false);
              setSelectedTime(time);
            }}
            onRefresh={frameCatalog.refresh}
          />
          <ReplayBookmarksPanel
            disabled={controlsDisabled}
            bookmarks={replayBookmarks.bookmarks}
            storageWarning={replayBookmarks.storageWarning}
            lastLoadedId={replayBookmarks.lastLoadedId}
            restoreHints={replayBookmarks.restoreHints}
            onSave={handleSaveBookmark}
            onLoad={handleLoadBookmark}
            onDelete={replayBookmarks.deleteBookmark}
            onRename={replayBookmarks.renameBookmark}
          />
          <IngestWindowPanel
            disabled={controlsDisabled}
            replayRangeStart={replayRange.resolvedRange?.start ?? null}
            replayRangeEnd={replayRange.resolvedRange?.end ?? null}
            form={ingestForm}
            onFormChange={handleIngestFormChange}
          />
          <ReplayRangeControls disabled={controlsDisabled} range={replayRange} />
          <PlanSelector plan={selectedPlan} accessInfo={accessInfo} onChange={setSelectedPlan} />
          <ReplayMapControls
            display={replayDisplay}
            onChange={(patch) => setReplayDisplay((current) => ({ ...current, ...patch }))}
            overlayBounds={displayOverlay?.bounds ?? decodedOverlay?.bounds}
            overlayAvailable={overlayMapReady}
            onFitToBounds={() => setFitBoundsToken((token) => token + 1)}
          />
          <DecodedOverlayPanel
            overlay={decodedOverlay}
            selectedTime={selectedTime}
            playbackFrameStatus={playbackFrameStatus}
            cacheStatus={cacheStatus}
            showGeorefDebug={replayDisplay.showGeorefDebug}
            showFrameQualityDetails={replayDisplay.showFrameQualityDetails}
            onRefresh={async () => {
              await refreshDecodedOverlay();
              refetchCacheStatus();
            }}
            refreshing={decodedOverlayRefreshing}
          />
          <ValidationStatusPanel
            summary={validationSummary}
            onRefresh={refreshValidationSummary}
            refreshing={validationRefreshing}
          />
          <LayerPanel layers={layers} selectedLayer={selectedLayer} onSelect={setSelectedLayer} />
          <TimestampDisplay
            timestamp={selectedTime}
            processedCount={processedTimes.length}
            totalCount={times.length}
          />
          <TimeSlider
            times={playbackTimes}
            selectedTime={selectedTime}
            cacheStatus={cacheStatus}
            rangeStartIndex={replayRange.resolvedRange?.startIndex ?? null}
            rangeEndIndex={replayRange.resolvedRange?.endIndex ?? null}
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
            playbackFrameStatus={playbackFrameStatus}
            cacheStatus={cacheStatus}
            range={replayRange}
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
