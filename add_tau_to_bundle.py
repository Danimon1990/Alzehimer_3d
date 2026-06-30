#!/usr/bin/env python3
"""
Adds TAU protein instances to the microtubule bundle.

<<<<<<< Updated upstream
What this does:
  1. microtubule_bundle.usda — adds TauBundle as a sibling of
     MicrotubuleBundle under a shared assembly Xform, which renders more
     reliably than nesting it under a PointInstancer.
  2. neuron_variant_scene.usda — adds TauGlow material and overrides the
     material binding on each TauBundle so it stays yellow (not overridden
     to green by the parent MicrotubuleGlow strongerThanDescendants binding).
=======
Approach: TauProtein is added as prototype[1] inside the existing
MicrotubuleBundle PointInstancer (alongside Segment as prototype[0]).
The instancer's positions/protoIndices arrays are extended so TAU
proteins are instanced the same way as microtubule segments.

This avoids the Omniverse rendering issue where non-Prototype children
of a PointInstancer are silently ignored by Hydra — only prims inside
the Prototypes/ scope are rendered as instances.
>>>>>>> Stashed changes

Run with:
    python3 add_tau_to_bundle.py
"""
import sys
from pathlib import Path
from pxr import Usd, UsdGeom, UsdShade, Gf, Sdf

# Add project root so we can reuse the bundle builder
sys.path.insert(0, str(Path(__file__).parent))
from neuron_usd.microtubule_bundle import build_stage as _build_bundle

BUNDLE_FILE = "output/microtubule_bundle.usda"
SCENE_FILE  = "output/neuron_variant_scene.usda"
TAU_ASSET   = "../assets/TAU.usdc"
TAU_PRIM    = "/root/NurbsPath"

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
# Regenerate the bundle fresh (keeps segment data clean), then extend it.

_build_bundle()   # writes output/microtubule_bundle.usda with Segment only

bundle = Usd.Stage.Open(BUNDLE_FILE)

<<<<<<< Updated upstream
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
=======
# Add TauProtein as prototype[1] inside the existing Prototypes scope
TAU_PROTO_PATH = "/World/MicrotubuleBundle/Prototypes/TauProtein"
tau_proto = bundle.DefinePrim(TAU_PROTO_PATH, "Xform")
tau_proto.GetReferences().AddReference(TAU_ASSET)
xf = UsdGeom.Xformable(tau_proto)
>>>>>>> Stashed changes
xf.AddRotateXOp().Set(-90.0)
if TAU_SCALE != 1.0:
    xf.AddScaleOp().Set(Gf.Vec3f(TAU_SCALE, TAU_SCALE, TAU_SCALE))

# Pull existing segment instance data (60 entries, all protoIndex 0)
instancer    = UsdGeom.PointInstancer(bundle.GetPrimAtPath("/World/MicrotubuleBundle"))
seg_pos      = list(instancer.GetPositionsAttr().Get())
seg_ori      = list(instancer.GetOrientationsAttr().Get())
seg_idx      = list(instancer.GetProtoIndicesAttr().Get())
seg_ids      = list(instancer.GetIdsAttr().Get())

# Build TAU instance data (protoIndex 1)
tau_pos, tau_ori = [], []
for cx, cz in CHAINS:
    for y in y_positions:
        tau_pos.append(Gf.Vec3f(cx, float(y), cz))
        tau_ori.append(Gf.Quath(1, 0, 0, 0))
tau_ids = [6000 + i for i in range(len(tau_pos))]

# Write combined arrays back
instancer.GetPositionsAttr().Set(seg_pos + tau_pos)
instancer.GetOrientationsAttr().Set(seg_ori + tau_ori)
instancer.GetProtoIndicesAttr().Set(seg_idx + [1] * len(tau_pos))
instancer.GetIdsAttr().Set(seg_ids + tau_ids)

