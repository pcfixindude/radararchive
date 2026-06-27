from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.access import router as access_router
from backend.app.api.routes import router as api_router
from backend.app.api.sources import router as sources_router
from backend.app.api.tiles import router as tiles_router
from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.storage import LocalStorage


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    session = next(get_db())
    try:
        if not settings.testing and catalog_is_empty(session):
            seed_demo_catalog(session, storage=LocalStorage(settings.local_storage_root))
    finally:
        session.close()
    yield


app = FastAPI(title="RadarArchive API", version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(access_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(tiles_router)
