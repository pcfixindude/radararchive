from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    session = next(get_db())
    try:
        if not settings.testing and catalog_is_empty(session):
            seed_demo_catalog(session)
    finally:
        session.close()
    yield


app = FastAPI(title="RadarArchive API", version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
