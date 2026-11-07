"""Public, stable views of pending mastery questions.

The persisted :class:`~deeptutor.learning.models.PendingQuestion` contains the
server-only expected answer. This module projects it into the smaller contract
that is safe to give to the tutor model and interactive clients. It also owns
the pure multiple-choice translations shared by registration, presentation,
and grading, so all three boundaries use the same immutable label/body map.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any
import unicodedata

from deeptutor.utils.text_display import decode_escaped_unicode_for_display

if TYPE_CHECKING:
    from deeptutor.learning.models import PendingQuestion


OPTION_PREFIX_RE = re.compile(r"^\s*([A-Z])\s*[.:：、)）-]\s*(.+)$", re.IGNORECASE | re.DOTALL)


def positional_label(index: int) -> str:
    """The label an option carries by its position: A, B, C, … then 27, 28, …"""
    return chr(ord("A") + index) if index < 26 else str(index + 1)


def _option_texts(options: list[str]) -> list[str]:
    return [text for text in (str(raw or "").strip() for raw in options) if text]


def _split_labelled(texts: list[str]) -> tuple[list[str], list[str]] | None:
    """``(labels, bodies)`` when every option carries a single-letter prefix."""
    labels: list[str] = []
    bodies: list[str] = []
    for text in texts:
        if len(text) == 1 and text.isalnum():
            # Legacy rows persisted the bare labels themselves.
            labels.append(text.upper())
            bodies.append(text)
            continue
        match = OPTION_PREFIX_RE.match(text)
        if match is None:
            return None
        labels.append(match.group(1).upper())
        bodies.append(match.group(2).strip())
    return labels, bodies


def option_label_intent(options: list[str]) -> list[str] | None:
    """The A/B/C labels the caller *meant* to give, or ``None`` if unlabelled.

    "Meant to" is decided by two things together: every option carries a
    single-letter prefix, and the first one is ``A``. A leading letter alone is
    not evidence — ``"x - 1 = 0"`` matches the prefix pattern and would
    otherwise register as option ``X`` with the body ``"1 = 0"``, which is how
    a maths question ended up with mislabelled and (once two options collided
    on one letter) duplicated choices.

    The returned labels may still be malformed — repeated or skipping a letter.
    :func:`parse_options` reads those positionally so nothing is lost, and
    registration rejects them so the model fixes the question instead.
    """
    split = _split_labelled(_option_texts(options))
    if split is None:
        return None
    labels, _ = split
    return labels if labels and labels[0] == "A" else None


def canonical_labels(count: int) -> set[str]:
    """The label set a well-formed *count*-option question must carry."""
    return {positional_label(index) for index in range(count)}


def parse_options(options: list[str]) -> dict[str, str]:
    """Map persisted option strings to their stable ``{label: body}`` form."""
    texts = _option_texts(options)
    split = _split_labelled(texts)
    if split is not None:
        labels, bodies = split
        if labels[:1] == ["A"] and set(labels) == canonical_labels(len(labels)):
            return dict(zip(labels, bodies, strict=True))
    return {positional_label(index): text for index, text in enumerate(texts)}


def has_option_bodies(options: dict[str, str]) -> bool:
    """Whether a choice map holds real answer text, not only A/B/C labels."""
    return len(options) >= 2 and all(
        value.strip() and value.strip().upper() != key.upper() for key, value in options.items()
    )


def resolve_answer(answer: str, options: dict[str, str]) -> str:
    """Resolve a label, labelled option, or unique body to its stable label."""
    candidate = str(answer or "").strip()
    if not candidate:
        return ""

    key = candidate.upper()
    if key in options:
        return key

    prefix_match = OPTION_PREFIX_RE.match(candidate)
    if prefix_match and prefix_match.group(1).upper() in options:
        return prefix_match.group(1).upper()

    needle = candidate.casefold()
    exact = [label for label, text in options.items() if text.casefold() == needle]
    if len(exact) == 1:
        return exact[0]
    contained = [label for label, text in options.items() if needle in text.casefold()]
    return contained[0] if len(contained) == 1 else ""


def _squeezed(value: str) -> str:
    """Case-folded with all whitespace removed, for comparing formulas."""
    return "".join(str(value or "").split()).casefold()


def _mentioned_labels(text: str, labels: Iterable[str]) -> list[str]:
    """Labels named in *text* as standalone tokens, not inside another word.

    ``\\b`` is useless here: Chinese is word-character too, so ``"选C"`` has no
    word boundary before the ``C``. The guard is therefore "not glued to
    another latin letter or digit", which accepts ``选C`` / ``答案是 C`` /
    ``C。`` and rejects the ``C`` inside ``ABC``.
    """
    return [
        label
        for label in labels
        if re.search(rf"(?<![0-9A-Za-z]){re.escape(label)}(?![0-9A-Za-z])", text, re.IGNORECASE)
    ]


def resolve_choice_submission(answer: str, options: dict[str, str]) -> str:
    """Resolve a learner submission to the option label it picked, or ``""``.

    A learner typing into the composer instead of tapping the card writes
    ``"选C"``, ``"答案是 C"`` or the option body itself — none of which the
    label-only comparison could read, so a correct answer was graded wrong.
    Every form that identifies exactly ONE option is accepted; anything
    ambiguous (two labels named, a body fragment matching several) resolves to
    nothing, which the caller must treat as "unreadable", never as wrong.

    Registration stays separately forgiving of a model-supplied body fragment
    through :func:`resolve_answer`.
    """
    candidate = str(answer or "").strip()
    if not candidate:
        return ""
    key = candidate.upper()
    if key in options:
        return key
    prefix_match = OPTION_PREFIX_RE.match(candidate)
    if prefix_match and prefix_match.group(1).upper() in options:
        return prefix_match.group(1).upper()
    needle = _squeezed(candidate)
    exact = [label for label, body in options.items() if _squeezed(body) == needle]
    if len(exact) == 1:
        return exact[0]
    mentioned = _mentioned_labels(candidate, options)
    return mentioned[0] if len(mentioned) == 1 else ""


def is_readable_choice_answer(answer: str, options: list[str] | dict[str, str]) -> bool:
    """Whether *answer* identifies exactly one option on a choice question.

    Composer text that is a clarifying question (or otherwise unmappable) must
    not be treated as a committed pick — see mastery gate stall #1004.
    """
    option_map = parse_options(options) if isinstance(options, list) else options
    if not option_map:
        return False
    candidate = str(answer or "").strip()
    resolved = resolve_choice_submission(candidate, option_map)
    if not resolved:
        return False

    # Exact labels (optionally followed by declarative punctuation), labelled
    # answers, and exact option bodies are unambiguous without extra wording.
    if re.fullmatch(rf"{re.escape(resolved)}[。.!！]?", candidate, re.IGNORECASE):
        return True
    prefix_match = OPTION_PREFIX_RE.match(candidate)
    if prefix_match and prefix_match.group(1).upper() == resolved:
        return True
    if _squeezed(candidate) == _squeezed(option_map[resolved]):
        return True

    # Merely mentioning one label is not an answer. In particular, questions
    # such as "why is B wrong?" used to resolve to B and freeze the gate.
    if re.search(
        r"[?？]|\b(?:why|what|how|can|could|would|explain)\b|"
        r"(?:为什么|为何|怎么|如何|什么|解释一下|请解释)",
        candidate,
        re.IGNORECASE,
    ):
        return False

    label = re.escape(resolved)
    return bool(
        re.search(
            rf"(?:\b(?:answer(?:\s+is)?|choose|pick|select|"
            rf"think(?:\s+it(?:'s|\s+is))?|go\s+with)\s*(?:option\s*)?{label}\b|"
            rf"(?:答案(?:是|为)?|我?选(?:择)?|应该是|我觉得是)\s*{label})",
            candidate,
            re.IGNORECASE,
        )
    )


@dataclass(frozen=True, slots=True)
class PublicPendingOption:
    """One learner-visible option; ``id`` and ``label`` are intentionally stable."""

    id: str
    label: str
    body: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "label": self.label, "body": self.body}


@dataclass(frozen=True, slots=True)
class PublicPendingQuestion:
    """Learner-visible pending state, deliberately excluding the answer key."""

    question_id: str
    prompt: str
    question_type: str
    options: tuple[PublicPendingOption, ...] = ()
    questions: tuple[PublicPendingQuestion, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = {
            "question_id": self.question_id,
            "prompt": self.prompt,
            "question_type": self.question_type,
            "options": [option.to_dict() for option in self.options],
        }
        if self.questions:
            result["questions"] = [question.to_dict() for question in self.questions]
        return result


# ── Mechanical question guards (deterministic; no model call) ────────────────
# Inspired by LogiNote's quickCheck diversity/optionOrder guards
# (main@d3ffa2e1, src/services/quickCheck/{diversity,optionOrder}.ts): a
# normalized-stem duplicate registry and a position-dependency blocker. Both
# are structural filters, not a semantic classifier — near-duplicates that
# survive them remain the tutor prompt's responsibility.

STEM_HISTORY_LIMIT = 20

# Cognitive operations a question can use (LogiNote quickCheck vocabulary,
# adapted to book learning). Frozen set: unknown operations are refused at
# registration instead of becoming free-text noise.
QUIZ_OPERATIONS = (
    "contrast",  # 比较：辨析相近概念、情形或做法的差异条件
    "counterfactual",  # 反事实：改变或移除一个关键条件，判断原结论是否仍成立
    "diagnose",  # 诊断：判断给定情形哪里出了问题、缺了什么
    "construct",  # 构造：给出满足条件的例子、方案或步骤
    "predict",  # 预测：用原理推断一个新情境会怎样
    "evidence_gap",  # 证据缺口：判断现有信息是否足以支撑一个结论
    "design_test",  # 设计检验：提出验证某个主张的具体检验办法
    "revise",  # 改写：修正一个有缺陷的说法、方案或步骤
)

# Mechanical variety hint: per-type preference order (LogiNote plans per
# criterion; our closest analogue is the objective type). Pure function —
# the tutor decides, the server only suggests.
_DEFAULT_OPERATION_ORDER = QUIZ_OPERATIONS
_OPERATION_PREFERENCES: dict[str, tuple[str, ...]] = {
    "concept": (
        "counterfactual",
        "contrast",
        "diagnose",
        "construct",
        "predict",
        "evidence_gap",
        "design_test",
        "revise",
    ),
    "design": (
        "construct",
        "design_test",
        "predict",
        "counterfactual",
        "contrast",
        "evidence_gap",
        "diagnose",
        "revise",
    ),
}
QUESTION_OPERATION_LIMIT = 10


def next_operation_hint(kp_type: str, recent: list[str]) -> str:
    """The highest-preference operation not among the objective's recent two.

    ``recent`` is the objective's rolling operation history (most recent
    last). When every preferred operation was used recently, fall back to
    the first preference rather than inventing an operation.
    """
    order = _OPERATION_PREFERENCES.get(kp_type, _DEFAULT_OPERATION_ORDER)
    recent_two = {op for op in recent[-2:] if op}
    return next((op for op in order if op not in recent_two), order[0])


# A stem or option body that hardcodes an option position would contradict
# the card after registration shuffles option order, so such questions are
# refused outright. The set is deliberately conservative: false positives
# block legitimate questions, misses only cost variety.
_POSITION_DEPENDENT_RE = re.compile(
    r"以上\s*(?:都|全|均|皆)?\s*不?\s*(?:对|正确|是|错|错误|真|假)"
    r"|上述\s*(?:所有|各项|选项)"
    r"|全选"
    r"|第\s*[一二三四1-4]\s*个?\s*选项"
    r"|选择\s*[A-Da-d]"
    r"|选\s*[A-Da-d]"
    r"|all\s+of\s+the\s+above"
    r"|none\s+of\s+the\s+above"
    r"|both\s+[a-d]\s+and\s+[a-d]",
    re.IGNORECASE,
)


def position_dependent_quiz_text(text: str) -> str:
    """Return the offending snippet when text hardcodes an option position.

    Checks stems and option bodies alike: '以上都对'/'选A'/'第X个选项'/
    'all of the above' stop making sense once option order is shuffled at
    registration.
    """
    match = _POSITION_DEPENDENT_RE.search(str(text or ""))
    return match.group(0) if match else ""


def quiz_stem_key(prompt: str) -> str:
    """Normalize a question stem for exact-duplicate detection.

    NFKC + casefold + strip punctuation/whitespace, mirroring LogiNote's
    ``quickCheckStemKey``: cosmetically reworded identical stems collide,
    different asks stay distinguishable.
    """
    normalized = unicodedata.normalize("NFKC", str(prompt or ""))
    return "".join(
        char
        for char in normalized.casefold()
        if not char.isspace() and not unicodedata.category(char).startswith(("P", "Z"))
    )


def public_pending_question(pending: PendingQuestion) -> PublicPendingQuestion:
    """Project persisted pending state without exposing ``expected_answer``."""
    options = (
        tuple(
            PublicPendingOption(id=option.label, label=option.label, body=option.body)
            for option in pending.options
        )
        if pending.question_type == "choice"
        else ()
    )
    return PublicPendingQuestion(
        question_id=pending.question_id,
        prompt=decode_escaped_unicode_for_display(pending.prompt),
        question_type=pending.question_type,
        questions=tuple(public_pending_question(q) for q in pending.questions),
        options=tuple(
            PublicPendingOption(
                id=option.id,
                label=decode_escaped_unicode_for_display(option.label),
                body=decode_escaped_unicode_for_display(option.body),
            )
            for option in options
        ),
    )


__all__ = [
    "OPTION_PREFIX_RE",
    "QUESTION_OPERATION_LIMIT",
    "QUIZ_OPERATIONS",
    "STEM_HISTORY_LIMIT",
    "canonical_labels",
    "PublicPendingOption",
    "PublicPendingQuestion",
    "has_option_bodies",
    "is_readable_choice_answer",
    "option_label_intent",
    "parse_options",
    "position_dependent_quiz_text",
    "next_operation_hint",
    "positional_label",
    "public_pending_question",
    "quiz_stem_key",
    "resolve_answer",
    "resolve_choice_submission",
]
