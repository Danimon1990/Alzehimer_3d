from dataclasses import dataclass
from pathlib import Path

from pxr import Kind, Usd, UsdGeom, UsdUtils

from healthy_vs_alz.constants import USD_ROOT


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str


def validate_stage(path: Path) -> list[Finding]:
    findings = []
    stage = Usd.Stage.Open(str(path), load=Usd.Stage.LoadNone)
    if stage is None:
        return [Finding(path, "stage could not be opened")]
    if not stage.GetDefaultPrim():
        findings.append(Finding(path, "missing default prim"))
    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.y:
        findings.append(Finding(path, "upAxis must be Y"))
    if abs(UsdGeom.GetStageMetersPerUnit(stage) - 0.01) > 1e-9:
        findings.append(Finding(path, "metersPerUnit must be 0.01"))
    if "/assets/" in path.as_posix():
        model = Usd.ModelAPI(stage.GetDefaultPrim())
        if model.GetKind() != Kind.Tokens.component:
            findings.append(Finding(path, "asset default prim must be a component"))
    _, _, unresolved_paths = UsdUtils.ComputeAllDependencies(str(path))
    if unresolved_paths:
        for unresolved in unresolved_paths:
            findings.append(Finding(path, f"unresolved dependency: {unresolved}"))
    return findings


def validate_publish() -> list[Finding]:
    findings = []
    for path in sorted(USD_ROOT.rglob("*.usd*")):
        findings.extend(validate_stage(path))
    return findings
