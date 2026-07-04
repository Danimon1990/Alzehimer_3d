#!/usr/bin/env python3
"""Build the layered 250-frame dementia environment scene."""

from __future__ import annotations

from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

ROOT_LAYER = OUTPUT_DIR / "dementia_environment.usda"
ANIMATION_LAYER = OUTPUT_DIR / "dementia_animation.usda"
CAMERAS_LAYER = OUTPUT_DIR / "dementia_cameras.usda"
PATHOLOGY_LAYER = OUTPUT_DIR / "dementia_pathology.usda"
PLAQUES_LAYER = OUTPUT_DIR / "dementia_plaques.usda"
NEURONS_LAYER = OUTPUT_DIR / "dementia_neurons.usda"
MATERIALS_LAYER = OUTPUT_DIR / "dementia_materials.usda"
LIGHTING_LAYER = OUTPUT_DIR / "dementia_lighting.usda"

NEURON_ASSET = "../assets/neuron_model.usda"
BROKEN_NEURON_ASSET = "../assets/Broken_neuron.usdc"
SICK_NEURON_ASSET = "../assets/Sick_neuron.usdc"
PLAQUE_ASSET = "../assets/plaques.usdc"
START_FRAME = 0.0
END_FRAME = 249.0
FPS = 24.0


def make_stage(path: Path) -> Usd.Stage:
    stage = Usd.Stage.CreateNew(str(path))
    stage.SetMetadata("metersPerUnit", 0.01)
    stage.SetMetadata("upAxis", "Y")
    stage.SetStartTimeCode(START_FRAME)
    stage.SetEndTimeCode(END_FRAME)
    stage.SetTimeCodesPerSecond(FPS)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    return stage


def add_transform(
    prim: Usd.Prim,
    translate: tuple[float, float, float],
    rotate: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    xformable = UsdGeom.Xformable(prim)
    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))
    xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotate))
    xformable.AddScaleOp().Set(Gf.Vec3f(*scale))


def bind_material(prim: Usd.Prim, material_path: str) -> None:
    UsdShade.MaterialBindingAPI.Apply(prim)
    relationship = prim.CreateRelationship("material:binding", custom=False)
    relationship.SetTargets([Sdf.Path(material_path)])
    relationship.SetMetadata("bindMaterialAs", "strongerThanDescendants")


def define_material(
    stage: Usd.Stage,
    name: str,
    color: tuple[float, float, float],
    roughness: float,
    metallic: float = 0.0,
    opacity: float = 1.0,
    emissive: tuple[float, float, float] | None = None,
) -> None:
    path = f"/World/Materials/{name}"
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    if emissive is not None:
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emissive))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")


