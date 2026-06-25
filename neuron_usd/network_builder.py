"""Compose a compact NeuralNetwork scene from referenced neuron layers + routing visuals."""

from __future__ import annotations

import argparse
from pathlib import Path

# Camera + synapse routing taken from the prior monolithic export (parity demo).
_CAMERA = """    def Camera "Camera"
    {
        float2 clippingRange = (0.01, 10000000)
        float focalLength = 18.147562
        float focusDistance = 400
        custom uniform vector3d omni:kit:centerOfInterest = (0, 0, -358.86988861191327)
        quatd xformOp:orient = (0.6747032048676167, -0.0528483587076229, 0.7345927633377323, 0.04853976076488145)
        double3 xformOp:scale = (1, 1, 1)
        double3 xformOp:translate = (600.0079605573809, 67.11942372070169, 5.678338934116065)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
    }"""

_SYNAPSES = """    def Scope "Synapses"
    {
        def BasisCurves "Synapse_RouteToN1" (
            prepend apiSchemas = ["MaterialBindingAPI"]
            customData = {
                string role = "parity_routed_synapse"
                string route_target = "N1"
            }
        )
        {
            uniform token basis = "bezier"
            int[] curveVertexCounts = [6]
            rel material:binding = </NeuralNetwork/SynapseMaterials/RouteToN1Mat> (
                bindMaterialAs = "strongerThanDescendants"
            )
            point3f[] points = [(147.1, 0, 0), (156.08226, 3.2844436, 16.739212), (167.1027, 4.379258, 32.293053), (178.87863, 3.831851, 47.401405), (190.1273, 2.189629, 62.804142), (199.56598, 0, 79.24115)]
            uniform token type = "linear"
            float[] widths = [0.55, 0.484, 0.418, 0.352, 0.286, 0.22] (
                interpolation = "vertex"
            )
            uniform token wrap = "nonperiodic"
        }

        def BasisCurves "Synapse_RouteToN2" (
            prepend apiSchemas = ["MaterialBindingAPI"]
            customData = {
                string role = "parity_routed_synapse"
                string route_target = "N2"
            }
        )
        {
            uniform token basis = "bezier"
            int[] curveVertexCounts = [6]
            rel material:binding = </NeuralNetwork/SynapseMaterials/RouteToN2Mat> (
                bindMaterialAs = "strongerThanDescendants"
            )
            point3f[] points = [(147.1, 0, 0), (159.0034, 3.2844436, -14.805106), (169.01971, 4.379258, -31.023796), (178.33092, 3.831851, -47.76405), (188.11902, 2.189629, -64.13384), (199.56598, 0, -79.24115)]
            uniform token type = "linear"
            float[] widths = [0.55, 0.484, 0.418, 0.352, 0.286, 0.22] (
                interpolation = "vertex"
            )
            uniform token wrap = "nonperiodic"
        }
    }"""

_SYNAPSE_MATERIALS = """    def Scope "SynapseMaterials"
    {
        def Material "RouteToN1Mat"
        {
            token outputs:surface.connect = </NeuralNetwork/SynapseMaterials/RouteToN1Mat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.75, 0.5575, 0.478)
                color3f inputs:emissiveColor = (0, 0, 0)
                color3f inputs:emissiveColor.timeSamples = {
                    58: (0, 0, 0),
                    66: (1, 0.5, 0.1),
                    78: (0, 0, 0),
                }
                float inputs:opacity = 1
                float inputs:roughness = 0.35
                token outputs:surface
            }
        }

        def Material "RouteToN2Mat"
        {
            token outputs:surface.connect = </NeuralNetwork/SynapseMaterials/RouteToN2Mat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.45250002, 0.6975, 0.79999995)
                color3f inputs:emissiveColor = (0, 0, 0)
                float inputs:opacity = 1
                float inputs:roughness = 0.35
                token outputs:surface
            }
        }
    }"""


def _ref_xform(name: str, ref_path: str, prim_path: str, translate: tuple[float, float, float]) -> str:
    tx, ty, tz = translate
    return f'''    def Xform "{name}" (
        prepend references = @{ref_path}@<{prim_path}>
    )
    {{
        double3 xformOp:translate = ({tx:g}, {ty:g}, {tz:g})
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}'''


def emit_network_composed(
    *,
    n0_ref: str = "./multipolar_neuron.usda",
    n1_ref: str = "./bilateral_neuron.usda",
    n2_ref: str = "./bilateral_neuron.usda",
) -> str:
    """Reference-based layout: N0 multipolar @ origin; N1/N2 bilateral @ ±Z."""
    n0 = _ref_xform("N0", n0_ref, "/MultipolarNeuron", (0, 0, 0))
    n1 = _ref_xform("N1", n1_ref, "/BilateralNeuron", (210, 0, 95))
    n2 = _ref_xform("N2", n2_ref, "/BilateralNeuron", (210, 0, -95))
    body = "\n\n".join([n0, n1, n2, _SYNAPSES, _SYNAPSE_MATERIALS, _CAMERA])
    return f'''#usda 1.0
(
    doc = """Three-neuron routing demo: even discrete input → N1 glow, odd → N2. Generated by neuron_usd.network_builder."""
    defaultPrim = "NeuralNetwork"
    endTimeCode = 119
    metersPerUnit = 0.01
    startTimeCode = 0
    subLayers = [
        @./lighting.usda@
    ]
    timeCodesPerSecond = 24
    upAxis = "Y"
)

def Xform "NeuralNetwork" (
    customData = {{
        string description = "N0 branches to N1 or N2; parity selects path."
        string even_input_targets = "N1"
        string network_routing_mode = "parity_even_odd"
        string odd_input_targets = "N2"
    }}
)
{{
{body}
}}
'''


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("output/Network_composed.usda"),
        help="Output path (default avoids clobbering output/Network.usda)",
    )
    p.add_argument("--n0", default="./multipolar_neuron.usda")
    p.add_argument("--n1", default="./bilateral_neuron.usda")
    p.add_argument("--n2", default="./bilateral_neuron.usda")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    if args.out.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {args.out} (pass --force).")

    text = emit_network_composed(n0_ref=args.n0, n1_ref=args.n1, n2_ref=args.n2)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"Wrote {args.out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
