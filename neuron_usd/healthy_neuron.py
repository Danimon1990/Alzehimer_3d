"""
healthy_neuron.py
=================

Generate output/healthy_neuron.usda: a translucent neuron shell with
PointInstancer copies of output/microtubule_chain.usda inside the soma and axon.

Run from the project root:
    python neuron_usd/healthy_neuron.py

OpenUSD study notes:
  1. The neuron asset is a referenced layer, not copied geometry.
  2. The membrane material uses UsdPreviewSurface opacity so the internal
     microtubules remain visible.
  3. The microtubules are one PointInstancer prototype. Positions place each
     chain, orientations align the prototype's local +Y axis to the branch
     tangent, and scales keep the chain inside the neuron.
  4. Because assets/neuron_model.usda is one unnamed Blender mesh, identity is
     inferred from the silhouette: the long -Y process is the axon.
"""

from __future__ import annotations

import math
from pathlib import Path
from statistics import median


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "output" / "healthy_neuron.usda"

NEURON_REFERENCE = "../assets/neuron_model.usda"
MICROTUBULE_CHAIN_REFERENCE = "./microtubule_chain.usda"

# After rotating the Blender Z-up neuron by Rx(-90), the mesh occupies roughly:
# X -5.0..4.2, Y -20.5..3.9, Z -4.6..4.4.  The soma is the bulb around Y 0..3.
SOMA = (-0.35, 1.25, 0.0)
INSTANCE_SCALE = (0.075, 0.075, 0.075)
NEURON_SCALE = 1.15
MICROTUBULE_OFFSET = (0.0, 0.0, 0.0)


def fmt_float(value: float) -> str:
    if abs(value) < 1e-8:
        value = 0.0
    return f"{value:.6g}"


def fmt_vec(values: tuple[float, ...]) -> str:
    return "(" + ", ".join(fmt_float(value) for value in values) + ")"


def fmt_array(values: list[tuple[float, ...]]) -> str:
    return "[" + ", ".join(fmt_vec(value) for value in values) + "]"


def add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a: tuple[float, float, float]) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: tuple[float, float, float]) -> tuple[float, float, float]:
    size = length(a)
    if size < 1e-8:
        return (0.0, 1.0, 0.0)
    return (a[0] / size, a[1] / size, a[2] / size)


def normalize_quat(a: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    size = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2] + a[3] * a[3])
    if size < 1e-8:
        return (1.0, 0.0, 0.0, 0.0)
    return (a[0] / size, a[1] / size, a[2] / size, a[3] / size)


def frame_from_tangent(
    tangent: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    tangent = normalize(tangent)
    guide = (0.0, 0.0, 1.0)
    if abs(dot(tangent, guide)) > 0.92:
        guide = (1.0, 0.0, 0.0)

    normal = normalize(cross(guide, tangent))
    binormal = normalize(cross(tangent, normal))
    return normal, binormal


def quadratic_bezier(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    u = 1.0 - t
    return add(add(mul(p0, u * u), mul(p1, 2.0 * u * t)), mul(p2, t * t))


def tangent_on_bezier(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    return normalize(add(mul(sub(p1, p0), 2.0 * (1.0 - t)), mul(sub(p2, p1), 2.0 * t)))


def quat_from_y_axis(tangent: tuple[float, float, float]) -> tuple[float, float, float, float]:
    """Return quaternion (w, x, y, z) rotating local +Y onto tangent."""
    source = (0.0, 1.0, 0.0)
    target = normalize(tangent)
    cosine = max(-1.0, min(1.0, dot(source, target)))

    if cosine > 0.999999:
        return (1.0, 0.0, 0.0, 0.0)
    if cosine < -0.999999:
        return (0.0, 1.0, 0.0, 0.0)

    axis = cross(source, target)
    real = math.sqrt((1.0 + cosine) * 2.0) * 0.5
    inv = 1.0 / (2.0 * real)
    return normalize_quat((real, axis[0] * inv, axis[1] * inv, axis[2] * inv))


def sample_process(
    name: str,
    points: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    count: int,
    radial_offsets: list[tuple[float, float]],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float, float]], list[str]]:
    p0, p1, p2 = points
    positions: list[tuple[float, float, float]] = []
    orientations: list[tuple[float, float, float, float]] = []
    labels: list[str] = []

    for index in range(count):
        t = (index + 0.5) / count
        center = quadratic_bezier(p0, p1, p2, t)
        tangent = tangent_on_bezier(p0, p1, p2, t)
        quaternion = quat_from_y_axis(tangent)
        normal, binormal = frame_from_tangent(tangent)

        for offset_index, (offset_a, offset_b) in enumerate(radial_offsets):
            offset = add(mul(normal, offset_a), mul(binormal, offset_b))
            positions.append(add(center, offset))
            orientations.append(quaternion)
            labels.append(f"{name}_{index:02d}_{offset_index:02d}")

    return positions, orientations, labels


def sample_polyline_process(
    name: str,
    centerline: list[tuple[float, float, float]],
    radial_offsets: list[tuple[float, float]],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float, float]], list[str]]:
    positions: list[tuple[float, float, float]] = []
    orientations: list[tuple[float, float, float, float]] = []
    labels: list[str] = []

    for index, center in enumerate(centerline):
        if index == 0:
            tangent = sub(centerline[1], center)
        elif index == len(centerline) - 1:
            tangent = sub(center, centerline[index - 1])
        else:
            tangent = sub(centerline[index + 1], centerline[index - 1])

        normal, binormal = frame_from_tangent(tangent)
        quaternion = quat_from_y_axis(tangent)

        for offset_index, (offset_a, offset_b) in enumerate(radial_offsets):
            offset = add(mul(normal, offset_a), mul(binormal, offset_b))
            positions.append(add(center, offset))
            orientations.append(quaternion)
            labels.append(f"{name}_{index:02d}_{offset_index:02d}")

    return positions, orientations, labels


