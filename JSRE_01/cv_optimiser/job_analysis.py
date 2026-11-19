"""Rule-based job requirement extraction and evidence matching."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cv_optimiser.models import MasterBlueprint


class JobAnalysisError(ValueError):
    """Raised when a job description cannot be analysed."""


@dataclass(frozen=True)
class JobRequirement:
    text: str
    priority: str
    category: str


@dataclass(frozen=True)
class RequirementMatch:
    requirement: JobRequirement
    status: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class JobAnalysis:
    job_title: str
    industry: str
    requirements: tuple[JobRequirement, ...]
    matches: tuple[RequirementMatch, ...]
    alignment_score: int


_ESSENTIAL_HEADINGS = (
    "requirements",
    "required qualifications",
    "minimum qualifications",
    "essential criteria",
    "what you'll need",
    "what you will need",
    "must have",
    "what we're looking for",
    "your experience",
    "qualifications",
)
_DESIRABLE_HEADINGS = (
    "preferred qualifications",
    "preferred",
    "desirable",
    "nice to have",
    "bonus",
    "additional qualifications",
)
_RESPONSIBILITY_HEADINGS = (
    "responsibilities",
    "what you'll do",
    "what you will do",
    "the role",
    "role overview",
)
_REQUIREMENT_SIGNAL = re.compile(
    r"\b(experience|experienced|proficiency|proficient|knowledge|ability|able|"
    r"familiar|expertise|skilled|qualification|degree|certification|must|required|"
    r"proven|strong|excellent|preferred|desirable|bonus|develop|manage|lead|"
    r"build|deliver|analyse|analyze|coordinate|communicate)\b",
    re.IGNORECASE,
)
_DESIRABLE_SIGNAL = re.compile(r"\b(preferred|desirable|ideally|bonus|nice to have)\b", re.IGNORECASE)
_CATEGORY_PATTERNS = (
    ("education", re.compile(r"\b(degree|bachelor|master|phd|education|qualification)\b", re.I)),
    ("certification", re.compile(r"\b(certification|certified|licence|license)\b", re.I)),
    ("experience", re.compile(r"\b(years?|experience|experienced)\b", re.I)),
    ("responsibility", re.compile(r"\b(manage|lead|deliver|coordinate|build|develop|own)\b", re.I)),
)
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in",
    "is", "it", "of", "on", "or", "our", "the", "this", "to", "we", "with", "you", "your",
    "ability", "able", "experience", "experienced", "knowledge", "proficiency", "proficient",
    "familiar", "expertise", "skilled", "strong", "excellent", "required", "preferred",
    "desirable", "bonus", "must", "plus", "minimum", "ideally",
}
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*", re.IGNORECASE)


def _heading_priority(line: str) -> str | None:
    heading = line.strip().casefold().rstrip(":").strip()
    for candidates, priority in (
        (_DESIRABLE_HEADINGS, "desirable"),
        (_ESSENTIAL_HEADINGS, "essential"),
        (_RESPONSIBILITY_HEADINGS, "essential"),
    ):
        if any(heading == candidate or heading.startswith(candidate + " ") for candidate in candidates):
            return priority
    return None


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) <= 90 and (stripped.endswith(":") or _heading_priority(stripped) is not None)


def _category(text: str) -> str:
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(text):
            return category
    return "skill"


def extract_requirements(description: str) -> tuple[JobRequirement, ...]:
    """Extract requirement statements from headings, bullets, and prose."""
    if not isinstance(description, str) or not description.strip():
        raise JobAnalysisError("Enter a job description before analysing it.")

    requirements: list[JobRequirement] = []
    seen: set[str] = set()
    section_priority: str | None = None

    for raw_line in description.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        detected_priority = _heading_priority(line)
        if _is_heading(line) and (detected_priority is not None or line.endswith(":")):
            section_priority = detected_priority
            continue

        cleaned = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s*", "", line).strip()
        fragments = re.split(r"(?<=[.;])\s+", cleaned)
        for fragment in fragments:
            text = fragment.strip(" \t-•;.")
            if not text:
                continue
            if section_priority is None and not _REQUIREMENT_SIGNAL.search(text):
                continue
            priority = "desirable" if _DESIRABLE_SIGNAL.search(text) else (section_priority or "essential")
            normalized = " ".join(text.casefold().split())
            if normalized in seen:
                continue
            seen.add(normalized)
            requirements.append(JobRequirement(text=text, priority=priority, category=_category(text)))

    return tuple(requirements)


def _tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN.findall(text)
        if token.casefold() not in _STOP_WORDS and len(token) > 1
    }


def _blueprint_evidence(blueprint: MasterBlueprint) -> list[tuple[str, str, bool]]:
    records: list[tuple[str, str, bool]] = []
    for index, experience in enumerate(blueprint.experience):
        records.append((experience.role, f"Experience {index + 1}: role", False))
        for responsibility_index, responsibility in enumerate(experience.responsibilities):
            records.append(
                (
                    responsibility,
                    f"Experience {index + 1}: responsibility {responsibility_index + 1}",
                    False,
                )
            )
        for achievement_index, achievement in enumerate(experience.achievements):
            content = " ".join(filter(None, (achievement.claim, achievement.evidence, achievement.metrics)))
            records.append(
                (
                    content,
                    f"Experience {index + 1}: achievement {achievement_index + 1}",
                    experience.verified and achievement.verified,
                )
            )
    for index, skill in enumerate(blueprint.skills):
        content = " ".join(filter(None, (skill.name, skill.proficiency, skill.evidence)))
        records.append((content, f"Skill {index + 1}: {skill.name}", skill.verified))
    for index, education in enumerate(blueprint.education):
        records.append(
            (f"{education.qualification} {education.institution} {' '.join(education.details)}",
             f"Education {index + 1}: {education.qualification}", False)
        )
    for index, certification in enumerate(blueprint.certifications):
        records.append(
            (f"{certification.name} {certification.organisation}",
             f"Certification {index + 1}: {certification.name}", certification.verified)
        )
    for index, language in enumerate(blueprint.languages):
        records.append((f"{language.name} {language.proficiency}", f"Language {index + 1}: {language.name}", False))
    return records


def match_requirements(
    requirements: tuple[JobRequirement, ...],
    blueprint: MasterBlueprint,
) -> tuple[tuple[RequirementMatch, ...], int]:
    """Match requirements to recorded evidence using transparent token overlap."""
    blueprint.validate()
    evidence_records = _blueprint_evidence(blueprint)
    token_records = [(text, source, verified, _tokens(text)) for text, source, verified in evidence_records]
    matches: list[RequirementMatch] = []
    score_total = 0.0
    weight_total = 0

    for requirement in requirements:
        required_tokens = _tokens(requirement.text)
        matched_records: list[tuple[str, bool, float]] = []
        for _, source, verified, evidence_tokens in token_records:
            if not required_tokens:
                continue
            coverage = len(required_tokens & evidence_tokens) / len(required_tokens)
            if coverage >= 0.25:
                matched_records.append((source, verified, coverage))

        best_verified = max((coverage for _, verified, coverage in matched_records if verified), default=0.0)
        verified_records = [record[3] for record in token_records if record[2]]
        verified_coverage = (
            len(required_tokens & set.union(*verified_records)) / len(required_tokens)
            if required_tokens and verified_records
            else 0.0
        )
        if best_verified >= 0.6 or verified_coverage >= 0.8:
            status = "direct"
            value = 1.0
        elif matched_records:
            status = "partial"
            value = 0.5
        else:
            status = "missing"
            value = 0.0
        sources = tuple(dict.fromkeys(source for source, _, _ in matched_records))
        matches.append(RequirementMatch(requirement=requirement, status=status, evidence=sources))
        weight = 2 if requirement.priority == "essential" else 1
        score_total += value * weight
        weight_total += weight

    score = round(score_total / weight_total * 100) if weight_total else 0
    return tuple(matches), score


def analyze_job_description(
    description: str,
    blueprint: MasterBlueprint,
    *,
    job_title: str = "",
    industry: str = "",
) -> JobAnalysis:
    requirements = extract_requirements(description)
    matches, score = match_requirements(requirements, blueprint)
    return JobAnalysis(
        job_title=job_title.strip(),
        industry=industry.strip(),
        requirements=requirements,
        matches=matches,
        alignment_score=score,
    )
