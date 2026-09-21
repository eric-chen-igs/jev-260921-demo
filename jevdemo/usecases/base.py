"""Types shared by every demo use case.

A use case bundles four things:

1. **State** — one or more realistic sample inputs.
2. **Questions** — the typed questions asked about that state.
3. **A `decide` function** — plain Python that turns typed answers into an
   action. This is displayed verbatim in the UI, because it is the whole point:
   the branching logic stays in your codebase where it can be reviewed and
   tested, and the model only supplies judgements that are awkward to express
   in code.
4. **Action labels** — bilingual names for each outcome `decide` can reach.

`decide` deliberately returns an action *key* rather than prose, so the same
function serves both interface languages without embedding translations in the
code that gets shown to the reader.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..schema import DecisionResult, Question

# Levels map onto Streamlit's callout styles.
OutcomeLevel = str  # "info" | "success" | "warning" | "error"


@dataclass
class Sample:
    """A named preset input for a use case."""

    id: str
    name: dict[str, str]
    state: Any
    # Answers a human considers correct for this preset. Used only by the
    # offline simulator so the no-key walkthrough stays coherent; ignored
    # entirely when a real API key is present.
    #
    # Values are normally bare: a probability for a noul, an option key for a
    # choice, a level for a score. A mapping such as
    # `{"choice": "other", "confidence": 0.31}` also pins the confidence, which
    # is how a demo shows a low-confidence branch deterministically.
    hint: dict[str, Any] = field(default_factory=dict)


@dataclass
class Outcome:
    """What the surrounding application decided to do."""

    action: str
    level: OutcomeLevel = "info"
    # Technical trace lines, shown as-is. These read like log output, so they
    # stay in English in both interface languages.
    trace: list[str] = field(default_factory=list)
    # Extra headline figures, e.g. a composite score.
    metrics: dict[str, str] = field(default_factory=dict)


@dataclass
class UseCase:
    id: str
    icon: str
    title: dict[str, str]
    category: dict[str, str]
    summary: dict[str, str]
    why: dict[str, str]
    samples: list[Sample]
    actions: dict[str, dict[str, str]]
    decide: Callable[[DecisionResult, Any], Outcome]
    questions: dict[str, Question] | None = None
    # Used when the question set depends on the state, e.g. one question per
    # retrieved passage.
    questions_builder: Callable[[Any], dict[str, Question]] | None = None

    def questions_for(self, state: Any) -> dict[str, Question]:
        if self.questions_builder is not None:
            return self.questions_builder(state)
        return dict(self.questions or {})

    def decide_source(self) -> str:
        """The verbatim source of the branching function, for display."""
        try:
            return textwrap.dedent(inspect.getsource(self.decide))
        except (OSError, TypeError):  # pragma: no cover - only if source is gone
            return "# source unavailable"

    def action_label(self, action: str, lang: str) -> str:
        labels = self.actions.get(action, {})
        return labels.get(lang) or labels.get("en") or action

    def sample_by_id(self, sample_id: str) -> Sample | None:
        for sample in self.samples:
            if sample.id == sample_id:
                return sample
        return None


def registry() -> list[UseCase]:
    """All demo use cases, in presentation order."""
    from .cases_realtime import CASES as REALTIME
    from .cases_routing import CASES as ROUTING
    from .cases_scoring import CASES as SCORING
    from .cases_verification import CASES as VERIFICATION

    return [*ROUTING, *VERIFICATION, *REALTIME, *SCORING]


def find(use_case_id: str) -> UseCase | None:
    for case in registry():
        if case.id == use_case_id:
            return case
    return None
