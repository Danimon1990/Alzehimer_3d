"""
neuron_microtubules_scene.py
============================
Builds a healthy-neuron scene in USD showing:

  • Translucent neuron shell  — membrane is visible but see-through
  • Axon microtubule bundle   — 7 parallel chains running the full axon length
  • Dendrite bundles          — 4 shorter bundles branching from the soma

Run from the project root:
    cd /home/daniel/Documents/healthy_vs_alz
    source /home/daniel/usd_root/python-usd-venv/bin/activate
    python neuron_usd/neuron_microtubules_scene.py
    usdview output/neuron_microtubules.usda

---------------------------------------------------------------------------
USD CONCEPTS TAUGHT IN THIS FILE  (look for [C-N] markers in the code)
---------------------------------------------------------------------------
[C-1]  Stage setup        upAxis, metersPerUnit, defaultPrim
[C-2]  References         Non-destructive asset composition
[C-3]  Override arcs      Suppress or modify a prim from a reference
[C-4]  UsdPreviewSurface  Cross-renderer PBR shader (the USD standard)
[C-5]  UsdShade.Material  The "terminal" container for a shader graph
[C-6]  MaterialBindingAPI Attach a material to a prim (inherits to children)
[C-7]  PointInstancer     GPU-efficient N-copy instancing
[C-8]  Prototype pattern  Geometry stored in /Prototypes, rendered elsewhere
[C-9]  Xform transforms   Chaining translate + rotate to aim a dendrite bundle

---------------------------------------------------------------------------
BIOLOGY ENCODED IN THIS SCENE
---------------------------------------------------------------------------
Axon:
  ALL microtubules run PARALLEL with the SAME polarity:
    plus-end  →  axon tip  (anterograde direction, toward the synapse)
  Kinesin motors carry cargo toward the plus-end (away from soma).
  Dynein motors carry cargo toward the minus-end (back to soma).
  A real axon has HUNDREDS of microtubules; we use 7 (hex cross-section)
  so you can see the bundle structure clearly.

Dendrites:
  MIXED polarity — some plus-ends toward soma, some away.
  This is one of the key molecular differences from axons.
  Shorter than the axon; branch from the soma in multiple directions.

Alzheimer's connection (for the future disease scene):
  Tau protein stabilises microtubules. Hyperphosphorylated tau detaches →
  microtubules depolymerise → transport fails → neuron dies.
  The healthy bundles here will become fragmented + tangled in the AD scene.
---------------------------------------------------------------------------
"""

from pxr import Usd, UsdGeom, UsdShade, Gf, Sdf
import math
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — change these to experiment with the scene
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH  = os.path.join(PROJECT_ROOT, "output", "neuron_microtubules.usda")

# Asset paths — RELATIVE to the output layer's directory.
# USD resolves these at load time relative to the layer that contains them.
NEURON_ASSET = "../assets/neuron_model.usda"    # shell mesh
MT_ASSET     = "../assets/microtubules.usdc"    # one microtubule segment

# ── Segment geometry (measured from the asset bounding box) ─────────────────
# The segment runs along Z in the asset (Blender Z-up).
# After Rx(-90°) it runs along Y in our Y-up scene.
# Z extent: -3.4659 to +2.4503  →  total length = 5.916 units = SEGMENT_STRIDE
SEGMENT_STRIDE = 5.916

# ── Axon bundle (runs along the long -Y axis of the neuron) ─────────────────
# Biology: hundreds of parallel microtubules, all same polarity.
# We model 7 — one centre + 6 neighbours in hexagonal close-packing.
AXON_N_CHAINS = 7        # 1 centre + 6 hex ring
AXON_HEX_R   = 1.1       # radius of the hex ring (scene units)
AXON_N_SEGS  = 4         # segments per chain → 4 × 5.916 ≈ 23.7 units

# The instancer positions go from the axon TIP (+Y) toward the soma.
# y_start = bottom of the chain (near axon tip).
AXON_Y_START  = -(AXON_N_SEGS * SEGMENT_STRIDE)   # ≈ -23.7

# ── Dendrite bundles ─────────────────────────────────────────────────────────
# Biology: shorter, branching from the soma in multiple directions.
# Mixed polarity (shown in comments; geometry looks the same both ways).
DEND_N_CHAINS = 3         # triangle cross-section (less dense than axon)
DEND_TRI_R   = 0.7        # triangle ring radius
DEND_N_SEGS  = 2          # 2 × 5.916 ≈ 11.8 units per dendrite

