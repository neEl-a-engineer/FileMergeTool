from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from file_merge_tool.api.routes import downloads, health, history, jobs, presets, settings, system


def create_app() -> FastAPI:
    app = FastAPI(title="File Merge Tool", version="0.1.0")
    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(presets.router)
    app.include_router(settings.router)
    app.include_router(system.router)
    app.include_router(history.router)
    app.include_router(downloads.router)

    static_dir = Path(__file__).resolve().parents[1] / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()
