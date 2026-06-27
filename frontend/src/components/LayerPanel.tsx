import type { Layer } from '../api/client';

type PanelLayer = Pick<Layer, 'id' | 'name' | 'available' | 'tile_support' | 'placeholder'>;

function isLayerSelectable(layer: PanelLayer): boolean {
  return Boolean(layer.available && layer.tile_support);
}

export default function LayerPanel({
  layers,
  selectedLayer,
  onSelect,
}: {
  layers: PanelLayer[];
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
            {!layer.tile_support ? ' (future layer)' : layer.placeholder ? ' (placeholder tiles)' : ''}
          </label>
        );
      })}
    </section>
  );
}
