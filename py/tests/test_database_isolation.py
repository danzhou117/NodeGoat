import pytest
from pymongo.uri_parser import parse_uri

from conftest import TEST_DATABASE_PREFIX, disposable_database_uri


@pytest.mark.parametrize(
    "server_uri",
    [
        "mongodb://localhost:27017",
        "mongodb://localhost:27017/",
        "mongodb://localhost:27017/nodegoat",
        "mongodb://h1:27017,h2:27018/nodegoat?replicaSet=rs0",
        "mongodb://user:p%40ss@db.example:27017/nodegoat?authSource=admin",
    ],
)
def test_disposable_database_uri_discards_the_configured_database(server_uri):
    name, uri = disposable_database_uri(server_uri)
    original, rewritten = parse_uri(server_uri), parse_uri(uri)
    assert name.startswith(TEST_DATABASE_PREFIX)
    assert rewritten["database"] == name
    for key in ("nodelist", "username", "password", "options"):
        assert rewritten[key] == original[key]


def test_disposable_database_uri_is_unique_per_call():
    assert disposable_database_uri("mongodb://localhost")[0] != disposable_database_uri("mongodb://localhost")[0]


def test_db_fixture_resets_only_the_disposable_database(db, test_database_name):
    assert db.name == test_database_name
    assert db.name.startswith(TEST_DATABASE_PREFIX)
