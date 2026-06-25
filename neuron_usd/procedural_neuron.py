"""Emit a single-neuron USDA layer (BasisCurves + PreviewSurface materials)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from neuron_usd.usd_emit import fmt_points, fmt_vec3f, fmt_widths, indent_block, join_lines


@dataclass(frozen=True)
class NeuronBuildSpec:
    source_comment: str
    default_prim: str
    root_prim: str
    custom_data_block: str
    soma_radius: float
    dendrite_primaries: int
    primary_points: int
    secondary_points: int
    spines_per_secondary: int
    axon_segments: int
    axon_z_start: float
    axon_segment_len: float
    bouton_count: int
    propagation_speed_ms: float
    bouton_rootlets_per_bouton: int = 5


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _bezier_linear_points(
    rng: random.Random,
    start: tuple[float, float, float],
    n: int,
    spread: float,
    bias: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    pts = [start]
    x, y, z = start
    bx, by, bz = bias
    for _ in range(n - 1):
        x += bx + rng.uniform(-spread, spread)
        y += by + rng.uniform(-spread, spread)
        z += bz + rng.uniform(-spread * 0.35, spread * 0.35)
        pts.append((x, y, z))
    return pts


def _taper_widths(n: float, base: float, tip: float) -> list[float]:
    if n < 2:
        return [base]
    return [base + (tip - base) * (i / (n - 1)) for i in range(int(n))]


def _basis_curve_block(
    name: str,
    material_path: str,
    points: list[tuple[float, float, float]],
    widths: list[float],
    indent: str = "        ",
    *,
    close: bool = True,
) -> str:
    n = len(points)
    i2 = indent + "    "
    tail = f"{indent}}}" if close else ""
    return f'''{indent}def BasisCurves "{name}" (
{i2}prepend apiSchemas = ["MaterialBindingAPI"]
{indent})
{indent}{{
{i2}uniform token basis = "bezier"
{i2}int[] curveVertexCounts = [{n}]
{i2}rel material:binding = <{material_path}> (
{i2}    bindMaterialAs = "strongerThanDescendants"
{i2})
{i2}point3f[] points = {fmt_points(points)}
{i2}uniform token type = "linear"
{i2}float[] widths = {fmt_widths(widths)} (
{i2}    interpolation = "vertex"
{i2})
{i2}uniform token wrap = "nonperiodic"
{tail}'''


def _sphere_block(
    name: str,
    material_path: str,
    radius: float,
    translate: tuple[float, float, float],
    indent: str = "                ",
) -> str:
    i2 = indent + "    "
    return f'''{indent}def Sphere "{name}" (
{i2}prepend apiSchemas = ["MaterialBindingAPI"]
{indent})
{indent}{{
{i2}rel material:binding = <{material_path}> (
{i2}    bindMaterialAs = "strongerThanDescendants"
{i2})
{i2}double radius = {radius}
{i2}double3 xformOp:translate = {fmt_vec3f(*translate)}
{i2}uniform token[] xformOpOrder = ["xformOp:translate"]
{indent}}}'''


def _emit_dendrites(
    rng: random.Random,
    spec: NeuronBuildSpec,
    membrane_path: str,
) -> str:
    primaries: list[str] = []
    r = spec.soma_radius
    for pi in range(spec.dendrite_primaries):
        ang = 2 * math.pi * (pi / spec.dendrite_primaries) + rng.uniform(-0.2, 0.2)
        start = (r * 0.85 * math.cos(ang), r * 0.12, r * 0.85 * math.sin(ang))
        bias = (
            rng.uniform(0.4, 1.1) * math.cos(ang),
            rng.uniform(0.1, 0.6),
            rng.uniform(0.4, 1.1) * math.sin(ang),
        )
        ppts = _bezier_linear_points(rng, start, spec.primary_points, 2.8, bias)
        pw = _taper_widths(float(len(ppts)), 1.5, 0.3)
        head = _basis_curve_block(
            f"Primary_{pi:02d}", membrane_path, ppts, pw, indent="        ", close=False
        )
        inner: list[str] = []
        n_sec = 2 if rng.random() < 0.9 else 1
        for si in range(n_sec):
            sstart = ppts[-1]
            sbias = (rng.uniform(-0.8, 0.8), rng.uniform(0.2, 1.0), rng.uniform(-0.8, 0.8))
            spts = _bezier_linear_points(rng, sstart, spec.secondary_points, 1.9, sbias)
            sw = _taper_widths(float(len(spts)), 0.825, 0.3)
            sec_blk = _basis_curve_block(
                f"Secondary_{si:02d}", membrane_path, spts, sw, indent="            ", close=False
            )
            spines = []
            for sp in range(spec.spines_per_secondary):
                t = spts[-1]
                off = (
                    t[0] + rng.uniform(-0.8, 0.8),
                    t[1] + rng.uniform(-0.6, 0.6),
                    t[2] + rng.uniform(-0.8, 0.8),
                )
                spines.append(_sphere_block(f"Spine_{sp:02d}", membrane_path, 0.45, off, indent="                "))
            inner.append(sec_blk + "\n" + "\n".join(spines) + "\n            }")
        if inner:
            prim_block = head + "\n" + "\n".join(inner) + "\n        }"
        else:
            prim_block = head + "\n        }"
        primaries.append(prim_block)
    body = "\n\n".join(primaries)
    return f'''    def Scope "Dendrites" (
        customData = {{
            string receptor_type = "AMPA"
            int synapse_count = {12 + spec.dendrite_primaries * 3}
        }}
    )
    {{
{body}
    }}'''


def _emit_bouton_rootlets(
    rng: random.Random,
    spec: NeuronBuildSpec,
    curve_material_path: str,
    bouton_centers: list[tuple[float, float, float]],
) -> str:
    """Short, twisty branches from each bouton (filopodia / synaptic fringe; visual only).

    Uses the same material as the bouton sphere so the cluster reads as one terminal arbor.
    """
    n_per = spec.bouton_rootlets_per_bouton
    if n_per <= 0 or not bouton_centers:
        return ""
    bouton_radius = 2.2
    prim_n = 6
    sec_n = 3
    primaries: list[str] = []
    for bi, center in enumerate(bouton_centers):
        for rj in range(n_per):
            theta = 2 * math.pi * (rj / max(1, n_per)) + rng.uniform(-0.45, 0.45)
            dip = rng.uniform(0.4, 0.98)
            nx = math.cos(theta) * (0.55 + 0.45 * (1.0 - dip))
            ny = -dip + rng.uniform(-0.2, 0.12)
            nz = math.sin(theta) * (0.55 + 0.45 * (1.0 - dip)) + rng.uniform(-0.4, 0.4)
            il = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
            nx, ny, nz = nx * il, ny * il, nz * il
            start = (
                center[0] + nx * bouton_radius,
                center[1] + ny * bouton_radius,
                center[2] + nz * bouton_radius,
            )
            bias = (
                rng.uniform(-0.14, 0.14),
                rng.uniform(-0.32, 0.04),
                rng.uniform(-0.14, 0.14),
            )
            ppts = _bezier_linear_points(rng, start, prim_n, 3.8, bias)
            pw = _taper_widths(float(len(ppts)), 0.58, 0.09)
            head = _basis_curve_block(
                f"Rootlet_{bi:02d}_{rj:02d}", curve_material_path, ppts, pw, indent="        ", close=False
            )
            inner: list[str] = []
            n_sec = 2 if rng.random() < 0.72 else 1
            for si in range(n_sec):
                sstart = ppts[-1]
                sbias = (
                    rng.uniform(-0.22, 0.22),
                    rng.uniform(-0.38, 0.06),
                    rng.uniform(-0.22, 0.22),
                )
                spts = _bezier_linear_points(rng, sstart, sec_n, 2.45, sbias)
                sw = _taper_widths(float(len(spts)), 0.32, 0.07)
                sec_blk = _basis_curve_block(
                    f"RootSec_{bi:02d}_{rj:02d}_{si:02d}",
                    curve_material_path,
                    spts,
                    sw,
                    indent="            ",
                    close=False,
                )
                inner.append(sec_blk + "\n            }")
            if inner:
                primaries.append(head + "\n" + "\n".join(inner) + "\n        }")
            else:
                primaries.append(head + "\n        }")
    body = "\n\n".join(primaries)
    n_roots = len(bouton_centers) * n_per
    return f'''    def Scope "BoutonRootlets" (
        customData = {{
            string role = "bouton_rootlets"
            int rootlet_count = {n_roots}
        }}
    )
    {{
{body}
    }}'''


def _emit_axon(
    spec: NeuronBuildSpec,
    root_path: str,
    rng: random.Random,
    membrane_path: str,
) -> str:
    mats = f"{root_path}/Materials"
    segs: list[str] = []
    mye: list[str] = []
    z0 = spec.axon_z_start
    L = spec.axon_segment_len
    for i in range(spec.axon_segments):
        z_a = z0 + i * L
        z_b = z_a + L
        myelinated = i % 3 != 2
        w0 = 1.2 - (1.2 - 0.55) * (i / max(1, spec.axon_segments - 1))
        w1 = 1.2 - (1.2 - 0.55) * ((i + 1) / max(1, spec.axon_segments - 1))
        segs.append(
            f'''        def BasisCurves "Segment_{i:02d}" (
            prepend apiSchemas = ["MaterialBindingAPI"]
            customData = {{
                double delay_offset_ms = {i * (1000.0 * L / spec.propagation_speed_ms):.1f}
                bool is_myelinated = {1 if myelinated else 0}
                int segment_index = {i}
            }}
        )
        {{
            uniform token basis = "bezier"
            int[] curveVertexCounts = [2]
            rel material:binding = <{mats}/PulseSeg_{i:02d}> (
                bindMaterialAs = "strongerThanDescendants"
            )
            point3f[] points = [(-0, -0, {z_a:.2f}), (-0, -0, {z_b:.2f})]
            uniform token type = "linear"
            float[] widths = [{w0:.7f}, {w1:.7f}] (
                interpolation = "vertex"
            )
            uniform token wrap = "nonperiodic"
        }}'''
        )
        if myelinated:
            mw0 = w0 * 1.55
            mw1 = w1 * 1.55
            mi = len(mye)
            mye.append(
                f'''        def BasisCurves "Myelin_{mi:02d}" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {{
            uniform token basis = "bezier"
            int[] curveVertexCounts = [2]
            rel material:binding = <{mats}/MyelinMat> (
                bindMaterialAs = "strongerThanDescendants"
            )
            point3f[] points = [(-0, -0, {z_a:.2f}), (-0, -0, {z_b:.2f})]
            uniform token type = "linear"
            float[] widths = [{mw0:.7f}, {mw1:.7f}] (
                interpolation = "vertex"
            )
            uniform token wrap = "nonperiodic"
        }}'''
            )

    z_end = z0 + spec.axon_segments * L
    boutons: list[str] = []
    bouton_centers: list[tuple[float, float, float]] = []
    for bi in range(spec.bouton_count):
        ang = 2 * math.pi * (bi / max(1, spec.bouton_count)) + rng.uniform(-0.3, 0.3)
        tr = (
            rng.uniform(-1.8, 1.8) + 0.4 * math.cos(ang),
            rng.uniform(-1.8, 1.8) + 0.2 * math.sin(ang),
            z_end + rng.uniform(-1.5, 2.5),
        )
        bouton_centers.append(tr)
        boutons.append(
            f'''        def Sphere "Bouton_{bi:02d}" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {{
            rel material:binding = <{mats}/TerminalFiredMat> (
                bindMaterialAs = "strongerThanDescendants"
            )
            double radius = 2.2
            double3 xformOp:translate = {fmt_vec3f(*tr)}
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }}'''
        )

    rootlets = _emit_bouton_rootlets(rng, spec, f"{mats}/TerminalFiredMat", bouton_centers)

    return join_lines(
        [
            f'''    def Scope "Axon"
    {{
{join_lines(segs)}

{join_lines(mye)}
    }}''',
            f'''    def Scope "AxonTerminals"
    {{
{join_lines(boutons)}
    }}''',
            rootlets,
        ]
    )


def _emit_materials(root_path: str, n_pulse: int) -> str:
    mats = f"{root_path}/Materials"
    pulse_blocks: list[str] = []
    for i in range(n_pulse):
        pulse_blocks.append(
            f'''        def Material "PulseSeg_{i:02d}"
        {{
            token outputs:surface.connect = <{mats}/PulseSeg_{i:02d}/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.7, 0.7, 0.85)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.35
                token outputs:surface
            }}
        }}'''
        )
    pulses = "\n\n".join(pulse_blocks)
    return f'''    def Scope "Materials"
    {{
        def Material "NeuronMembraneMat"
        {{
            token outputs:surface.connect = <{mats}/NeuronMembraneMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.85, 0.75, 0.6)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.6
                token outputs:surface
            }}
        }}

        def Material "AxonMat"
        {{
            token outputs:surface.connect = <{mats}/AxonMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.7, 0.7, 0.85)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.4
                token outputs:surface
            }}
        }}

        def Material "MyelinMat"
        {{
            token outputs:surface.connect = <{mats}/MyelinMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.88, 0.93, 1)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 0.3
                float inputs:roughness = 0.2
                token outputs:surface
            }}
        }}

        def Material "PulseMat"
        {{
            token outputs:surface.connect = <{mats}/PulseMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.7, 0.7, 0.85)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.35
                token outputs:surface
            }}
        }}

        def Material "TerminalFiredMat"
        {{
            token outputs:surface.connect = <{mats}/TerminalFiredMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.7, 0.7, 0.85)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.35
                token outputs:surface
            }}
        }}

{pulses}
    }}'''


def emit_neuron_usda(spec: NeuronBuildSpec, seed: int) -> str:
    rng = _rng(seed)
    root = spec.root_prim
    root_path = f"/{root}"
    membrane_path = f"{root_path}/Materials/NeuronMembraneMat"

    soma = f'''    def Sphere "Soma" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        rel material:binding = <{membrane_path}> (
            bindMaterialAs = "strongerThanDescendants"
        )
        double radius = {spec.soma_radius}
        float3 xformOp:scale = (1.0, 1.0, 1.0)
        double3 xformOp:translate = (0, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }}'''

    dend = _emit_dendrites(rng, spec, membrane_path)
    axon = _emit_axon(spec, root_path, rng, membrane_path)
    mats = _emit_materials(root_path, spec.axon_segments)

    body = join_lines([soma, dend, axon, mats])

    header = f'''#usda 1.0
# Live-updated by {spec.source_comment}
(
    defaultPrim = "{spec.default_prim}"
    endTimeCode = 120
    metersPerUnit = 0.01
    startTimeCode = 0
    timeCodesPerSecond = 24
    upAxis = "Y"
)

def Xform "{root}" (
{indent_block(spec.custom_data_block.strip(), 1)}
)
{{
{body}
}}'''
    return header


def default_spec_for(kind: str) -> NeuronBuildSpec:
    """Presets aligned with labels used in output/*.usda metadata."""
    common = dict(
        source_comment="neuron_usd/main.py",
        dendrite_primaries=4,
        primary_points=8,
        secondary_points=6,
        spines_per_secondary=2,
        axon_segments=12,
        axon_z_start=14.25,
        axon_segment_len=10.0,
        bouton_count=4,
        bouton_rootlets_per_bouton=5,
    )
    if kind == "pyramidal":
        return NeuronBuildSpec(
            **common,
            default_prim="Neuron",
            root_prim="Neuron",
            custom_data_block='''customData = {
        string neuron_type = "pyramidal"
        double propagation_speed_ms = 80
        double refractory_period_ms = 2
        double signal_threshold = 0.65
        string species = "human"
    }''',
            soma_radius=15,
            propagation_speed_ms=80.0,
        )
    if kind == "bilateral":
        return NeuronBuildSpec(
            **common,
            default_prim="BilateralNeuron",
            root_prim="BilateralNeuron",
            custom_data_block='''customData = {
        string neuron_type = "multipolar_bilateral"
        double propagation_speed_ms = 75
        double refractory_period_ms = 2.5
        double signal_threshold = 0.6
        string species = "human"
    }''',
            soma_radius=18,
            propagation_speed_ms=75.0,
        )
    if kind == "multipolar":
        return NeuronBuildSpec(
            **common,
            default_prim="MultipolarNeuron",
            root_prim="MultipolarNeuron",
            custom_data_block='''customData = {
        string neuron_type = "multipolar"
        double propagation_speed_ms = 75
        double refractory_period_ms = 2.5
        double signal_threshold = 0.6
        string species = "human"
    }''',
            soma_radius=18,
            propagation_speed_ms=75.0,
        )
    raise ValueError(f"unknown kind {kind!r}")


def msn_spec(variant: str) -> NeuronBuildSpec:
    pathway = "striatopallidal" if variant == "msn" else "striatonigral"
    subtype = "D1_direct_pathway" if variant == "msn" else "D2_indirect_pathway"
    return NeuronBuildSpec(
        source_comment="neuron_usd/msn_builder.py",
        default_prim="MediumSpinyNeuron",
        root_prim="MediumSpinyNeuron",
        custom_data_block=f'''customData = {{
        string circuit_role = "striatal_projection"
        string neuron_type = "medium_spiny_neuron"
        string neurotransmitter = "GABA"
        string projection_type = "{pathway}"
        double propagation_speed_ms = 35
        string receptor_type = "AMPA_NMDA_D1"
        double refractory_period_ms = 2.5
        double signal_threshold = 0.7
        string species = "human"
        string subtype = "{subtype}"
        string target_structure = "globus_pallidus"
    }}''',
        soma_radius=10,
        dendrite_primaries=5,
        primary_points=7,
        secondary_points=5,
        spines_per_secondary=3,
        axon_segments=12,
        axon_z_start=12.0,
        axon_segment_len=8.5,
        bouton_count=5,
        bouton_rootlets_per_bouton=5,
        propagation_speed_ms=35.0,
    )


def cortical_spec() -> NeuronBuildSpec:
    return NeuronBuildSpec(
        source_comment="neuron_usd/cortical_pyramidal_builder.py",
        default_prim="CorticalPyramidal",
        root_prim="CorticalPyramidal",
        custom_data_block='''customData = {
        string circuit_role = "cortical_input"
        string neuron_type = "cortical_pyramidal"
        string projection_type = "corticostriatal"
        double propagation_speed_ms = 70
        double refractory_period_ms = 1.8
        double signal_threshold = 0.55
        string species = "human"
        string target_structure = "striatum"
    }''',
        soma_radius=14,
        dendrite_primaries=4,
        primary_points=8,
        secondary_points=6,
        spines_per_secondary=2,
        axon_segments=12,
        axon_z_start=13.5,
        axon_segment_len=9.0,
        bouton_count=4,
        bouton_rootlets_per_bouton=5,
        propagation_speed_ms=70.0,
    )


def neuron_with_dendrites_spec() -> NeuronBuildSpec:
    """Pyramidal preset with extra bouton rootlets (same as default_spec_for today)."""
    base = default_spec_for("pyramidal")
    return NeuronBuildSpec(
        source_comment="neuron_usd/procedural_neuron.py",
        default_prim=base.default_prim,
        root_prim=base.root_prim,
        custom_data_block=base.custom_data_block,
        soma_radius=base.soma_radius,
        dendrite_primaries=base.dendrite_primaries,
        primary_points=base.primary_points,
        secondary_points=base.secondary_points,
        spines_per_secondary=base.spines_per_secondary,
        axon_segments=base.axon_segments,
        axon_z_start=base.axon_z_start,
        axon_segment_len=base.axon_segment_len,
        bouton_count=base.bouton_count,
        propagation_speed_ms=base.propagation_speed_ms,
        bouton_rootlets_per_bouton=8,
    )


