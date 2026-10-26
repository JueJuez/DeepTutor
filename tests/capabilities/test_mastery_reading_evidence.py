"""Reader references must remain verifiable after a card and process outlive a turn."""

import json
from types import SimpleNamespace
from zipfile import ZipFile

import pymupdf
import pytest

from deeptutor.capabilities.mastery import tools
from deeptutor.learning import semantic_assessment as semantic
from deeptutor.learning.lesson_evidence import LessonUnavailable
from deeptutor.learning.models import KnowledgeType, PendingQuestion
from deeptutor.learning.reading_evidence import reading_packet
from deeptutor.learning.service import LearningService, MasteryInteractionError
from deeptutor.learning.storage import LearningStore
from deeptutor.reading.store import ReadingStore
from deeptutor.services.session.sqlite_store import SQLiteSessionStore

pytest_plugins = ["tests.capabilities.test_mastery_question_groups"]
TEXT = "The gradient points uphill. Descent moves in the opposite direction."


def material(tmp_path, extension):
    path = tmp_path / f"source.{extension}"
    if extension == "pdf":
        with pymupdf.open() as document:
            document.new_page().insert_text((40, 60), TEXT)
            document.save(path)
    else:
        with ZipFile(path, "w") as archive:
            archive.writestr("mimetype", "application/epub+zip")
            archive.writestr(
                "META-INF/container.xml",
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
            )
            archive.writestr(
                "book.opf",
                '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">synthetic</dc:identifier><dc:title>Gradient</dc:title><dc:language>en</dc:language></metadata><manifest><item id="u1" href="unit.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="u1"/></spine></package>',
            )
            archive.writestr(
                "unit.xhtml",
                f'<html xmlns="http://www.w3.org/1999/xhtml"><body><p>{TEXT}</p></body></html>',
            )
    store = ReadingStore(tmp_path / "reading")
    manifest = store.ingest(path)
    return store, {
        "material_id": manifest.material_id,
        "revision": manifest.revision,
        "locators": [1],
    }


def wire(monkeypatch, service, reading, verdict=True):
    monkeypatch.setattr("deeptutor.reading.references.ReadingStore", lambda: reading)
    monkeypatch.setattr(tools, "_new_service", lambda: service)
    calls = []

    async def request(config, instruction, payload, **kwargs):
        calls.append(payload)
        assert TEXT in payload["sources"][0]["text"]
        return {
            "supported": verdict,
            "explanation_valid": True,
            "citations": [{"index": 0, "quote": TEXT}],
            "provenance": "adapted",
        }

    monkeypatch.setattr(semantic, "_request", request)
    return calls


async def pose(reference):
    return await tools.MasteryQuizTool().execute(
        _mastery_path_id="p",
        _session_id="s",
        _turn_id="t",
        _mastery_reading_references=[reference],
        knowledge_point_id="kp1",
        question="Which direction is descent?",
        expected_answer="opposite",
        explanation="Descent moves opposite to the uphill gradient.",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("extension", ["pdf", "epub"])
async def test_review_reload_grade_and_notebook_keep_original_unit(
    service, tmp_path, monkeypatch, extension
):
    reading, reference = material(tmp_path, extension)
    calls = wire(monkeypatch, service, reading)
    sessions = SQLiteSessionStore(tmp_path / "sessions.db")
    await sessions.create_session(title="Synthetic", session_id="s")
    monkeypatch.setattr("deeptutor.services.session.get_sqlite_session_store", lambda: sessions)

    result = await pose(reference)
    assert result.success, result.content
    assert len(calls) == 1
    assert "text_sha256" not in json.dumps(result.metadata)
    learning = LearningStore(service.store._root)
    saved = learning.load("p")
    assert saved.source_grounded is True
    assert saved.pending_question.source_evidence["kind"] == "reading"
    semantic.validate_question(learning, saved, saved.pending_question)

    reopened = LearningService(learning)
    question_id = saved.pending_question.question_id
    await reopened.grade_interaction_semantic(
        "p", answer="opposite", question_id=question_id, session_id="s", turn_id="answer"
    )
    from deeptutor.learning.notebook_recovery import reconcile_mastery_notebook

    await reconcile_mastery_notebook(learning_store=learning, path_id="p")
    attempts = await sessions.list_assessment_attempts("s")
    assert len(attempts) == 1
    assert attempts[0]["material_id"] == reference["material_id"]
    assert attempts[0]["material_revision"] == reference["revision"]
    assert attempts[0]["section_id"] == "1"
    assert attempts[0]["source_evidence"]["kind"] == "reading"

    await reopened.grade_interaction_semantic(
        "p", answer="opposite", question_id=question_id, session_id="s", turn_id="answer"
    )
    await reconcile_mastery_notebook(learning_store=learning, path_id="p")
    assert len(await sessions.list_assessment_attempts("s")) == 1
    assert len(calls) == 1  # Exact grade and replay do not re-request the model.
    # The next turn need not resubmit source text or silently switch revision.
    next_question = PendingQuestion(
        question_id="next",
        knowledge_point_id="kp1",
        prompt="Which direction?",
        expected_answer="opposite",
    )
    await semantic.bind_question(learning, learning.load("p"), next_question)
    assert next_question.source_evidence["sources"][0]["reading_reference"] == reference
    assert len(calls) == 2
    monkeypatch.setattr("deeptutor.learning.storage.LearningStore", lambda: learning)
    from deeptutor.services.session._turn_runtime_shared import _topic_material_manifest

    manifest, index = _topic_material_manifest("p")
    assert "Reading Sources" in manifest and any(TEXT in text for text in index.values())


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["missing_revision", "unsupported", "forged_quote"])
async def test_unverified_reading_card_never_marks_grounded(
    service, tmp_path, monkeypatch, failure
):
    reading, reference = material(tmp_path, "pdf")
    calls = wire(monkeypatch, service, reading, verdict=failure != "unsupported")
    if failure == "missing_revision":
        reference["revision"] = 99
    elif failure == "forged_quote":

        async def forged(*args, **kwargs):
            return {
                "supported": True,
                "explanation_valid": True,
                "citations": [{"index": 0, "quote": "NOT IN THE ORIGINAL"}],
            }

        monkeypatch.setattr(semantic, "_request", forged)
    result = await pose(reference)
    assert not result.success
    assert not service.store.load("p").source_grounded
    assert service.store.get_active_interaction("p") is None
    if failure == "missing_revision":
        assert not calls


