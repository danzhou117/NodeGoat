import os
import subprocess
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from pymongo import MongoClient
from pymongo.database import Database

from nodegoat.dao.users import UserDAO

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_MONGODB_URI = os.environ.get("TEST_MONGODB_URI", "mongodb://localhost:27017")
NODE_BIN = os.environ.get("NODE_BIN", "node")
TEST_DATABASE_PREFIX = "nodegoat_pytest_"


def disposable_database_uri(server_uri: str) -> tuple[str, str]:
    """Return a fresh database name and ``server_uri`` rewritten to point at it.

    Any database named in ``server_uri`` is discarded, so the reset script can
    never be aimed at a database the suite did not create.
    """
    name = TEST_DATABASE_PREFIX + uuid.uuid4().hex[:12]
    return name, urlsplit(server_uri)._replace(path=f"/{name}").geturl()


@pytest.fixture(scope="session")
def test_database() -> tuple[str, str]:
    return disposable_database_uri(TEST_MONGODB_URI)


@pytest.fixture(scope="session")
def test_database_name(test_database: tuple[str, str]) -> str:
    return test_database[0]


@pytest.fixture(scope="session")
def mongodb_uri(test_database: tuple[str, str]) -> str:
    return test_database[1]


@pytest.fixture(scope="session")
def mongo_client(mongodb_uri: str, test_database_name: str) -> Iterator[MongoClient]:
    if not (REPO_ROOT / "node_modules" / "mongodb").exists():
        pytest.fail("run `npm ci --omit=dev` at the repo root")
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        pytest.fail(f"MongoDB unavailable; set TEST_MONGODB_URI to a reachable server: {exc}")
    yield client
    client.drop_database(test_database_name)
    client.close()


@pytest.fixture(scope="session")
def run_node(mongodb_uri: str) -> Callable[..., subprocess.CompletedProcess[str]]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [NODE_BIN, *args],
            cwd=REPO_ROOT,
            env={**os.environ, "MONGODB_URI": mongodb_uri, "NODE_ENV": "test"},
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result

    return run


@pytest.fixture
def db(mongo_client: MongoClient, run_node, test_database_name: str) -> Database:
    run_node("artifacts/db-reset.js")
    return mongo_client[test_database_name]


@pytest.fixture
def user_dao(db: Database) -> UserDAO:
    return UserDAO(db)


def field_types(db, query) -> list[tuple[str, str]]:
    result = db.users.aggregate(
        [
            {"$match": query},
            {
                "$project": {
                    "_id": 0,
                    "fields": {
                        "$map": {
                            "input": {"$objectToArray": "$$ROOT"},
                            "in": {"k": "$$this.k", "t": {"$type": "$$this.v"}},
                        }
                    },
                }
            },
        ]
    )
    document = next(result)
    return [(field["k"], field["t"]) for field in document["fields"]]
