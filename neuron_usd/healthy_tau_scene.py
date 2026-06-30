#!/usr/bin/env python3
"""
Build a layered "healthy TAU" scene by composing the existing proven scene.

Why this version exists:
  The earlier script tried to rebuild the scene from individual references and
  transforms. That is educational, but it changed the final composition. Since
  `output/neuron_variant_scene.usda` already has the exact microtubule bundle
  placement you want, the safest professional workflow is:

    1. Treat the current scene as the approved layout source
    2. Compose it into a new root stage
    3. Put camera animation in its own layer
    4. Put material overrides in their own layer

This keeps the visual result aligned with the current approved scene while
still demonstrating good USD layering practices.

Study notes:
  - A USD "layer" is a file.
  - A USD "stage" is the composed result of one or more layers.
  - Sublayering is often the cleanest way to preserve an approved base scene.
  - Stronger layers can override weaker layers without modifying the source.
"""

from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

ROOT_LAYER = OUTPUT_DIR / "healthy_tau.usda"
BASE_LAYER = OUTPUT_DIR / "healthy_tau_base.usda"
MATERIALS_LAYER = OUTPUT_DIR / "healthy_tau_materials.usda"
CAMERA_LAYER = OUTPUT_DIR / "healthy_tau_camera.usda"

SOURCE_SCENE = "./neuron_variant_scene.usda"


def make_stage(path: Path) -> Usd.Stage:
    """
    Create a new stage with the same scene-wide metadata used elsewhere.
    """
    stage = Usd.Stage.CreateNew(str(path))
    stage.SetMetadata("metersPerUnit", 0.01)
    stage.SetMetadata("upAxis", "Y")
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    return stage


def set_preview_surface(
    stage: Usd.Stage,
    material_path: str,
    diffuse: Gf.Vec3f,
    emissive: Gf.Vec3f | None,
    opacity: float,
    roughness: float,
    metallic: float = 0.0,
) -> None:
    """
    Author or override a simple UsdPreviewSurface material.

    This helper is intentionally compact so you can study the common pattern:
      Material -> Shader -> inputs -> connect shader to material surface output
    """
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, material_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse)
    if emissive is not None:
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(emissive)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")


def build_base_layer() -> None:
    """
    Compose the approved source scene into a dedicated base layer.

    This is the key design decision:
      Instead of rebuilding the microtubule placement, we preserve the exact
      scene that already works visually and compose from that.
    """
    stage = make_stage(BASE_LAYER)
    root = stage.GetRootLayer()
    root.subLayerPaths = [SOURCE_SCENE]
    stage.Save()


def build_materials_layer() -> None:
    """
    Put the main look-dev materials in a stronger, separate layer.

    Even if the values match the source scene today, having this layer gives
    you a clean place to iterate on look-dev later without touching layout.
    """
    stage = make_stage(MATERIALS_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Materials")

    set_preview_surface(
        stage,
        "/World/Materials/NeuronMembrane",
        diffuse=Gf.Vec3f(0.56, 0.38, 0.78),
        emissive=None,
        opacity=0.18,
        roughness=0.18,
    )
    set_preview_surface(
        stage,
        "/World/Materials/MicrotubuleGlow",
        diffuse=Gf.Vec3f(0.16, 0.88, 0.48),
        emissive=Gf.Vec3f(0.04, 0.24, 0.10),
        opacity=1.0,
        roughness=0.28,
    )
    set_preview_surface(
        stage,
        "/World/Materials/TauGlow",
        diffuse=Gf.Vec3f(0.90, 0.75, 0.05),
        emissive=Gf.Vec3f(0.25, 0.18, 0.01),
        opacity=1.0,
        roughness=0.28,
    )

    stage.Save()


def build_camera_layer() -> None:
    """
    Author a separate camera fly-through layer.

    The base scene already contains viewport/camera metadata from Omniverse.
    This layer adds a dedicated study camera you can animate independently.
    """
    stage = make_stage(CAMERA_LAYER)
    UsdGeom.Scope.Define(stage, "/World/Cameras")

    camera = UsdGeom.Camera.Define(stage, "/World/Cameras/FlyThrough")
    camera.CreateFocalLengthAttr(35.0)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 10000.0))

    xform = UsdGeom.Xformable(camera)
    translate = xform.AddTranslateOp()
    rotate_y = xform.AddRotateYOp()
    rotate_x = xform.AddRotateXOp()

    # Simple upward pass through the axon region.
    translate.Set(Gf.Vec3d(-0.4, -52.0, 0.0), 1.0)
    translate.Set(Gf.Vec3d(-0.4, 6.0, 0.0), 240.0)
    rotate_y.Set(0.0, 1.0)
    rotate_y.Set(0.0, 240.0)
    rotate_x.Set(-90.0, 1.0)
    rotate_x.Set(-90.0, 240.0)

    # Make this camera the intended camera in a standard USD-friendly way.
    render_settings = stage.OverridePrim("/Render/HealthyTauRenderSettings")
    render_settings.SetTypeName("RenderSettings")
    camera_rel = render_settings.CreateRelationship("camera", custom=False)
    camera_rel.SetTargets([Sdf.Path("/World/Cameras/FlyThrough")])

    stage.Save()


def build_root_stage() -> None:
    """
    Build the final thin compositor stage.

    Layer order matters:
      - base layer provides the approved scene
      - materials layer can override looks
      - camera layer adds/overrides camera setup
    """
    stage = make_stage(ROOT_LAYER)
    root = stage.GetRootLayer()
    root.subLayerPaths = [
        CAMERA_LAYER.name,
        MATERIALS_LAYER.name,
        BASE_LAYER.name,
    ]
    stage.Save()


def main() -> None:
    """
    Author the layered healthy TAU scene files.

    This writes files only. It does not open viewers or render output.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_base_layer()
    build_materials_layer()
    build_camera_layer()
    build_root_stage()


if __name__ == "__main__":
    main()