# Update prototypes relationship: index 0 = Segment, index 1 = TauProtein
instancer.CreatePrototypesRel().SetTargets([
    Sdf.Path("/World/MicrotubuleBundle/Prototypes/Segment"),
    Sdf.Path(TAU_PROTO_PATH),
])

bundle.Save()
<<<<<<< Updated upstream
print(f"Bundle saved — {len(positions)} TAU instances inside {TAU_PATH}")
=======
print(f"Bundle saved — {len(seg_pos)} Segment + {len(tau_pos)} TauProtein instances")
print(f"TAU Y positions per chain: {[round(y, 3) for y in y_positions]}")
>>>>>>> Stashed changes

# ── 2. neuron_variant_scene.usda ──────────────────────────────────────────────

scene = Usd.Stage.Open(SCENE_FILE)

# Add TauGlow material (idempotent — skip if already present)
tau_mat_path = "/World/Materials/TauGlow"
if not scene.GetPrimAtPath(tau_mat_path):
    tau_mat    = UsdShade.Material.Define(scene, tau_mat_path)
    tau_shader = UsdShade.Shader.Define(scene, tau_mat_path + "/Shader")
    tau_shader.CreateIdAttr("UsdPreviewSurface")
    tau_shader.CreateInput("diffuseColor",  Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.9,  0.75, 0.05))
    tau_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.25, 0.18, 0.01))
    tau_shader.CreateInput("metallic",      Sdf.ValueTypeNames.Float  ).Set(0.0)
    tau_shader.CreateInput("roughness",     Sdf.ValueTypeNames.Float  ).Set(0.28)
    tau_shader.CreateInput("opacity",       Sdf.ValueTypeNames.Float  ).Set(1.0)
    tau_mat.CreateSurfaceOutput().ConnectToSource(tau_shader.ConnectableAPI(), "surface")
else:
    tau_mat = UsdShade.Material(scene.GetPrimAtPath(tau_mat_path))

# Microtubules_01 … _10 plus the ArtistNeuron variant's "Microtubules" prim
bundle_prims = [f"/World/NeuronModel/Microtubules_{i:02d}" for i in range(1, 11)]
bundle_prims.append("/World/NeuronModel/Microtubules")

mt_material = UsdShade.Material(scene.GetPrimAtPath("/World/Materials/MicrotubuleGlow"))

for mt_path in bundle_prims:
    # Clean up old TauBundle override from the previous approach
    old_tau_over = Sdf.Path(mt_path + "/TauBundle")
    if scene.GetPrimAtPath(old_tau_over):
        scene.RemovePrim(old_tau_over)

    # The parent prim's strongerThanDescendants MicrotubuleGlow binding wins
    # over everything below it — including any prototype-level overrides.
    # Fix: weaken the parent binding to weakerThanDescendants so that
    # prototype-level strongerThanDescendants bindings can take effect.
    mt_prim = scene.GetPrimAtPath(mt_path)
    if mt_prim:
        UsdShade.MaterialBindingAPI(mt_prim).Bind(
            mt_material, UsdShade.Tokens.weakerThanDescendants
        )

    # Apply strongerThanDescendants on each prototype directly, so the
    # correct material wins regardless of what the parent or the source
    # asset (.usdc) contains.
    seg_over = scene.OverridePrim(Sdf.Path(mt_path + "/Prototypes/Segment"))
    UsdShade.MaterialBindingAPI.Apply(seg_over)
    UsdShade.MaterialBindingAPI(seg_over).Bind(
        mt_material, UsdShade.Tokens.strongerThanDescendants
    )

    tau_over = scene.OverridePrim(Sdf.Path(mt_path + "/Prototypes/TauProtein"))
    UsdShade.MaterialBindingAPI.Apply(tau_over)
    UsdShade.MaterialBindingAPI(tau_over).Bind(
        tau_mat, UsdShade.Tokens.strongerThanDescendants
    )

scene.Save()
print("Scene saved — Segment=MicrotubuleGlow, TauProtein=TauGlow (both strongerThanDescendants on prototypes)")
