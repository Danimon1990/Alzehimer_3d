#!/usr/bin/env python3
"""
Create a lightweight intro setup using only the base neuron mesh.

This script writes `output/healthy_tau_intro_matrix.usda`:
  - a grid of instanceable references to `assets/neuron_model.usda`
  - the same purple membrane material used by the healthy TAU scene
  - no microtubules, TAU, cameras, or extra scene composition
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSET_PATH = PROJECT_ROOT / "assets" / "neuron_model.usda"
INTRO_SCENE = OUTPUT_DIR / "healthy_tau_intro_matrix.usda"

DEFAULT_GRID_LAYERS = 1
DEFAULT_GRID_ROWS = 6
DEFAULT_GRID_COLUMNS = 6
NEURON_SCALE = 1.15


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def make_stage(path: Path) -> Usd.Stage:
    stage = Usd.Stage.CreateNew(str(path))
    stage.SetMetadata("metersPerUnit", 0.01)
    stage.SetMetadata("upAxis", "Y")
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    return stage


def set_preview_surface(
    stage: Usd.Stage,
    material_path: str,
    *,
    diffuse: Gf.Vec3f,
    opacity: float,
    roughness: float,
) -> None:
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, material_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")


def compute_neuron_size() -> Gf.Vec3d:
    stage = Usd.Stage.Open(str(ASSET_PATH))
    if not stage:
        raise RuntimeError(f"Could not open asset stage: {ASSET_PATH}")

    root = stage.GetDefaultPrim()
    if not root:
        raise RuntimeError(f"Missing default prim in asset: {ASSET_PATH}")

    bbox_cache = UsdGeom.BBoxCache(1.0, [UsdGeom.Tokens.default_], useExtentsHint=True)
    box = bbox_cache.ComputeWorldBound(root).ComputeAlignedBox()
    size = box.GetMax() - box.GetMin()
    return Gf.Vec3d(size[0] * NEURON_SCALE, size[1] * NEURON_SCALE, size[2] * NEURON_SCALE)


def add_grid_instance(
    stage: Usd.Stage,
    name: str,
    translate_value: tuple[float, float, float],
) -> None:
    prim = UsdGeom.Xform.Define(stage, f"/World/NeuronGrid/{name}")
    prim.GetPrim().GetReferences().AddReference("../assets/neuron_model.usda")
    prim.GetPrim().SetInstanceable(True)

    xformable = UsdGeom.Xformable(prim)
    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate_value))
    xformable.AddRotateXOp().Set(-90.0)
    xformable.AddScaleOp().Set(Gf.Vec3f(NEURON_SCALE, NEURON_SCALE, NEURON_SCALE))

    UsdShade.MaterialBindingAPI.Apply(prim.GetPrim()).Bind(
        UsdShade.Material.Get(stage, "/World/Materials/NeuronMembrane")
    )


def build_intro_scene(
    neuron_size: Gf.Vec3d,
    *,
    grid_layers: int,
    grid_rows: int,
    grid_columns: int,
) -> None:
    stage = make_stage(INTRO_SCENE)
    stage.SetStartTimeCode(1.0)
    stage.SetEndTimeCode(1.0)
    stage.SetTimeCodesPerSecond(24.0)
    stage.GetRootLayer().customLayerData = {}

    UsdGeom.Scope.Define(stage, "/World/Materials")
    set_preview_surface(
        stage,
        "/World/Materials/NeuronMembrane",
        diffuse=Gf.Vec3f(0.56, 0.38, 0.78),
        opacity=0.18,
        roughness=0.18,
    )
    UsdGeom.Xform.Define(stage, "/World/NeuronGrid")

    spacing_x = max(float(neuron_size[0]) * 1.15, 24.0)
    spacing_z = max(float(neuron_size[2]) * 1.15, 24.0)
    spacing_y = max(float(neuron_size[1]) * 0.78, 18.0)

    x_center = (grid_columns - 1) * spacing_x * 0.5
    z_center = (grid_rows - 1) * spacing_z * 0.5
    y_center = (grid_layers - 1) * spacing_y * 0.5

    for layer_index in range(grid_layers):
        for row_index in range(grid_rows):
            for column_index in range(grid_columns):
                x_pos = column_index * spacing_x - x_center
                y_pos = layer_index * spacing_y - y_center
                z_pos = row_index * spacing_z - z_center
                add_grid_instance(
                    stage,
                    f"Neuron_{layer_index:02d}_{row_index:02d}_{column_index:02d}",
                    (x_pos, y_pos, z_pos),
                )

    stage.Save()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layers", type=positive_int, default=DEFAULT_GRID_LAYERS)
    parser.add_argument("--rows", type=positive_int, default=DEFAULT_GRID_ROWS)
    parser.add_argument("--columns", type=positive_int, default=DEFAULT_GRID_COLUMNS)
    args = parser.parse_args(argv)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_intro_scene(
        compute_neuron_size(),
        grid_layers=args.layers,
        grid_rows=args.rows,
        grid_columns=args.columns,
    )


if __name__ == "__main__":
    main()
