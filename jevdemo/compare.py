"""Run one decision task through both engines and quantify the difference."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .jev_client import JevClient
from .llm_client import LLMClient
from .schema import Answer, DecisionResult, Question

# Tolerances for calling two answers "in agreement". Choices must match exactly;
# the continuous types are allowed to differ by a modest amount, since a 0.1
# gap in probability is not a disagreement about the decision.
NOUL_TOLERANCE = 0.25
SCORE_TOLERANCE = 0.5


@dataclass
class QuestionDelta:
    key: str
    type: str
    label: str
    jev_display: str
    llm_display: str
    agrees: bool
    # Absolute gap on the question's native scale; None for choices.
    gap: float | None = None
    jev_confidence: float | None = None
    llm_confidence: float | None = None


@dataclass
class ComparisonRun:
    jev: DecisionResult
    llm: DecisionResult
    deltas: list[QuestionDelta] = field(default_factory=list)

    @property
    def agreement_rate(self) -> float | None:
        if not self.deltas:
            return None
        return sum(1 for d in self.deltas if d.agrees) / len(self.deltas)

    @property
    def speedup(self) -> float | None:
        """How many times faster Jev answered."""
        if not (self.jev.ok and self.llm.ok):
            return None
        if self.jev.latency_ms <= 0:
            return None
        return self.llm.latency_ms / self.jev.latency_ms

    @property
    def cost_ratio(self) -> float | None:
        """How many times cheaper Jev was."""
        if not (self.jev.ok and self.llm.ok):
            return None
        jev_cost, llm_cost = self.jev.cost_usd, self.llm.cost_usd
        if not jev_cost or llm_cost is None:
            return None
        return llm_cost / jev_cost

    @property
    def disagreements(self) -> list[QuestionDelta]:
        return [d for d in self.deltas if not d.agrees]


def run_comparison(
    jev_client: JevClient,
    llm_client: LLMClient,
    state: Any,
    questions: dict[str, Question],
    *,
    include_llm: bool = True,
    session_id: str | None = None,
    simulation_hint: dict[str, Any] | None = None,
) -> ComparisonRun:
    """Issue both requests concurrently so wall-clock timings stay independent."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        jev_future = pool.submit(
            jev_client.decide,
            state,
            questions,
            session_id=session_id,
            simulation_hint=simulation_hint,
        )
        llm_future = (
            pool.submit(llm_client.decide, state, questions, session_id=session_id)
            if include_llm
            else None
        )
        jev_result = jev_future.result()
        llm_result = (
            llm_future.result()
            if llm_future is not None
            else DecisionResult(
                engine="llm",
                model=llm_client.config.model,
                answers={},
                latency_ms=0.0,
                error="Skipped: LLM comparison disabled for this run.",
            )
        )

    return ComparisonRun(
        jev=jev_result,
        llm=llm_result,
        deltas=build_deltas(jev_result, llm_result, questions),
    )


def build_deltas(
    jev: DecisionResult, llm: DecisionResult, questions: dict[str, Question]
) -> list[QuestionDelta]:
    """Pair up answers question by question and decide whether they agree."""
    if not (jev.ok and llm.ok):
        return []

    deltas: list[QuestionDelta] = []
    for key, question in questions.items():
        jev_answer, llm_answer = jev.get(key), llm.get(key)
        if jev_answer is None or llm_answer is None:
            continue
        agrees, gap = _compare_answers(jev_answer, llm_answer)
        deltas.append(
            QuestionDelta(
                key=key,
                type=question.type,
                label=question.display_label(),
                jev_display=jev_answer.display_value(),
                llm_display=llm_answer.display_value(),
                agrees=agrees,
                gap=gap,
                jev_confidence=jev_answer.effective_confidence,
                llm_confidence=llm_answer.effective_confidence,
            )
        )
    return deltas


def _compare_answers(jev: Answer, llm: Answer) -> tuple[bool, float | None]:
    if jev.type == "choice":
        return jev.choice == llm.choice, None
    if jev.type == "noul":
        if jev.noul is None or llm.noul is None:
            return False, None
        gap = abs(jev.noul - llm.noul)
        # Agreement requires both a similar magnitude and the same side of the
        # 0.5 decision boundary, since that is what calling code branches on.
        same_side = (jev.noul >= 0.5) == (llm.noul >= 0.5)
        return (gap <= NOUL_TOLERANCE and same_side), gap
    if jev.score is None or llm.score is None:
        return False, None
    gap = abs(jev.score - llm.score)
    return gap <= SCORE_TOLERANCE, gap
