import os
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

INSTALLED_APP_CHECK = """
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import nodegoat
from nodegoat.app import create_app
from nodegoat.settings import Settings

site, mongodb_uri = Path(sys.argv[1]), sys.argv[2]
settings = Settings(mongodb_uri=mongodb_uri)
assert Path(nodegoat.__file__).resolve().is_relative_to(site), nodegoat.__file__
assert settings.assets_dir.is_relative_to(site), settings.assets_dir
assert settings.views_dir.is_relative_to(site), settings.views_dir

app = create_app(settings)
assert "login.html" in app.state.templates.env.list_templates()
with TestClient(app) as client:
    assert client.get("/healthz").status_code == 200
    assert client.get("/favicon.ico").status_code == 200
"""


def test_built_wheel_runs_outside_the_checkout(tmp_path, mongodb_uri):
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-w", tmp_path, PROJECT_DIR],
        check=True,
        capture_output=True,
    )
    (wheel,) = tmp_path.glob("nodegoat-*.whl")
    site = (tmp_path / "site").resolve()
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(site)

    result = subprocess.run(
        [sys.executable, "-c", INSTALLED_APP_CHECK, site, mongodb_uri],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(site)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
