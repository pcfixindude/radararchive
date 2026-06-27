import { TILE_SUPPORTED_LAYERS } from '../map/layers';

type Layer = { id: string; name: string; available: boolean };

function isLayerSelectable(layer: Layer): boolean {
  return layer.available && TILE_SUPPORTED_LAYERS.has(layer.id);
}

export default function LayerPanel({
  layers,
  selectedLayer,
  onSelect,
}: {
  layers: Layer[];
  selectedLayer: string;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="panel">
      <h2>Layers</h2>
      {layers.map((layer) => {
        const selectable = isLayerSelectable(layer);
        return (
          <label key={layer.id} className={!selectable ? 'disabled' : ''}>
            <input
              type="radio"
              checked={selectedLayer === layer.id}
              disabled={!selectable}
              onChange={() => onSelect(layer.id)}
            />{' '}
            {layer.name}
            {!TILE_SUPPORTED_LAYERS.has(layer.id) ? ' (tiles later)' : ''}
          </label>
        );
      })}
    </section>
  );
}
