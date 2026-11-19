import unittest

from cv_optimiser.attestation import attest_skills, mark_all_verified
from cv_optimiser.job_analysis import analyze_job_description
from cv_optimiser.models import Achievement, Experience, MasterBlueprint, Skill
from cv_optimiser.tailoring import build_tailored_cv


class AttestationTests(unittest.TestCase):
    def test_confirming_imported_items_makes_them_exportable(self) -> None:
        blueprint = MasterBlueprint(
            experience=[
                Experience(
                    employer="Acme",
                    role="Analyst",
                    achievements=[Achievement(claim="Ran vulnerability scans", evidence="CV", verified=False)],
                    verified=False,
                )
            ],
            skills=[Skill(name="Python", verified=False)],
        )
        analysis = analyze_job_description("Requirements:\n- Python", blueprint, job_title="Analyst")
        self.assertEqual(build_tailored_cv(blueprint, analysis).skills, ())
        self.assertEqual(mark_all_verified(blueprint), 3)
        analysis = analyze_job_description("Requirements:\n- Python", blueprint, job_title="Analyst")
        cv = build_tailored_cv(blueprint, analysis)
        self.assertEqual([skill.name for skill in cv.skills], ["Python"])
        self.assertEqual(len(cv.experience[0].achievements), 1)

    def test_attested_requirements_become_labelled_verified_skills(self) -> None:
        blueprint = MasterBlueprint()
        added = attest_skills(blueprint, ["Experience with ISO 27001 audits.", "experience with iso 27001 audits"], "GRC")
        self.assertEqual(added, 1)
        skill = blueprint.skills[0]
        self.assertTrue(skill.verified)
        self.assertEqual(skill.name, "Experience with ISO 27001 audits")
        self.assertIn("Confirmed by the candidate", skill.evidence or "")
        blueprint.validate()


if __name__ == "__main__":
    unittest.main()
