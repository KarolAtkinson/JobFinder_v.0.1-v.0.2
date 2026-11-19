"""Candidate-confirmed additions to the blueprint (the user attests; nothing is assumed)."""

from __future__ import annotations

from collections.abc import Iterable

from cv_optimiser.models import MasterBlueprint, Skill

MAX_SKILL_NAME = 120


def mark_all_verified(blueprint: MasterBlueprint) -> int:
    """Mark every imported record as confirmed by the candidate; returns how many changed."""
    changed = 0
    for experience in blueprint.experience:
        if not experience.verified:
            experience.verified = True
            changed += 1
        for achievement in experience.achievements:
            if not achievement.verified:
                achievement.verified = True
                changed += 1
    for collection in (
        blueprint.skills, blueprint.education, blueprint.certifications, blueprint.languages, blueprint.projects
    ):
        for item in collection:
            if not item.verified:
                item.verified = True
                changed += 1
    return changed


def attest_skills(blueprint: MasterBlueprint, requirements: Iterable[str], job_title: str) -> int:
    """Add candidate-confirmed skills for requirements; returns how many were added."""
    existing = {skill.name.casefold() for skill in blueprint.skills}
    context = f" for '{job_title}'" if job_title.strip() else ""
    added = 0
    for requirement in requirements:
        name = " ".join(requirement.split()).strip(" .;:-•")
        if len(name) > MAX_SKILL_NAME:
            name = name[:MAX_SKILL_NAME].rsplit(" ", 1)[0].strip(" ,.;:-•")
        if not name or name.casefold() in existing:
            continue
        blueprint.skills.append(
            Skill(
                name=name,
                evidence=f"Confirmed by the candidate{context}; no specific achievement recorded.",
                verified=True,
            )
        )
        existing.add(name.casefold())
        added += 1
    return added
