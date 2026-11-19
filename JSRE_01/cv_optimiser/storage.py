"""Local JSON persistence for career blueprints."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from cv_optimiser.models import BlueprintValidationError, MasterBlueprint


def default_blueprint_path() -> Path:
    """Return a per-user data path outside the source workspace."""
    if os.name == "nt":
        data_directory = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        data_directory = Path.home() / "Library" / "Application Support"
    else:
        data_directory = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_directory / "cv-optimiser" / "master_cv.json"


def load_blueprint(path: str | Path) -> MasterBlueprint:
    """Load and validate a blueprint from a UTF-8 JSON file."""
    blueprint_path = Path(path)
    try:
        with blueprint_path.open("r", encoding="utf-8") as source:
            data = json.load(source)
    except json.JSONDecodeError as error:
        raise BlueprintValidationError(f"{blueprint_path} is not valid JSON: {error.msg}.") from error
    return MasterBlueprint.from_dict(data)


def save_blueprint(blueprint: MasterBlueprint, path: str | Path) -> None:
    """Validate and atomically save a blueprint as UTF-8 JSON."""
    data = blueprint.to_dict()
    blueprint_path = Path(path)
    blueprint_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=blueprint_path.parent,
            prefix=f".{blueprint_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as destination:
            temporary_path = destination.name
            json.dump(data, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary_path, blueprint_path)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)