# Soma junction — where dendrite bundles are anchored in world space.
# The neuron model (after Rx(-90°)) spans Y = -20.5 to +3.9.
# The wider soma region is roughly Y = 0 to +3.
SOMA_Y = 1.8
SOMA_X = -0.4   # slight X offset to match the neuron mesh centroid
SOMA_Z =  0.0

# ── Visual design ─────────────────────────────────────────────────────────────
NEURON_DIFFUSE  = Gf.Vec3f(0.70, 0.55, 0.88)   # soft violet membrane
NEURON_OPACITY  = 0.15                           # very translucent
MT_DIFFUSE      = Gf.Vec3f(0.10, 0.90, 0.45)   # bright green microtubules
MT_EMISSIVE     = Gf.Vec3f(0.02, 0.20, 0.10)   # faint glow to pop inside the shell


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — hexagonal close-packing offsets
# ─────────────────────────────────────────────────────────────────────────────
def hex_offsets(n: int, radius: float) -> list:
    """
    Return (x, z) centre positions for a hexagonal bundle cross-section.

    n=1  → [(0,0)]
    n=7  → centre + 6 at 60° intervals
    n=19 → two complete rings (we don't use this here but the function supports it)

    WHY hexagonal?
    Microtubules in a real axon are roughly cylindrical and pack in hexagonal
    close-packing — the densest arrangement for equal-radius circles.
    """
    offsets = [(0.0, 0.0)]
    ring = 1
    while len(offsets) < n:
        for k in range(6):
            angle = math.radians(60 * k)
            ax = radius * ring * math.cos(angle)
            az = radius * ring * math.sin(angle)
            for step in range(ring):
                step_angle = math.radians(60 * k + 120)
                x = ax + math.cos(step_angle) * radius * step
                z = az + math.sin(step_angle) * radius * step
                offsets.append((x, z))
                if len(offsets) >= n:
                    return offsets[:n]
        ring += 1
    return offsets[:n]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — build one microtubule bundle
# ─────────────────────────────────────────────────────────────────────────────
def build_bundle(
    stage,
    instancer_path: str,
    chain_xz: list,
    y_start: float,
    n_segs: int,
    mt_material,
):
    """
    Create one PointInstancer that renders a bundle of parallel chains.

    [C-7]  UsdGeomPointInstancer
    A PointInstancer stores N copies of a prototype prim at N world positions.
    Compared to N separate Xform children it is:
      • Scene-graph efficient  — one prim, N entries in position/index arrays
      • GPU efficient          — one draw call per prototype, transformed on GPU

    Three arrays are REQUIRED on every instancer:
      prototypes    — relationship → list of prototype prims
      protoIndices  — int[] per instance, which prototype to render (index into prototypes)
      positions     — Vec3f[] per instance, where to place the pivot

    Optional arrays:  orientations (Quatf[]), scales (Vec3f[]), velocities (Vec3f[])

    [C-8]  Prototype pattern
    Prototypes live INSIDE the instancer under a /Prototypes scope.
    They are NOT rendered at their prim position — the instancer places them.
    Think of /Prototypes as a "template drawer": store here, stamp elsewhere.

    chain_xz  : list of (x, z) offsets — one per parallel chain in the bundle
    y_start   : Y position of the first segment in each chain (local space)
    n_segs    : number of segments stacked per chain
    """
    instancer = UsdGeom.PointInstancer.Define(stage, instancer_path)

    # ── Prototype ─────────────────────────────────────────────────────────────
    proto_scope_path = instancer_path + "/Prototypes"
    UsdGeom.Scope.Define(stage, proto_scope_path)

    proto_path = proto_scope_path + "/Segment"
    proto = UsdGeom.Xform.Define(stage, proto_path)

    # [C-2] Reference — compose the external segment asset here.
    # This does NOT copy the geometry; USD loads it at render/traversal time.
    proto.GetPrim().GetReferences().AddReference(MT_ASSET)

    # COORDINATE CORRECTION:
    # microtubules.usdc is Z-up (Blender default).  Our stage is Y-up.
    # Rotation Rx(-90°) maps  Z → +Y  and  Y → -Z.
    # Result: the segment, which runs along Z in the asset, now runs along Y.
    proto.AddRotateXOp().Set(-90.0)

    # [C-3] Override arc — suppress the DomeLight that Blender exported into
    # the microtubule asset.  We create a lightweight "over" prim and mark it
    # inactive without touching the source file.
    light_override = stage.OverridePrim(proto_path + "/env_light")
    light_override.SetActive(False)

    # [C-6] Bind the microtubule material to the prototype.
    # Because neither the asset nor any of its children have their own bindings,
    # this inherited binding applies to all mesh children inside the reference.
    UsdShade.MaterialBindingAPI(proto.GetPrim()).Bind(mt_material)

    # ── Wire prototype into instancer ─────────────────────────────────────────
    instancer.CreatePrototypesRel().SetTargets([Sdf.Path(proto_path)])

    # ── Instance arrays ───────────────────────────────────────────────────────
    # Layout: for each parallel chain × each segment, emit one instance.
    #
    #   chain 0, seg 0 → (cx0, y_start + 0*stride,  cz0)
    #   chain 0, seg 1 → (cx0, y_start + 1*stride,  cz0)
    #   ...
    #   chain 1, seg 0 → (cx1, y_start + 0*stride,  cz1)
    #   ...
    #
    # All positions are in the instancer's LOCAL coordinate space.
    # The parent Xform's transform is applied on top automatically.
    positions = []
    for (cx, cz) in chain_xz:
        for j in range(n_segs):
            positions.append(Gf.Vec3f(cx, y_start + j * SEGMENT_STRIDE, cz))

    n_inst = len(positions)
    instancer.CreateProtoIndicesAttr().Set([0] * n_inst)   # all use prototype 0
    instancer.CreatePositionsAttr().Set(positions)

    print(f"    {instancer_path.split('/')[-2]}/{instancer_path.split('/')[-1]}: "
          f"{len(chain_xz)} chains × {n_segs} segs = {n_inst} instances")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  STAGE SETUP
