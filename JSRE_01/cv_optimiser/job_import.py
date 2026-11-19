"""Local .txt job-posting import that pre-fills the job application fields."""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from pathlib import Path

MAX_JOB_FILE_BYTES = 1024 * 1024
_TITLE_LABELS = (
    "job title", "position title", "position", "role", "title", "vacancy",
    "stanowisko", "nazwa stanowiska",
)
_INDUSTRY_LABELS = ("industry", "sector", "branża", "branza", "sektor")
_LABELLED = re.compile(r"^\s*(?:[-*•]\s*)?([^:：|]{2,30})\s*[:：]\s*(.+?)\s*$")


class JobImportError(ValueError):
    """Raised when a job posting file cannot be safely read."""


@dataclass(frozen=True)
class JobPosting:
    title: str
    industry: str
    description: str


def _decode(data: bytes) -> str:
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise JobImportError("The file's text encoding is not supported. Save it as UTF-8 and try again.")


def parse_job_posting(text: str) -> JobPosting:
    """Split a pasted/loaded posting into title, optional industry and the full description."""
    description = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").strip()
    if not description:
        raise JobImportError("The job application file is empty.")

    title = ""
    industry = ""
    for line in description.splitlines()[:40]:
        match = _LABELLED.match(line)
        if not match:
            continue
        label = match.group(1).strip().casefold()
        value = match.group(2).strip()
        if not title and label in _TITLE_LABELS:
            title = value
        elif not industry and label in _INDUSTRY_LABELS:
            industry = value

    if not title:
        for line in description.splitlines():
            candidate = line.strip()
            if candidate and len(candidate) <= 100 and not _LABELLED.match(candidate):
                title = candidate
                break
    return JobPosting(title=title[:200], industry=industry[:200], description=description)


def load_job_posting(path: str | Path) -> JobPosting:
    """Read a .txt job posting from disk without any network access."""
    file_path = Path(path)
    try:
        with file_path.open("rb") as source:
            data = source.read(MAX_JOB_FILE_BYTES + 1)
    except OSError as error:
        raise JobImportError(f"Could not read {file_path}: {error}") from error
    if len(data) > MAX_JOB_FILE_BYTES:
        raise JobImportError("The job application file is larger than the 1 MB import limit.")
    return parse_job_posting(_decode(data))
