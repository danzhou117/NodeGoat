import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from nodegoat.app import create_app
from nodegoat.settings import REPO_ROOT, Settings


@pytest.fixture
def settings(mongodb_uri):
    return Settings(mongodb_uri=mongodb_uri)


def test_healthz(settings):
    with TestClient(create_app(settings)) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_assets_served_from_app_assets_at_root(settings):
    with TestClient(create_app(settings)) as client:
        response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.content == (REPO_ROOT / "app" / "assets" / "favicon.ico").read_bytes()


def test_openapi_routes_disabled(settings):
    with TestClient(create_app(settings)) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404


def test_jinja_env_matches_swig_config(settings):
    app = create_app(settings)
    env = app.state.templates.env
    assert env.autoescape is False
    assert env.from_string("{{ x }}").render(x="<b>") == "<b>"
    assert "login.html" in env.list_templates()


def test_lifespan_exposes_database(settings, test_database_name):
    app = create_app(settings)
    with TestClient(app):
        assert app.state.db.name == test_database_name
        assert app.state.db.client is app.state.mongo_client


def test_routes_added_after_create_app_are_reachable(settings):
    app = create_app(settings)

    @app.get("/late")
    def late() -> dict[str, bool]:
        return {"late": True}

    with TestClient(app) as client:
        assert client.get("/late").json() == {"late": True}
        assert client.get("/missing").status_code == 404


def test_static_file_takes_precedence_over_a_route_like_express(settings):
    app = create_app(settings)

    @app.get("/favicon.ico")
    def shadowed() -> dict[str, bool]:
        return {"route": True}

    with TestClient(app) as client:
        response = client.get("/favicon.ico")
    assert response.content == (REPO_ROOT / "app" / "assets" / "favicon.ico").read_bytes()


def test_only_get_and_head_are_served_from_assets(settings):
    with TestClient(create_app(settings)) as client:
        assert client.head("/vendor/jquery.min.js").status_code == 200
        assert client.post("/vendor/jquery.min.js").status_code == 404


def test_startup_fails_when_mongo_unreachable():
    settings = Settings(
        mongodb_uri="mongodb://127.0.0.1:1/nodegoat?serverSelectionTimeoutMS=200"
    )
    with pytest.raises(ServerSelectionTimeoutError):
        with TestClient(create_app(settings)):
            pass


def test_settings_from_env():
    configured = Settings.from_env(
        {"MONGODB_URI": "mongodb://db:27017/x", "PORT": "5000", "COOKIE_SECRET": "s3"}
    )
    assert configured.mongodb_uri == "mongodb://db:27017/x"
    assert configured.port == 5000
    assert configured.cookie_secret == "s3"
    for env in ({}, {"PORT": "", "MONGODB_URI": "", "COOKIE_SECRET": ""}):
        defaults = Settings.from_env(env)
        assert defaults.mongodb_uri == "mongodb://localhost:27017/nodegoat"
        assert defaults.port == 4000
        assert defaults.cookie_secret == "session_cookie_secret_key_here"
