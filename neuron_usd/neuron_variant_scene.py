"""Assemble artist and procedural neurons as an OpenUSD variant set.

This stage intentionally contains no microtubules yet. It establishes the
stable model choices and shared materials before internal structures are added.

Run:
    python neuron_usd/neuron_variant_scene.py
"""

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


OUTPUT_PATH = "output/neuron_variant_scene.usda"
ARTIST_NEURON_ASSET = "../assets/neuron_model.usda"
PROCEDURAL_NEURON_ASSET = "./structured_neuron.usda"
MICROTUBULE_BUNDLE_ASSET = "./microtubule_bundle.usda"


def create_preview_material(stage, path, color, opacity, roughness, emissive=None):
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(*color)
    )
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    if emissive:
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(*emissive)
        )

    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def create_artist_variant(stage, variant_set, membrane_material, microtubule_material):
    variant_set.AddVariant("ArtistNeuron")
    variant_set.SetVariantSelection("ArtistNeuron")

    with variant_set.GetVariantEditContext():
        shell = UsdGeom.Xform.Define(stage, "/World/NeuronModel/NeuronShell")
        shell.GetPrim().GetReferences().AddReference(ARTIST_NEURON_ASSET)

        # Blender asset is Z-up; rotate it into this Y-up stage and enlarge it.
        shell.AddRotateXOp().Set(-90.0)
        shell.AddScaleOp().Set(Gf.Vec3f(2.15, 2.15, 2.15))
        UsdShade.MaterialBindingAPI.Apply(shell.GetPrim()).Bind(
            membrane_material,
            bindingStrength=UsdShade.Tokens.strongerThanDescendants,
        )

        # Reference the complete flattened bundle. Its source points along +Y;
        # the artist neuron's axon points along -Y after the Blender correction.
        bundle_prim = stage.DefinePrim("/World/NeuronModel/Microtubules")
        bundle_prim.GetReferences().AddReference(
            MICROTUBULE_BUNDLE_ASSET,
            Sdf.Path("/World/MicrotubuleBundle"),
        )
        bundle = UsdGeom.Xformable(bundle_prim)
        bundle.AddTranslateOp().Set(Gf.Vec3d(-0.40, 1.40, 0.0))
        bundle.AddRotateXOp().Set(180.0)
        bundle.AddScaleOp().Set(Gf.Vec3f(0.15, 0.15, 0.15))
        UsdShade.MaterialBindingAPI.Apply(bundle_prim).Bind(
            microtubule_material,
            bindingStrength=UsdShade.Tokens.strongerThanDescendants,
        )


def create_procedural_variant(stage, variant_set, membrane_material):
    variant_set.AddVariant("ProceduralNeuron")
    variant_set.SetVariantSelection("ProceduralNeuron")

    with variant_set.GetVariantEditContext():
        shell = stage.DefinePrim("/World/NeuronModel/NeuronShell")
        shell.GetReferences().AddReference(
            PROCEDURAL_NEURON_ASSET,
            Sdf.Path("/World/Neuron"),
        )
        UsdShade.MaterialBindingAPI.Apply(shell).Bind(
            membrane_material,
            bindingStrength=UsdShade.Tokens.strongerThanDescendants,
        )

        # Guides are authored separately so render geometry and placement data
        # remain distinct while switching together in the same model variant.
        guides = stage.DefinePrim("/World/NeuronModel/Guides")
        guides.GetReferences().AddReference(
            PROCEDURAL_NEURON_ASSET,
            Sdf.Path("/World/Guides"),
        )


def build_stage():
    stage = Usd.Stage.CreateNew(OUTPUT_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Scope.Define(stage, "/World/Materials")

    # These values match healthy_neuron.py exactly.
    membrane_material = create_preview_material(
        stage,
        "/World/Materials/NeuronMembrane",
        color=(0.56, 0.38, 0.78),
        opacity=0.18,
        roughness=0.18,
    )
    microtubule_material = create_preview_material(
        stage,
        "/World/Materials/MicrotubuleGlow",
        color=(0.16, 0.88, 0.48),
        opacity=1.0,
        roughness=0.28,
        emissive=(0.04, 0.24, 0.10),
    )

    model = UsdGeom.Xform.Define(stage, "/World/NeuronModel")
    variant_set = model.GetPrim().GetVariantSets().AddVariantSet("neuronModel")

    create_artist_variant(
        stage,
        variant_set,
        membrane_material,
        microtubule_material,
    )
    create_procedural_variant(stage, variant_set, membrane_material)

    # The artist-authored neuron is the presentation default.
    variant_set.SetVariantSelection("ArtistNeuron")
    stage.GetRootLayer().Save()
    return stage


if __name__ == "__main__":
    build_stage()
    print(f"Saved: {OUTPUT_PATH}")
    print("Variant set: neuronModel")
    print("Variants: ArtistNeuron, ProceduralNeuron")
    print("Default selection: ArtistNeuron")