@pytest.mark.asyncio
async def test_archived_revision_survives_refresh_but_revoked_access_cannot_grade(
    service, tmp_path, monkeypatch
):
    reading, reference = material(tmp_path, "pdf")
    wire(monkeypatch, service, reading)
    result = await pose(reference)
    assert result.success, result.content
    reading.refresh_document(reference["material_id"])
    progress = service.store.load("p")
    semantic.validate_question(service.store, progress, progress.pending_question)
    assert (
        progress.pending_question.source_evidence["sources"][0]["reading_reference"]["revision"]
        == 1
    )
    monkeypatch.setattr(
        "deeptutor.multi_user.learning_access.learning_material_allowed", lambda _: False
    )
    with pytest.raises(MasteryInteractionError, match="unavailable"):
        await service.grade_interaction_semantic(
            "p", answer="opposite", question_id=progress.pending_question.question_id
        )
    assert not service.store.load("p").quiz_attempts
    assert not service.store.load("p").learning_evidence


def test_packet_rejects_forged_text_and_excessive_context(service, tmp_path, monkeypatch):
    from deeptutor.learning import reading_evidence

    reading, reference = material(tmp_path, "pdf")
    wire(monkeypatch, service, reading)
    progress = service.store.load("p")
    packet = reading_packet(progress, "kp1", [reference])
    packet["sources"][0]["text"] += " Forged."
    with pytest.raises(LessonUnavailable, match="changed"):
        reading_evidence.validate_reading_packet(progress, "kp1", packet)
    monkeypatch.setattr(reading_evidence, "MAX_CHARS", 1)
    with pytest.raises(LessonUnavailable, match="24,000"):
        reading_packet(progress, "kp1", [reference])


@pytest.mark.asyncio
async def test_reading_does_not_bypass_existing_selected_kb_scope(service, tmp_path, monkeypatch):
    from deeptutor.learning import lesson_evidence

    reading, reference = material(tmp_path, "pdf")
    calls = wire(monkeypatch, service, reading)
    monkeypatch.setattr(lesson_evidence, "selected_scope", lambda *args: {"kb": None})
    result = await pose(reference)
    assert not result.success and not calls
    assert not service.store.load("p").source_grounded


