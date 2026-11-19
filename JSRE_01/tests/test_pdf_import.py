import io
import unittest
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from cv_optimiser.job_analysis import analyze_job_description
from cv_optimiser.models import MasterBlueprint
from cv_optimiser.pdf_import import (
    PDFImportError,
    draft_blueprint_from_pdf,
    extract_pdf_text,
)
from cv_optimiser.tailoring import build_tailored_cv


class FakePage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


class FakeReader:
    pages: list[FakePage] = []
    is_encrypted = False

    def __init__(self, _stream: io.BytesIO, strict: bool) -> None:
        del _stream
        if strict:
            raise AssertionError("PDF import should use tolerant parsing.")
        self.pages = self.__class__.pages
        self.is_encrypted = self.__class__.is_encrypted


class PDFTextExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeReader.pages = [FakePage("page one"), FakePage("page two")]
        FakeReader.is_encrypted = False
        self.reader_patch = patch("cv_optimiser.pdf_import.PdfReader", FakeReader)
        self.reader_patch.start()
        self.addCleanup(self.reader_patch.stop)

    def test_extracts_text_from_all_pages(self) -> None:
        extracted = extract_pdf_text(b"%PDF-test")

        self.assertEqual(extracted.page_count, 2)
        self.assertEqual(extracted.text, "page one\npage two")

    def test_extracts_text_from_a_real_pdf(self) -> None:
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        resources = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): writer._add_object(font)}
                )
            }
        )
        page[NameObject("/Resources")] = writer._add_object(resources)
        stream = DecodedStreamObject()
        stream.set_data(
            b"BT /F1 12 Tf 72 720 Td "
            b"(Alex Example) Tj 0 -20 Td "
            b"(alex@example.test) Tj 0 -20 Td "
            b"(Professional Experience) Tj 0 -20 Td "
            b"(Project Coordinator | Example Ltd | 2021 - 2024) Tj 0 -20 Td "
            b"(Skills) Tj 0 -20 Td "
            b"(Python, Excel) Tj ET"
        )
        page[NameObject("/Contents")] = writer._add_object(stream)
        output = io.BytesIO()
        writer.write(output)

        self.reader_patch.stop()
        self.addCleanup(self.reader_patch.start)
        extracted = extract_pdf_text(output.getvalue())

        self.assertEqual(extracted.page_count, 1)
        self.assertIn("Alex Example", extracted.text)
        self.assertIn("Professional Experience", extracted.text)

    def test_rejects_non_pdf_files(self) -> None:
        with self.assertRaisesRegex(PDFImportError, "not a valid PDF"):
            extract_pdf_text(b"not a pdf")

    def test_rejects_scanned_pdfs_without_selectable_text(self) -> None:
        FakeReader.pages = [FakePage(None), FakePage("  ")]

        with self.assertRaisesRegex(PDFImportError, "scanned/image-only"):
            extract_pdf_text(b"%PDF-test")

    def test_rejects_password_protected_pdfs(self) -> None:
        FakeReader.is_encrypted = True

        with self.assertRaisesRegex(PDFImportError, "password-protected"):
            extract_pdf_text(b"%PDF-test")

    def test_does_not_extract_a_year_range_as_a_phone_number(self) -> None:
        FakeReader.pages = [FakePage("Project Coordinator | Example Ltd | 2021 - 2024")]

        draft = draft_blueprint_from_pdf(b"%PDF-test")

        self.assertEqual(draft.profile.phone, "")


class PDFBlueprintDraftTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeReader.pages = [
            FakePage(
                """Alex Example
alex@example.com
+44 20 1234 5678

Professional Experience

Project Coordinator | Example Ltd | 2021 - 2024
• Coordinated monthly stakeholder reporting
Managed project documentation

Skills
Python, Excel; stakeholder management

Education
BSc Computer Science

Certifications
Project Management Certificate

Languages
English - Fluent
"""
            )
        ]
        FakeReader.is_encrypted = False
        self.reader_patch = patch("cv_optimiser.pdf_import.PdfReader", FakeReader)
        self.reader_patch.start()
        self.addCleanup(self.reader_patch.stop)

    def test_extracts_profile_sections_and_unverified_records(self) -> None:
        blueprint = draft_blueprint_from_pdf(b"%PDF-test")

        self.assertEqual(blueprint.profile.name, "Alex Example")
        self.assertEqual(blueprint.profile.email, "alex@example.com")
        self.assertEqual(blueprint.profile.phone, "+44 20 1234 5678")
        self.assertEqual(len(blueprint.experience), 1)
        experience = blueprint.experience[0]
        self.assertEqual(experience.role, "Project Coordinator")
        self.assertEqual(experience.employer, "Example Ltd")
        self.assertEqual((experience.start_date, experience.end_date), ("2021", "2024"))
        self.assertFalse(experience.verified)
        self.assertFalse(experience.achievements[0].verified)
        self.assertEqual(blueprint.experience[0].responsibilities, ["Managed project documentation"])
        self.assertEqual([item.name for item in blueprint.skills], [
            "Python",
            "Excel",
            "stakeholder management",
        ])
        self.assertTrue(all(not item.verified for item in blueprint.skills))
        self.assertEqual(blueprint.education[0].qualification, "BSc Computer Science")
        self.assertFalse(blueprint.education[0].verified)
        self.assertEqual(blueprint.certifications[0].name, "Project Management Certificate")
        self.assertFalse(blueprint.certifications[0].verified)
        self.assertEqual((blueprint.languages[0].name, blueprint.languages[0].proficiency), ("English", "Fluent"))
        self.assertFalse(blueprint.languages[0].verified)
        self.assertIn("Managed project documentation", blueprint.imported_cv_text)

    def test_imported_experience_is_not_exported_before_review(self) -> None:
        blueprint = draft_blueprint_from_pdf(b"%PDF-test")
        analysis = analyze_job_description(
            "Requirements:\n- Experience coordinating stakeholder reporting.",
            blueprint,
        )

        cv = build_tailored_cv(blueprint, analysis)

        self.assertEqual(cv.experience, ())
        self.assertEqual(cv.skills, ())

    def test_original_blueprint_is_not_modified_by_import(self) -> None:
        existing = MasterBlueprint.from_dict({"profile": {"name": "Existing Profile"}})
        before = existing.to_dict()

        imported = draft_blueprint_from_pdf(b"%PDF-test")

        self.assertEqual(existing.to_dict(), before)
        self.assertEqual(imported.profile.name, "Alex Example")

    def test_pdf_bytes_over_limit_are_rejected_before_parsing(self) -> None:
        with patch("cv_optimiser.pdf_import.MAX_PDF_BYTES", 4):
            with self.assertRaisesRegex(PDFImportError, "50 MB import limit"):
                draft_blueprint_from_pdf(b"%PDF-" + b"x" * 5)

    def test_polish_cv_layout_is_parsed(self) -> None:
        FakeReader.pages = [
            FakePage(
                """1
Jan Kowalski
jan@example.com

UMIEJĘTNOŚCI
Narzędzia
• Git, Python.

DOŚWIADCZENIE ZAWODOWE
Stażysta – Firma Sp. z o.o.
Styczeń 2020 – obecnie | Warszawa
• Wsparcie zespołu
przy projekcie IT.

EDUKACJA
Master of Science (MSc) – Cyber Security
Uniwersytet X
2025 – 2026
Wynik: Merit

INFORMACJE DODATKOWE
• Język polski: ojczysty
"""
            )
        ]
        with patch("cv_optimiser.pdf_import.PdfReader", FakeReader):
            draft = draft_blueprint_from_pdf(b"%PDF-1.4 fake")
        job = draft.experience[0]
        self.assertEqual(draft.profile.name, "Jan Kowalski")
        self.assertEqual((job.role, job.employer), ("Stażysta", "Firma Sp. z o.o."))
        self.assertEqual((job.start_date, job.end_date), ("2020", "Present"))
        self.assertEqual(job.achievements[0].claim, "Wsparcie zespołu przy projekcie IT.")
        self.assertEqual([skill.name for skill in draft.skills], ["Git", "Python"])
        self.assertEqual(draft.education[0].institution, "Uniwersytet X")
        self.assertEqual(draft.languages[0].name, "polski")


    def test_imports_summary_section_into_profile(self) -> None:
        FakeReader.pages = [
            FakePage(
                """Jan Kowalski
jan@example.com

PODSUMOWANIE KANDYDATA
Absolwent cyberbezpieczeństwa
z praktyką w SOC.

UMIEJĘTNOŚCI
• Git
"""
            )
        ]
        with patch("cv_optimiser.pdf_import.PdfReader", FakeReader):
            draft = draft_blueprint_from_pdf(b"%PDF-1.4 fake")

        self.assertEqual(draft.profile.summary, "Absolwent cyberbezpieczeństwa z praktyką w SOC.")


if __name__ == "__main__":
    unittest.main()
