#!/usr/bin/env python3
"""
Build a layered scene that reuses the approved neuron layout, but replaces the
static microtubule bundle with repeated instances of the animated Blender asset.

This script is intentionally structured as a small USD study example:

1. `animated_tau_breakdown_base.usda`
   - brings in the current approved scene as the weakest layer
2. `animated_tau_breakdown_chain.usda`
   - defines one reusable animated chain prototype
3. `animated_tau_breakdown_layout.usda`
   - hides the old static bundles
   - places the new animated chains at the same transforms
4. `animated_tau_breakdown.usda`
   - thin root stage that composes the other layers

Important design note:
  The new asset contains skeletal animation (`SkelRoot` / `Skeleton` /
  `SkelAnimation`). For that reason, this script uses scenegraph instances of a
  referenced animated chain instead of a top-level `PointInstancer` for the
  whole neuron layout. That keeps the composition robust for animation.

  Inside the reusable chain layer, we still use a `PointInstancer` to build the
  repeated local chain from the animated unit. That gives you the "chain of
  repeated units" you asked for, while keeping each neuron placement clean.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

ROOT_LAYER = OUTPUT_DIR / "animated_tau_breakdown.usda"
BASE_LAYER = OUTPUT_DIR / "animated_tau_breakdown_base.usda"
CHAIN_LAYER = OUTPUT_DIR / "animated_tau_breakdown_chain.usda"
LAYOUT_LAYER = OUTPUT_DIR / "animated_tau_breakdown_layout.usda"

SOURCE_SCENE = "./neuron_variant_scene.usda"
ANIMATED_ASSET = "../assets/Anima_scene_tau_mt.usdc"
ANIMATED_ASSET_PRIM = Sdf.Path("/root")

# The Blender export is larger than one microtubule segment. Five repeated units
# spaced by the animated asset length gives a chain close to the original bundle
# length used in `microtubule_bundle.usda`.
CHAIN_COUNT = 5
CHAIN_SPACING = 15.35


@dataclass(frozen=True)
class Placement:
    name: str
    translate: tuple[float, float, float]
    rotate: tuple[float, float, float]
    scale: tuple[float, float, float]


PLACEMENTS = [
    Placement("Microtubules_01", (-0.4, -7.733460325034177, 4.5002969044673766e-29), (180.0, 0.0, 0.0), (0.15, 0.15, 0.15)),
    Placement("Microtubules_02", (-0.4, -19.762036118033034, -6.352650832591862e-30), (180.0, 0.0, 0.0), (0.15, 0.15, 0.15)),
    Placement("Microtubules_03", (-0.39999999999999963, -26.60000000000001, 4.226416694238857e-17), (179.57585, -0.063509375, -0.9031304), (0.1, 0.1, 0.1)),
    Placement("Microtubules_04", (-0.4, -33.600000000000016, 1.2954789903763435e-15), (177.0, 0.0, 0.0), (0.1, 0.1, 0.1)),
    Placement("Microtubules_05", (-0.4, -40.59040674328204, 0.3663516937006086), (173.04268, 0.10218263, 0.57034796), (0.1, 0.1, 0.1)),
    Placement("Microtubules_06", (-0.729890560267854, -47.52847753032135, 1.7313329221558182), (169.1283, 3.803126, 10.4081955), (0.1, 0.1, 0.1)),
    Placement("Microtubules_07", (-1.5763882459739773, 0.5846368954187088, -7.071029151820076), (71.96148, -0.15596047, 54.396183), (0.1, 0.1, 0.1)),
    Placement("Microtubules_08", (-3.806913919112263, 0.8510111967519306, 2.6872357243723286), (71.96148, -0.15596047, 54.396183), (0.1, 0.1, 0.1)),
    Placement("Microtubules_09", (-7.883053705122286, 1.1627821373987655, 4.589669678386052), (197.13977, 43.02415, 115.97241), (0.1, 0.1, 0.1)),
    Placement("Microtubules_10", (0.22511187683954395, 1.1220048432090912, 1.809692525407168), (135.52682, -13.722503, 86.36963), (0.1, 0.1, 0.1)),
    Placement("Microtubules", (-0.4, 1.4, 0.0), (180.0, 0.0, 0.0), (0.15, 0.15, 0.15)),
]


def make_stage(path: Path) -> Usd.Stage:
    """Create a stage with project-wide metadata and `/World` as default prim."""
    stage = Usd.Stage.CreateNew(str(path))
    stage.SetMetadata("metersPerUnit", 0.01)
    stage.SetMetadata("upAxis", "Y")
    stage.SetStartTimeCode(0.0)
    stage.SetEndTimeCode(72.0)
    stage.SetTimeCodesPerSecond(24.0)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    return stage


def add_transform_ops(
    prim: Usd.Prim,
    translate_value: tuple[float, float, float],
    rotate_value: tuple[float, float, float],
    scale_value: tuple[float, float, float],
) -> None:
    """Author the common translate / rotateZ / rotateY / rotateX / scale stack."""
    xformable = UsdGeom.Xformable(prim)
    translate = xformable.AddTranslateOp()
    rotate_z = xformable.AddRotateZOp()
    rotate_y = xformable.AddRotateYOp()
    rotate_x = xformable.AddRotateXOp()
    scale = xformable.AddScaleOp()

    translate.Set(Gf.Vec3d(*translate_value))
    rotate_z.Set(float(rotate_value[2]))
    rotate_y.Set(float(rotate_value[1]))
    rotate_x.Set(float(rotate_value[0]))
    scale.Set(Gf.Vec3f(*scale_value))


def bind_material(
    stage: Usd.Stage,
    prim_path: str,
    material_path: str,
    bind_strength: str = "weakerThanDescendants",
) -> None:
    """Apply a material binding relationship without requiring the material layer to be loaded."""
    prim = stage.OverridePrim(prim_path)
    UsdShade.MaterialBindingAPI.Apply(prim)
    relationship = prim.CreateRelationship("material:binding", custom=False)
    relationship.SetTargets([Sdf.Path(material_path)])
    relationship.SetMetadata("bindMaterialAs", bind_strength)


def build_base_layer() -> None:
    """Reuse the approved neuron scene as the weakest composition layer."""
    stage = make_stage(BASE_LAYER)
    stage.GetRootLayer().subLayerPaths = [SOURCE_SCENE]
    stage.Save()


def build_chain_layer() -> None:
    """
    Build one reusable animated chain asset.

    The prototype references the full animated Blender export so the internal
    skeletal animation remains intact. The dome light from Blender is hidden
    here so it does not leak into the main scene.
    """
    stage = make_stage(CHAIN_LAYER)

    chain = UsdGeom.PointInstancer.Define(stage, "/World/AnimatedTauChain")
    chain.CreatePositionsAttr([Gf.Vec3f(0.0, CHAIN_SPACING * index, 0.0) for index in range(CHAIN_COUNT)])
    chain.CreateProtoIndicesAttr([0] * CHAIN_COUNT)
    chain.CreatePrototypesRel().SetTargets([Sdf.Path("/World/AnimatedTauChain/Prototypes/AnimatedUnit")])

    UsdGeom.Scope.Define(stage, "/World/AnimatedTauChain/Prototypes")

    prototype = UsdGeom.Xform.Define(stage, "/World/AnimatedTauChain/Prototypes/AnimatedUnit")
    prototype.GetPrim().GetReferences().AddReference(ANIMATED_ASSET, ANIMATED_ASSET_PRIM.pathString)

    # Blender exported the asset in Z-up, so we rotate it once at the prototype
    # level so the local chain extends along USD Y-up.
    add_transform_ops(
        prototype.GetPrim(),
        translate_value=(0.0, 0.0, 0.0),
        rotate_value=(-90.0, 0.0, 0.0),
        scale_value=(1.0, 1.0, 1.0),
    )

    # Remove the embedded environment light from the reusable prototype.
    env_light = stage.OverridePrim("/World/AnimatedTauChain/Prototypes/AnimatedUnit/env_light")
    env_light.CreateAttribute("visibility", Sdf.ValueTypeNames.Token).Set("invisible")

    # Bind the animated asset to the same materials used in the approved scene.
    bind_material(stage, "/World/AnimatedTauChain/Prototypes/AnimatedUnit", "/World/Materials/MicrotubuleGlow")
    bind_material(
        stage,
        "/World/AnimatedTauChain/Prototypes/AnimatedUnit/NurbsPath",
        "/World/Materials/TauGlow",
        bind_strength="strongerThanDescendants",
    )

    stage.Save()


def build_layout_layer() -> None:
    """
    Hide the old static bundles and place the new animated chains in their place.

    This is the layer that mirrors the approved transforms from
    `output/neuron_variant_scene.usda`.
    """
    stage = make_stage(LAYOUT_LAYER)

    for placement in PLACEMENTS:
        old_prim = stage.OverridePrim(f"/World/NeuronModel/{placement.name}")
        UsdGeom.Imageable(old_prim).CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)

        new_name = f"{placement.name}_Animated"
        new_prim = UsdGeom.Xform.Define(stage, f"/World/NeuronModel/{new_name}")
        new_prim.GetPrim().GetReferences().AddReference(f"./{CHAIN_LAYER.name}", "/World/AnimatedTauChain")
        new_prim.GetPrim().SetInstanceable(True)
        add_transform_ops(new_prim.GetPrim(), placement.translate, placement.rotate, placement.scale)

    stage.Save()


def build_root_stage() -> None:
    """Compose the new animated layout above the approved base scene."""
    stage = make_stage(ROOT_LAYER)
    stage.GetRootLayer().subLayerPaths = [
        LAYOUT_LAYER.name,
        CHAIN_LAYER.name,
        BASE_LAYER.name,
    ]
    stage.Save()


def main() -> None:
    """Write all layers for the animated tau breakdown scene."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_base_layer()
    build_chain_layer()
    build_layout_layer()
    build_root_stage()


if __name__ == "__main__":
    main()
