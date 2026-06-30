#!/usr/bin/env python3
"""
Build a layered healthy neuron scene with microtubules, TAU, and camera setup.

This script is intentionally authoring-only. It creates USD layers but does not
launch viewers or render anything.

Key USD goals:
  - Thin root stage
  - Separate layers for materials, geometry composition, and camera animation
  - Reuse existing assets and transforms from the current project
  - Keep camera animation isolated from model/material authoring
"""

from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSET_DIR = PROJECT_ROOT / "assets"

ROOT_LAYER = OUTPUT_DIR / "healthy_tau.usda"
MATERIALS_LAYER = OUTPUT_DIR / "healthy_tau_materials.usda"
MICROTUBULES_LAYER = OUTPUT_DIR / "healthy_tau_microtubules.usda"
TAU_LAYER = OUTPUT_DIR / "healthy_tau_tau.usda"
CAMERA_LAYER = OUTPUT_DIR / "healthy_tau_camera.usda"

NEURON_ASSET = "../assets/neuron_model.usda"
MICROTUBULE_BUNDLE_ASSET = "./microtubule_bundle.usda"

# Reused from the committed neuron_variant_scene.usda setup.
NEURON_TRANSLATE = Gf.Vec3d(-0.7692236665569981, 4.718571919619595, -6.6885030774645844e-15)
NEURON_ROTATE = Gf.Vec3f(-93.738335, 0.44405317, 6.523333)
NEURON_SCALE = Gf.Vec3f(3.3, 3.3, 3.3)

MICROTUBULE_INSTANCES = [
    {
        "name": "Microtubules_01",
        "translate": Gf.Vec3d(-0.4, -7.733460325034177, 4.5002969044673766e-29),
        "rotate": Gf.Vec3f(180.0, 0.0, 0.0),
        "scale": Gf.Vec3f(0.15, 0.15, 0.15),
        "segment_override": None,
    },
    {
        "name": "Microtubules_02",
        "translate": Gf.Vec3d(-0.4, -19.762036118033034, -6.352650832591862e-30),
        "rotate": Gf.Vec3f(180.0, 0.0, 0.0),
        "scale": Gf.Vec3f(0.15, 0.15, 0.15),
        "segment_override": {
            "translate": Gf.Vec3d(0.0, -18.75350068705029, -2.296641458920211e-15),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
    {
        "name": "Microtubules_03",
        "translate": Gf.Vec3d(-0.39999999999999963, -26.60000000000001, 4.226416694238857e-17),
        "rotate": Gf.Vec3f(179.57585, -0.063509375, -0.9031304),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": None,
    },
    {
        "name": "Microtubules_04",
        "translate": Gf.Vec3d(-0.4, -33.600000000000016, 1.2954789903763435e-15),
        "rotate": Gf.Vec3f(177.0, 0.0, 0.0),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": None,
    },
    {
        "name": "Microtubules_05",
        "translate": Gf.Vec3d(-0.4, -40.59040674328204, 0.3663516937006086),
        "rotate": Gf.Vec3f(173.04268, 0.10218263, 0.57034796),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": None,
    },
    {
        "name": "Microtubules_06",
        "translate": Gf.Vec3d(-0.729890560267854, -47.52847753032135, 1.7313329221558182),
        "rotate": Gf.Vec3f(169.1283, 3.803126, 10.4081955),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": {
            "translate": Gf.Vec3d(9.999999850988381, 2.8421709430404007e-13, 9.999999850988445),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
    {
        "name": "Microtubules_07",
        "translate": Gf.Vec3d(-1.5763882459739773, 0.5846368954187088, -7.071029151820076),
        "rotate": Gf.Vec3f(71.96148, -0.15596047, 54.396183),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": {
            "translate": Gf.Vec3d(29.96829093201537, 2.0698357698624292, 3.46871208806094),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
    {
        "name": "Microtubules_08",
        "translate": Gf.Vec3d(-3.806913919112263, 0.8510111967519306, 2.6872357243723286),
        "rotate": Gf.Vec3f(71.96148, -0.15596047, 54.396183),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": {
            "translate": Gf.Vec3d(29.96829093201537, 2.0698357698624292, 3.46871208806094),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
    {
        "name": "Microtubules_09",
        "translate": Gf.Vec3d(-7.883053705122286, 1.1627821373987655, 4.589669678386052),
        "rotate": Gf.Vec3f(197.13977, 43.02415, 115.97241),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": {
            "translate": Gf.Vec3d(36.65153137704881, 2.0698357698621734, 4.579582104226738),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
    {
        "name": "Microtubules_10",
        "translate": Gf.Vec3d(0.22511187683954395, 1.1220048432090912, 1.809692525407168),
        "rotate": Gf.Vec3f(135.52682, -13.722503, 86.36963),
        "scale": Gf.Vec3f(0.1, 0.1, 0.1),
        "segment_override": {
            "translate": Gf.Vec3d(29.96829093201537, 2.0698357698624292, 3.46871208806094),
            "rotate": Gf.Vec3f(-90.0, 0.0, 0.0),
            "scale": Gf.Vec3f(1.0, 1.0, 1.0),
        },
    },
]


def make_stage(path: Path) -> Usd.Stage:
    stage = Usd.Stage.CreateNew(str(path))
    stage.SetMetadata("metersPerUnit", 0.01)
    stage.SetMetadata("upAxis", "Y")
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    return stage


def add_transform_ops(xformable: UsdGeom.Xformable, translate: Gf.Vec3d, rotate: Gf.Vec3f, scale: Gf.Vec3f) -> None:
    xformable.AddTranslateOp().Set(translate)
    xformable.AddRotateZOp().Set(float(rotate[2]))
    xformable.AddRotateYOp().Set(float(rotate[1]))
    xformable.AddRotateXOp().Set(float(rotate[0]))
    xformable.AddScaleOp().Set(scale)


def bind_material_path(prim: Usd.Prim, material_path: str) -> None:
    binding = prim.CreateRelationship("material:binding", custom=False)
    binding.SetTargets([Sdf.Path(material_path)])


def build_materials_layer() -> None:
    stage = make_stage(MATERIALS_LAYER)
    materials = UsdGeom.Scope.Define(stage, "/World/Materials")

    neuron_mat = UsdShade.Material.Define(stage, "/World/Materials/NeuronMembrane")
    neuron_shader = UsdShade.Shader.Define(stage, "/World/Materials/NeuronMembrane/Shader")
    neuron_shader.CreateIdAttr("UsdPreviewSurface")
    neuron_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.56, 0.38, 0.78))
    neuron_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.18)
    neuron_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.18)
    neuron_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    neuron_mat.CreateSurfaceOutput().ConnectToSource(neuron_shader.ConnectableAPI(), "surface")

    mt_mat = UsdShade.Material.Define(stage, "/World/Materials/MicrotubuleGlow")
    mt_shader = UsdShade.Shader.Define(stage, "/World/Materials/MicrotubuleGlow/Shader")
    mt_shader.CreateIdAttr("UsdPreviewSurface")
    mt_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.16, 0.88, 0.48))
    mt_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.04, 0.24, 0.1))
    mt_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0)
    mt_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.28)
    mt_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    mt_mat.CreateSurfaceOutput().ConnectToSource(mt_shader.ConnectableAPI(), "surface")

    tau_mat = UsdShade.Material.Define(stage, "/World/Materials/TauGlow")
    tau_shader = UsdShade.Shader.Define(stage, "/World/Materials/TauGlow/Shader")
    tau_shader.CreateIdAttr("UsdPreviewSurface")
    tau_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.9, 0.75, 0.05))
    tau_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.25, 0.18, 0.01))
    tau_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0)
    tau_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.28)
    tau_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    tau_mat.CreateSurfaceOutput().ConnectToSource(tau_shader.ConnectableAPI(), "surface")

    stage.Save()


