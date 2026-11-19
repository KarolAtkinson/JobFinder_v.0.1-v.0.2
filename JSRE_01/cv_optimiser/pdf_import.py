"""Local PDF text extraction and review-first CV blueprint drafting."""

from __future__ import annotations

import re
from io import BytesIO
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, cast

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from cv_optimiser.models import (
    Achievement,
    BlueprintValidationError,
    Certification,
    Education,
    Experience,
    Language,
    MasterBlueprint,
    Profile,
    Project,
    Skill,
)


MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARACTERS = 500_000
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s()./-]{5,}\d(?!\w)")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_BULLET = re.compile(r"^\s*(?:[-*+•▪◦]|\d+[.)])\s*")

_SECTIONS = {
    "experience": {
        "experience",
        "employment",
        "employment history",
        "career history",
        "professional experience",
        "work experience",
        "work history",
        "doświadczenie zawodowe",
        "doświadczenie",
    },
    "skills": {
        "skills",
        "core skills",
        "core competencies",
        "key skills",
        "technical skills",
        "competencies",
        "umiejętności",
        "kompetencje",
    },
    "education": {
        "education",
        "education and qualifications",
        "qualifications",
        "academic background",
        "education and training",
        "edukacja",
        "wykształcenie",
    },
    "certifications": {
        "certification",
        "certifications",
        "certificates",
        "licences and certifications",
        "licenses and certifications",
        "professional certifications",
        "certyfikaty",
        "certyfikaty i kursy",
    },
    "languages": {"languages", "language skills", "języki", "znajomość języków"},
    "additional": {"additional information", "informacje dodatkowe"},
    "ignored": {
        "zgoda na przetwarzanie danych osobowych",
        "klauzula rodo",
        "references",
        "referencje",
    },
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "career summary",
        "personal statement",
        "objective",
        "podsumowanie kandydata",
        "podsumowanie",
        "profil zawodowy",
    },
    "projects": {
        "projects",
        "selected projects",
        "project experience",
        "projekty",
        "projekty akademickie",
    },
}
_ALL_HEADINGS = {heading for headings in _SECTIONS.values() for heading in headings}
_NAME_LINE = re.compile(r"^[^\W\d_][\w'. -]{1,79}$", re.UNICODE)


class PDFImportError(ValueError):
    """Raised when a PDF cannot be safely read or contains no extractable text."""


@dataclass(frozen=True)
class ExtractedPDF:
    text: str
    page_count: int