# ─────────────────────────────────────────────────────────────────────────────
# [C-1] Every USD stage should declare three pieces of metadata:
#
#   upAxis        — which world axis points "up"
#                   Y = USD/Pixar default, Z = Blender/engineering default
#                   Setting this explicitly avoids renderer confusion.
#
#   metersPerUnit — real-world scale of one scene unit
#                   Neurons are microscopic; we treat 1 unit ≈ 1 µm here.
#                   (Blender exports as 1 unit = 1 m; we override that.)
#
#   defaultPrim   — which prim is "the scene" when someone references this file.
#                   Without it, a downstream reference must specify a prim path
#                   manually — fragile if you ever rename it.

stage = Usd.Stage.CreateNew(OUTPUT_PATH)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
stage.SetMetadata("metersPerUnit", 0.000001)   # 1 unit = 1 micrometre

world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

print(f"\nBuilding scene: {OUTPUT_PATH}\n")
print("[ Stage setup complete ]")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  MATERIALS
# ─────────────────────────────────────────────────────────────────────────────
# [C-5] UsdShade.Material is NOT the shader — it is the "terminal" prim that
# renderers and material-binding lookups connect to.  The actual PBR inputs
# live on a Shader prim (id = "UsdPreviewSurface") wired into the Material.
#
# Shader graph for any surface material:
#
#   /World/Materials/Foo           ← Material prim  (the terminal)
#     /World/Materials/Foo/Shader  ← Shader prim    (the parameters)
#
#   Shader.outputs:surface  ──▶  Material.outputs:surface
#
# [C-4] UsdPreviewSurface is the USD standard cross-renderer PBR material.
# Supported by usdview (Hydra/Storm), Omniverse, Houdini, Maya, Blender, etc.
# Key inputs used here:
#   diffuseColor   — base RGB colour
#   opacity        — 0.0 = invisible, 1.0 = fully opaque
#   roughness      — 0.0 = perfect mirror, 1.0 = perfectly matte
#   emissiveColor  — light the surface emits (independent of scene lights)

UsdGeom.Scope.Define(stage, "/World/Materials")

# ── Neuron membrane: translucent violet ───────────────────────────────────────
neuron_mat = UsdShade.Material.Define(stage, "/World/Materials/NeuronMembrane")
n_shd = UsdShade.Shader.Define(stage, "/World/Materials/NeuronMembrane/Shader")
n_shd.CreateIdAttr("UsdPreviewSurface")
n_shd.CreateInput("diffuseColor",  Sdf.ValueTypeNames.Color3f).Set(NEURON_DIFFUSE)
n_shd.CreateInput("opacity",       Sdf.ValueTypeNames.Float  ).Set(NEURON_OPACITY)
n_shd.CreateInput("roughness",     Sdf.ValueTypeNames.Float  ).Set(0.25)
n_shd.CreateInput("metallic",      Sdf.ValueTypeNames.Float  ).Set(0.0)
# Connect shader output → material surface terminal
neuron_mat.CreateSurfaceOutput().ConnectToSource(n_shd.ConnectableAPI(), "surface")

