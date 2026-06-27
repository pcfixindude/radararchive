import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { tileUrlTemplate, tilesAvailable } from '../api/client';
import { layerHasTileSupport } from './layers';
import {
  BASEMAP_STYLE,
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  RADAR_LAYER_ID,
  RADAR_SOURCE_ID,
} from './mapConfig';

export default function WeatherMap({
  selectedTime,
  selectedLayer,
  layerAvailable,
  loading,
  opacity,
}: {
  selectedTime: string;
  selectedLayer: string;
  layerAvailable: boolean;
  loading: boolean;
  opacity: number;
}) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [tilesReady, setTilesReady] = useState(false);
  const tileSupport = layerHasTileSupport(selectedLayer, layerAvailable);

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
      if (!selectedTime || loading || !tileSupport) {
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
  }, [selectedLayer, selectedTime, loading, tileSupport]);

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

    if (!tilesReady || !selectedTime || !tileSupport) {
      removeRadarLayer();
      return;
    }

    removeRadarLayer();

    map.addSource(RADAR_SOURCE_ID, {
      type: 'raster',
      tiles: [tileUrlTemplate(selectedLayer, selectedTime)],
      tileSize: 256,
    });

    map.addLayer({
      id: RADAR_LAYER_ID,
      type: 'raster',
      source: RADAR_SOURCE_ID,
      paint: {
        'raster-opacity': opacity,
      },
    });
  }, [mapReady, selectedLayer, selectedTime, tilesReady, tileSupport, opacity]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !map.getLayer(RADAR_LAYER_ID)) {
      return;
    }
    map.setPaintProperty(RADAR_LAYER_ID, 'raster-opacity', opacity);
  }, [opacity, mapReady]);

  const statusMessage = loading
    ? 'Loading timestamps...'
    : !selectedTime
      ? 'No timestamps loaded.'
      : !tileSupport
        ? 'Selected layer has no placeholder tile support yet.'
        : tilesReady
          ? `Placeholder tiles active for ${selectedTime}`
          : 'No processed tiles for this timestamp — run make process-once.';

  return (
    <section className="map-panel" aria-label="Weather map">
      <div ref={mapContainerRef} className="map-container" />
      <div className="map-badge">Placeholder tiles — not real radar</div>
      <p className="map-status">{statusMessage}</p>
    </section>
  );
}