def build_materials_layer() -> None:
    stage = make_stage(MATERIALS_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Materials")
    define_material(stage, "DeadNeuron", (0.39, 0.28, 0.19), 0.82)
    define_material(stage, "ResistingNeuron", (0.69, 0.61, 0.28), 0.58)
    define_material(stage, "Plaque", (0.43, 0.25, 0.08), 0.9)
    define_material(stage, "Waste", (0.16, 0.09, 0.05), 0.96)
    define_material(stage, "TauTangle", (0.35, 0.14, 0.05), 0.72)
    define_material(stage, "Microtubule", (0.23, 0.48, 0.42), 0.42)
    define_material(stage, "BlockedCargo", (0.65, 0.31, 0.08), 0.5, emissive=(0.05, 0.015, 0.0))
    stage.Save()


def define_neuron(
    stage: Usd.Stage,
    name: str,
    translate: tuple[float, float, float],
    rotate_y: float,
    material: str,
    state: str,
    asset_path: str = NEURON_ASSET,
) -> None:
    neuron = UsdGeom.Xform.Define(stage, f"/World/Neurons/{name}")
    neuron.GetPrim().CreateAttribute("userProperties:state", Sdf.ValueTypeNames.String).Set(state)
    add_transform(neuron.GetPrim(), translate, (0.0, rotate_y, 0.0))

    asset = UsdGeom.Xform.Define(stage, f"/World/Neurons/{name}/NeuronAsset")
    asset.GetPrim().GetReferences().AddReference(asset_path, "/root")
    add_transform(asset.GetPrim(), (0.0, 0.0, 0.0), (-90.0, 0.0, 0.0), (2.15, 2.15, 2.15))
    bind_material(asset.GetPrim(), f"/World/Materials/{material}")

    UsdGeom.Scope.Define(stage, f"/World/Neurons/{name}/AttachmentPoints")
    UsdGeom.Xform.Define(stage, f"/World/Neurons/{name}/AttachmentPoints/AxonInterior")
    UsdGeom.Xform.Define(stage, f"/World/Neurons/{name}/AttachmentPoints/AxonBreak")


def build_neurons_layer() -> None:
    stage = make_stage(NEURONS_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Neurons")
    define_neuron(
        stage,
        "Neuron_01_Dead",
        (-18.0, 0.0, 0.0),
        -18.0,
        "DeadNeuron",
        "dead",
        BROKEN_NEURON_ASSET,
    )
    define_neuron(
        stage,
        "Neuron_02_Resisting",
        (18.0, 1.5, -1.5),
        162.0,
        "ResistingNeuron",
        "resisting",
        SICK_NEURON_ASSET,
    )
    stage.Save()


PLAQUE_PLACEMENTS = {
    "DeadNeuronPlaques": [
        (-28.0, -8.0, 5.0, 0.42),
        (-23.0, 8.0, -7.0, 0.3),
        (-14.0, -12.0, -5.0, 0.36),
        (-8.0, 4.0, 7.0, 0.28),
        (-20.0, 14.0, 4.0, 0.24),
    ],
    "ResistingNeuronPlaques": [
        (7.0, -7.0, 5.0, 0.32),
        (12.0, 10.0, -6.0, 0.38),
        (21.0, -12.0, -5.0, 0.28),
        (27.0, 7.0, 7.0, 0.4),
        (32.0, -3.0, -6.0, 0.3),
        (18.0, 15.0, 4.0, 0.26),
        (35.0, 11.0, 2.0, 0.22),
    ],
    "EnvironmentPlaques": [
        (-42.0, -18.0, -12.0, 0.26),
        (-36.0, 17.0, 13.0, 0.34),
        (-29.0, 2.0, -18.0, 0.22),
        (-11.0, 20.0, -11.0, 0.3),
        (-5.0, -18.0, 14.0, 0.38),
        (0.0, 12.0, -16.0, 0.24),
        (3.0, -4.0, 18.0, 0.32),
        (10.0, 21.0, 12.0, 0.28),
        (25.0, -20.0, 13.0, 0.36),
        (31.0, 18.0, -13.0, 0.26),
        (40.0, -12.0, -10.0, 0.33),
        (44.0, 9.0, 14.0, 0.23),
    ],
}


def build_plaques_layer() -> None:
    stage = make_stage(PLAQUES_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Plaques")
    for group_name, placements in PLAQUE_PLACEMENTS.items():
        UsdGeom.Scope.Define(stage, f"/World/Plaques/{group_name}")
        for index, (x, y, z, scale) in enumerate(placements, start=1):
            plaque = UsdGeom.Xform.Define(stage, f"/World/Plaques/{group_name}/Plaque_{index:02d}")
            plaque.GetPrim().GetReferences().AddReference(PLAQUE_ASSET, "/root")
            plaque.GetPrim().SetInstanceable(True)
            add_transform(
                plaque.GetPrim(),
                (x, y, z),
                (-90.0, float((index * 47) % 360), float((index * 29) % 360)),
                (scale, scale, scale),
            )
            bind_material(plaque.GetPrim(), "/World/Materials/Plaque")
    stage.Save()


def define_placeholder(stage: Usd.Stage, path: str, purpose: str, asset_hint: str = "") -> None:
    placeholder = UsdGeom.Xform.Define(stage, path)
    placeholder.GetPrim().CreateAttribute("userProperties:status", Sdf.ValueTypeNames.Token).Set("placeholder")
    placeholder.GetPrim().CreateAttribute("userProperties:purpose", Sdf.ValueTypeNames.String).Set(purpose)
    if asset_hint:
        placeholder.GetPrim().CreateAttribute("userProperties:assetHint", Sdf.ValueTypeNames.String).Set(asset_hint)


def build_pathology_layer() -> None:
    stage = make_stage(PATHOLOGY_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Pathology")
    define_placeholder(stage, "/World/Pathology/BrokenAxonPieces", "Rigid debris from Neuron_01 axon", "future broken-neuron Blender asset")
    define_placeholder(stage, "/World/Pathology/Microtubules", "Internal microtubule accumulation in Neuron_02", "../assets/microtubules.usdc")
    define_placeholder(stage, "/World/Pathology/TauTangles", "Intracellular tau accumulation in Neuron_02", "../assets/TAU.usdc")
    define_placeholder(stage, "/World/Pathology/BlockedCargo", "Nutrients and organelles stalled in Neuron_02 axon")
    stage.Save()


def build_animation_layer() -> None:
    stage = make_stage(ANIMATION_LAYER)
    controls = UsdGeom.Scope.Define(stage, "/World/Animation")
    controls.GetPrim().CreateAttribute("userProperties:shotDescription", Sdf.ValueTypeNames.String).Set(
        "250-frame progression from dead neuron to resisting neuron"
    )
    for name, frame in (
        ("Establish", 0),
        ("DeadNeuronReveal", 50),
        ("BrokenAxonReveal", 110),
        ("ResistingNeuronReveal", 180),
        ("PathologyCloseup", 225),
        ("FinalHold", 249),
    ):
        marker = UsdGeom.Xform.Define(stage, f"/World/Animation/Markers/{name}")
        marker.GetPrim().CreateAttribute("userProperties:frame", Sdf.ValueTypeNames.Int).Set(frame)
    stage.Save()


def build_cameras_layer() -> None:
    stage = make_stage(CAMERAS_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Cameras")

    camera_specs = (
        ("Camera_Main", (0.0, 5.0, 115.0), 52.0),
        ("Camera_DeadNeuron", (-18.0, 3.0, 62.0), 58.0),
        ("Camera_ResistingNeuron", (18.0, 4.0, 62.0), 58.0),
        ("Camera_PathologyCloseup", (18.0, -5.0, 30.0), 70.0),
    )
    for name, translate, focal_length in camera_specs:
        camera = UsdGeom.Camera.Define(stage, f"/World/Cameras/{name}")
        camera.CreateFocalLengthAttr(focal_length)
        camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 10000.0))
        add_transform(camera.GetPrim(), translate)

    render_settings = stage.DefinePrim("/Render/DementiaEnvironment", "RenderSettings")
    render_settings.CreateRelationship("camera", custom=False).SetTargets([Sdf.Path("/World/Cameras/Camera_Main")])
    stage.Save()


def build_lighting_layer() -> None:
    stage = make_stage(LIGHTING_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Lights")
    dome = UsdLux.DomeLight.Define(stage, "/World/Lights/Environment")
    dome.CreateIntensityAttr(1.1)
    dome.CreateColorAttr(Gf.Vec3f(0.42, 0.38, 0.32))
    key = UsdLux.DistantLight.Define(stage, "/World/Lights/Key")
    key.CreateIntensityAttr(1.4)
    key.CreateColorAttr(Gf.Vec3f(1.0, 0.82, 0.58))
    add_transform(key.GetPrim(), (0.0, 0.0, 0.0), (-35.0, -25.0, 0.0))
    stage.Save()


def build_root_layer() -> None:
    stage = make_stage(ROOT_LAYER)
    stage.GetRootLayer().subLayerPaths = [
        ANIMATION_LAYER.name,
        CAMERAS_LAYER.name,
        PATHOLOGY_LAYER.name,
        PLAQUES_LAYER.name,
        NEURONS_LAYER.name,
        MATERIALS_LAYER.name,
        LIGHTING_LAYER.name,
    ]
    stage.Save()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_materials_layer()
    build_lighting_layer()
    build_neurons_layer()
    build_plaques_layer()
    build_pathology_layer()
    build_cameras_layer()
    build_animation_layer()
    build_root_layer()


if __name__ == "__main__":
    main()