# ── Microtubule: bright green with faint glow ─────────────────────────────────
mt_mat = UsdShade.Material.Define(stage, "/World/Materials/Microtubule")
m_shd = UsdShade.Shader.Define(stage, "/World/Materials/Microtubule/Shader")
m_shd.CreateIdAttr("UsdPreviewSurface")
m_shd.CreateInput("diffuseColor",  Sdf.ValueTypeNames.Color3f).Set(MT_DIFFUSE)
m_shd.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(MT_EMISSIVE)
m_shd.CreateInput("opacity",       Sdf.ValueTypeNames.Float  ).Set(1.0)
m_shd.CreateInput("roughness",     Sdf.ValueTypeNames.Float  ).Set(0.35)
m_shd.CreateInput("metallic",      Sdf.ValueTypeNames.Float  ).Set(0.0)
mt_mat.CreateSurfaceOutput().ConnectToSource(m_shd.ConnectableAPI(), "surface")

print("[ Materials defined: NeuronMembrane (translucent violet), Microtubule (green) ]")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  NEURON SHELL
# ─────────────────────────────────────────────────────────────────────────────
# [C-2] Reference — compose the neuron mesh into our scene.
# The neuron_model.usda file is NOT copied; USD loads it lazily at runtime.
# Our scene only stores the reference arc + any overrides we apply on top.

neuron_shell = UsdGeom.Xform.Define(stage, "/World/NeuronShell")
neuron_shell.GetPrim().GetReferences().AddReference(NEURON_ASSET)

# The neuron model was exported from Blender (Z-up, upAxis=Z).
# Our stage is Y-up.  Rx(-90°) maps  Z → +Y,  Y → -Z.
# After this rotation the neuron's long axis (originally Z) runs along Y.
# Result: soma near Y=+3, axon tip near Y=-20.
neuron_shell.AddRotateXOp().Set(-90.0)

# [C-3] Override arc — deactivate the DomeLight that Blender included.
# stage.OverridePrim() creates a minimal "over" prim: it carries only the
# properties we explicitly set, composing on top of the reference.
env_over = stage.OverridePrim("/World/NeuronShell/env_light")
env_over.SetActive(False)

# [C-6] MaterialBindingAPI — attach the translucent material to the shell.
# The binding is INHERITED by all descendant Mesh prims.
# Because the neuron mesh has no competing direct binding of its own,
# this binding reaches all the way down to the geometry.
UsdShade.MaterialBindingAPI(neuron_shell.GetPrim()).Bind(neuron_mat)

print("[ Neuron shell: reference + Rx(-90°) + translucent violet material ]")
print("  Asset local extent → world after rotation:")
print("    X: -5.0 .. +4.2   (width ~9 units)")
print("    Y: -20.5 .. +3.9  (long axis — axon below soma)")
print("    Z: -4.6  .. +4.4  (depth ~9 units)")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  MICROTUBULE BUNDLES
# ─────────────────────────────────────────────────────────────────────────────
mt_root = UsdGeom.Xform.Define(stage, "/World/Microtubules")

# Cross-section patterns
axon_xz = hex_offsets(AXON_N_CHAINS, AXON_HEX_R)   # 7 positions, hexagonal
dend_xz = hex_offsets(DEND_N_CHAINS, DEND_TRI_R)   # 3 positions, triangle

print(f"\n[ Axon bundle: {AXON_N_CHAINS} chains × {AXON_N_SEGS} segs, hex cross-section ]")

# ── 4a. Axon bundle ──────────────────────────────────────────────────────────
# BIOLOGY:
#   All microtubules run PARALLEL with the SAME polarity (plus-end → axon tip).
#   Kinesin carries cargo anterograde (soma → synapse), dynein retrograde.
#   The axon tip is at Y ≈ -20.5 in world space; the soma is at Y ≈ 0.
#
# GEOMETRY:
#   The instancer positions instances along +Y (from AXON_Y_START upward).
#   AXON_Y_START ≈ -23.7 so the 4 segments stack to ≈ Y=0.
#   Chain XZ offsets centre the bundle inside the axon (width ≈ 2 × AXON_HEX_R).