def resample_centerline(
    centerline: list[tuple[float, float, float]],
    count: int,
) -> list[tuple[float, float, float]]:
    if len(centerline) <= count:
        return centerline

    samples: list[tuple[float, float, float]] = []
    for index in range(count):
        source_index = round(index * (len(centerline) - 1) / (count - 1))
        samples.append(centerline[source_index])
    return samples


def load_neuron_world_points() -> list[tuple[float, float, float]]:
    try:
        from pxr import Usd, UsdGeom
    except ImportError:
        return []

    stage = Usd.Stage.Open(str(PROJECT_ROOT / "assets" / "neuron_model.usda"))
    if stage is None:
        return []

    world_points: list[tuple[float, float, float]] = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue

        mesh_points = UsdGeom.Mesh(prim).GetPointsAttr().Get() or []
        for point in mesh_points:
            # The referenced shell uses Rx(-90): Blender Z becomes USD Y.
            world_points.append((
                float(point[0]) * NEURON_SCALE,
                float(point[2]) * NEURON_SCALE,
                float(-point[1]) * NEURON_SCALE,
            ))

    return world_points


def axon_centerline_from_mesh(points: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    if not points:
        return [
            mul(SOMA, NEURON_SCALE),
            (-0.65, -7.5, 0.35),
            (-0.55, -18.9, 0.2),
        ]

    y_min = min(point[1] for point in points)
    y_max = min(-0.8, max(point[1] for point in points))
    steps = 16
    centerline: list[tuple[float, float, float]] = []
    previous: tuple[float, float] | None = None

    for step in range(steps):
        t = step / (steps - 1)
        y_value = y_max * (1.0 - t) + (y_min + 1.2) * t
        band = [point for point in points if abs(point[1] - y_value) < 0.45]
        if len(band) < 20:
            band = sorted(points, key=lambda point: abs(point[1] - y_value))[:120]

        if previous is not None:
            band = sorted(
                band,
                key=lambda point: (point[0] - previous[0]) * (point[0] - previous[0])
                + (point[2] - previous[1]) * (point[2] - previous[1]),
            )[: max(30, len(band) // 3)]

        x_values = sorted(point[0] for point in band)
        z_values = sorted(point[2] for point in band)
        center = (median(x_values), y_value, median(z_values))
        if centerline:
            last = centerline[-1]
            center = (last[0] * 0.35 + center[0] * 0.65, center[1], last[2] * 0.35 + center[2] * 0.65)

        centerline.append(center)
        previous = (center[0], center[2])

    return centerline


def material_block(name: str, color: tuple[float, float, float], opacity: float, roughness: float, emissive: tuple[float, float, float] | None = None) -> str:
    emissive_line = ""
    if emissive is not None:
        emissive_line = f"\n                color3f inputs:emissiveColor = {fmt_vec(emissive)}"

    return f"""        def Material "{name}"
        {{
            token outputs:surface.connect = </World/Materials/{name}/Shader.outputs:surface>

            def Shader "Shader"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = {fmt_vec(color)}{emissive_line}
                float inputs:opacity = {fmt_float(opacity)}
                float inputs:roughness = {fmt_float(roughness)}
                float inputs:metallic = 0
                token outputs:surface
            }}
        }}"""


def build_usda() -> str:
    axon_offsets = [
        (0.0, 0.0),
        (0.12, 0.0),
        (-0.12, 0.0),
        (0.0, 0.12),
        (0.0, -0.12),
        (0.085, 0.085),
        (-0.085, -0.085),
    ]
    soma_offsets = [
        (0.0, 0.0),
        (0.18, 0.0),
        (-0.18, 0.0),
        (0.0, 0.18),
        (0.0, -0.18),
        (0.13, 0.13),
        (-0.13, 0.13),
        (0.13, -0.13),
        (-0.13, -0.13),
    ]
    neuron_points = load_neuron_world_points()
    axon_centerline = resample_centerline(axon_centerline_from_mesh(neuron_points), 6)

    positions: list[tuple[float, float, float]] = []
    orientations: list[tuple[float, float, float, float]] = []
    branch_positions, branch_orientations, _ = sample_polyline_process("Axon", axon_centerline, axon_offsets)
    positions.extend(branch_positions)
    orientations.extend(branch_orientations)

    soma_centerline = [
        mul(SOMA, NEURON_SCALE),
        add(mul(SOMA, NEURON_SCALE), (0.0, -0.85, 0.0)),
    ]
    branch_positions, branch_orientations, _ = sample_polyline_process("Soma", soma_centerline, soma_offsets)
    positions.extend(branch_positions)
    orientations.extend(branch_orientations)
    positions = [add(position, MICROTUBULE_OFFSET) for position in positions]

    proto_indices = ", ".join("0" for _ in positions)
    scales = ", ".join(fmt_vec(INSTANCE_SCALE) for _ in positions)

    return f"""#usda 1.0
(
    defaultPrim = "World"
    doc = "Healthy neuron with point-instanced references to output/microtubule_chain.usda inside the soma and axon."
    metersPerUnit = 0.000001
    upAxis = "Y"
)

def Xform "World"
{{
    def Scope "Materials"
    {{
{material_block("NeuronMembrane", (0.56, 0.38, 0.78), 0.18, 0.18)}

{material_block("MicrotubuleGlow", (0.08, 0.92, 0.48), 1.0, 0.32, (0.01, 0.18, 0.08))}
    }}

    def Xform "NeuronShell" (
        prepend apiSchemas = ["MaterialBindingAPI"]
        prepend references = @{NEURON_REFERENCE}@
    )
    {{
        rel material:binding = </World/Materials/NeuronMembrane>
        double3 xformOp:translate = (0, 0, 0)
        float xformOp:rotateX = -90
        float3 xformOp:scale = ({fmt_float(NEURON_SCALE)}, {fmt_float(NEURON_SCALE)}, {fmt_float(NEURON_SCALE)})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateX", "xformOp:scale"]

        over "env_light" (
            active = false
        )
        {{
        }}
    }}

    def PointInstancer "MicrotubuleChains"
    {{
        point3f[] positions = {fmt_array(positions)}
        quath[] orientations = {fmt_array(orientations)}
        float3[] scales = [{scales}]
        int[] protoIndices = [{proto_indices}]
        rel prototypes = </World/MicrotubuleChains/Prototypes/HealthyChain>

        def Scope "Prototypes"
        {{
            def Xform "HealthyChain" (
                prepend apiSchemas = ["MaterialBindingAPI"]
                prepend references = @{MICROTUBULE_CHAIN_REFERENCE}@
            )
            {{
                rel material:binding = </World/Materials/MicrotubuleGlow>
            }}
        }}
    }}

    def DistantLight "KeyLight"
    {{
        float inputs:angle = 0.45
        float inputs:intensity = 650
        float3 xformOp:rotateXYZ = (-45, 25, 15)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def DomeLight "SoftFill"
    {{
        color3f inputs:color = (0.08, 0.09, 0.11)
        float inputs:intensity = 80
    }}

    def Camera "Camera"
    {{
        double3 xformOp:translate = (9, 12, 26)
        float3 xformOp:rotateXYZ = (-58, 18, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
        float focalLength = 55
    }}
}}
"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_usda(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
