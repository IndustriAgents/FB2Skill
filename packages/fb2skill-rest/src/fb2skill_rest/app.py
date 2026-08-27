from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import convert, export, graphdb, health, ontology, skills
from .settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings()
    app = FastAPI(
        title="fb2skill REST",
        version="0.1.0",
        description="Convert IEC 61499 project zips into CaSk/CaSkMan skill TTL.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # API routers must be registered BEFORE the SPA catch-all so they take priority.
    app.include_router(health.router)
    app.include_router(convert.router)
    app.include_router(skills.router)
    app.include_router(ontology.router)
    app.include_router(graphdb.router)
    app.include_router(export.router)

    dist = s.effective_web_dist
    if dist is not None:
        assets_dir = dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        index_html = dist / "index.html"

        @app.get("/", include_in_schema=False)
        async def _serve_root() -> FileResponse:
            return FileResponse(index_html)

        @app.get("/{full_path:path}", include_in_schema=False)
        async def _spa_fallback(full_path: str) -> FileResponse:
            candidate = dist / full_path
            if candidate.is_file() and candidate.is_relative_to(dist):
                return FileResponse(candidate)
            return FileResponse(index_html)

    return app


app = create_app()
