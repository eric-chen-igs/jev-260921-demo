"""Client for TypeSafe's System One decision API.

Two live transports are supported, because the same model is reachable two ways
and they differ in three small details:

| Detail          | OpenRouter                  | TypeSafe first-party   |
|-----------------|-----------------------------|------------------------|
| Path            | `/api/alpha/decisions`      | `/v1/systemone`        |
| Model slug      | `typesafe/jev-latest`       | `jev-latest`           |
| Auth            | OpenRouter key              | TypeSafe key           |

The request body (`{model, state, questions}`), the three question types, and
the answer shapes are otherwise identical.

A third "simulated" engine runs with no network access at all so the demo is
presentable without a key. It is always surfaced in the UI as simulated.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

from .schema import (
    Answer,
    Choice,
    DecisionResult,
    Noul,
    Question,
    Score,
    parse_answers,
    questions_to_wire,
)

OPENROUTER_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
TYPESAFE_SYSTEMONE_URL = "https://api.typesafe.ai/v1/systemone"

# Published Jev pricing: input only, output free.
JEV_INPUT_USD_PER_MTOK = 0.042

DEFAULT_OPENROUTER_MODEL = "typesafe/jev-latest"
DEFAULT_TYPESAFE_MODEL = "jev-latest"

# Model slugs OpenRouter currently routes to TypeSafe's Decisions endpoint.
JEV_MODEL_CHOICES = [
    "typesafe/jev-latest",
    "typesafe/jev-1.13",
]


class JevError(RuntimeError):
    """Raised when the decision endpoint returns an error."""


@dataclass
class JevConfig:
    api_key: str = ""
    model: str = DEFAULT_OPENROUTER_MODEL
    transport: str = "openrouter"  # "openrouter" | "typesafe" | "simulated"
    timeout: float = 60.0
    referer: str = "https://github.com/eric-chen-igs/jev-260921-demo"
    title: str = "Jev vs LLM Demo"

    @property
    def is_simulated(self) -> bool:
        return self.transport == "simulated" or not self.api_key

    @property
    def endpoint(self) -> str:
        return (
            TYPESAFE_SYSTEMONE_URL
            if self.transport == "typesafe"
            else OPENROUTER_DECISIONS_URL
        )

    def normalised_model(self) -> str:
        """Align the slug with the transport's namespace convention."""
        model = (self.model or "").strip()
        if self.transport == "typesafe":
            return model.split("/", 1)[-1] or DEFAULT_TYPESAFE_MODEL
        if not model:
            return DEFAULT_OPENROUTER_MODEL
        if "/" not in model:
            return f"typesafe/{model}"
        return model


