from pathlib import Path

from pxr import Usd, UsdGeom


def create_stage(
    destination: Path,
    default_prim: str,
    *,
    start_frame: float | None = None,
    end_frame: float | None = None,
    frames_per_second: float = 24.0,
) -> Usd.Stage:
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(destination))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    root = UsdGeom.Xform.Define(stage, f"/{default_prim}")
    stage.SetDefaultPrim(root.GetPrim())
    if start_frame is not None and end_frame is not None:
        stage.SetStartTimeCode(start_frame)
        stage.SetEndTimeCode(end_frame)
        stage.SetFramesPerSecond(frames_per_second)
        stage.SetTimeCodesPerSecond(frames_per_second)
    return stage


def save(stage: Usd.Stage) -> None:
    stage.GetRootLayer().Save()

