"""Typed question and answer primitives for TypeSafe's System One API.

Jev exposes exactly three question types. This module models them once so that
both the real Jev transport (`jev_client`) and the LLM comparison wrapper
(`llm_client`) can consume the identical definition, which is what makes the
side-by-side comparison fair.

Wire format reference: OpenRouter `POST /api/alpha/decisions`
(`createApiAlphaDecisions` in https://openrouter.ai/openapi.json).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

QuestionType = Literal["noul", "choice", "score"]

# Neutral filler used when a caller supplies only one side of a noul's criteria.
# OpenRouter's schema marks `true` and `false` as both-required whenever the
# `criteria` object is present at all, while TypeSafe's first-party API treats
# each side as independently optional. Normalising here keeps user-authored
# questions portable across both transports.
_NOUL_FILLER = "Anything that does not match the other description."


@dataclass
class Question:
    """Base class for the three System One question types."""

    instructions: str
    # Display-only label shown in the UI. The model always receives
    # `instructions`; `label` exists purely so the UI can be localised without
    # changing what is sent over the wire.
    label: str | None = None

    @property
    def type(self) -> QuestionType:  # pragma: no cover - overridden
        raise NotImplementedError

    def to_wire(self) -> dict[str, Any]:  # pragma: no cover - overridden
        raise NotImplementedError

    def display_label(self) -> str:
        return self.label or self.instructions


@dataclass
class Noul(Question):
    """A yes/no judgement returned as a calibrated probability in [0, 1].

    Named by TypeSafe after the unit of a single belief. The returned number
    *is* the confidence, so noul answers carry no separate confidence field.
    """

    true_criteria: str | None = None
    false_criteria: str | None = None

    @property
    def type(self) -> QuestionType:
        return "noul"

    def to_wire(self) -> dict[str, Any]:
        wire: dict[str, Any] = {"type": "noul", "instructions": self.instructions}
        if self.true_criteria or self.false_criteria:
            # Both sides are required together once criteria is present.
            wire["criteria"] = {
                "true": self.true_criteria or _NOUL_FILLER,
                "false": self.false_criteria or _NOUL_FILLER,
            }
        return wire


@dataclass
class Choice(Question):
    """Exactly one option out of a named set. Supports up to 255 options.

    `criteria` maps the machine-readable option key (what your code branches on)
    to a natural-language description of when that option applies.
    """

    criteria: dict[str, str] = field(default_factory=dict)

    @property
    def type(self) -> QuestionType:
        return "choice"

    @property
    def options(self) -> list[str]:
        return list(self.criteria.keys())

    def to_wire(self) -> dict[str, Any]:
        if not self.criteria:
            raise ValueError("Choice questions require at least one criterion.")
        return {
            "type": "choice",
            "instructions": self.instructions,
            "criteria": dict(self.criteria),
        }


@dataclass
class Score(Question):
    """A position on an ordered spectrum of 2-10 described levels.

    The returned score is continuous and may land between levels (e.g. 1.99),
    which is what lets calling code apply its own thresholds.
    """

    criteria: list[str] = field(default_factory=list)

    @property
    def type(self) -> QuestionType:
        return "score"

    @property
    def max_level(self) -> int:
        return max(len(self.criteria) - 1, 1)

    def to_wire(self) -> dict[str, Any]:
        if not self.criteria:
            raise ValueError("Score questions require at least one level.")
        return {
            "type": "score",
            "instructions": self.instructions,
            "criteria": list(self.criteria),
        }


def questions_to_wire(questions: dict[str, Question]) -> dict[str, Any]:
    """Serialise a question map into the Decisions request `questions` object."""
    return {key: q.to_wire() for key, q in questions.items()}


# --------------------------------------------------------------------------
# Answers
# --------------------------------------------------------------------------


@dataclass
class Answer:
    """A single decoded answer, normalised across transports."""

    key: str
    type: QuestionType
    # Exactly one of these is meaningful, depending on `type`.
    noul: float | None = None
    choice: str | None = None
    score: float | None = None
    confidence: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    legend: dict[str, Any] = field(default_factory=dict)

    @property
    def value(self) -> float | str | None:
        """The primary decided value, whatever the question type."""
        if self.type == "noul":
            return self.noul
        if self.type == "choice":
            return self.choice
        return self.score

    @property
    def effective_confidence(self) -> float | None:
        """Confidence on a comparable 0-1 scale for every question type.

        A noul has no separate confidence field because the probability itself
        is the belief, so we fold it to distance-from-uncertain instead: 0.5
        maps to 0 confidence, and 0.0 or 1.0 map to 1.0.
        """
        if self.type == "noul":
            if self.noul is None:
                return None
            return abs(self.noul - 0.5) * 2
        return self.confidence

    def display_value(self) -> str:
        if self.type == "noul":
            return "n/a" if self.noul is None else f"{self.noul:.0%}"
        if self.type == "choice":
            return self.choice or "n/a"
        return "n/a" if self.score is None else f"{self.score:.2f}"


def parse_answers(raw: dict[str, Any]) -> dict[str, Answer]:
    """Decode the `answers` object of a Decisions response."""
    out: dict[str, Answer] = {}
    for key, payload in (raw or {}).items():
        if not isinstance(payload, dict):
            continue
        atype = payload.get("type")
        if atype not in ("noul", "choice", "score"):
            # Infer the type when a transport omits the discriminator.
            if "noul" in payload:
                atype = "noul"
            elif "choice" in payload:
                atype = "choice"
            elif "score" in payload:
                atype = "score"
            else:
                continue
        probabilities = payload.get("probabilities") or {}
        if not isinstance(probabilities, dict):
            probabilities = {}
        out[key] = Answer(
            key=key,
            type=atype,  # type: ignore[arg-type]
            noul=_as_float(payload.get("noul")),
            choice=payload.get("choice"),
            score=_as_float(payload.get("score")),
            confidence=_as_float(payload.get("confidence")),
            probabilities={k: _as_float(v) or 0.0 for k, v in probabilities.items()},
            legend=payload.get("legend") or {},
        )
    return out


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


@dataclass
class DecisionResult:
    """The outcome of one decision request, from either engine."""

    engine: str  # "jev" or "llm"
    model: str
    answers: dict[str, Answer]
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    provider: str | None = None
    request_id: str | None = None
    raw_request: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] = field(default_factory=dict)
    # Populated when the engine failed outright.
    error: str | None = None
    # Schema violations recovered from or rejected. Always empty for Jev, where
    # conformance is structural rather than best-effort.
    schema_errors: list[str] = field(default_factory=list)
    simulated: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def type_safe(self) -> bool:
        return not self.schema_errors

    def get(self, key: str) -> Answer | None:
        return self.answers.get(key)

    def value(self, key: str, default: Any = None) -> Any:
        answer = self.answers.get(key)
        return default if answer is None else answer.value

    def noul(self, key: str, default: float = 0.0) -> float:
        answer = self.answers.get(key)
        if answer is None or answer.noul is None:
            return default
        return answer.noul

    def score(self, key: str, default: float = 0.0) -> float:
        answer = self.answers.get(key)
        if answer is None or answer.score is None:
            return default
        return answer.score

    def choice(self, key: str, default: str = "") -> str:
        answer = self.answers.get(key)
        if answer is None or answer.choice is None:
            return default
        return answer.choice

    def confidence(self, key: str, default: float = 0.0) -> float:
        answer = self.answers.get(key)
        if answer is None:
            return default
        conf = answer.effective_confidence
        return default if conf is None else conf
