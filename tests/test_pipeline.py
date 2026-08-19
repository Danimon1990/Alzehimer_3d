import unittest

from pxr import Kind, Usd, UsdGeom

from healthy_vs_alz.usd.assets import publish_all_assets
from healthy_vs_alz.usd.shots import publish_all_shots
from healthy_vs_alz.usd.validation import validate_publish


class PublishedUsdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        publish_all_assets()
        publish_all_shots()

    def test_assets_have_component_default_prims(self) -> None:
        for path in publish_all_assets():
            stage = Usd.Stage.Open(str(path), load=Usd.Stage.LoadNone)
            self.assertTrue(stage.GetDefaultPrim(), path)
            self.assertEqual(
                Usd.ModelAPI(stage.GetDefaultPrim()).GetKind(),
                Kind.Tokens.component,
            )

    def test_published_stages_use_project_metrics(self) -> None:
        for path in publish_all_shots():
            stage = Usd.Stage.Open(str(path), load=Usd.Stage.LoadNone)
            self.assertEqual(UsdGeom.GetStageUpAxis(stage), UsdGeom.Tokens.y)
            self.assertAlmostEqual(UsdGeom.GetStageMetersPerUnit(stage), 0.01)

    def test_publish_has_no_validation_findings(self) -> None:
        self.assertEqual(validate_publish(), [])


if __name__ == "__main__":
    unittest.main()
