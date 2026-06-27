"""Phase 1 stub catalog.

These values are fake/demo timestamps and layer metadata only.
Real MRMS collection and catalog indexing come in a later phase.
"""

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

# Fixed UTC timestamps for local development without cloud credentials.
DEMO_TIMES: List[str] = [
    "2026-06-27T20:00:00Z",
    "2026-06-27T20:05:00Z",
    "2026-06-27T20:10:00Z",
    "2026-06-27T20:15:00Z",
    "2026-06-27T20:20:00Z",
]
