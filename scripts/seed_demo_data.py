"""Print where Phase 1 demo catalog data lives."""

from backend.app.demo.catalog import DEMO_LAYERS, DEMO_TIMES

print("Phase 1 demo catalog (stub data, not real NOAA/MRMS downloads):")
print(f"  layers: {len(DEMO_LAYERS)}")
print(f"  mrms demo timestamps: {len(DEMO_TIMES)}")
