import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { Layer } from '../api/client';
import { tileUrlTemplate, tilesAvailable } from '../api/client';
import {
  BASEMAP_STYLE,
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  RADAR_LAYER_ID,
  RADAR_SOURCE_ID,
} from './mapConfig';

type LayerMeta = Pick<Layer, 'available' | 'tile_support' | 'bounds' | 'minzoom' | 'maxzoom' | 'placeholder'>;

export default function WeatherMap({
  selectedTime,
  selectedLayer,
  layerMeta,
  loading,
  backendDown,
  noProcessedTiles,
  selectedNotProcessed,
  opacity,
}: {
  selectedTime: string;
  selectedLayer: string;
  layerMeta?: LayerMeta;
  loading: boolean;
  backendDown: boolean;
  noProcessedTiles: boolean;
  selectedNotProcessed: boolean;
  opacity: number;
}) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [tilesReady, setTilesReady] = useState(false);

  const tileSupport = Boolean(layerMeta?.available && layerMeta?.tile_support);
  const bounds = layerMeta?.bounds ?? undefined;
  const minzoom = layerMeta?.minzoom ?? undefined;
  const maxzoom = layerMeta?.maxzoom ?? undefined;

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
      if (!selectedTime || loading || !tileSupport || backendDown || noProcessedTiles) {
        if (!cancelled) {
          setTilesReady(false);
        }
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
  }, [selectedLayer, selectedTime, loading, tileSupport, backendDown, noProcessedTiles]);

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

    if (!tilesReady || !selectedTime || !tileSupport || selectedNotProcessed) {
      removeRadarLayer();
      return;
    }

    removeRadarLayer();

    map.addSource(RADAR_SOURCE_ID, {
      type: 'raster',
      tiles: [tileUrlTemplate(selectedLayer, selectedTime)],
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
  }, [mapReady, selectedLayer, selectedTime, tilesReady, tileSupport, selectedNotProcessed, opacity, bounds, minzoom, maxzoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !bounds) {
      return;
    }
    map.fitBounds(
      [
        [bounds[0], bounds[1]],
        [bounds[2], bounds[3]],
      ],
      { padding: 24, duration: 0 },
    );
  }, [mapReady, bounds]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !map.getLayer(RADAR_LAYER_ID)) {
      return;
    }
    map.setPaintProperty(RADAR_LAYER_ID, 'raster-opacity', opacity);
  }, [opacity, mapReady]);

  const statusMessage = backendDown
    ? 'Backend unavailable.'
    : loading
      ? 'Loading timestamps...'
      : noProcessedTiles
        ? 'No processed placeholder tiles. Run make process-once.'
        : !selectedTime
          ? 'No timestamps loaded.'
          : !tileSupport
            ? 'Selected layer has no tile support yet.'
            : selectedNotProcessed
              ? 'Selected timestamp is not processed.'
              : tilesReady
                ? `Placeholder tiles active`
                : 'Checking tile availability...';

  return (
    <section className="map-panel" aria-label="Weather map">
      <div ref={mapContainerRef} className="map-container" />
      <div className="map-badge">Placeholder tiles — not real radar</div>
      <p className="map-status">{statusMessage}</p>
    </section>
  );
}