class JevClient:
    """Calls the System One endpoint and normalises the response."""

    def __init__(self, config: JevConfig | None = None) -> None:
        self.config = config or JevConfig()

    # -- public API -------------------------------------------------------

    def decide(
        self,
        state: Any,
        questions: dict[str, Question],
        *,
        session_id: str | None = None,
        simulation_hint: dict[str, Any] | None = None,
    ) -> DecisionResult:
        """Answer every question about `state` in a single parallel call."""
        if self.config.is_simulated:
            return simulate_decision(
                state, questions, model=self.config.normalised_model(),
                hint=simulation_hint,
            )

        body: dict[str, Any] = {
            "model": self.config.normalised_model(),
            "state": state,
            "questions": questions_to_wire(questions),
        }
        if session_id:
            body["session_id"] = session_id

        started = time.perf_counter()
        try:
            response = requests.post(
                self.config.endpoint,
                headers=self._headers(),
                json=body,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:
            return DecisionResult(
                engine="jev",
                model=body["model"],
                answers={},
                latency_ms=(time.perf_counter() - started) * 1000,
                raw_request=body,
                error=f"Request failed: {exc}",
            )
        latency_ms = (time.perf_counter() - started) * 1000

        payload, error = _decode(response)
        if error:
            return DecisionResult(
                engine="jev",
                model=body["model"],
                answers={},
                latency_ms=latency_ms,
                raw_request=body,
                raw_response=payload if isinstance(payload, dict) else {},
                error=error,
            )

        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        cost = usage.get("cost")
        if cost is None:
            cost = input_tokens / 1_000_000 * JEV_INPUT_USD_PER_MTOK

        return DecisionResult(
            engine="jev",
            # Echo back the versioned ID that actually answered, so thresholds
            # tuned against a pinned release can be traced.
            model=payload.get("model") or body["model"],
            answers=parse_answers(payload.get("answers") or {}),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=int(usage.get("output_tokens") or 0),
            cost_usd=float(cost),
            provider=payload.get("provider"),
            request_id=payload.get("id"),
            raw_request=body,
            raw_response=payload,
        )

    # -- internals --------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        if self.config.transport == "openrouter":
            # Optional attribution headers used by OpenRouter's dashboards.
            headers["HTTP-Referer"] = self.config.referer
            headers["X-Title"] = self.config.title
        return headers


def _decode(response: requests.Response) -> tuple[dict[str, Any], str | None]:
    """Parse a response body, returning a human-readable error when unusable."""
    try:
        payload = response.json()
    except ValueError:
        snippet = (response.text or "")[:200]
        return {}, (
            f"HTTP {response.status_code}: response was not JSON. "
            f"Body starts with: {snippet!r}"
        )

    if not isinstance(payload, dict):
        return {}, f"HTTP {response.status_code}: unexpected response shape."

    if response.status_code >= 400 or "error" in payload:
        err = payload.get("error")
        if isinstance(err, dict):
            message = err.get("message") or json.dumps(err)
        else:
            message = err or f"HTTP {response.status_code}"
        return payload, f"HTTP {response.status_code}: {message}"

    if "answers" not in payload:
        return payload, (
            f"HTTP {response.status_code}: response contained no `answers` object."
        )
    return payload, None


# --------------------------------------------------------------------------
# Offline simulator
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to", "of",
    "and", "or", "in", "on", "at", "for", "with", "that", "this", "it", "as",
    "by", "from", "has", "have", "had", "not", "no", "but", "if", "then",
    "any", "all", "some", "there", "their", "they", "i", "you", "we", "my",
}


def state_to_text(state: Any) -> str:
    """Flatten any accepted state shape into plain text."""
    if isinstance(state, str):
        return state
    try:
        return json.dumps(state, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(state)


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


def _overlap(state_tokens: set[str], text: str) -> float:
    """Fraction of a criterion's distinctive words present in the state."""
    candidate = _tokens(text)
    if not candidate:
        return 0.0
    return len(state_tokens & candidate) / len(candidate)


def _jitter(seed_text: str, spread: float = 0.06) -> float:
    """Deterministic pseudo-noise so simulated ties break consistently."""
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:12], 16))
    return rng.uniform(-spread, spread)


def _split_hint(given: Any, value_field: str) -> tuple[Any, float | None]:
    """Unpack a simulation hint into a target value and a pinned confidence.

    Hints are normally a bare value (`"billing"`, `2.0`). A mapping such as
    `{"choice": "other", "confidence": 0.34}` additionally pins the confidence,
    which lets a demo show a low-confidence path deterministically.
    """
    if isinstance(given, dict):
        confidence = given.get("confidence")
        try:
            confidence = None if confidence is None else float(confidence)
        except (TypeError, ValueError):
            confidence = None
        return given.get(value_field), confidence
    return given, None


def _softmax(values: list[float], temperature: float = 0.35) -> list[float]:
    if not values:
        return []
    scaled = [v / max(temperature, 1e-6) for v in values]
    peak = max(scaled)
    exps = [math.exp(v - peak) for v in scaled]
    total = sum(exps) or 1.0
    return [e / total for e in exps]


