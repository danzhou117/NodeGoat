import os
from pathlib import Path
import shlex
import subprocess
import time

import httpx
import pytest
from pymongo import MongoClient

from helpers import ADMIN, USER1, USER2


TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BASE_URL = os.environ.get("BASE_URL", "http://localhost:4000").rstrip("/")
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/nodegoat")
DB_RESET_CMD = os.environ.get("DB_RESET_CMD", "node artifacts/db-reset.js")
RESET_SENTINEL = {"_id": "tests_shared_reset_sentinel"}


@pytest.fixture(scope="session", autouse=True)
def app_is_available():
    deadline = time.monotonic() + 10
    last_problem = "no response"
    while time.monotonic() < deadline:
        try:
            with httpx.Client(base_url=BASE_URL, timeout=2.0) as client:
                response = client.get("/login")
            if response.status_code == 200:
                return
            last_problem = f"GET /login returned HTTP {response.status_code}"
        except httpx.HTTPError as error:
            last_problem = str(error)
        time.sleep(0.1)
    pytest.exit(
        f"NodeGoat is not ready at BASE_URL={BASE_URL}: {last_problem}",
        returncode=2,
    )


@pytest.fixture(scope="session")
def db():
    client = MongoClient(
        MONGODB_URI,
        tz_aware=True,
        serverSelectionTimeoutMS=5000,
    )
    database = client.get_default_database(default="test")
    yield database
    client.close()


@pytest.fixture(autouse=True)
def reseed_db(db):
    environment = os.environ.copy()
    environment["MONGODB_URI"] = MONGODB_URI
    db.counters.replace_one(RESET_SENTINEL, RESET_SENTINEL, upsert=True)
    try:
        result = subprocess.run(
            shlex.split(DB_RESET_CMD),
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        db.counters.delete_one(RESET_SENTINEL)
        pytest.fail(f"Database reset failed: {error}")
    sentinel_survived = db.counters.delete_one(RESET_SENTINEL).deleted_count
    if result.returncode:
        pytest.fail(
            "Database reset failed with exit code "
            f"{result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    if sentinel_survived:
        pytest.exit(
            f"DB_RESET_CMD ran but did not reset the database '{db.name}' selected by MONGODB_URI. "
            "The reset command and the suite must target the same database.",
            returncode=2,
        )
    assert db.users.count_documents({}) == 3
    assert db.allocations.count_documents({}) == 3
    assert db.counters.find_one({"_id": "userId"}) == {"_id": "userId", "seq": 3}
    yield


@pytest.fixture
def make_client():
    clients = []

    def factory():
        client = httpx.Client(
            base_url=BASE_URL,
            follow_redirects=False,
            timeout=10.0,
        )
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.close()


@pytest.fixture
def anon(make_client):
    return make_client()


@pytest.fixture
def login(make_client):
    def factory(user_name, password):
        client = make_client()
        response = client.post(
            "/login",
            data={"userName": user_name, "password": password},
        )
        assert response.status_code == 302
        assert response.headers["location"] in {"/dashboard", "/benefits"}
        return client

    return factory


@pytest.fixture
def user1(login):
    return login(*USER1)


@pytest.fixture
def user2(login):
    return login(*USER2)


@pytest.fixture
def admin(login):
    return login(*ADMIN)
