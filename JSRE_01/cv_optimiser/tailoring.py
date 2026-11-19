"""Create conservative CV drafts from a blueprint and a job analysis."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from collections.abc import Iterable

from docx import Document
from docx.document import Document as DocumentObject

from cv_optimiser.job_analysis import JobAnalysis
from cv_optimiser.models import (
    Achievement,
    Certification,
    Education,
    Experience,
    Language,
    MasterBlueprint,
    Project,
    Skill,
)


@dataclass(frozen=True)
class TailoredAchievement:
    source: Achievement


@dataclass(frozen=True)
class TailoredExperience:
    source: Experience
    achievements: tuple[TailoredAchievement, ...]


@dataclass(frozen=True)
class TailoredProject:
    source: Project


@dataclass(frozen=True)
class TailoredCV:
    job_title: str
    name: str
    email: str
    phone: str
    location: str
    experience: tuple[TailoredExperience, ...]
    skills: tuple[Skill, ...]
    education: tuple[Education, ...]
    certifications: tuple[Certification, ...]
    languages: tuple[Language, ...]
    summary: str = ""
    projects: tuple[TailoredProject, ...] = ()


def build_tailored_cv(blueprint: MasterBlueprint, analysis: JobAnalysis) -> TailoredCV:
    """Select verified blueprint content, prioritising evidence matched to the job."""
    blueprint.validate()
    relevant_sources = {
        source
        for match in analysis.matches
        if match.status in {"direct", "partial"}
        for source in match.evidence
    }

    experiences_with_scores: list[tuple[int, TailoredExperience]] = []
    for index, item in enumerate(blueprint.experience):
        if not item.verified:
            continue
        verified_achievements = [
            (achievement_index, achievement)
            for achievement_index, achievement in enumerate(item.achievements)
            if achievement.verified
        ]
        verified_achievements.sort(
            key=lambda pair: f"Experience {index + 1}: achievement {pair[0] + 1}" not in relevant_sources
        )
        relevance = sum(
            source.startswith(f"Experience {index + 1}:")
            for source in relevant_sources
        )
        experiences_with_scores.append(
            (
                relevance,
                TailoredExperience(
                    source=item,
                    achievements=tuple(
                        TailoredAchievement(source=achievement) for _, achievement in verified_achievements
                    ),
                ),
            )
        )
    experiences_with_scores.sort(key=lambda pair: -pair[0])
    experiences = [item for _, item in experiences_with_scores]
    projects = tuple(TailoredProject(source=project) for project in blueprint.projects if project.verified)

    skills = [
        (index, skill)
        for index, skill in enumerate(blueprint.skills)
        if skill.verified
    ]
    skills.sort(key=lambda pair: f"Skill {pair[0] + 1}: {pair[1].name}" not in relevant_sources)

    return TailoredCV(
        job_title=analysis.job_title,
        name=blueprint.profile.name,
        email=blueprint.profile.email,
        phone=blueprint.profile.phone,
        location=blueprint.profile.location,
        experience=tuple(experiences),
        skills=tuple(skill for _, skill in skills),
        education=tuple(item for item in blueprint.education if item.verified),
        certifications=tuple(item for item in blueprint.certifications if item.verified),
        languages=tuple(item for item in blueprint.languages if item.verified),
        summary=blueprint.profile.summary,
        projects=projects,
    )


def _add_section(document: DocumentObject, title: str) -> None:
    document.add_heading(title, level=1)


_SKILL_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Security, Risk & Compliance", (
        "nist", "iso", "iec", "grc", "risk", "ryzyk", "zagro", "threat", "podatno", "vulnerab", "owasp", "incyd",
        "incident", "nis2", "ksc", "audyt", "audit", "complian", "soc", "siem", "uwierzytel", "authent", "secur",
        "bezpiecz", "security", "monitor", "detect", "forensic",
    )),
    ("Systems & Networking", (
        "windows", "linux", "ubuntu", "debian", "kali", "active directory", "tcp", "network", "sieci", "firewall",
        "zapór", "dns", "tls", "apache", "operacyjn", "server", "vmware", "virtualbox",
    )),
    ("Programming & Databases", (
        "python", "bash", "sql", "html", "css", "javascript", "c++", "c#", "język", "php", "maria", "baz", "database",
        "powershell", "java",
    )),
    ("Tools & Platforms", (
        "git", "github", "visual studio", "cloudflare", "supabase", "neon", "pages", "hosting", "publikacj",
    )),
)
_CONFIRMED_GROUP = "Job-relevant competencies"


def group_skills(skills: Iterable[Skill]) -> list[tuple[str, list[str]]]:
    """Organise skills into named groups (keyword-based); order follows _SKILL_GROUPS."""
    grouped: dict[str, list[str]] = {}
    for skill in skills:
        name = skill.name.strip()
        if not name:
            continue
        lowered = name.casefold()
        if (skill.evidence or "").startswith("Confirmed by the candidate"):
            label = _CONFIRMED_GROUP
        else:
            label = next(
                (group for group, keys in _SKILL_GROUPS if any(key in lowered for key in keys)),
                "Other skills",
            )
        if name not in grouped.setdefault(label, []):
            grouped[label].append(name)
    order = [group for group, _ in _SKILL_GROUPS] + ["Other skills", _CONFIRMED_GROUP]
    return [(label, grouped[label]) for label in order if label in grouped]


DEFAULT_LANGUAGE = "en-GB"

_LABELS: dict[str, dict[str, str]] = {
    "en-GB": {
        "target_role": "Target role",
        "summary": "Professional Summary",
        "experience": "Professional Experience",
        "projects": "Academic Projects",
        "skills": "Skills",
        "education": "Education",
        "certifications": "Certifications",
        "languages": "Languages",
        "Security, Risk & Compliance": "Security, Risk & Compliance",
        "Systems & Networking": "Systems & Networking",
        "Programming & Databases": "Programming & Databases",
        "Tools & Platforms": "Tools & Platforms",
        "Other skills": "Other skills",
        "Job-relevant competencies": "Job-relevant competencies",
        "present": "Present",
    },
    "pl": {
        "target_role": "Stanowisko docelowe",
        "summary": "Podsumowanie kandydata",
        "experience": "Doświadczenie zawodowe",
        "projects": "Projekty akademickie",
        "skills": "Umiejętności",
        "education": "Edukacja",
        "certifications": "Certyfikaty",
        "languages": "Języki",
        "Security, Risk & Compliance": "Bezpieczeństwo, ryzyko i zgodność",
        "Systems & Networking": "Systemy i sieci",
        "Programming & Databases": "Programowanie i bazy danych",
        "Tools & Platforms": "Narzędzia i platformy",
        "Other skills": "Pozostałe umiejętności",
        "Job-relevant competencies": "Kompetencje istotne dla stanowiska",
        "present": "obecnie",
    },
}


def _labels(language: str) -> dict[str, str]:
    if language not in _LABELS:
        raise ValueError(f"Unsupported CV language: {language}")
    return _LABELS[language]


def _localise_date(value: str, labels: dict[str, str]) -> str:
    return labels["present"] if value.strip().casefold() in {"present", "obecnie", "current"} else value


def render_docx(cv: TailoredCV, language: str = DEFAULT_LANGUAGE) -> bytes:
    """Render the verified-only tailored draft."""
    labels = _labels(language)

    document = Document()
    document.core_properties.title = f"CV - {cv.job_title}" if cv.job_title else "CV"
    document.core_properties.language = language
    if cv.name:
        document.add_heading(cv.name, level=0)
    contact = " | ".join(value for value in (cv.email, cv.phone, cv.location) if value)
    if contact:
        document.add_paragraph(contact)
    if cv.job_title:
        document.add_paragraph(f"{labels['target_role']}: {cv.job_title}")
    if cv.summary:
        _add_section(document, labels["summary"])
        document.add_paragraph(cv.summary)

    if cv.experience:
        _add_section(document, labels["experience"])
        for entry in cv.experience:
            dates = " - ".join(
                _localise_date(value, labels)
                for value in (entry.source.start_date, entry.source.end_date)
                if value
            )
            heading = " | ".join(
                value
                for value in (entry.source.role, entry.source.employer, dates)
                if value and not value.startswith("[Review")
            )
            document.add_heading(heading, level=2)
            for achievement in entry.achievements:
                claim = achievement.source.claim
                if achievement.source.metrics and achievement.source.metrics not in claim:
                    claim = f"{claim} ({achievement.source.metrics})"
                document.add_paragraph(claim, style="List Bullet")

    if cv.projects:
        _add_section(document, labels["projects"])
        for project in cv.projects:
            document.add_heading(project.source.name, level=2)
            for bullet in project.source.bullets:
                document.add_paragraph(bullet, style="List Bullet")

    if cv.skills:
        _add_section(document, labels["skills"])
        for label, names in group_skills(cv.skills):
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.add_run(f"{labels.get(label, label)}: ").bold = True
            paragraph.add_run("; ".join(names))

    if cv.education:
        _add_section(document, labels["education"])
        for item in cv.education:
            dates = " - ".join(
                _localise_date(value, labels) for value in (item.start_date, item.end_date) if value
            )
            line = " | ".join(value for value in (item.qualification, item.institution, dates) if value)
            document.add_paragraph(line)
            for detail in item.details:
                document.add_paragraph(detail, style="List Bullet")

    if cv.certifications:
        _add_section(document, labels["certifications"])
        for item in cv.certifications:
            line = " | ".join(value for value in (item.name, item.organisation, item.expiry_date) if value)
            document.add_paragraph(line, style="List Bullet")

    if cv.languages:
        _add_section(document, labels["languages"])
        for item in cv.languages:
            line = " | ".join(value for value in (item.name, item.proficiency) if value)
            document.add_paragraph(line, style="List Bullet")

    output = BytesIO()
    document.save(output)
    return output.getvalue()
