import os
import subprocess
from pathlib import Path

import pytest
from pymongo import MongoClient

from nodegoat.dao.users import UserDAO

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_MONGODB_URI = os.environ.get("TEST_MONGODB_URI", "mongodb://localhost:27017/nodegoat_pytest")
NODE_BIN = os.environ.get("NODE_BIN", "node")


def run_node(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [NODE_BIN, *args],
        cwd=REPO_ROOT,
        env={**os.environ, "MONGODB_URI": TEST_MONGODB_URI, "NODE_ENV": "test"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result


@pytest.fixture(name="run_node")
def run_node_fixture():
    return run_node


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    if not (REPO_ROOT / "node_modules" / "mongodb").exists():
        pytest.fail("run `npm ci --omit=dev` at the repo root")
    client = MongoClient(TEST_MONGODB_URI, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        pytest.fail(f"MongoDB unavailable at {TEST_MONGODB_URI}: {exc}")
    return client


@pytest.fixture
def db(mongo_client: MongoClient):
    run_node("artifacts/db-reset.js")
    return mongo_client.get_default_database()


@pytest.fixture
def user_dao(db) -> UserDAO:
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
