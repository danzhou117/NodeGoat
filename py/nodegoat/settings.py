import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = "mongodb://localhost:27017/nodegoat"
    port: int = 4000
    cookie_secret: str = "session_cookie_secret_key_here"  # PARITY: P-013
    assets_dir: Path = REPO_ROOT / "app" / "assets"
    views_dir: Path = REPO_ROOT / "app" / "views"

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        return cls(
            mongodb_uri=env.get("MONGODB_URI") or cls.mongodb_uri,
            port=int(env.get("PORT") or cls.port),
            cookie_secret=env.get("COOKIE_SECRET") or cls.cookie_secret,
        )
