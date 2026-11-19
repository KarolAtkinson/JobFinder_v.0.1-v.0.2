import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cv_optimiser.models import BlueprintValidationError, MasterBlueprint
from cv_optimiser.storage import default_blueprint_path, load_blueprint, save_blueprint


class BlueprintModelTests(unittest.TestCase):
    def test_round_trip_preserves_verified_achievement_evidence(self) -> None:
        source = {
            "profile": {"name": "Alex Example", "target_roles": ["Project Manager"]},
            "experience": [
                {
                    "employer": "Example Ltd",
                    "role": "Project Coordinator",
                    "achievements": [
                        {
                            "claim": "Improved reporting",
                            "evidence": "Introduced a shared reporting template",
                            "metrics": None,
                            "verified": True,
                        }
                    ],
                }
            ],
            "skills": [{"name": "Reporting", "evidence": "Monthly project reports", "verified": True}],
        }

        blueprint = MasterBlueprint.from_dict(source)

        self.assertEqual(blueprint.to_dict()["experience"][0]["achievements"][0]["evidence"],
                         "Introduced a shared reporting template")
        self.assertTrue(blueprint.to_dict()["experience"][0]["achievements"][0]["verified"])

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaisesRegex(BlueprintValidationError, "unknown field"):
            MasterBlueprint.from_dict({"unexpected": "data"})

    def test_rejects_missing_achievement_evidence(self) -> None:
        with self.assertRaisesRegex(BlueprintValidationError, "evidence"):
            MasterBlueprint.from_dict(
                {
                    "experience": [
                        {
                            "employer": "Example Ltd",
                            "role": "Analyst",
                            "achievements": [{"claim": "Improved a process"}],
                        }
                    ]
                }
            )

    def test_rejects_invalid_preferred_cv_length(self) -> None:
        with self.assertRaisesRegex(BlueprintValidationError, "positive integer"):
            MasterBlueprint.from_dict({"preferences": {"preferred_cv_length_pages": 0}})

    def test_save_and_load_round_trip(self) -> None:
        blueprint = MasterBlueprint.from_dict({"profile": {"name": "Alex"}, "languages": [{"name": "English"}]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "master_cv.json"

            save_blueprint(blueprint, path)
            loaded = load_blueprint(path)

        self.assertEqual(loaded.to_dict(), blueprint.to_dict())

    def test_load_reports_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "master_cv.json"
            path.write_text("{broken", encoding="utf-8")

            with self.assertRaisesRegex(BlueprintValidationError, "not valid JSON"):
                load_blueprint(path)

    @unittest.skipUnless(os.name == "nt", "Windows local-app-data path test")
    def test_default_path_uses_local_app_data(self) -> None:
        with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\Example\AppData\Local"}):
            path = default_blueprint_path()

        self.assertEqual(
            path,
            Path(r"C:\Users\Example\AppData\Local") / "cv-optimiser" / "master_cv.json",
        )


if __name__ == "__main__":
    unittest.main()
