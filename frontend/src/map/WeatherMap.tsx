import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { AccessCurrentInfo, DecodedOverlayInfo, DemoPlan, Layer } from '../api/client';
import { decodedOverlayPreviewUrl, decodedOverlayTileUrlTemplate, tileUrlTemplate, tilesAvailable, tileBlockedByPlan } from '../api/client';
import { playbackStatusLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';
import {
  BASEMAP_STYLE,
  DECODED_OVERLAY_LAYER_ID,
  DECODED_OVERLAY_SOURCE_ID,
  DECODED_OVERLAY_TILE_LAYER_ID,
  DECODED_OVERLAY_TILE_SOURCE_ID,
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  RADAR_LAYER_ID,
  RADAR_SOURCE_ID,
} from './mapConfig';

type LayerMeta = Pick<Layer, 'available' | 'tile_support' | 'bounds' | 'minzoom' | 'maxzoom' | 'placeholder'>;

export default function WeatherMap({
  selectedTime,
  selectedLayer,
  selectedPlan,
  layerMeta,
  loading,
  backendDown,
  noProcessedTiles,
  selectedNotProcessed,
  selectedOutsidePlan,
  accessInfo,
  opacity,
  decodedOverlay,
  overlayTransitioning = false,
  playbackFrameStatus = 'idle',
}: {
  selectedTime: string;
  selectedLayer: string;
  selectedPlan: DemoPlan;
  layerMeta?: LayerMeta;
  loading: boolean;
  backendDown: boolean;
  noProcessedTiles: boolean;
  selectedNotProcessed: boolean;
  selectedOutsidePlan: boolean;
  accessInfo: AccessCurrentInfo | null;
  opacity: number;
  decodedOverlay: DecodedOverlayInfo | null;
  overlayTransitioning?: boolean;
  playbackFrameStatus?: PlaybackFrameStatus;
}) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [tilesReady, setTilesReady] = useState(false);
  const [planBlocked, setPlanBlocked] = useState(false);

  const tileSupport = Boolean(layerMeta?.available && layerMeta?.tile_support);
  const bounds = layerMeta?.bounds ?? undefined;
  const minzoom = layerMeta?.minzoom ?? undefined;
  const maxzoom = layerMeta?.maxzoom ?? undefined;

  const overlayActive =
    Boolean(decodedOverlay?.overlay_visible && decodedOverlay.bounds?.length === 4);
  const overlayTileTemplate = decodedOverlay ? decodedOverlayTileUrlTemplate(decodedOverlay) : null;
  const useOverlayTiles = Boolean(overlayActive && overlayTileTemplate);
  const overlayStatus = decodedOverlay?.overlay_status ?? 'missing';

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return undefined;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLE,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      attributionControl: { compact: true },
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.on('load', () => setMapReady(true));
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function checkTiles() {
      if (!selectedTime || loading || !tileSupport || backendDown || noProcessedTiles || selectedOutsidePlan) {
        if (!cancelled) {
          setTilesReady(false);
          setPlanBlocked(selectedOutsidePlan);
        }
        return;
      }

      const blocked = await tileBlockedByPlan(selectedLayer, selectedTime, selectedPlan);
      if (blocked) {
        if (!cancelled) {
          setTilesReady(false);
          setPlanBlocked(true);
        }
        return;
      }

      const ready = await tilesAvailable(selectedLayer, selectedTime, selectedPlan);
      if (!cancelled) {
        setPlanBlocked(false);
        setTilesReady(ready);
      }
    }

    checkTiles();
    return () => {
      cancelled = true;
    };
  }, [selectedLayer, selectedTime, selectedPlan, loading, tileSupport, backendDown, noProcessedTiles, selectedOutsidePlan]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }

    const removeRadarLayer = () => {
      if (map.getLayer(RADAR_LAYER_ID)) {
        map.removeLayer(RADAR_LAYER_ID);
      }
      if (map.getSource(RADAR_SOURCE_ID)) {
        map.removeSource(RADAR_SOURCE_ID);
      }
    };

    if (!tilesReady || !selectedTime || !tileSupport || selectedNotProcessed || planBlocked) {
      removeRadarLayer();
      return;
    }

    removeRadarLayer();

    map.addSource(RADAR_SOURCE_ID, {
      type: 'raster',
      tiles: [tileUrlTemplate(selectedLayer, selectedTime, selectedPlan)],
      tileSize: 256,
      ...(bounds ? { bounds } : {}),
      ...(minzoom !== undefined ? { minzoom } : {}),
      ...(maxzoom !== undefined ? { maxzoom } : {}),
    });

    map.addLayer({
      id: RADAR_LAYER_ID,
      type: 'raster',
      source: RADAR_SOURCE_ID,
      paint: {
        'raster-opacity': opacity,
      },
    });
  }, [
    mapReady,
    selectedLayer,
    selectedTime,
    selectedPlan,
    tilesReady,
    tileSupport,
    selectedNotProcessed,
    planBlocked,
    opacity,
    bounds,
    minzoom,
    maxzoom,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }

    const removeOverlay = () => {
      for (const layerId of [DECODED_OVERLAY_LAYER_ID, DECODED_OVERLAY_TILE_LAYER_ID]) {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId);
        }
      }
      for (const sourceId of [DECODED_OVERLAY_SOURCE_ID, DECODED_OVERLAY_TILE_SOURCE_ID]) {
        if (map.getSource(sourceId)) {
          map.removeSource(sourceId);
        }
      }
    };

    if (!overlayActive || !decodedOverlay) {
      if (!overlayTransitioning) {
        removeOverlay();
      }
      return;
    }

    const [west, south, east, north] = decodedOverlay.bounds;
    removeOverlay();

    if (useOverlayTiles && overlayTileTemplate) {
      map.addSource(DECODED_OVERLAY_TILE_SOURCE_ID, {
        type: 'raster',
        tiles: [overlayTileTemplate],
        tileSize: 256,
        bounds: [west, south, east, north],
        minzoom: 0,
        maxzoom: decodedOverlay.tile_max_z ?? 1,
      });
      map.addLayer({
        id: DECODED_OVERLAY_TILE_LAYER_ID,
        type: 'raster',
        source: DECODED_OVERLAY_TILE_SOURCE_ID,
        paint: {
          'raster-opacity': Math.min(1, opacity + 0.1),
        },
      });
      return;
    }

    if (!decodedOverlay.preview_url) {
      return;
    }

    map.addSource(DECODED_OVERLAY_SOURCE_ID, {
      type: 'image',
      url: decodedOverlayPreviewUrl(decodedOverlay),
      coordinates: [
        [west, north],
        [east, north],
        [east, south],
        [west, south],
      ],
    });

    map.addLayer({
      id: DECODED_OVERLAY_LAYER_ID,
      type: 'raster',
      source: DECODED_OVERLAY_SOURCE_ID,
      paint: {
        'raster-opacity': Math.min(1, opacity + 0.1),
      },
    });
  }, [mapReady, overlayActive, useOverlayTiles, overlayTileTemplate, decodedOverlay, opacity, overlayTransitioning]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !decodedOverlay?.bounds?.length) {
      return;
    }
    const [west, south, east, north] = decodedOverlay.bounds;
    map.fitBounds(
      [
        [west, south],
        [east, north],
      ],
      { padding: 24, duration: 0 },
    );
  }, [mapReady, decodedOverlay?.bounds]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !map.getLayer(RADAR_LAYER_ID)) {
      return;
    }
    map.setPaintProperty(RADAR_LAYER_ID, 'raster-opacity', opacity);
  }, [opacity, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }
    const overlayOpacity = Math.min(1, opacity + 0.1);
    if (map.getLayer(DECODED_OVERLAY_LAYER_ID)) {
      map.setPaintProperty(DECODED_OVERLAY_LAYER_ID, 'raster-opacity', overlayOpacity);
    }
    if (map.getLayer(DECODED_OVERLAY_TILE_LAYER_ID)) {
      map.setPaintProperty(DECODED_OVERLAY_TILE_LAYER_ID, 'raster-opacity', overlayOpacity);
    }
  }, [opacity, mapReady]);

  const statusMessage = backendDown
    ? 'Backend unavailable.'
    : loading
      ? 'Loading timestamps...'
      : noProcessedTiles
        ? 'No processed placeholder tiles. Run make process-once.'
        : selectedOutsidePlan || planBlocked
          ? `${selectedPlan} plan blocked this timestamp. ${accessInfo?.upgrade_message ?? 'Choose a higher plan.'}`
          : !selectedTime
            ? 'No timestamps loaded.'
            : !tileSupport
              ? 'Selected layer has no tile support yet.'
              : selectedNotProcessed
                ? 'Selected timestamp is not processed.'
                : tilesReady
                  ? 'Placeholder tiles active'
                  : 'Checking tile availability...';

  const overlayBadge =
    overlayTransitioning
      ? 'Loading next frame…'
      : playbackFrameStatus === 'decoding'
        ? 'Decoding selected frame…'
        : decodedOverlay?.sync_status === 'matched'
      ? useOverlayTiles
        ? 'Decoded color tiles synced — local dev only'
        : 'Decoded color overlay synced — local dev only'
      : decodedOverlay?.sync_status === 'mismatch'
        ? 'Decoded overlay hidden — time mismatch'
        : overlayActive
          ? `${overlayStatus.replace(/_/g, ' ')} overlay — local dev only`
          : 'Select matching catalog frame for decoded overlay';

  return (
    <section className="map-panel" aria-label="Weather map">
      <div ref={mapContainerRef} className="map-container" />
      <div className="map-badge">Placeholder tiles — not real radar</div>
      <div className={`map-badge map-badge--overlay ${overlayActive ? 'map-badge--overlay-active' : ''}`}>
        {overlayBadge}
      </div>
      <p className="map-status">{statusMessage}</p>
    </section>
  );
}
