import uvicorn

from nodegoat.app import create_app
from nodegoat.settings import Settings

settings = Settings.from_env()
uvicorn.run(create_app(settings), host="0.0.0.0", port=settings.port)  # PARITY: P-014
