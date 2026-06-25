"""
microtubule_chain.py

Builds a vertical chain of microtubule segments using UsdGeomPointInstancer.
Output: output/microtubule_chain.usda

Key USD concepts demonstrated:
  - UsdGeomPointInstancer  : GPU-efficient N-copy instancing
  - Prototype pattern      : geometry lives inside /Prototypes, not rendered standalone
  - Coordinate correction  : asset is Z-up (Blender), scene is Y-up (USD default)
  - Separation of concerns : this script is an assembly layer, not the geometry layer
"""
from pxr import Usd, UsdGeom, Gf, Sdf

# ── Configuration ─────────────────────────────────────────────────────────────
STAGE_PATH    = "output/microtubule_chain.usda"
ASSET_PATH    = "../assets/microtubules.usdc"   # relative to the output layer

# Measured from the asset bounding box:
#   Mesh Z extent = -3.4659 to +2.4503  →  total length = 5.916 units
SEGMENT_STRIDE = 5.916   # world-space Y step between each instance pivot
INSTANCE_COUNT = 10

# ── Stage setup ───────────────────────────────────────────────────────────────
# ALWAYS call Stage.CreateNew before writing anything.
# Opening an existing stage with CreateNew will overwrite it — intentional here.
stage = Usd.Stage.CreateNew(STAGE_PATH)

# USD default up-axis is Y. Setting it explicitly makes the file self-documenting
# and lets Omniverse/usdview know how to orient the scene.
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

# World root — every production scene has one. SetDefaultPrim makes referencing
# this layer into another stage unambiguous (no need to specify a prim path).
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

# ── PointInstancer ────────────────────────────────────────────────────────────
# The instancer prim IS the chain. It holds three required arrays:
#   prototypes rel  : which geometry to copy
#   protoIndices[]  : one int per instance — which prototype to use (index into prototypes)
#   positions[]     : one Vec3f per instance — where to place the pivot
instancer = UsdGeom.PointInstancer.Define(stage, "/World/MicrotubuleChain")

# ── Prototypes scope ──────────────────────────────────────────────────────────
# USD convention: prototypes live INSIDE the instancer under a "Prototypes" scope.
# They are NOT rendered at their own position — the instancer handles all rendering.
# Think of this as a "template drawer": geometry is stored here, drawn elsewhere.
UsdGeom.Scope.Define(stage, "/World/MicrotubuleChain/Prototypes")

proto = UsdGeom.Xform.Define(stage, "/World/MicrotubuleChain/Prototypes/Segment")
proto.GetPrim().GetReferences().AddReference(ASSET_PATH)

# COORDINATE CORRECTION:
# The asset (microtubules.usdc) was exported from Blender with upAxis=Z.
# Our scene uses upAxis=Y. A -90° rotation around X maps asset-Z → scene-Y:
#   Rx(-90°): (x, y, z)  →  (x, z, -y)
#   So the Z-oriented segment becomes Y-oriented (pointing up in our scene).
proto.AddRotateXOp().Set(-90.0)

# ── Wire prototype to instancer ───────────────────────────────────────────────
PROTO_PATH = Sdf.Path("/World/MicrotubuleChain/Prototypes/Segment")
instancer.CreatePrototypesRel().SetTargets([PROTO_PATH])

# All 10 instances use prototype index 0 (we only have one prototype here).
# In a multi-prototype setup (e.g. healthy vs damaged segment), you'd vary these.
instancer.CreateProtoIndicesAttr().Set([0] * INSTANCE_COUNT)

# ── Instance positions ────────────────────────────────────────────────────────
# Stack along Y (up-axis). Each instance's pivot is offset by SEGMENT_STRIDE.
# Because the segment origin sits INSIDE the geometry (not at its base),
# instance 0 at Y=0 spans Y=-3.47..+2.45, instance 1 at Y=5.916 spans Y=2.45..8.37.
# They meet exactly end-to-end — stride == full Z/Y extent of the mesh.
positions = [Gf.Vec3f(0.0, i * SEGMENT_STRIDE, 0.0) for i in range(INSTANCE_COUNT)]
instancer.CreatePositionsAttr().Set(positions)

# ── Save ──────────────────────────────────────────────────────────────────────
stage.Save()

total_height = INSTANCE_COUNT * SEGMENT_STRIDE
print(f"Saved: {STAGE_PATH}")
print(f"Chain: {INSTANCE_COUNT} segments × {SEGMENT_STRIDE} = {total_height:.2f} units tall")
print(f"Prototype: {PROTO_PATH}")
