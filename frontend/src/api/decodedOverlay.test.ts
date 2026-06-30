import { describe, expect, it } from 'vitest';
import { decodedOverlayPreviewUrl, type DecodedOverlayInfo } from '../api/client';

describe('decodedOverlayPreviewUrl', () => {
  it('appends cache-bust query from ran_at', () => {
    const overlay: DecodedOverlayInfo = {
      available: true,
      overlay_status: 'decoded_prototype',
      preview_url: '/api/dev/decoded-overlay/preview.png',
      ran_at: '2026-06-28T14:00:00Z',
      bounds: [-125, 24, -66, 50],
      georef_mode: 'rasterio_bounds',
      geo_accurate: false,
      labels: [],
      refresh_commands: [],
      verified_mrms: false,
      local_dev_only: true,
      prototype: true,
      production_tile_serving: false,
    };
    expect(decodedOverlayPreviewUrl(overlay)).toContain('/api/dev/decoded-overlay/preview.png?v=');
    expect(decodedOverlayPreviewUrl(overlay)).toContain('2026-06-28T14%3A00%3A00Z');
  });
});
