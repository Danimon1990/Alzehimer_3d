#!/usr/bin/env python3
"""
Adds TAU protein instances to the scene.

What this does:
  1. microtubule_bundle.usda — adds TauBundle as a sibling of
     MicrotubuleBundle under a shared assembly Xform, which renders more
     reliably than nesting it under a PointInstancer.
  2. neuron_variant_scene.usda — adds TauGlow material and overrides the
     material binding on each TauBundle so it stays yellow (not overridden
     to green by the parent MicrotubuleGlow strongerThanDescendants binding).

Run with:
    python3 add_tau_to_bundle.py
"""
from pxr import Usd, UsdGeom, UsdShade, Gf, Sdf

BUNDLE_FILE = "/home/daniel/Documents/healthy_vs_alz/output/microtubule_bundle.usda"
SCENE_FILE  = "/home/daniel/Documents/healthy_vs_alz/output/neuron_variant_scene.usda"
TAU_ASSET   = "../assets/TAU.usdc"
TAU_PRIM    = "/root/NurbsPath"

# Adjust after first look in Omniverse — at 1.0 TAU is ~1/6th one segment height
TAU_SCALE = 1.0

CHAINS = [
    ( 0.0,        0.0       ),
    ( 3.0,        0.0       ),
    ( 0.927051,   2.8531694 ),
    (-2.427051,   1.7633557 ),
    (-2.427051,  -1.7633557 ),
    ( 0.927051,  -2.8531694 ),
]
CHAIN_Y_MAX     = 53.244
N_TAU_PER_CHAIN = 4
y_positions = [CHAIN_Y_MAX * i / (N_TAU_PER_CHAIN + 1)
               for i in range(1, N_TAU_PER_CHAIN + 1)]

# ── 1. microtubule_bundle.usda ────────────────────────────────────────────────

bundle = Usd.Stage.Open(BUNDLE_FILE)

# Clean up any prims written by the previous run
for old in ["/World/TauBundle", "/World/MicrotubuleAssembly", "/World/Materials"]:
    if bundle.GetPrimAtPath(old):
        bundle.RemovePrim(Sdf.Path(old))

# Build positions
positions    = []
orientations = []
for cx, cz in CHAINS:
    for y in y_positions:
        positions.append(Gf.Vec3f(cx, float(y), cz))
        orientations.append(Gf.Quath(1, 0, 0, 0))
proto_indices = [0] * len(positions)

# TauBundle as a sibling of MicrotubuleBundle under a shared assembly
ASSEMBLY_PATH = "/World/MicrotubuleAssembly"
TAU_PATH = ASSEMBLY_PATH + "/TauBundle"
UsdGeom.Xform.Define(bundle, ASSEMBLY_PATH)
instancer = UsdGeom.PointInstancer.Define(bundle, TAU_PATH)
instancer.CreatePositionsAttr().Set(positions)
instancer.CreateOrientationsAttr().Set(orientations)
instancer.CreateProtoIndicesAttr().Set(proto_indices)
instancer.CreatePrototypesRel().SetTargets(
    [Sdf.Path(TAU_PATH + "/Prototypes/TauProtein")]
)

UsdGeom.Scope.Define(bundle, TAU_PATH + "/Prototypes")
proto = bundle.DefinePrim(TAU_PATH + "/Prototypes/TauProtein", "Xform")
proto.GetReferences().AddReference(TAU_ASSET, Sdf.Path(TAU_PRIM))

xf = UsdGeom.Xformable(proto)
xf.AddRotateXOp().Set(-90.0)
if TAU_SCALE != 1.0:
    xf.AddScaleOp().Set(Gf.Vec3f(TAU_SCALE, TAU_SCALE, TAU_SCALE))

bundle.Save()
print(f"Bundle saved — {len(positions)} TAU instances inside {TAU_PATH}")

# ── 2. neuron_variant_scene.usda ──────────────────────────────────────────────

scene = Usd.Stage.Open(SCENE_FILE)

# Add TauGlow material alongside the existing MicrotubuleGlow
tau_mat    = UsdShade.Material.Define(scene, "/World/Materials/TauGlow")
tau_shader = UsdShade.Shader.Define(scene,   "/World/Materials/TauGlow/Shader")
tau_shader.CreateIdAttr("UsdPreviewSurface")
tau_shader.CreateInput("diffuseColor",  Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.9,  0.75, 0.05))
tau_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.25, 0.18, 0.01))
tau_shader.CreateInput("metallic",      Sdf.ValueTypeNames.Float  ).Set(0.0)
tau_shader.CreateInput("roughness",     Sdf.ValueTypeNames.Float  ).Set(0.28)
tau_shader.CreateInput("opacity",       Sdf.ValueTypeNames.Float  ).Set(1.0)
tau_mat.CreateSurfaceOutput().ConnectToSource(tau_shader.ConnectableAPI(), "surface")

# Every microtubule bundle in the scene — Microtubules_01 … _10 plus the
# ArtistNeuron variant's plain "Microtubules" prim
bundle_prims = [f"/World/NeuronModel/Microtubules_{i:02d}" for i in range(1, 11)]
bundle_prims.append("/World/NeuronModel/Microtubules")

for mt_path in bundle_prims:
    # Override TauBundle with a strongerThanDescendants TauGlow binding so the
    # parent's MicrotubuleGlow strongerThanDescendants binding doesn't win.
    # (The closest ancestor's strongerThanDescendants always takes precedence.)
    tau_over = scene.OverridePrim(Sdf.Path(mt_path + "/TauBundle"))
    UsdShade.MaterialBindingAPI.Apply(tau_over)
    UsdShade.MaterialBindingAPI(tau_over).Bind(
        tau_mat, UsdShade.Tokens.strongerThanDescendants
    )

scene.Save()
print("Scene saved — TauGlow material added and bound on every TauBundle")
print(f"Y positions per chain: {[round(y, 3) for y in y_positions]}")