def build_microtubules_layer() -> None:
    stage = make_stage(MICROTUBULES_LAYER)
    neuron_model = UsdGeom.Xform.Define(stage, "/World/NeuronModel")

    neuron_shell = stage.DefinePrim("/World/NeuronModel/NeuronShell", "Xform")
    neuron_shell.GetReferences().AddReference(NEURON_ASSET)
    bind_material_path(neuron_shell, "/World/Materials/NeuronMembrane")
    add_transform_ops(UsdGeom.Xformable(neuron_shell), NEURON_TRANSLATE, NEURON_ROTATE, NEURON_SCALE)

    for item in MICROTUBULE_INSTANCES:
        prim = stage.DefinePrim(f"/World/NeuronModel/{item['name']}", "Xform")
        prim.GetReferences().AddReference(MICROTUBULE_BUNDLE_ASSET, Sdf.Path("/World/MicrotubuleBundle"))
        bind_material_path(prim, "/World/Materials/MicrotubuleGlow")
        add_transform_ops(UsdGeom.Xformable(prim), item["translate"], item["rotate"], item["scale"])

        if item["segment_override"] is not None:
            segment = stage.OverridePrim(f"/World/NeuronModel/{item['name']}/Prototypes/Segment")
            add_transform_ops(
                UsdGeom.Xformable(segment),
                item["segment_override"]["translate"],
                item["segment_override"]["rotate"],
                item["segment_override"]["scale"],
            )

    stage.Save()


def build_tau_layer() -> None:
    stage = make_stage(TAU_LAYER)
    for item in MICROTUBULE_INSTANCES:
        tau_over = stage.OverridePrim(f"/World/NeuronModel/{item['name']}/TauBundle")
        bind_material_path(tau_over, "/World/Materials/TauGlow")
    stage.Save()


def build_camera_layer() -> None:
    stage = make_stage(CAMERA_LAYER)
    camera = UsdGeom.Camera.Define(stage, "/World/Cameras/FlyThrough")
    camera.CreateFocalLengthAttr(35.0)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 10000.0))

    xform = UsdGeom.Xformable(camera)
    translate = xform.AddTranslateOp()
    rotate_y = xform.AddRotateYOp()
    rotate_x = xform.AddRotateXOp()

    translate.Set(Gf.Vec3d(-0.4, -52.0, 0.0), 1.0)
    translate.Set(Gf.Vec3d(-0.4, 6.0, 0.0), 240.0)
    rotate_y.Set(0.0, 1.0)
    rotate_y.Set(0.0, 240.0)
    rotate_x.Set(-90.0, 1.0)
    rotate_x.Set(-90.0, 240.0)

    stage.Save()


def build_root_stage() -> None:
    stage = make_stage(ROOT_LAYER)
    root = stage.GetRootLayer()
    root.subLayerPaths = [
        CAMERA_LAYER.name,
        TAU_LAYER.name,
        MICROTUBULES_LAYER.name,
        MATERIALS_LAYER.name,
    ]
    stage.Save()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_materials_layer()
    build_microtubules_layer()
    build_tau_layer()
    build_camera_layer()
    build_root_stage()


if __name__ == "__main__":
    main()
