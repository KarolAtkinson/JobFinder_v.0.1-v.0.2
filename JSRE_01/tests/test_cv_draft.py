import io
import json

from docx import Document

from cv_optimiser.cv_draft import (
    CVDraft,
    draft_from_canvas,
    fill_draft,
    render_draft_docx,
    save_draft,
    split_lines,
)
from cv_optimiser.job_analysis import analyze_job_description
from cv_optimiser.models import (
    Achievement,
    Certification,
    Education,
    Experience,
    Language,
    MasterBlueprint,
    Profile,
    Project,
    Skill,
)


def _master() -> MasterBlueprint:
    return MasterBlueprint(
        profile=Profile(name="Jan Kowalski", email="jan@example.com", summary="Jestem specjalistą ds. bezpieczeństwa."),
        experience=[
            Experience(
                employer="Firma Sp. z o.o.",
                role="Specjalista IT",
                start_date="2022",
                end_date="Present",
                achievements=[Achievement(claim="Wdrożyłem politykę haseł", evidence="x", verified=True)],
                verified=True,
            ),
            Experience(employer="Ukryta", role="Rola", verified=False),
        ],
        skills=[Skill(name="Linux", verified=True), Skill(name="Analiza ryzyka", verified=True)],
        education=[Education(qualification="Magister", institution="Uczelnia", verified=True)],
        certifications=[Certification(name="ISO 27001", organisation="BSI", verified=True)],
        languages=[Language(name="Angielski", proficiency="C1", verified=True)],
        projects=[Project(name="Praca magisterska", bullets=["Projekt systemu IDS"], verified=True)],
    )


class Client:
    """Answers each section request from its own keys, like a well-behaved model."""

    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.calls = []

    def chat(self, system, user, schema=None):
        payload = json.loads(user)
        self.calls.append(payload)
        if "master_summary" in payload:
            kind, answer = "summary", {"text": "Jestem specjalistą, który wdraża zabezpieczenia."}
        elif "project" in payload:
            kind, answer = "project", {"bullets": ["Projektuję system IDS."]}
        elif "role" in payload:
            kind, answer = "experience", {"bullets": ["Wdrażam politykę haseł."]}
        else:
            kind, answer = "skills", {"groups": [{"label": "Systemy", "skills": ["Linux", "Nieznana umiejętność"]}]}
        return json.dumps(self.overrides.get(kind, answer))


def _canvas() -> MasterBlueprint:
    """Same layout as the master, with every body left empty."""
    return MasterBlueprint(
        profile=Profile(name="Jan Kowalski", email="jan@example.com"),
        experience=[Experience(employer="Firma Sp. z o.o.", role="Specjalista IT", start_date="2022", end_date="Present")],
        projects=[Project(name="Praca magisterska")],
    )


def _analysis(master):
    return analyze_job_description("Requirements:\n- Linux administration\n", master, job_title="Analityk")


def test_canvas_keeps_headings_and_copies_missing_facts_from_the_master():
    draft = draft_from_canvas(_canvas(), _master(), "Analityk")
    assert draft.summary == "" and draft.skills == []
    assert [e.employer for e in draft.experience] == ["Firma Sp. z o.o."]
    assert draft.experience[0].bullets == []
    assert draft.projects[0].name == "Praca magisterska" and draft.projects[0].bullets == []
    assert draft.certifications == ["ISO 27001 – BSI"] and draft.languages == ["Angielski – C1"]
    assert draft.education[0].qualification == "Magister"


def test_sections_that_already_have_text_in_the_canvas_are_kept():
    canvas = _canvas()
    canvas.profile.summary = "Moje własne podsumowanie."
    canvas.projects[0].bullets = ["Własny opis projektu."]
    master = _master()
    client = Client()
    draft, _ = fill_draft(master, canvas, _analysis(master), client, "pl")
    assert draft.summary == "Moje własne podsumowanie."
    assert draft.projects[0].bullets == ["Własny opis projektu."]
    assert len(client.calls) == 2  # only the experience and skills sections were empty


def test_canvas_slot_without_a_master_entry_is_reported_not_guessed():
    canvas = _canvas()
    canvas.experience[0].employer = "Zupełnie inna firma"
    canvas.projects.append(Project(name="Inny projekt"))
    master = _master()
    draft, warnings = fill_draft(master, canvas, _analysis(master), Client(), "pl")
    assert draft.experience[0].bullets == []
    assert sum("no matching entry" in w for w in warnings) == 2


def test_fill_draft_writes_each_section_with_a_narrow_request():
    master = _master()
    client = Client()
    steps = []
    draft, warnings = fill_draft(master, _canvas(), _analysis(master), client, "pl", lambda *step: steps.append(step))
    assert warnings == []
    assert len(client.calls) == 4  # summary, one experience, skills, one project
    assert draft.summary.startswith("Jestem specjalistą")
    assert draft.experience[0].bullets == ["Wdrażam politykę haseł."]
    assert draft.projects[0].bullets == ["Projektuję system IDS."]
    assert steps[-1][1] == steps[-1][2]
    # The agent never sees unverified experience.
    assert all("Ukryta" not in json.dumps(call, ensure_ascii=False) for call in client.calls)


def test_skills_not_in_the_blueprint_are_dropped():
    master = _master()
    draft, _ = fill_draft(master, _canvas(), _analysis(master), Client(), "pl")
    assert [s for g in draft.skills for s in g.skills] == ["Linux"]


def test_invented_numbers_fall_back_to_the_source_wording():
    master = _master()
    client = Client({"experience": {"bullets": ["Wdrożyłem politykę dla 500 użytkowników."]}})
    draft, warnings = fill_draft(master, _canvas(), _analysis(master), client, "pl")
    assert draft.experience[0].bullets == ["Wdrożyłem politykę haseł"]
    assert any("Firma" in warning for warning in warnings)


def test_english_output_is_rejected_for_the_polish_cv():
    master = _master()
    client = Client({"summary": {"text": "I am a specialist and the team uses the tools with the process."}})
    draft, warnings = fill_draft(master, _canvas(), _analysis(master), client, "pl")
    assert draft.summary == master.profile.summary
    assert any("Summary" in warning for warning in warnings)


def test_render_uses_polish_headings_and_skips_empty_sections():
    master = _master()
    draft, _ = fill_draft(master, _canvas(), _analysis(master), Client(), "pl")
    document = Document(io.BytesIO(render_draft_docx(draft, "pl")))
    text = "\n".join(p.text for p in document.paragraphs)
    for expected in ("DOŚWIADCZENIE ZAWODOWE", "UMIEJĘTNOŚCI", "PROJEKTY AKADEMICKIE", "obecnie", "ISO 27001 – BSI"):
        assert expected in text
    empty = render_draft_docx(CVDraft(name="X"), "pl")
    assert "DOŚWIADCZENIE" not in "\n".join(p.text for p in Document(io.BytesIO(empty)).paragraphs)


def test_draft_round_trips_through_json(tmp_path):
    master = _master()
    draft, _ = fill_draft(master, _canvas(), _analysis(master), Client(), "pl")
    path = tmp_path / "draft.json"
    save_draft(draft, path)
    assert CVDraft.from_dict(json.loads(path.read_text(encoding="utf-8"))) == draft


def test_split_lines_strips_bullet_marks():
    assert split_lines("• jeden\n- dwa\n\n  trzy ") == ["jeden", "dwa", "trzy"]
