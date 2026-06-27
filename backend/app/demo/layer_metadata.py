"""Static tile metadata merged into /api/layers responses (Phase 6)."""

from typing import Any, Dict, Optional

# Approximate CONUS bounds for placeholder MRMS reflectivity tiles.
MRMS_CONUS_BOUNDS = [-125.0, 24.0, -66.0, 50.0]

LAYER_TILE_METADATA: Dict[str, Dict[str, Any]] = {
    "mrms_reflectivity": {
        "bounds": MRMS_CONUS_BOUNDS,
        "minzoom": 3,
        "maxzoom": 8,
        "tile_support": True,
        "placeholder": True,
    },
    "nws_warnings": {
        "bounds": None,
        "minzoom": None,
        "maxzoom": None,
        "tile_support": False,
        "placeholder": False,
    },
    "hrrr_wind": {
        "bounds": None,
        "minzoom": None,
        "maxzoom": None,
        "tile_support": False,
        "placeholder": False,
    },
    "wpc_fronts": {
        "bounds": None,
        "minzoom": None,
        "maxzoom": None,
        "tile_support": False,
        "placeholder": False,
    },
}


def get_layer_tile_metadata(layer_id: str) -> Dict[str, Any]:
    return LAYER_TILE_METADATA.get(
        layer_id,
        {
            "bounds": None,
            "minzoom": None,
            "maxzoom": None,
            "tile_support": False,
            "placeholder": False,
        },
    )
