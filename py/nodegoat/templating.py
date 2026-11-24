from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def create_jinja_env(views_dir: Path) -> Environment:
    return Environment(loader=FileSystemLoader(views_dir), autoescape=False)  # PARITY: P-012
