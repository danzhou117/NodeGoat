from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class SharedResourcesHook(BuildHookInterface):
    """Ship the Node app's assets and views inside the package.

    They live in ``app/`` at the repository root, outside this project. When
    building from an sdist they are already inside ``nodegoat/`` and ``app/``
    is absent, so there is nothing to add.
    """

    def initialize(self, version: str, build_data: dict) -> None:
        app_dir = Path(self.root).parent / "app"
        for name in ("assets", "views"):
            if (app_dir / name).is_dir():
                build_data["force_include"][str(app_dir / name)] = f"nodegoat/{name}"
