import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]


def _resource_dir(name: str) -> Path:
    packaged = PACKAGE_DIR / name
    return packaged if packaged.is_dir() else REPO_ROOT / "app" / name


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = "mongodb://localhost:27017/nodegoat"
    port: int = 4000
    cookie_secret: str = "session_cookie_secret_key_here"  # PARITY: P-013
    assets_dir: Path = _resource_dir("assets")
    views_dir: Path = _resource_dir("views")

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        return cls(
            mongodb_uri=env.get("MONGODB_URI") or cls.mongodb_uri,
            port=int(env.get("PORT") or cls.port),
            cookie_secret=env.get("COOKIE_SECRET") or cls.cookie_secret,
        )