def extract_pdf_text(source: bytes | bytearray | BinaryIO) -> ExtractedPDF:
    """Extract selectable text from a PDF without making network calls."""
    if isinstance(source, (bytes, bytearray)):
        pdf_bytes = bytes(source)
    else:
        try:
            pdf_bytes = source.read(MAX_PDF_BYTES + 1)
        except OSError as error:
            raise PDFImportError(f"Could not read the selected PDF: {error}") from error
    if not pdf_bytes:
        raise PDFImportError("The selected PDF file is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PDFImportError("The PDF is larger than the 50 MB import limit.")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise PDFImportError("The selected file is not a valid PDF.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
    except (OSError, ValueError, PyPdfError, TypeError, KeyError, IndexError) as error:
        raise PDFImportError(f"Could not open this PDF: {error}") from error

    if reader.is_encrypted:
        raise PDFImportError("This PDF is password-protected. Remove its password and import it again.")
    page_count = len(reader.pages)
    if page_count == 0:
        raise PDFImportError("The PDF contains no pages.")
    if page_count > MAX_PDF_PAGES:
        raise PDFImportError(f"The PDF has {page_count} pages; the limit is {MAX_PDF_PAGES}.")

    page_texts: list[str] = []
    total_characters = 0
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
        except (OSError, ValueError, PyPdfError, TypeError, KeyError, IndexError) as error:
            raise PDFImportError(f"Could not extract text from PDF page {page_number}: {error}") from error
        if not page_text:
            page_text = ""
        if not isinstance(page_text, str):
            raise PDFImportError(f"PDF page {page_number} returned invalid text.")
        total_characters += len(page_text)
        if total_characters > MAX_EXTRACTED_CHARACTERS:
            raise PDFImportError("The PDF contains more than 500,000 characters of text.")
        page_texts.append(cast(str, page_text))

    text = "\n".join(page_texts).strip()
    if not text:
        raise PDFImportError(
            "No selectable text was found. This may be a scanned/image-only PDF; "
            "run OCR on it first, then import the searchable PDF."
        )
    return ExtractedPDF(text=text, page_count=page_count)


def _normalized_heading(line: str) -> str:
    heading = re.sub(r"^\s*\d+[.)]?\s*", "", line).strip().rstrip(":").strip().casefold()
    return re.sub(r"\s+", " ", heading)


def _section_blocks(text: str) -> tuple[dict[str, list[list[str]]], list[str]]:
    sections: dict[str, list[list[str]]] = {}
    top_lines: list[str] = []
    active_section: str | None = None
    current_block: list[str] = []

    def finish_block() -> None:
        nonlocal current_block
        if active_section is not None and current_block:
            sections.setdefault(active_section, []).append(current_block)
        current_block = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.isdigit():
            finish_block()
            continue
        section = next(
            (name for name, headings in _SECTIONS.items() if _normalized_heading(line) in headings),
            None,
        )
        if section is not None:
            finish_block()
            active_section = section
            continue
        if _normalized_heading(line) in _ALL_HEADINGS:
            continue
        if active_section is None:
            top_lines.append(line)
        else:
            current_block.append(line)
    finish_block()
    return sections, top_lines


def _name_from_top_lines(lines: list[str]) -> str:
    for line in lines:
        candidate = line.strip()
        if candidate.isdigit():
            continue
        if _EMAIL.search(candidate) or _PHONE.search(candidate):
            continue
        if len(candidate.split()) >= 2 and _NAME_LINE.fullmatch(candidate):
            return candidate
        break
    return ""


def _phone_from_text(text: str) -> str:
    for line in text.splitlines():
        for match in _PHONE.finditer(line):
            candidate = match.group().strip()
            digits = sum(character.isdigit() for character in candidate)
            digit_groups = re.findall(r"\d{2,}", candidate)
            looks_like_year_range = len(digit_groups) == 2 and all(
                _YEAR.fullmatch(group) for group in digit_groups
            )
            if digits >= 7 and len(digit_groups) >= 3 and not looks_like_year_range:
                return candidate
    return ""


def _bullet_text(line: str) -> tuple[str, bool]:
    match = _BULLET.match(line)
    return (line[match.end():].strip(), True) if match else (line.strip(), False)


def _is_date_line(line: str) -> bool:
    if _BULLET.match(line):
        return False
    head = line.split("|")[0]
    return (
        len(head) <= 90
        and bool(_YEAR.search(head))
        and bool(re.search(r"[–—-]|\bobecnie\b|\bpresent\b", head, re.IGNORECASE))
    )


def _split_dated_entries(blocks: list[list[str]]) -> list[list[str]]:
    """Regroup entries written as a title line followed by a date line (any language)."""
    lines = [line for block in blocks for line in block if line.strip()]
    starts = [
        index - 1
        for index, line in enumerate(lines)
        if index > 0 and _is_date_line(line) and not _BULLET.match(lines[index - 1])
        and not _is_date_line(lines[index - 1])
    ]
    if not starts or any("|" in block[0] and len(block[0].split("|")) >= 3 for block in blocks if block):
        return blocks
    regrouped: list[list[str]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        title = lines[start]
        dates = lines[start + 1].split("|")[0].strip()
        parts = [part.strip() for part in re.split(r"\s[–—-]\s", title, maxsplit=1)]
        if len(parts) > 1 and re.search(r"\b(?:sp\.|s\.a\.|ltd|inc|gmbh|llc|plc|corp)", parts[1], re.IGNORECASE):
            role, employer = parts
        else:
            role, employer = title.strip(), "[Review employer]"
        regrouped.append([f"{role} | {employer} | {dates}", *lines[start + 2:end]])
    return regrouped


def _education_entries(blocks: list[list[str]]) -> list[Education]:
    lines = [line for block in blocks for line in block if line.strip()]
    degree = re.compile(
        r"^(?:master|bachelor|foundation|diploma|degree|msc|bsc|phd|licencjat|magister|inżynier|studia)\b",
        re.IGNORECASE,
    )
    groups: list[list[str]] = []
    for line in lines:
        if degree.match(line) or not groups:
            groups.append([line])
        else:
            groups[-1].append(line)
    entries: list[Education] = []
    for group in groups:
        institution = "[Review institution]"
        years: list[str] = []
        details: list[str] = []
        for line in group[1:]:
            if _YEAR.search(line) and len(line) <= 90:
                years.extend(_YEAR.findall(line.split("|")[0]))
            elif institution == "[Review institution]" and not re.match(r"^(?:wynik|grade|result)\b", line, re.IGNORECASE):
                institution = line
            else:
                details.append(line)
        entries.append(
            Education(
                qualification=group[0],
                institution=institution,
                start_date=years[0] if years else "",
                end_date=years[1] if len(years) > 1 else "",
                details=details,
                verified=False,
            )
        )
    return entries


def _experience_entries(blocks: list[list[str]]) -> list[Experience]:
    blocks = _split_dated_entries(blocks)
    entries: list[Experience] = []
    evidence_note = "Extracted from PDF; confirm this text against the original CV."
    for block in blocks:
        lines = [line for line in block if line.strip()]
        if not lines:
            continue

        role = "[Review role]"
        employer = "[Review employer]"
        start_date = ""
        end_date = ""
        first_line = lines[0]
        if "|" in first_line:
            parts = [part.strip() for part in first_line.split("|") if part.strip()]
            if len(parts) >= 2:
                role, employer = parts[0], parts[1]
                date_part = " ".join(parts[2:])
                years = _YEAR.findall(date_part)
                if years:
                    start_date = years[0]
                    end_date = years[1] if len(years) > 1 else ""
                if re.search(r"\b(?:present|current|obecnie)\b", date_part, re.IGNORECASE):
                    end_date = "Present"
                lines = lines[1:]

        achievements: list[Achievement] = []
        responsibilities: list[str] = []
        for line in lines:
            clean_line, is_bullet = _bullet_text(line)
            if not clean_line:
                continue
            if is_bullet:
                achievements.append(
                    Achievement(claim=clean_line, evidence=evidence_note, verified=False)
                )
            elif achievements and clean_line[:1].islower():
                previous = achievements[-1]
                achievements[-1] = Achievement(
                    claim=f"{previous.claim} {clean_line}", evidence=evidence_note, verified=False
                )
            else:
                responsibilities.append(clean_line)
        entries.append(
            Experience(
                employer=employer,
                role=role,
                start_date=start_date,
                end_date=end_date,
                responsibilities=responsibilities,
                achievements=achievements,
                verified=False,
            )
        )
    return entries


def _skill_names(text: str) -> list[str]:
    """Split a skills line into tools only when every piece is short; otherwise keep the whole sentence."""
    pieces = [piece.strip() for piece in re.split(r"[,;|•](?![^(]*\))", text) if piece.strip()]
    if pieces and all(len(piece.split()) <= 4 for piece in pieces):
        return pieces
    whole = text.strip().rstrip(".")
    return [whole[:160]] if whole else []


def _project_entries(blocks: list[list[str]]) -> list[Project]:
    """Title line followed by bullet lines; bullets that wrap onto lowercase lines are merged."""
    lines = [line for block in blocks for line in block if line.strip()]
    projects: list[Project] = []
    for line in lines:
        text, is_bullet = _bullet_text(line)
        text = text.strip()
        if is_bullet:
            if projects:
                projects[-1].bullets.append(text)
        elif projects and projects[-1].bullets and text[:1].islower():
            projects[-1].bullets[-1] = f"{projects[-1].bullets[-1]} {text}"
        else:
            projects.append(Project(name=text, verified=False))
    return [project for project in projects if project.bullets or project.name]


def draft_blueprint_from_pdf(source: bytes | bytearray | BinaryIO) -> MasterBlueprint:
    """Create an unverified, editable blueprint draft from a text-based CV PDF."""
    extracted = extract_pdf_text(source)
    sections, top_lines = _section_blocks(extracted.text)
    email_match = _EMAIL.search(extracted.text)
    profile = Profile(
        name=_name_from_top_lines(top_lines),
        email=email_match.group() if email_match else "",
        phone=_phone_from_text(extracted.text),
        summary=" ".join(
            _bullet_text(line)[0].strip()
            for block in sections.get("summary", [])
            for line in block
            if line.strip()
        ),
    )
    skill_lines = [line for block in sections.get("skills", []) for line in block]
    if any(_BULLET.match(line) for line in skill_lines):
        skill_lines = [line for line in skill_lines if _BULLET.match(line)]
    skills = [
        Skill(
            name=skill_name.strip().rstrip("."),
            evidence="Imported from PDF; confirm this skill against the original CV.",
            verified=False,
        )
        for line in skill_lines
        for skill_name in _skill_names(_bullet_text(line)[0])
    ]
    education = _education_entries(sections.get("education", []))
    certifications = [
        Certification(name=line, verified=False)
        for block in sections.get("certifications", [])
        for line in block
        if line.strip()
    ]
    language_lines = [line for block in sections.get("languages", []) for line in block]
    language_lines += [
        line
        for block in sections.get("additional", [])
        for line in block
        if re.match(r"^\s*(?:[-*+•▪◦]\s*)?(?:język|language)\b", line, re.IGNORECASE)
    ]
    languages: list[Language] = []
    for line in language_lines:
        clean_line, _ = _bullet_text(line)
        clean_line = re.sub(r"^(?:język|language)\s+", "", clean_line, flags=re.IGNORECASE)
        if not clean_line:
            continue
        parts = re.split(r"\s*(?:[-–—:|])\s*", clean_line, maxsplit=1)
        languages.append(
            Language(
                name=parts[0].strip(),
                proficiency=parts[1].strip() if len(parts) > 1 else "",
                verified=False,
            )
        )

    blueprint = MasterBlueprint(
        profile=profile,
        experience=_experience_entries(sections.get("experience", [])),
        skills=skills,
        education=education,
        certifications=certifications,
        languages=languages,
        projects=_project_entries(sections.get("projects", [])),
        imported_cv_text=extracted.text,
    )
    try:
        blueprint.validate()
    except BlueprintValidationError as error:
        raise PDFImportError(f"Extracted PDF details could not be prepared for review: {error}") from error
    return blueprint


def draft_blueprint_from_pdf_path(path: str | Path) -> MasterBlueprint:
    """Read a selected PDF and create an unverified blueprint draft."""
    pdf_path = Path(path)
    try:
        with pdf_path.open("rb") as source:
            return draft_blueprint_from_pdf(source)
    except OSError as error:
        raise PDFImportError(f"Could not read {pdf_path}: {error}") from error
