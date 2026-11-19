"""Validated data models for a user's career blueprint."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class BlueprintValidationError(ValueError):
    """Raised when blueprint data is malformed or incomplete."""


def _object(value: Any, context: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BlueprintValidationError(f"{context} must be a JSON object.")
    unknown = set(value) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise BlueprintValidationError(f"{context} has unknown field(s): {names}.")
    return value


def _text(value: Any, context: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if optional and isinstance(value, str) and not value.strip():
        return None
    if not isinstance(value, str) or not value.strip():
        raise BlueprintValidationError(f"{context} must be a non-empty string.")
    return value.strip()


def _required_text(value: Any, context: str) -> str:
    result = _text(value, context)
    if result is None:
        raise BlueprintValidationError(f"{context} must be a non-empty string.")
    return result


def _text_list(value: Any, context: str) -> list[str]:
    if not isinstance(value, list):
        raise BlueprintValidationError(f"{context} must be a list.")
    return [_required_text(item, f"{context}[{index}]") for index, item in enumerate(value)]


def _boolean(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise BlueprintValidationError(f"{context} must be a boolean.")
    return value


@dataclass
class Profile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    target_roles: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: Any) -> Profile:
        data = _object(value, "profile", {"name", "email", "phone", "location", "summary", "target_roles"})
        return cls(
            name=_text(data.get("name", ""), "profile.name", optional=True) or "",
            email=_text(data.get("email", ""), "profile.email", optional=True) or "",
            phone=_text(data.get("phone", ""), "profile.phone", optional=True) or "",
            location=_text(data.get("location", ""), "profile.location", optional=True) or "",
            summary=_text(data.get("summary", ""), "profile.summary", optional=True) or "",
            target_roles=_text_list(data.get("target_roles", []), "profile.target_roles"),
        )


@dataclass
class Achievement:
    claim: str
    evidence: str
    metrics: str | None = None
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, context: str) -> Achievement:
        data = _object(value, context, {"claim", "evidence", "metrics", "verified"})
        return cls(
            claim=_required_text(data.get("claim"), f"{context}.claim"),
            evidence=_required_text(data.get("evidence"), f"{context}.evidence"),
            metrics=_text(data.get("metrics"), f"{context}.metrics", optional=True),
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Experience:
    employer: str
    role: str
    start_date: str = ""
    end_date: str = ""
    responsibilities: list[str] = field(default_factory=list)
    achievements: list[Achievement] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    verified: bool = True

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Experience:
        context = f"experience[{index}]"
        data = _object(
            value,
            context,
            {
                "employer",
                "role",
                "start_date",
                "end_date",
                "responsibilities",
                "achievements",
                "skills",
                "verified",
            },
        )
        achievements = data.get("achievements", [])
        if not isinstance(achievements, list):
            raise BlueprintValidationError(f"{context}.achievements must be a list.")
        return cls(
            employer=_required_text(data.get("employer"), f"{context}.employer"),
            role=_required_text(data.get("role"), f"{context}.role"),
            start_date=_text(data.get("start_date", ""), f"{context}.start_date", optional=True) or "",
            end_date=_text(data.get("end_date", ""), f"{context}.end_date", optional=True) or "",
            responsibilities=_text_list(data.get("responsibilities", []), f"{context}.responsibilities"),
            achievements=[
                Achievement.from_dict(item, f"{context}.achievements[{achievement_index}]")
                for achievement_index, item in enumerate(achievements)
            ],
            skills=_text_list(data.get("skills", []), f"{context}.skills"),
            verified=_boolean(data.get("verified", True), f"{context}.verified"),
        )


@dataclass
class Skill:
    name: str
    proficiency: str | None = None
    evidence: str | None = None
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Skill:
        context = f"skills[{index}]"
        data = _object(value, context, {"name", "proficiency", "evidence", "verified"})
        return cls(
            name=_required_text(data.get("name"), f"{context}.name"),
            proficiency=_text(data.get("proficiency"), f"{context}.proficiency", optional=True),
            evidence=_text(data.get("evidence"), f"{context}.evidence", optional=True),
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Education:
    qualification: str
    institution: str
    start_date: str = ""
    end_date: str = ""
    details: list[str] = field(default_factory=list)
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Education:
        context = f"education[{index}]"
        data = _object(value, context, {"qualification", "institution", "start_date", "end_date", "details", "verified"})
        return cls(
            qualification=_required_text(data.get("qualification"), f"{context}.qualification"),
            institution=_required_text(data.get("institution"), f"{context}.institution"),
            start_date=_text(data.get("start_date", ""), f"{context}.start_date", optional=True) or "",
            end_date=_text(data.get("end_date", ""), f"{context}.end_date", optional=True) or "",
            details=_text_list(data.get("details", []), f"{context}.details"),
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Certification:
    name: str
    organisation: str = ""
    expiry_date: str = ""
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Certification:
        context = f"certifications[{index}]"
        data = _object(value, context, {"name", "organisation", "expiry_date", "verified"})
        return cls(
            name=_required_text(data.get("name"), f"{context}.name"),
            organisation=_text(data.get("organisation", ""), f"{context}.organisation", optional=True) or "",
            expiry_date=_text(data.get("expiry_date", ""), f"{context}.expiry_date", optional=True) or "",
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Language:
    name: str
    proficiency: str = ""
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Language:
        context = f"languages[{index}]"
        data = _object(value, context, {"name", "proficiency", "verified"})
        return cls(
            name=_required_text(data.get("name"), f"{context}.name"),
            proficiency=_text(data.get("proficiency", ""), f"{context}.proficiency", optional=True) or "",
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Project:
    name: str
    bullets: list[str] = field(default_factory=list)
    verified: bool = False

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Project:
        context = f"projects[{index}]"
        data = _object(value, context, {"name", "bullets", "verified"})
        return cls(
            name=_required_text(data.get("name"), f"{context}.name"),
            bullets=_text_list(data.get("bullets", []), f"{context}.bullets"),
            verified=_boolean(data.get("verified", False), f"{context}.verified"),
        )


@dataclass
class Preferences:
    target_locations: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    seniority: str = ""
    preferred_cv_length_pages: int | None = None

    @classmethod
    def from_dict(cls, value: Any) -> Preferences:
        data = _object(
            value,
            "preferences",
            {"target_locations", "industries", "seniority", "preferred_cv_length_pages"},
        )
        pages = data.get("preferred_cv_length_pages")
        if pages is not None and (not isinstance(pages, int) or isinstance(pages, bool) or pages < 1):
            raise BlueprintValidationError("preferences.preferred_cv_length_pages must be a positive integer or null.")
        return cls(
            target_locations=_text_list(data.get("target_locations", []), "preferences.target_locations"),
            industries=_text_list(data.get("industries", []), "preferences.industries"),
            seniority=_text(data.get("seniority", ""), "preferences.seniority", optional=True) or "",
            preferred_cv_length_pages=pages,
        )


@dataclass
class MasterBlueprint:
    profile: Profile = field(default_factory=Profile)
    experience: list[Experience] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    languages: list[Language] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    preferences: Preferences = field(default_factory=Preferences)
    schema_version: int = 1
    imported_cv_text: str = ""

    @classmethod
    def from_dict(cls, value: Any) -> MasterBlueprint:
        data = _object(
            value,
            "blueprint",
            {
                "profile",
                "experience",
                "skills",
                "education",
                "certifications",
                "languages",
                "projects",
                "preferences",
                "schema_version",
                "imported_cv_text",
            },
        )
        version = data.get("schema_version", 1)
        if not isinstance(version, int) or isinstance(version, bool) or version != 1:
            raise BlueprintValidationError(f"Unsupported blueprint schema_version: {version!r}.")

        def entries(key: str) -> list[Any]:
            result = data.get(key, [])
            if not isinstance(result, list):
                raise BlueprintValidationError(f"{key} must be a list.")
            return result

        blueprint = cls(
            profile=Profile.from_dict(data.get("profile", {})),
            experience=[Experience.from_dict(item, i) for i, item in enumerate(entries("experience"))],
            skills=[Skill.from_dict(item, i) for i, item in enumerate(entries("skills"))],
            education=[Education.from_dict(item, i) for i, item in enumerate(entries("education"))],
            certifications=[
                Certification.from_dict(item, i) for i, item in enumerate(entries("certifications"))
            ],
            languages=[Language.from_dict(item, i) for i, item in enumerate(entries("languages"))],
            projects=[Project.from_dict(item, i) for i, item in enumerate(entries("projects"))],
            preferences=Preferences.from_dict(data.get("preferences", {})),
            schema_version=version,
            imported_cv_text=_text(
                data.get("imported_cv_text", ""),
                "blueprint.imported_cv_text",
                optional=True,
            )
            or "",
        )
        blueprint.validate()
        return blueprint

    def validate(self) -> None:
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool) or self.schema_version != 1:
            raise BlueprintValidationError(f"Unsupported blueprint schema_version: {self.schema_version!r}.")
        if not isinstance(self.profile, Profile):
            raise BlueprintValidationError("profile must be a Profile.")
        if not isinstance(self.preferences, Preferences):
            raise BlueprintValidationError("preferences must be a Preferences.")
        for field_name in ("name", "email", "phone", "location", "summary"):
            _text(getattr(self.profile, field_name), f"profile.{field_name}", optional=True)
        _text_list(self.profile.target_roles, "profile.target_roles")
        for name, values, expected_type in (
            ("experience", self.experience, Experience),
            ("skills", self.skills, Skill),
            ("education", self.education, Education),
            ("certifications", self.certifications, Certification),
            ("languages", self.languages, Language),
            ("projects", self.projects, Project),
        ):
            if not isinstance(values, list) or any(not isinstance(item, expected_type) for item in values):
                raise BlueprintValidationError(f"{name} contains invalid entries.")
        for index, item in enumerate(self.experience):
            _text(item.employer, f"experience[{index}].employer")
            _text(item.role, f"experience[{index}].role")
            _boolean(item.verified, f"experience[{index}].verified")
            _text(item.start_date, f"experience[{index}].start_date", optional=True)
            _text(item.end_date, f"experience[{index}].end_date", optional=True)
            _text_list(item.responsibilities, f"experience[{index}].responsibilities")
            _text_list(item.skills, f"experience[{index}].skills")
            if not isinstance(item.achievements, list) or any(
                not isinstance(achievement, Achievement) for achievement in item.achievements
            ):
                raise BlueprintValidationError(f"experience[{index}].achievements contains invalid entries.")
            for achievement_index, achievement in enumerate(item.achievements):
                context = f"experience[{index}].achievements[{achievement_index}]"
                _text(achievement.claim, f"{context}.claim")
                _text(achievement.evidence, f"{context}.evidence")
                _text(achievement.metrics, f"{context}.metrics", optional=True)
                _boolean(achievement.verified, f"experience[{index}].achievements[{achievement_index}].verified")
        for index, skill in enumerate(self.skills):
            _text(skill.name, f"skills[{index}].name")
            _text(skill.proficiency, f"skills[{index}].proficiency", optional=True)
            _text(skill.evidence, f"skills[{index}].evidence", optional=True)
            _boolean(skill.verified, f"skills[{index}].verified")
        for index, item in enumerate(self.education):
            context = f"education[{index}]"
            _text(item.qualification, f"{context}.qualification")
            _text(item.institution, f"{context}.institution")
            _text(item.start_date, f"{context}.start_date", optional=True)
            _text(item.end_date, f"{context}.end_date", optional=True)
            _text_list(item.details, f"{context}.details")
            _boolean(item.verified, f"{context}.verified")
        for index, item in enumerate(self.certifications):
            context = f"certifications[{index}]"
            _text(item.name, f"{context}.name")
            _text(item.organisation, f"{context}.organisation", optional=True)
            _text(item.expiry_date, f"{context}.expiry_date", optional=True)
            _boolean(item.verified, f"{context}.verified")
        for index, item in enumerate(self.languages):
            context = f"languages[{index}]"
            _text(item.name, f"{context}.name")
            _text(item.proficiency, f"{context}.proficiency", optional=True)
            _boolean(item.verified, f"{context}.verified")
        if not isinstance(self.preferences, Preferences):
            raise BlueprintValidationError("preferences must be a Preferences.")
        _text_list(self.preferences.target_locations, "preferences.target_locations")
        _text_list(self.preferences.industries, "preferences.industries")
        _text(self.preferences.seniority, "preferences.seniority", optional=True)
        pages = self.preferences.preferred_cv_length_pages
        if pages is not None and (not isinstance(pages, int) or isinstance(pages, bool) or pages < 1):
            raise BlueprintValidationError("preferences.preferred_cv_length_pages must be a positive integer or null.")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
