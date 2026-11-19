import tempfile
import unittest
from pathlib import Path

from cv_optimiser.job_import import JobImportError, load_job_posting, parse_job_posting


class JobImportTests(unittest.TestCase):
    def test_labelled_fields_are_extracted(self) -> None:
        posting = parse_job_posting("Company: Acme\nJob title: Security Analyst\nIndustry: Finance\n\nRequired: SIEM")
        self.assertEqual((posting.title, posting.industry), ("Security Analyst", "Finance"))
        self.assertIn("Required: SIEM", posting.description)

    def test_polish_labels(self) -> None:
        posting = parse_job_posting("Stanowisko: Analityk Cyberbezpieczeństwa\nBranża: IT\nWymagania: SQL")
        self.assertEqual((posting.title, posting.industry), ("Analityk Cyberbezpieczeństwa", "IT"))

    def test_first_short_line_is_title_fallback(self) -> None:
        posting = parse_job_posting("\nGRC Consultant\nWe need someone with ISO 27001 experience.")
        self.assertEqual(posting.title, "GRC Consultant")
        self.assertEqual(posting.industry, "")

    def test_empty_text_is_rejected(self) -> None:
        with self.assertRaises(JobImportError):
            parse_job_posting("  \n ")

    def test_file_encodings_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            utf8 = Path(folder, "a.txt")
            utf8.write_bytes("Stanowisko: Inżynier\nSQL".encode("utf-8-sig"))
            self.assertEqual(load_job_posting(utf8).title, "Inżynier")
            legacy = Path(folder, "b.txt")
            legacy.write_bytes("Stanowisko: Inżynier\nSQL".encode("cp1250"))
            self.assertEqual(load_job_posting(legacy).title, "Inżynier")
            big = Path(folder, "c.txt")
            big.write_bytes(b"x" * (1024 * 1024 + 1))
            with self.assertRaisesRegex(JobImportError, "1 MB"):
                load_job_posting(big)
            with self.assertRaises(JobImportError):
                load_job_posting(Path(folder, "missing.txt"))


if __name__ == "__main__":
    unittest.main()
