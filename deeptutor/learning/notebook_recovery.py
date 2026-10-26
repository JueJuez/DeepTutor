"""Transactional Mastery → Notebook snapshots and model-free delivery.

Snapshots belong to the learning transaction. Delivery may repeat after a
crash; the session store's immutable attempt identity makes that safe.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
import uuid

from deeptutor.learning.assessment import AssessmentRecord, build_grade_result
from deeptutor.learning.policy import find_knowledge_point

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from deeptutor.learning.storage import LearningStore, LearningTransaction


def capture_notebook_assessment(
    tx: LearningTransaction,
    event_type: str,
    payload: dict,
    *,
    session_id: str,
    turn_id: str,
    event_id: int,
    now: float,
) -> dict | None:
    """Build a snapshot only from evidence present in the source transaction."""
    if event_type not in {
        "attempt.recorded",
        "practice.ungraded",
        "assessment.corrected",
        "assessment.voided",
        "mastery.assessed",
    }:
        return None
    progress = tx.progress
    qualitative = event_type == "mastery.assessed"
    question_id = str(payload.get("question_id") or payload.get("interaction_id") or "")
    interaction = tx.get_interaction(question_id) if question_id else None
    if not qualitative and (interaction is None or interaction.question.questions):
        # Old attempts without a stored question cannot be reconstructed honestly.
        return None
    kp_id = str(payload.get("knowledge_point_id") or "")
    kp, _, _ = find_knowledge_point(progress, kp_id)
    evidence = next(
        (
            item
            for item in reversed(progress.learning_evidence)
            if item.knowledge_point_id == kp_id
            and (
                item.assessment_type == "qualitative"
                if qualitative
                else item.question_id == question_id
            )
        ),
        None,
    )
    if qualitative:
        if evidence is None:
            return None
        session_id, turn_id = evidence.session_id, evidence.turn_id
    else:
        session_id = interaction.session_id or session_id
        turn_id = interaction.turn_id or turn_id
    if not session_id:
        return None
    question = interaction.question if interaction else None
    result = (
        evidence.result
        if qualitative
        else build_grade_result(
            result=str(interaction.result.get("result") or ""),
            is_correct=interaction.result.get("is_correct"),
        )
    )
    if event_type == "assessment.voided":
        result = "voided"
    # Snapshot the captured assist count; when the source evidence never
    # captured one (None, legacy), fall back to the question's own assist
    # markers instead of inventing "no hints used".
    if evidence is not None and evidence.hints_used is not None:
        assistance: int | None = evidence.hints_used
    else:
        assistance = int(
            bool(
                question and (question.assistance_used or question.visual_context.get("hints_used"))
            )
        )
    from deeptutor.learning.reading_evidence import reading_origin

    sources = question.source_evidence if question else progress.lesson_evidence.get(kp_id, {})
    origin = reading_origin(sources)
    record = AssessmentRecord(
        session_id=session_id,
        turn_id=turn_id,
        question_id=f"qual:{kp_id}" if qualitative else question_id,
        question=(kp.name if kp else kp_id) if qualitative else question.prompt,
        question_type=(
            "written"
            if qualitative or question.question_type == "open"
            else "choice"
            if question.question_type == "choice"
            else "short_answer"
        ),
        options=question.choice_map if question else {},
        correct_answer=question.expected_answer if question else "",
        explanation=question.explanation if question else "",
        difficulty=question.difficulty if question else "",
        user_answer=evidence.learner_answer if qualitative else interaction.user_answer,
        result=result,
        is_correct=result == "correct",
        source="mastery_path",
        assessment_type="qualitative" if qualitative else "quiz",
        material_id=origin.get("material_id", progress.book_id),
        material_revision=origin.get("material_revision", 0),
        material_title=progress.name,
        section_id=origin.get("section_id", kp_id),
        section_title=origin.get("section_title", kp.name if kp else ""),
        mastery_path_id=progress.book_id,
        knowledge_point_id=kp_id,
        hints_used=assistance,
        attempt_count=evidence.attempt_count if evidence else 1,
        confidence=evidence.confidence if evidence else None,
        response_time=evidence.response_time if evidence else None,
        quality=evidence.quality if evidence else None,
        visual_context=question.visual_context if question else {},
        created_at=now,
        updated_at=now,
        attempt_id=f"mastery:{uuid.uuid4().hex}",
        projection_stream=progress.book_id,
        projection_sequence=event_id,
        correction_reason=str(payload.get("reason") or ""),
        previous_result=payload.get("previous_result") or {},
        source_evidence=sources,
    )
    return record.model_dump(mode="json")


async def reconcile_mastery_notebook(
    *, learning_store: LearningStore | None = None, path_id: str = ""
) -> tuple[int, int]:
    """Deliver pending snapshots; acknowledge only after destination commit."""
    from deeptutor.learning.assessment import record_assessment
    from deeptutor.learning.storage import LearningStore

    store = learning_store if learning_store is not None else LearningStore()
    pending = await asyncio.to_thread(store.pending_notebook_assessments, path_id)
    recovered = failed = 0
    for event_id, snapshot in pending:
        try:
            await record_assessment(AssessmentRecord.model_validate(snapshot))
            await asyncio.to_thread(store.mark_notebook_assessment_applied, event_id)
            recovered += 1
        except Exception:
            failed += 1
            logger.exception("Could not deliver mastery Notebook event %s", event_id)
    return recovered, failed


async def sync_durable_mastery(path_id: str, question_id: str) -> bool:
    """Prefer durable snapshots over the legacy best-effort tool payload."""
    from deeptutor.learning.storage import LearningStore

    try:
        store = LearningStore()
        if not await asyncio.to_thread(store.has_notebook_assessment, path_id, question_id):
            return False
        await reconcile_mastery_notebook(learning_store=store, path_id=path_id)
    except Exception:
        # The source commit is already durable. Do not fall back to an
        # untracked duplicate or invite a model regrade when delivery fails.
        logger.exception("Could not synchronize durable mastery Notebook for %s", path_id)
    return True