@pytest.mark.parametrize("tool", ["mastery_quiz", "mastery_prepare_lesson"])
def test_runtime_overrides_model_supplied_private_reading_references(tool):
    from deeptutor.capabilities.mastery.loop import MasteryLoopCapability
    from deeptutor.core.context import UnifiedContext

    selected = [{"material_id": "12345678", "revision": 1, "locators": [1]}]
    context = UnifiedContext(
        session_id="s",
        user_message="quiz",
        metadata={
            "mastery_mode": True,
            "mastery_path_id": "p",
            "reading_references": selected,
        },
    )
    kwargs = MasteryLoopCapability().augment_kwargs(
        tool,
        {"_mastery_reading_references": [{"text": "forged"}]},
        context,
    )
    assert kwargs["_mastery_reading_references"] == selected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "focus,covered,missing,can_grade",
    [
        ("", True, "", True),
        ("direction", True, "", False),
        ("", False, "Step-size reasoning is absent.", False),
    ],
)
async def test_reading_preparation_coverage_cache_and_qualitative_evidence(
    service,
    tmp_path,
    monkeypatch,
    focus,
    covered,
    missing,
    can_grade,
):
    from deeptutor.learning import lesson_evidence
    from deeptutor.learning.notebook_recovery import reconcile_mastery_notebook

    reading, reference = material(tmp_path, "epub")
    wire(monkeypatch, service, reading)

    def concept(tx):
        tx.progress.modules[0].knowledge_points[0].type = KnowledgeType.CONCEPT
        tx.touch()

    service.store.mutate("p", concept)
    calls = []

    async def request(config, instruction, payload, **kwargs):
        calls.append(payload)
        if instruction.startswith("Check whether"):
            assert TEXT in payload["sources"][0]["text"]
            return {
                "covered": covered,
                "missing": missing,
                "citations": [{"index": 0, "quote": TEXT}],
            }
        assert payload[0]["source_evidence"]["kind"] == "reading"
        return {
            "verdicts": [
                {
                    "question_id": "kp1",
                    "result": "correct",
                    "confidence": 0.95,
                    "feedback": "The causal explanation matches the source.",
                }
            ]
        }

    monkeypatch.setattr(semantic, "_request", request)
    config = SimpleNamespace(model="test", binding="openai")
    packet = await lesson_evidence.prepare_lesson(
        service.store, "p", "kp1", config, reading_references=[reference], focus=focus
    )
    assert packet["coverage"]["complete"] == covered
    assert not service.store.load("p").learning_evidence
    again = await lesson_evidence.prepare_lesson(service.store, "p", "kp1", config, focus=focus)
    assert again["id"] == packet["id"] and len(calls) == 1

    if not can_grade:
        with pytest.raises(MasteryInteractionError, match="evidence needs"):
            await service.assess_qualitative_semantic(
                "p", "kp1", learner_answer="Opposite to uphill."
            )
        assert not service.store.load("p").learning_evidence
        assert len(calls) == 1
        return
    sessions = SQLiteSessionStore(tmp_path / "qualitative.db")
    await sessions.create_session(title="Synthetic", session_id="s")
    monkeypatch.setattr("deeptutor.services.session.get_sqlite_session_store", lambda: sessions)
    progress, receipt = await service.assess_qualitative_semantic(
        "p",
        "kp1",
        learner_answer="The gradient points uphill, so descending moves in the opposite direction.",
        session_id="s",
        turn_id="qualitative",
    )
    assert receipt["result"] == "correct" and progress.qualitative_mastery["kp1"]
    await reconcile_mastery_notebook(learning_store=service.store, path_id="p")
    attempts = await sessions.list_assessment_attempts("s")
    assert len(attempts) == 1
    assert attempts[0]["material_revision"] == 1
    assert attempts[0]["material_id"] == reference["material_id"]
    assert attempts[0]["source_evidence"]["kind"] == "reading"


@pytest.mark.asyncio
async def test_reviewed_practice_does_not_substitute_for_full_objective_evidence(
    service, tmp_path, monkeypatch
):
    reading, reference = material(tmp_path, "pdf")
    calls = wire(monkeypatch, service, reading)

    def concept(tx):
        tx.progress.modules[0].knowledge_points[0].type = KnowledgeType.CONCEPT
        tx.touch()

    service.store.mutate("p", concept)
    assert (await pose(reference)).success
    with pytest.raises(MasteryInteractionError, match="Prepare verified reading"):
        await service.assess_qualitative_semantic("p", "kp1", learner_answer="Opposite to uphill.")
    assert len(calls) == 1 and not service.store.load("p").learning_evidence


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["race", "provider_failure", "forged_quote"])
async def test_failed_preparation_never_marks_grounded(service, tmp_path, monkeypatch, failure):
    from deeptutor.learning import lesson_evidence

    reading, reference = material(tmp_path, "pdf")
    wire(monkeypatch, service, reading)

    async def request(*args, **kwargs):
        if failure == "provider_failure":
            raise semantic.AssessmentUnavailable("Controlled outage")
        if failure == "race":

            def change(tx):
                tx.progress.modules[0].name = "Concurrent change"
                tx.touch()

            service.store.mutate("p", change)
        return {
            "covered": True,
            "missing": "",
            "citations": [
                {"index": 0, "quote": "FORGED SOURCE" if failure == "forged_quote" else TEXT}
            ],
        }

    monkeypatch.setattr(semantic, "_request", request)
    with pytest.raises(LessonUnavailable):
        await lesson_evidence.prepare_lesson(
            service.store,
            "p",
            "kp1",
            SimpleNamespace(model="test", binding="openai"),
            reading_references=[reference],
        )
    progress = service.store.load("p")
    assert not progress.source_grounded and not progress.lesson_evidence
    assert not progress.learning_evidence
