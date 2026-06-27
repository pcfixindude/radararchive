type Layer = { id: string; name: string; available: boolean };
export default function LayerPanel({ layers, selectedLayer, onSelect }: { layers: Layer[]; selectedLayer: string; onSelect: (id: string) => void }) {
  return <section className="panel"><h2>Layers</h2>{layers.map(layer => <label key={layer.id} className={!layer.available ? 'disabled' : ''}><input type="radio" checked={selectedLayer === layer.id} disabled={!layer.available} onChange={() => onSelect(layer.id)} /> {layer.name}</label>)}</section>;
}
