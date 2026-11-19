import unittest
from io import BytesIO

from docx import Document

from cv_optimiser.job_analysis import analyze_job_description
from cv_optimiser.models import MasterBlueprint
from cv_optimiser.tailoring import build_tailored_cv, render_docx


class TailoredCVTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blueprint = MasterBlueprint.from_dict(
            {
                "profile": {
                    "name": "Alex Example",
                    "email": "alex@example.test",
                    "location": "London",
                },
                "experience": [
                    {
                        "employer": "Earlier Ltd",
                        "role": "Assistant",
                        "achievements": [
                            {
                                "claim": "Supported payroll administration",
                                "evidence": "Payroll project notes",
                                "verified": False,
                            }
                        ],
                    },
                    {
                        "employer": "Current Ltd",
                        "role": "Project Coordinator",
                        "start_date": "2021",
                        "achievements": [
                            {
                                "claim": "Coordinated verified stakeholder reporting",
                                "evidence": "Monthly reports and project records",
                                "verified": True,
                            },
                            {
                                "claim": "Unverified budget result",
                                "evidence": "Needs confirmation",
                                "verified": False,
                            },
                        ],
                    },
                ],
                "skills": [
                    {"name": "Unverified SQL", "verified": False},
                    {"name": "Stakeholder management", "verified": True},
                ],
                "education": [
                    {"qualification": "Degree", "institution": "Example University", "verified": True},
                    {"qualification": "Unverified course", "institution": "Training Centre"},
                ],
                "certifications": [
                    {"name": "Verified Certificate", "verified": True},
                    {"name": "Unverified Certificate"},
                ],
                "languages": [
                    {"name": "English", "proficiency": "Fluent", "verified": True},
                    {"name": "Unverified language"},
                ],
            }
        )
        self.analysis = analyze_job_description(
            "Requirements:\n- Experience coordinating stakeholder reporting.",
            self.blueprint,
            job_title="Project Manager",
        )

    def test_tailoring_includes_verified_content_only(self) -> None:
        cv = build_tailored_cv(self.blueprint, self.analysis)

        self.assertEqual(cv.experience[0].source.role, "Project Coordinator")
        self.assertEqual(
            [achievement.source.claim for achievement in cv.experience[0].achievements],
            ["Coordinated verified stakeholder reporting"],
        )
        self.assertEqual([skill.name for skill in cv.skills], ["Stakeholder management"])
        self.assertEqual([item.qualification for item in cv.education], ["Degree"])
        self.assertEqual([item.name for item in cv.certifications], ["Verified Certificate"])
        self.assertEqual([item.name for item in cv.languages], ["English"])

    def test_docx_contains_draft_content_and_omits_unverified_claims(self) -> None:
        cv = build_tailored_cv(self.blueprint, self.analysis)
        document = Document(BytesIO(render_docx(cv)))
        content = "\n".join(paragraph.text for paragraph in document.paragraphs)

        self.assertIn("Alex Example", content)
        self.assertIn("Target role: Project Manager", content)
        self.assertIn("Coordinated verified stakeholder reporting", content)
        self.assertIn("Stakeholder management", content)
        self.assertNotIn("Unverified budget result", content)
        self.assertNotIn("Unverified SQL", content)

    def test_docx_uses_master_summary(self) -> None:
        self.blueprint.profile.summary = "Master summary written by the candidate."
        cv = build_tailored_cv(self.blueprint, self.analysis)

        content = "\n".join(p.text for p in Document(BytesIO(render_docx(cv))).paragraphs)

        self.assertIn("Professional Summary", content)
        self.assertIn("Master summary written by the candidate.", content)

    def test_docx_headings_follow_the_selected_language(self) -> None:
        self.blueprint.profile.summary = "Podsumowanie."
        cv = build_tailored_cv(self.blueprint, self.analysis)

        polish = "\n".join(p.text for p in Document(BytesIO(render_docx(cv, language="pl"))).paragraphs)
        english = "\n".join(p.text for p in Document(BytesIO(render_docx(cv))).paragraphs)

        self.assertIn("Doświadczenie zawodowe", polish)
        self.assertIn("Podsumowanie kandydata", polish)
        self.assertIn("Stanowisko docelowe", polish)
        self.assertIn("Professional Experience", english)
        self.assertNotIn("Doświadczenie zawodowe", english)
        with self.assertRaises(ValueError):
            render_docx(cv, language="de")


class SkillGroupTests(unittest.TestCase):
    def test_groups_skills_and_separates_confirmed_ones(self) -> None:
        from cv_optimiser.models import Skill
        from cv_optimiser.tailoring import group_skills

        groups = dict(
            group_skills(
                [
                    Skill(name="Python", verified=True),
                    Skill(name="Git", verified=True),
                    Skill(name="Linux", verified=True),
                    Skill(name="NIST framework", verified=True),
                    Skill(name="Mentoring", verified=True),
                    Skill(name="L1 SOC experience", evidence="Confirmed by the candidate for 'X'", verified=True),
                ]
            )
        )

        self.assertEqual(groups["Programming & Databases"], ["Python"])
        self.assertEqual(groups["Tools & Platforms"], ["Git"])
        self.assertEqual(groups["Systems & Networking"], ["Linux"])
        self.assertEqual(groups["Security, Risk & Compliance"], ["NIST framework"])
        self.assertEqual(groups["Other skills"], ["Mentoring"])
        self.assertEqual(groups["Job-relevant competencies"], ["L1 SOC experience"])


if __name__ == "__main__":
    unittest.main()
