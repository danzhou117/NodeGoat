from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from nodegoat.db import connect, default_database
from nodegoat.settings import Settings
from nodegoat.templating import create_jinja_env


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = connect(settings.mongodb_uri)
        app.state.mongo_client = client
        app.state.db = default_database(client)
        try:
            yield
        finally:
            client.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.templates = Jinja2Templates(env=create_jinja_env(settings.views_dir))

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/", StaticFiles(directory=settings.assets_dir), name="assets")
    return app
