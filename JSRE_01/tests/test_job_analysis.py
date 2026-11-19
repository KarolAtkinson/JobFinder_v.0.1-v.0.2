import unittest

from cv_optimiser.job_analysis import (
    JobAnalysisError,
    analyze_job_description,
    extract_requirements,
)
from cv_optimiser.models import MasterBlueprint


class JobRequirementExtractionTests(unittest.TestCase):
    def test_extracts_essential_and_desirable_bullets(self) -> None:
        requirements = extract_requirements(
            """Project Manager
Requirements:
- Experience managing project budgets.
- Strong stakeholder management skills.
Nice to have:
- Familiarity with Agile methods.
"""
        )

        self.assertEqual([item.priority for item in requirements], ["essential", "essential", "desirable"])
        self.assertEqual(requirements[0].category, "experience")
        self.assertEqual(requirements[2].category, "skill")

    def test_extracts_requirement_sentences_without_headings(self) -> None:
        requirements = extract_requirements(
            "We need a candidate with experience using Python. A degree is preferred."
        )

        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[1].priority, "desirable")

    def test_rejects_empty_description(self) -> None:
        with self.assertRaisesRegex(JobAnalysisError, "Enter a job description"):
            extract_requirements("  ")


class RequirementMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blueprint = MasterBlueprint.from_dict(
            {
                "experience": [
                    {
                        "employer": "Example Ltd",
                        "role": "Project Coordinator",
                        "achievements": [
                            {
                                "claim": "Improved stakeholder reporting",
                                "evidence": "Coordinated monthly updates with stakeholders",
                                "verified": True,
                            }
                        ],
                    }
                ],
                "skills": [
                    {
                        "name": "Python",
                        "evidence": "Used Python to automate internal reporting",
                        "verified": True,
                    }
                ],
            }
        )

    def test_reports_verified_support_and_unsupported_requirements(self) -> None:
        result = analyze_job_description(
            """Requirements:
- Experience coordinating stakeholder reporting.
- Experience managing multi-million euro budgets.
""",
            self.blueprint,
            job_title="Project Manager",
            industry="Operations",
        )

        self.assertEqual(result.job_title, "Project Manager")
        self.assertEqual(result.industry, "Operations")
        self.assertEqual([match.status for match in result.matches], ["direct", "missing"])
        self.assertIn("Experience 1: achievement 1", result.matches[0].evidence)
        self.assertEqual(result.alignment_score, 50)

    def test_unverified_responsibility_is_partial_not_direct(self) -> None:
        blueprint = MasterBlueprint.from_dict(
            {
                "experience": [
                    {
                        "employer": "Example Ltd",
                        "role": "Project Coordinator",
                        "responsibilities": ["Managed project budgets"],
                    }
                ]
            }
        )

        result = analyze_job_description(
            "Requirements:\n- Experience managing project budgets.",
            blueprint,
        )

        self.assertEqual(result.matches[0].status, "partial")
        self.assertEqual(result.alignment_score, 50)

    def test_unverified_records_cannot_boost_verified_coverage(self) -> None:
        blueprint = MasterBlueprint.from_dict(
            {
                "skills": [
                    {"name": "Python", "evidence": "Verified Python experience", "verified": True},
                    {"name": "SQL Excel Tableau", "verified": False},
                ]
            }
        )

        result = analyze_job_description(
            "Requirements:\n- Python SQL Excel Tableau experience.",
            blueprint,
        )

        self.assertEqual(result.matches[0].status, "partial")


if __name__ == "__main__":
    unittest.main()
