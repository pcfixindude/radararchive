"""Phase 2 demo catalog constants used only for seeding the SQLite database."""

from typing import Dict, List

DEMO_LAYERS: List[Dict[str, object]] = [
    {
        "id": "mrms_reflectivity",
        "name": "MRMS Reflectivity",
        "type": "raster",
        "available": True,
        "source": "demo",
    },
    {
        "id": "nws_warnings",
        "name": "NWS Warning Polygons",
        "type": "vector",
        "available": False,
        "source": "demo",
    },
    {
        "id": "hrrr_wind",
        "name": "HRRR Wind Streamlines",
        "type": "vector",
        "available": False,
        "source": "demo",
    },
    {
        "id": "wpc_fronts",
        "name": "WPC Fronts",
        "type": "vector",
        "available": False,
        "source": "demo",
    },
]

DEMO_PRODUCTS: List[Dict[str, str]] = [
    {
        "id": "mrms_reflectivity",
        "layer_id": "mrms_reflectivity",
        "name": "MRMS Reflectivity (demo)",
        "source": "demo",
    },
]

DEMO_TIMES: List[str] = [
    "2026-06-27T20:00:00Z",
    "2026-06-27T20:05:00Z",
    "2026-06-27T20:10:00Z",
    "2026-06-27T20:15:00Z",
    "2026-06-27T20:20:00Z",
]

DEMO_ACCESS_PLANS: List[Dict[str, object]] = [
    {"id": "free", "name": "Free", "history_days": 0},
    {"id": "basic", "name": "Basic", "history_days": 7},
    {"id": "pro", "name": "Pro", "history_days": 90},
    {"id": "business", "name": "Business", "history_days": None},
]
