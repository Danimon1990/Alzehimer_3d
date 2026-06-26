"""Build one bundle of six parallel, instanceable microtubule chains.

Run from the project root:
    python neuron_usd/hexa-tubules.py

Output:
    output/hexa-tubules.usda
"""

import math

from pxr import Gf, Sdf, Usd, UsdGeom


STAGE_PATH = "output/hexa-tubules.usda"
CHAIN_ASSET_PATH = "./microtubule_chain.usda"
CHAIN_PRIM_PATH = Sdf.Path("/World/MicrotubuleChain")

RING_INSTANCE_COUNT = 5
RING_RADIUS = 3.0


def create_bundle_positions():
    """Return one center position plus five positions on an XZ circle."""
    positions = [Gf.Vec3f(0.0, 0.0, 0.0)]

    for index in range(RING_INSTANCE_COUNT):
        angle = (2.0 * math.pi * index) / RING_INSTANCE_COUNT
        x = RING_RADIUS * math.cos(angle)
        z = RING_RADIUS * math.sin(angle)
        positions.append(Gf.Vec3f(x, 0.0, z))

    return positions


def add_chain_reference(stage, prim_path, position):
    """Create one lightweight instance of the complete chain asset."""
    chain_prim = stage.DefinePrim(prim_path)
    chain_prim.GetReferences().AddReference(
        CHAIN_ASSET_PATH,
        CHAIN_PRIM_PATH,
    )
    UsdGeom.Xformable(chain_prim).AddTranslateOp().Set(Gf.Vec3d(position))

    # USD creates and shares an implicit prototype for matching instanceable prims.
    chain_prim.SetInstanceable(True)
    return chain_prim


def build_stage():
    stage = Usd.Stage.CreateNew(STAGE_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    UsdGeom.Xform.Define(stage, "/World/HexaTubules")
    positions = create_bundle_positions()

    for index, position in enumerate(positions):
        name = "CenterChain" if index == 0 else f"RingChain_{index:02d}"
        add_chain_reference(
            stage,
            f"/World/HexaTubules/{name}",
            position,
        )

    stage.GetRootLayer().Save()
    return stage, positions


if __name__ == "__main__":
    _, bundle_positions = build_stage()
    print(f"Saved: {STAGE_PATH}")
    print(f"Chain instances: {len(bundle_positions)} (1 center + 5 around it)")
    print(f"Ring radius: {RING_RADIUS}")
