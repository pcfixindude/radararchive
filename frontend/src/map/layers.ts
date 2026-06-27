export const DEFAULT_LAYER = 'mrms_reflectivity';

/** Layers with placeholder raster tile support in Phase 5. */
export const TILE_SUPPORTED_LAYERS = new Set<string>([DEFAULT_LAYER]);

export function layerHasTileSupport(layerId: string, available: boolean): boolean {
  return available && TILE_SUPPORTED_LAYERS.has(layerId);
}
