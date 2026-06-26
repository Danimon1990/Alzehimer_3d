"""Create six long microtubule chains with one flattened PointInstancer.

This is the efficient pattern we will later bend along the neuron axon:

    one segment asset -> one prototype -> many positioned instances

Run from the project root:
    python neuron_usd/microtubule_bundle.py

Output:
    output/microtubule_bundle.usda
"""

import math

from pxr import Gf, Sdf, Usd, UsdGeom


# Paths authored inside output/microtubule_bundle.usda are relative to that file.
OUTPUT_PATH = "output/microtubule_bundle.usda"
SEGMENT_ASSET_PATH = "../assets/microtubules.usdc"

# The Blender segment is 5.916 units long on its local Z axis.
SEGMENT_STRIDE = 5.916
SEGMENTS_PER_CHAIN = 10

# Bundle layout: one center chain plus five chains around it.
OUTER_CHAIN_COUNT = 5
BUNDLE_RADIUS = 3.0


def create_chain_offsets():
    """Return the XZ offset of each complete chain in the bundle."""
    offsets = [Gf.Vec2f(0.0, 0.0)]

    for chain_index in range(OUTER_CHAIN_COUNT):
        angle = 2.0 * math.pi * chain_index / OUTER_CHAIN_COUNT
        offsets.append(
            Gf.Vec2f(
                BUNDLE_RADIUS * math.cos(angle),
                BUNDLE_RADIUS * math.sin(angle),
            )
        )

    return offsets


def create_instance_data():
    """Flatten six logical chains into PointInstancer attribute arrays."""
    positions = []
    orientations = []
    instance_ids = []

    for chain_index, offset in enumerate(create_chain_offsets()):
        for segment_index in range(SEGMENTS_PER_CHAIN):
            positions.append(
                Gf.Vec3f(
                    offset[0],
                    segment_index * SEGMENT_STRIDE,
                    offset[1],
                )
            )

            # Identity for now because every straight segment points along +Y.
            # In the neuron version, each value will rotate +Y onto the axon tangent.
            orientations.append(Gf.Quath(1.0, Gf.Vec3h(0.0, 0.0, 0.0)))

            # Stable IDs are useful for debugging and future time-sampled animation.
            instance_ids.append(chain_index * 1000 + segment_index)

    return positions, orientations, instance_ids


def build_stage():
    stage = Usd.Stage.CreateNew(OUTPUT_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    instancer = UsdGeom.PointInstancer.Define(stage, "/World/MicrotubuleBundle")

    # A PointInstancer stores geometry once in a prototype and transforms it many times.
    UsdGeom.Scope.Define(stage, "/World/MicrotubuleBundle/Prototypes")
    prototype_path = Sdf.Path("/World/MicrotubuleBundle/Prototypes/Segment")
    prototype = UsdGeom.Xform.Define(stage, prototype_path)
    prototype.GetPrim().GetReferences().AddReference(SEGMENT_ASSET_PATH)

    # Convert the Blender Z-up segment into this stage's Y-up coordinates once.
    prototype.AddRotateXOp().Set(-90.0)

    positions, orientations, instance_ids = create_instance_data()

    instancer.CreatePrototypesRel().SetTargets([prototype_path])
    instancer.CreateProtoIndicesAttr().Set([0] * len(positions))
    instancer.CreatePositionsAttr().Set(positions)
    instancer.CreateOrientationsAttr().Set(orientations)
    instancer.CreateIdsAttr().Set(instance_ids)

    stage.GetRootLayer().Save()
    return stage, positions


if __name__ == "__main__":
    _, generated_positions = build_stage()
    chain_count = OUTER_CHAIN_COUNT + 1
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Logical chains: {chain_count}")
    print(f"Segments per chain: {SEGMENTS_PER_CHAIN}")
    print(f"Total lightweight instances: {len(generated_positions)}")