def simulate_decision(
    state: Any,
    questions: dict[str, Question],
    *,
    model: str = DEFAULT_OPENROUTER_MODEL,
    hint: dict[str, Any] | None = None,
) -> DecisionResult:
    """Produce plausible, deterministic answers with no network call.

    Two sources feed this. When the calling demo supplies a `hint` for a
    question (the answer a human considers correct for that preset), it is used
    so the offline walkthrough stays coherent. Otherwise answers fall back to a
    lexical-overlap heuristic over the criteria descriptions.

    This is emphatically NOT Jev. It exists so the UI is explorable without a
    key, and every surface that renders it marks the output as simulated.
    """
    text = state_to_text(state)
    state_tokens = _tokens(text)
    hint = hint or {}

    answers: dict[str, Answer] = {}
    for key, question in questions.items():
        seed = f"{key}|{text[:400]}"
        given = hint.get(key)

        if isinstance(question, Noul):
            if isinstance(given, (int, float)) and not isinstance(given, bool):
                prob = float(given)
            elif isinstance(given, bool):
                prob = 0.93 if given else 0.06
            else:
                true_text = question.true_criteria or question.instructions
                false_text = question.false_criteria or ""
                margin = _overlap(state_tokens, true_text) - _overlap(
                    state_tokens, false_text
                )
                prob = 1 / (1 + math.exp(-6 * (margin + _jitter(seed))))
            prob = min(max(prob + _jitter(seed, 0.03), 0.01), 0.99)
            answers[key] = Answer(key=key, type="noul", noul=round(prob, 3))

        elif isinstance(question, Choice):
            options = question.options
            target, forced_confidence = _split_hint(given, "choice")
            if isinstance(target, str) and target in question.criteria:
                # A low pinned confidence produces a deliberately flat
                # distribution, so the rendered probabilities stay consistent
                # with the confidence figure beside them.
                boost = 1.9 if forced_confidence is None else 0.15 + forced_confidence * 1.8
                raw = [
                    (boost if opt == target else 0.0) + _jitter(f"{seed}|{opt}", 0.04)
                    for opt in options
                ]
            else:
                raw = [
                    _overlap(state_tokens, f"{opt} {question.criteria[opt]}")
                    + _jitter(f"{seed}|{opt}")
                    for opt in options
                ]
            probs = _softmax(raw)
            # `probs` is derived from `options`, so the lengths always match.
            ranked = sorted(zip(options, probs, strict=True), key=lambda pair: -pair[1])
            top, top_p = ranked[0]
            runner_p = ranked[1][1] if len(ranked) > 1 else 0.0
            confidence = (
                forced_confidence
                if forced_confidence is not None
                # Calibrated confidence tracks the margin over the runner-up,
                # not the raw probability mass.
                else min(max(top_p - runner_p + 0.45, 0.2), 0.99)
            )
            answers[key] = Answer(
                key=key,
                type="choice",
                choice=top,
                confidence=round(confidence, 3),
                probabilities={
                    opt: round(p, 3) for opt, p in zip(options, probs, strict=True)
                },
            )

        else:  # Score
            assert isinstance(question, Score)
            levels = question.criteria
            centre, forced_confidence = _split_hint(given, "score")
            if isinstance(centre, (int, float)) and not isinstance(centre, bool):
                sharpness = 2.2 if forced_confidence is None else 0.4 + forced_confidence * 2.4
                raw = [
                    -abs(i - float(centre)) * sharpness + _jitter(f"{seed}|{i}", 0.05)
                    for i in range(len(levels))
                ]
            else:
                raw = [
                    _overlap(state_tokens, level) + _jitter(f"{seed}|{i}")
                    for i, level in enumerate(levels)
                ]
            probs = _softmax(raw)
            expected = sum(i * p for i, p in enumerate(probs))
            top_p = max(probs) if probs else 0.0
            confidence = (
                forced_confidence
                if forced_confidence is not None
                else min(max(top_p + 0.1, 0.2), 0.99)
            )
            answers[key] = Answer(
                key=key,
                type="score",
                score=round(expected, 3),
                confidence=round(confidence, 3),
                probabilities={str(i): round(p, 3) for i, p in enumerate(probs)},
                legend={str(i): level for i, level in enumerate(levels)},
            )

    # Mirror Jev's published envelope: ~4 chars per token, output free.
    wire = questions_to_wire(questions)
    input_tokens = max(
        1, (len(text) + len(json.dumps(wire, ensure_ascii=False))) // 4
    )
    latency = 70 + (abs(hash(text)) % 230)
    time.sleep(min(latency, 260) / 1000)

    return DecisionResult(
        engine="jev",
        model=f"{model} (simulated)",
        answers=answers,
        latency_ms=float(latency),
        input_tokens=input_tokens,
        output_tokens=len(questions) * 12,
        cost_usd=input_tokens / 1_000_000 * JEV_INPUT_USD_PER_MTOK,
        provider="simulated",
        raw_request={"model": model, "state": state, "questions": wire},
        simulated=True,
    )
