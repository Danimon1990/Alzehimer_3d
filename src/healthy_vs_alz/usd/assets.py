import os
from pathlib import Path

from pxr import Gf, Kind, Sdf, Usd, UsdGeom

from healthy_vs_alz.constants import PROJECT_ROOT, USD_ROOT
from healthy_vs_alz.usd.stage import create_stage, save


ASSETS = {
    "neuron": ("Neuron", "assets/neuron_model.usda", "/root", 2.15),
    "sick_neuron": ("Neuron", "assets/Sick_neuron.usdc", "/root", 2.15),
    "broken_neuron": ("Neuron", "assets/Broken_neuron.usdc", "/root", 2.15),
    "microtubule": ("Microtubule", "assets/microtubules.usdc", "/root", 1.0),
    "tau": ("Tau", "assets/TAU.usdc", "/root", 1.0),
    "plaque": ("Plaque", "assets/plaques.usdc", "/root", 1.0),
}


def _relative_asset(source: Path, destination: Path) -> str:
    return Path(os.path.relpath(source, destination.parent)).as_posix()


def publish_asset(name: str) -> Path:
    prim_name, source_name, source_prim, scale = ASSETS[name]
    destination = USD_ROOT / "assets" / name / f"{name}.usda"
    stage = create_stage(destination, prim_name)
    root = stage.GetDefaultPrim()
    root.SetMetadata("kind", Kind.Tokens.component)
    model = Usd.ModelAPI(root)
    model.SetAssetName(name)
    model.SetAssetIdentifier(Sdf.AssetPath(f"./{name}.usda"))

    payload = UsdGeom.Xform.Define(stage, f"/{prim_name}/Geometry")
    source = PROJECT_ROOT / source_name
    asset_path = _relative_asset(source, destination)
    if source_prim:
        payload.GetPrim().GetPayloads().AddPayload(asset_path, Sdf.Path(source_prim))
    else:
        payload.GetPrim().GetPayloads().AddPayload(asset_path)
    payload.AddRotateXOp().Set(-90.0)
    if scale != 1.0:
        payload.AddScaleOp().Set(Gf.Vec3f(scale, scale, scale))
    save(stage)
    return destination


def publish_all_assets() -> list[Path]:
    return [publish_asset(name) for name in ASSETS]