axon_xform = UsdGeom.Xform.Define(stage, "/World/Microtubules/Axon")
# Slight X translation to sit inside the neuron mesh centroid
axon_xform.AddTranslateOp().Set(Gf.Vec3d(SOMA_X, 0.0, SOMA_Z))

build_bundle(
    stage,
    instancer_path="/World/Microtubules/Axon/Bundle",
    chain_xz=axon_xz,
    y_start=AXON_Y_START,
    n_segs=AXON_N_SEGS,
    mt_material=mt_mat,
)

# ── 4b. Dendrite bundles ─────────────────────────────────────────────────────
# BIOLOGY:
#   Mixed polarity (shown here with uniform +Y orientation for clarity).
#   Shorter than the axon, branch outward from the soma.
#   Dendritic spines (where synapses form) are actin-based, not microtubule.
#
# [C-9] Xform rotation chains for bundle direction:
#
#   Each dendrite bundle sits inside its own Xform.
#   The PointInstancer inside places instances along +Y in LOCAL space.
#   The parent Xform rotates/translates the whole bundle into position.
#
#   Example — BasalDendrite1, rotateZ(-55°):
#     Local  Y unit vector  = (0, 1, 0)
#     After rotateZ(-55°)   = (sin 55°, cos 55°, 0) = (+0.82, +0.57, 0)
#     → bundle grows upward and to the +X side from the soma
#
#   The Xform op order matters:
#     1. rotateZ (applied first, in local space)
#     2. translate (applied after — moves the already-rotated bundle to soma)
#
#   In USD, ops are applied in declaration ORDER (bottom of stack → top):
#     AddTranslateOp → parent in the op stack → applied LAST in world space
#     AddRotateZOp   → child in the op stack  → applied FIRST in local space

print(f"\n[ Dendrite bundles: {DEND_N_CHAINS} chains × {DEND_N_SEGS} segs each ]")

# (name, rotateZ_deg, rotateX_deg, description)
DENDRITE_CONFIGS = [
    ("ApicalDendrite",  0.0,    0.0,   "straight up — apical trunk"),
    ("BasalDendrite1", -55.0,   0.0,   "upper-right basal branch"),
    ("BasalDendrite2", +55.0,   0.0,   "upper-left basal branch"),
    ("BasalDendrite3",  0.0,  -55.0,   "forward basal branch (toward -Z)"),
]

for (name, rz, rx, desc) in DENDRITE_CONFIGS:
    dend_xform = UsdGeom.Xform.Define(stage, f"/World/Microtubules/{name}")

    # USD evaluates Xform ops in declaration order (first declared = innermost).
    # We declare rotate BEFORE translate so the rotation happens in soma-local
    # space and the translate then moves the rotated bundle to the soma position.
    if rz != 0.0:
        dend_xform.AddRotateZOp().Set(rz)
    if rx != 0.0:
        dend_xform.AddRotateXOp().Set(rx)
    dend_xform.AddTranslateOp().Set(Gf.Vec3d(SOMA_X, SOMA_Y, SOMA_Z))

    build_bundle(
        stage,
        instancer_path=f"/World/Microtubules/{name}/Bundle",
        chain_xz=dend_xz,
        y_start=0.0,          # start at soma junction (local Y=0)
        n_segs=DEND_N_SEGS,
        mt_material=mt_mat,
    )
    print(f"      → {desc}")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  SAVE
# ─────────────────────────────────────────────────────────────────────────────
stage.Save()

print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  Scene saved: output/neuron_microtubules.usda
║
║  To view:
║    source /home/daniel/usd_root/python-usd-venv/bin/activate
║    cd /home/daniel/Documents/healthy_vs_alz
║    usdview output/neuron_microtubules.usda
║
║  Scene summary:
║    Neuron shell  — 1 reference, opacity={NEURON_OPACITY}, violet
║    Axon bundle   — {AXON_N_CHAINS} chains × {AXON_N_SEGS} segs = {AXON_N_CHAINS * AXON_N_SEGS} microtubule instances
║    Dendrites     — 4 bundles × {DEND_N_CHAINS} chains × {DEND_N_SEGS} segs = {4 * DEND_N_CHAINS * DEND_N_SEGS} instances
║    Materials     — NeuronMembrane + Microtubule (both UsdPreviewSurface)
╚══════════════════════════════════════════════════════════════════╝
""")
