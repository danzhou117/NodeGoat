from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send


class StaticFilesFirst:
    """Serve a matching file from ``directory``, otherwise pass the request on.

    This mirrors ``app.use(express.static(directory))`` registered ahead of the
    routes: GET and HEAD requests are checked against the directory first, and
    whatever it cannot serve falls through to the application.
    """

    def __init__(self, app: ASGIApp, directory: Path) -> None:
        self.app = app
        self.static = StaticFiles(directory=directory)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in ("GET", "HEAD"):
            try:
                response = await self.static.get_response(self.static.get_path(scope), scope)
            except HTTPException:
                response = None
            if response is not None:
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
