"""Create a lightweight neuron whose paths can drive microtubule instancing.

The visible membrane curves and hidden guide curves use identical points. This
centerline-first design guarantees that later microtubules follow the neuron.

Run:
    python neuron_usd/structured_neuron.py
"""

import math

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


OUTPUT_PATH = "output/structured_neuron.usda"
SOMA_RADIUS = 10.0
AXON_LENGTH = 120.0
AXON_SAMPLE_SPACING = 5.916
DENDRITE_COUNT = 8


def lerp(start, end, amount):
    return start + (end - start) * amount


def create_material(stage):
    material = UsdShade.Material.Define(stage, "/World/Neuron/Looks/CellMembrane")
    shader = UsdShade.Shader.Define(
        stage, "/World/Neuron/Looks/CellMembrane/PreviewSurface"
    )
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.32, 0.12, 0.48)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.38)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.32)
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.38)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def create_curve(stage, path, points, widths, material=None, purpose=None):
    curve = UsdGeom.BasisCurves.Define(stage, path)
    curve.CreateTypeAttr(UsdGeom.Tokens.linear)
    curve.CreateWrapAttr(UsdGeom.Tokens.nonperiodic)
    curve.CreateCurveVertexCountsAttr([len(points)])
    curve.CreatePointsAttr(points)
    curve.CreateWidthsAttr(widths)
    curve.SetWidthsInterpolation(UsdGeom.Tokens.vertex)

    if purpose:
        curve.CreatePurposeAttr(purpose)
    if material:
        UsdShade.MaterialBindingAPI.Apply(curve.GetPrim()).Bind(material)

    return curve


def create_visible_and_guide(stage, name, points, widths, material, role):
    visible_path = f"/World/Neuron/Neurites/{name}"
    guide_path = f"/World/Guides/{name}"

    create_curve(stage, visible_path, points, widths, material=material)
    guide = create_curve(
        stage,
        guide_path,
        points,
        [0.15] * len(points),
        purpose=UsdGeom.Tokens.guide,
    )
    guide.GetPrim().CreateAttribute("neuron:role", Sdf.ValueTypeNames.Token).Set(role)


def create_straight_axon(stage, material):
    sample_count = math.ceil(AXON_LENGTH / AXON_SAMPLE_SPACING) + 1
    points = []
    widths = []

    for index in range(sample_count):
        distance = min(index * AXON_SAMPLE_SPACING, AXON_LENGTH)
        points.append(Gf.Vec3f(0.0, -SOMA_RADIUS - distance, 0.0))
        widths.append(lerp(5.2, 3.4, distance / AXON_LENGTH))

    create_visible_and_guide(stage, "Axon", points, widths, material, "axon")


def create_dendrites(stage, material):
    for dendrite_index in range(DENDRITE_COUNT):
        angle = 2.0 * math.pi * dendrite_index / DENDRITE_COUNT
        radial = Gf.Vec3f(math.cos(angle), 0.0, math.sin(angle))
        vertical_sign = 1.0 if dendrite_index % 2 == 0 else -1.0

        primary_points = []
        for sample_index in range(9):
            t = sample_index / 8.0
            radius = SOMA_RADIUS * 0.78 + 38.0 * t
            bend = math.sin(math.pi * t) * (4.0 + dendrite_index % 3)
            primary_points.append(
                Gf.Vec3f(
                    radial[0] * radius,
                    vertical_sign * (5.0 * t + bend),
                    radial[2] * radius,
                )
            )

        primary_widths = [lerp(4.2, 1.2, index / 8.0) for index in range(9)]
        primary_name = f"Dendrite_{dendrite_index:02d}_Primary"
        create_visible_and_guide(
            stage, primary_name, primary_points, primary_widths, material, "dendrite"
        )

        branch_origin = primary_points[5]
        for branch_index, branch_turn in enumerate((-0.42, 0.42)):
            branch_angle = angle + branch_turn
            branch_direction = Gf.Vec3f(
                math.cos(branch_angle),
                0.0,
                math.sin(branch_angle),
            )
            branch_points = []
            for sample_index in range(6):
                t = sample_index / 5.0
                branch_points.append(
                    branch_origin
                    + branch_direction * (24.0 * t)
                    + Gf.Vec3f(0.0, vertical_sign * 7.0 * t, 0.0)
                )
            branch_widths = [lerp(2.0, 0.65, index / 5.0) for index in range(6)]
            branch_name = f"Dendrite_{dendrite_index:02d}_Branch_{branch_index:02d}"
            create_visible_and_guide(
                stage, branch_name, branch_points, branch_widths, material, "dendrite"
            )


def create_axon_collaterals(stage, material):
    for collateral_index, distance in enumerate((36.0, 72.0)):
        direction = -1.0 if collateral_index == 0 else 1.0
        points = []
        for sample_index in range(7):
            t = sample_index / 6.0
            points.append(
                Gf.Vec3f(
                    direction * 32.0 * t,
                    -SOMA_RADIUS - distance - 8.0 * t,
                    math.sin(math.pi * t) * 5.0,
                )
            )
        widths = [lerp(2.4, 0.8, index / 6.0) for index in range(7)]
        name = f"AxonCollateral_{collateral_index:02d}"
        create_visible_and_guide(stage, name, points, widths, material, "axonCollateral")


def build_stage():
    stage = Usd.Stage.CreateNew(OUTPUT_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Xform.Define(stage, "/World/Neuron")
    UsdGeom.Scope.Define(stage, "/World/Neuron/Neurites")
    UsdGeom.Scope.Define(stage, "/World/Guides")
    UsdGeom.Scope.Define(stage, "/World/Neuron/Looks")

    material = create_material(stage)

    soma = UsdGeom.Sphere.Define(stage, "/World/Neuron/Soma")
    soma.CreateRadiusAttr(SOMA_RADIUS)
    soma.AddScaleOp().Set(Gf.Vec3f(1.12, 0.92, 1.04))
    UsdShade.MaterialBindingAPI.Apply(soma.GetPrim()).Bind(material)

    create_straight_axon(stage, material)
    create_dendrites(stage, material)
    create_axon_collaterals(stage, material)

    stage.GetRootLayer().Save()
    return stage


if __name__ == "__main__":
    build_stage()
    print(f"Saved: {OUTPUT_PATH}")
    print("Straight axon: 120 units")
    print("Dendrites: 8 primary paths, each with 2 branches")
    print("Axon collaterals: 2")
    print("Every visible neurite has a matching /World/Guides centerline")
