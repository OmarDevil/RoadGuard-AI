"""FastAPI application for RoadGuard AI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.database import init_db
from api.routes.analytics import router as analytics_router
from api.routes.analyze import router as analyze_router
from api.routes.upload import router as upload_router

ROOT_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="RoadGuard AI API",
    description="Smart traffic violation detection and road analytics backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=ROOT_DIR / "outputs"), name="outputs")
app.mount("/frontend", StaticFiles(directory=ROOT_DIR / "frontend", html=True), name="frontend")

app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(analytics_router)


@app.on_event("startup")
def startup() -> None:
    """Initialize SQLite tables at API startup."""
    init_db()

