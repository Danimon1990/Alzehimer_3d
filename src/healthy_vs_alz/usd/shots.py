import os
import tomllib
from pathlib import Path

from healthy_vs_alz.constants import CONFIG_ROOT, PROJECT_ROOT, USD_ROOT
from healthy_vs_alz.usd.stage import create_stage, save


DEPARTMENTS = ("layout", "animation", "lighting", "cameras", "render")


def _config(name: str) -> dict:
    with (CONFIG_ROOT / f"{name}.toml").open("rb") as stream:
        return tomllib.load(stream)["shot"]


def _department_layer(destination: Path, name: str, config: dict) -> None:
    stage = create_stage(
        destination,
        "World",
        start_frame=config["start_frame"],
        end_frame=config["end_frame"],
    )
    world = stage.GetDefaultPrim()
    world.SetCustomDataByKey("department", name)
    if name == "layout":
        source = PROJECT_ROOT / config["source"]
        relative = Path(os.path.relpath(source, destination.parent)).as_posix()
        stage.GetRootLayer().subLayerPaths = [relative]
    save(stage)


def publish_shot(name: str) -> Path:
    config = _config(name)
    shot_dir = USD_ROOT / "sequences" / "comparison" / name
    layers = {}
    for department in DEPARTMENTS:
        path = shot_dir / f"{department}.usda"
        _department_layer(path, department, config)
        layers[department] = path

    destination = shot_dir / f"{name}.usda"
    stage = create_stage(
        destination,
        "World",
        start_frame=config["start_frame"],
        end_frame=config["end_frame"],
    )
    stage.GetRootLayer().subLayerPaths = [
        layers[department].name for department in reversed(DEPARTMENTS)
    ]
    save(stage)
    return destination


def publish_all_shots() -> list[Path]:
    return [publish_shot("healthy"), publish_shot("alzheimers")]
