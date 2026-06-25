#!/usr/bin/env python3
"""
Stylized cortical pyramidal neuron (OpenUSD / pxr).

- Triangular / pyramidal soma mesh (two upper rear corners feed the main apical pair).
- Dendrites: bezier + linear BasisCurves (same family as neuron_usd/procedural_neuron), with
  primary → secondary branching and small bouton spheres at tips.
- Axon: mostly straight along +X (matches common diagram screenshots), with discrete myelin
  sheath segments (wider short curves) and a *small* terminal arbor (few branches).

Requires: pxr (OpenUSD Python bindings).
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

# Output next to this script
OUTPUT_FILE = Path(__file__).resolve().parent / "pyramidal_neuron.usda"


# ---------------------------------------------------------------------------
# Organic points (similar spirit to procedural_neuron._bezier_linear_points)
# ---------------------------------------------------------------------------
def _walk_branch(
    rng: random.Random,
    start: tuple[float, float, float],
    n: int,
    spread: float,
    bias: tuple[float, float, float],
) -> list[Gf.Vec3f]:
    x, y, z = start
    bx, by, bz = bias
    pts: list[Gf.Vec3f] = [Gf.Vec3f(x, y, z)]
    for _ in range(n - 1):
        x += bx + rng.uniform(-spread, spread)
        y += by + rng.uniform(-spread, spread)
        z += bz + rng.uniform(-spread * 0.4, spread * 0.4)
        pts.append(Gf.Vec3f(x, y, z))
    return pts


def _taper_widths(count: int, base: float, tip: float) -> list[float]:
    if count < 2:
        return [base]
    return [base + (tip - base) * (i / (count - 1)) for i in range(count)]


def _make_linear_bezier_curve(
    stage: Usd.Stage,
    path: str,
    points: list[Gf.Vec3f],
    widths: list[float],
) -> UsdGeom.BasisCurves:
    """Match procedural USDA: basis=bezier, type=linear, vertex interpolation on widths."""
    curve = UsdGeom.BasisCurves.Define(stage, path)
    curve.CreateBasisAttr("bezier")
    curve.CreateTypeAttr("linear")
    curve.CreateWrapAttr("nonperiodic")
    curve.CreateCurveVertexCountsAttr([len(points)])
    curve.CreatePointsAttr(points)
    w_attr = curve.CreateWidthsAttr(widths)
    w_attr.SetMetadata("interpolation", "vertex")
    return curve


def _make_myelin_segment(
    stage: Usd.Stage,
    path: str,
    p0: Gf.Vec3f,
    p1: Gf.Vec3f,
    w0: float,
    w1: float,
) -> UsdGeom.BasisCurves:
    c = UsdGeom.BasisCurves.Define(stage, path)
    c.CreateBasisAttr("bezier")
    c.CreateTypeAttr("linear")
    c.CreateWrapAttr("nonperiodic")
    c.CreateCurveVertexCountsAttr([2])
    c.CreatePointsAttr([p0, p1])
    w_attr = c.CreateWidthsAttr([w0, w1])
    w_attr.SetMetadata("interpolation", "vertex")
    return c


def _bind_material(stage: Usd.Stage, prim_path: str, material_path: str) -> None:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        return
    mat_prim = stage.GetPrimAtPath(material_path)
    mat = UsdShade.Material(mat_prim)
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(
        mat,
        bindingStrength=UsdShade.Tokens.weakerThanDescendants,
    )


def _make_preview_material(stage: Usd.Stage, mat_path: str, diffuse: tuple[float, float, float]) -> None:
    mat = UsdShade.Material.Define(stage, mat_path)
    sh = UsdShade.Shader.Define(stage, f"{mat_path}/PreviewSurface")
    sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*diffuse))
    sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.55)
    sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")


def build_triangular_soma(stage: Usd.Stage, path: str) -> tuple[Gf.Vec3f, Gf.Vec3f, Gf.Vec3f]:
    """
    Triangular frustum soma: two rear top corners + forward apex; taper to a single tip.
    Apical dendrites anchor from the two rear corners; axon uses a separate hillock point (+X).
    """
    t0 = Gf.Vec3f(-1.15, 1.0, -0.55)
    t1 = Gf.Vec3f(1.15, 1.0, -0.55)
    t2 = Gf.Vec3f(0.0, 1.05, 1.0)

    m0 = Gf.Vec3f(-1.35, 0.25, -0.65)
    m1 = Gf.Vec3f(1.35, 0.25, -0.65)
    m2 = Gf.Vec3f(0.0, 0.3, 1.15)

    l0 = Gf.Vec3f(-1.05, -0.75, -0.5)
    l1 = Gf.Vec3f(1.05, -0.75, -0.5)
    l2 = Gf.Vec3f(0.0, -0.7, 0.85)

    tip = Gf.Vec3f(0.0, -1.45, 0.0)

    points = [t0, t1, t2, m0, m1, m2, l0, l1, l2, tip]

    indices = [
        0,
        1,
        4,
        3,
        1,
        2,
        5,
        4,
        2,
        0,
        3,
        5,
        3,
        4,
        7,
        6,
        4,
        5,
        8,
        7,
        5,
        3,
        6,
        8,
        6,
        7,
        9,
        7,
        8,
        9,
        8,
        6,
        9,
    ]
    counts = [4, 4, 4, 4, 4, 4, 3, 3, 3]

    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr("catmullClark")

    hillock = Gf.Vec3f(1.12, -0.62, 0.0)
    return t0, t1, hillock


def build_neuron(seed: int = 42) -> None:
    rng = random.Random(seed)
    stage = Usd.Stage.CreateNew(str(OUTPUT_FILE))

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(120)
    stage.GetRootLayer().timeCodesPerSecond = 24.0

    root = UsdGeom.Xform.Define(stage, "/Neuron")
    stage.SetDefaultPrim(root.GetPrim())
    root_xform = UsdGeom.Xformable(root.GetPrim())
    root_xform.AddScaleOp().Set(Gf.Vec3f(14.0, 14.0, 14.0))

    # --- Materials (soft biological palette, close to procedural neuron) ---
    mem = "/Neuron/Materials/NeuronMembraneMat"
    mye = "/Neuron/Materials/MyelinMat"
    axn = "/Neuron/Materials/AxonMat"
    trm = "/Neuron/Materials/TerminalMat"
    _make_preview_material(stage, mem, (0.82, 0.74, 0.62))
    _make_preview_material(stage, mye, (0.9, 0.92, 0.98))
    _make_preview_material(stage, axn, (0.72, 0.72, 0.86))
    _make_preview_material(stage, trm, (0.78, 0.78, 0.88))

    t0, t1, hillock = build_triangular_soma(stage, "/Neuron/Soma")
    _bind_material(stage, "/Neuron/Soma", mem)

    # Nucleus (subtle)
    nuc = UsdGeom.Sphere.Define(stage, "/Neuron/Nucleus")
    nuc.CreateRadiusAttr(0.42)
    xf = UsdGeom.Xformable(nuc.GetPrim())
    xf.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.15, 0.12))
    xf.AddScaleOp().Set(Gf.Vec3f(1.05, 0.95, 1.0))
    _bind_material(stage, "/Neuron/Nucleus", mem)

    # --- Apical pair from the two upper rear corners (reference silhouette) ---
    def apical_from_corner(corner: Gf.Vec3f, side_sign: float) -> tuple[list[Gf.Vec3f], list[float]]:
        start = Gf.Vec3f(corner[0], corner[1] + 0.08, corner[2])
        bias = (side_sign * 0.35, 0.85, 0.55)
        pts = _walk_branch(rng, (start[0], start[1], start[2]), 8, 0.45, bias)
        w = _taper_widths(len(pts), 0.2, 0.04)
        return pts, w

    pL, wL = apical_from_corner(t0, -1.0)
    pR, wR = apical_from_corner(t1, 1.0)
    _make_linear_bezier_curve(stage, "/Neuron/ApicalPrimary_L", pL, wL)
    _make_linear_bezier_curve(stage, "/Neuron/ApicalPrimary_R", pR, wR)
    for p in ("/Neuron/ApicalPrimary_L", "/Neuron/ApicalPrimary_R"):
        _bind_material(stage, p, mem)

    # Secondaries (one each side, from mid-branch)
    midL = pL[len(pL) // 2]
    midR = pR[len(pR) // 2]
    sL = _walk_branch(rng, (midL[0], midL[1], midL[2]), 6, 0.38, (-0.55, 0.35, -0.4))
    sR = _walk_branch(rng, (midR[0], midR[1], midR[2]), 6, 0.38, (0.55, 0.35, -0.4))
    _make_linear_bezier_curve(stage, "/Neuron/ApicalSecondary_L", sL, _taper_widths(6, 0.09, 0.02))
    _make_linear_bezier_curve(stage, "/Neuron/ApicalSecondary_R", sR, _taper_widths(6, 0.09, 0.02))
    _bind_material(stage, "/Neuron/ApicalSecondary_L", mem)
    _bind_material(stage, "/Neuron/ApicalSecondary_R", mem)

    # --- Basal dendrites (oblique from lower sides) ---
    def basal(side: float) -> tuple[list[Gf.Vec3f], list[float]]:
        sx = 0.85 * side
        start = (sx * 1.2, 0.05, -0.35)
        bias = (side * 0.9, -0.35, -0.25)
        pts = _walk_branch(rng, start, 7, 0.42, bias)
        return pts, _taper_widths(7, 0.14, 0.035)

    bL, bwL = basal(-1.0)
    bR, bwR = basal(1.0)
    _make_linear_bezier_curve(stage, "/Neuron/Basal_L", bL, bwL)
    _make_linear_bezier_curve(stage, "/Neuron/Basal_R", bR, bwR)
    _bind_material(stage, "/Neuron/Basal_L", mem)
    _bind_material(stage, "/Neuron/Basal_R", mem)

    # --- Axon along +X (horizontal, diagram-style), thin core + myelin donuts ---
    axon_start = Gf.Vec3f(hillock[0] + 0.15, hillock[1], hillock[2])
    axon_len = 9.5
    n_ax_pts = 10
    ax_pts: list[Gf.Vec3f] = []
    for i in range(n_ax_pts):
        t = i / (n_ax_pts - 1)
        # tiny sag for organic feel
        sag = 0.06 * math.sin(t * math.pi)
        ax_pts.append(
            Gf.Vec3f(
                axon_start[0] + t * axon_len,
                axon_start[1] - sag,
                axon_start[2] + rng.uniform(-0.04, 0.04),
            )
        )
    ax_w = _taper_widths(n_ax_pts, 0.11, 0.075)
    _make_linear_bezier_curve(stage, "/Neuron/Axon_Hillock", ax_pts, ax_w)
    _bind_material(stage, "/Neuron/Axon_Hillock", axn)

    # Myelin: thick short segments along the axon (every other internode for a light look)
    gap = 0.24
    thick_w = 0.28
    mi = 0
    for i in range(0, n_ax_pts - 1, 2):
        a = ax_pts[i]
        b = ax_pts[i + 1]
        mid = (a + b) * 0.5
        direction = b - a
        ln = direction.GetLength()
        if ln < 1e-6:
            continue
        direction.Normalize()
        half = gap * 0.5
        p0 = mid - direction * half
        p1 = mid + direction * half
        path = f"/Neuron/Myelin_{mi:02d}"
        _make_myelin_segment(stage, path, p0, p1, thick_w * 0.95, thick_w * 0.85)
        _bind_material(stage, path, mye)
        mi += 1

    axon_tip = ax_pts[-1]

    def add_bouton(path: str, p: Gf.Vec3f, r: float = 0.09) -> None:
        s = UsdGeom.Sphere.Define(stage, path)
        s.CreateRadiusAttr(r)
        UsdGeom.Xformable(s.GetPrim()).AddTranslateOp().Set(p)
        _bind_material(stage, path, trm)

    # --- Small terminal arbor (3 branches + boutons on tips; reference-style sparse arbor) ---
    terminal_dirs = [
        (0.15, -0.35, 0.45),
        (0.55, -0.25, -0.15),
        (0.35, -0.45, 0.05),
    ]
    for ti, direction in enumerate(terminal_dirs):
        d = Gf.Vec3f(*direction).GetNormalized()
        bias = (d[0] * 0.55, d[1] * 0.45, d[2] * 0.55)
        tpts = _walk_branch(
            rng,
            (axon_tip[0], axon_tip[1], axon_tip[2]),
            5,
            0.22,
            (bias[0], bias[1], bias[2]),
        )
        _make_linear_bezier_curve(
            stage,
            f"/Neuron/AxonTerminal_{ti}",
            tpts,
            _taper_widths(5, 0.065, 0.018),
        )
        _bind_material(stage, f"/Neuron/AxonTerminal_{ti}", trm)
        add_bouton(f"/Neuron/Bouton_Terminal_{ti}", tpts[-1], 0.06)

    # Bouton spheres at dendrite tips
    add_bouton("/Neuron/Bouton_ApicalL", pL[-1])
    add_bouton("/Neuron/Bouton_ApicalR", pR[-1])
    add_bouton("/Neuron/Bouton_BasalL", bL[-1])
    add_bouton("/Neuron/Bouton_BasalR", bR[-1])

    stage.GetRootLayer().documentation = (
        "Pyramidal neuron — triangular soma, paired apicals, horizontal axon + myelin, sparse terminals."
    )
    stage.Save()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_neuron()
