import { describe, expect, it } from 'vitest';
import {
  decodedOverlayPreviewUrl,
  decodedOverlayTileUrlTemplate,
  type DecodedOverlayInfo,
} from '../api/client';

const baseOverlay: DecodedOverlayInfo = {
  available: true,
  artifact_available: true,
  overlay_visible: true,
  overlay_status: 'decoded_prototype',
  sync_status: 'matched',
  sync_message: 'Selected time matches decoded frame.',
  selected_timestamp: '2026-06-28T13:26:38Z',
  candidate_timestamp: '2026-06-28T13:26:38Z',
  preview_url: '/api/dev/decoded-overlay/preview.png',
  ran_at: '2026-06-28T14:00:00Z',
  bounds: [-125, 24, -66, 50],
  georef_mode: 'rasterio_bounds',
  georef_quality: 'rasterio_wgs84_affine',
  georef_notes: [],
  geo_accurate: false,
  labels: [],
  refresh_commands: [],
  verified_mrms: false,
  local_dev_only: true,
  prototype: true,
  production_tile_serving: false,
};

describe('decodedOverlayPreviewUrl', () => {
  it('appends cache-bust query from ran_at', () => {
    expect(decodedOverlayPreviewUrl(baseOverlay)).toContain('/api/dev/decoded-overlay/preview.png?v=');
    expect(decodedOverlayPreviewUrl(baseOverlay)).toContain('2026-06-28T14%3A00%3A00Z');
  });
});

describe('decodedOverlayTileUrlTemplate', () => {
  it('returns tile template when local raster tiles are available', () => {
    const overlay: DecodedOverlayInfo = {
      ...baseOverlay,
      tile_mode: 'local_raster_tiles',
      tile_url_template: '/api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png',
      tile_max_z: 1,
      tile_count: 5,
    };
    const template = decodedOverlayTileUrlTemplate(overlay);
    expect(template).toContain('/api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png');
  });

  it('returns null for single image mode', () => {
    expect(decodedOverlayTileUrlTemplate(baseOverlay)).toBeNull();
  });
});
