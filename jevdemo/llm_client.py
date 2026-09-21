"""Constrain a general-purpose LLM to produce the same typed decisions as Jev.

TypeSafe calls this a "System One LLM wrapper" and uses it for their own
published comparisons: rather than penalising an LLM for being chatty, we give
it every advantage by handing it a strict JSON Schema derived from the exact
same question set Jev receives. That makes the two columns comparable on
latency, cost, and agreement.

It also makes the type-safety difference measurable instead of rhetorical. Jev
cannot return a value outside the schema because the output space *is* the
schema. An LLM emits tokens that we then have to parse and validate, so this
module records every violation it finds in `DecisionResult.schema_errors`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import requests

from .jev_client import state_to_text
from .schema import Choice, DecisionResult, Noul, Question, Score, parse_answers

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Sensible comparison targets, all verified present on OpenRouter. The first is
# the model TypeSafe themselves used for the launch side-by-side, on the grounds
# that it was the closest match to Jev's intelligence on System One tasks.
LLM_MODEL_CHOICES = [
    "openai/gpt-5.6-terra",
    "openai/gpt-5.6-sol",
    "openai/gpt-5.6-luna",
    "openai/gpt-6-astra",
    "anthropic/claude-opus-5",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-fable-5.1",
    "anthropic/claude-haiku-4.5",
    "google/gemini-3.8-flash",
    "deepseek/deepseek-v4.1-flash",
]

SYSTEM_PROMPT = """\
You are a calibrated decision engine embedded inside a software workflow. You \
will be given program state and a set of typed questions about it. Answer every \
question and return a single JSON object, nothing else.

Rules:
- Answer strictly from the supplied state. Do not invent facts.
- `noul` questions: return the probability the statement is true, as a number \
between 0 and 1.
- `choice` questions: return one of the listed option keys verbatim, a \
probability for every option (summing to 1), and your confidence.
- `score` questions: return a position on the described scale. Level indices \
start at 0. The value may be fractional if the state sits between two levels.
- Confidence must be calibrated: only report high confidence when you would be \
right that fraction of the time. Report low confidence on genuinely ambiguous \
input.
"""


@dataclass
class LLMConfig:
    api_key: str = ""
    model: str = "openai/gpt-5.6-terra"
    timeout: float = 180.0
    temperature: float = 0.0
    max_tokens: int = 4096
    # Reasoning effort passed through to models that support it. "none" keeps
    # the comparison closest to Jev's single-pass behaviour.
    reasoning_effort: str = "default"
    referer: str = "https://github.com/eric-chen-igs/jev-260921-demo"
    title: str = "Jev vs LLM Demo"


class LLMClient:
    """Runs the same decision task through an OpenRouter chat model."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()

    def decide(
        self,
        state: Any,
        questions: dict[str, Question],
        *,
        session_id: str | None = None,
    ) -> DecisionResult:
        if not self.config.api_key:
            return DecisionResult(
                engine="llm",
                model=self.config.model,
                answers={},
                latency_ms=0.0,
                error=(
                    "No OpenRouter API key. The LLM column needs a real key, "
                    "because there is nothing meaningful to simulate about its "
                    "latency or token cost."
                ),
            )

        schema = build_json_schema(questions)
        body: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": render_prompt(state, questions)},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "system_one_decisions",
                    "strict": True,
                    "schema": schema,
                },
            },
            # Ask OpenRouter to bill-stamp the response so cost is measured,
            # not estimated from a price table.
            "usage": {"include": True},
        }
        if self.config.reasoning_effort != "default":
            body["reasoning"] = {"effort": self.config.reasoning_effort}

        started = time.perf_counter()
        try:
            response = requests.post(
                OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.config.referer,
                    "X-Title": self.config.title,
                },
                json=body,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:
            return DecisionResult(
                engine="llm",
                model=self.config.model,
                answers={},
                latency_ms=(time.perf_counter() - started) * 1000,
                raw_request=body,
                error=f"Request failed: {exc}",
            )
        latency_ms = (time.perf_counter() - started) * 1000

        try:
            payload = response.json()
        except ValueError:
            return DecisionResult(
                engine="llm",
                model=self.config.model,
                answers={},
                latency_ms=latency_ms,
                raw_request=body,
                error=f"HTTP {response.status_code}: response was not JSON.",
            )

        if response.status_code >= 400 or "error" in payload:
            err = payload.get("error")
            message = (
                err.get("message") if isinstance(err, dict) else err
            ) or f"HTTP {response.status_code}"
            return DecisionResult(
                engine="llm",
                model=self.config.model,
                answers={},
                latency_ms=latency_ms,
                raw_request=body,
                raw_response=payload,
                error=f"HTTP {response.status_code}: {message}",
            )

        usage = payload.get("usage") or {}
        choices = payload.get("choices") or []
        content = ""
        if choices and isinstance(choices[0], dict):
            content = (choices[0].get("message") or {}).get("content") or ""

        raw_answers, schema_errors = parse_llm_content(content, questions)

        return DecisionResult(
            engine="llm",
            model=payload.get("model") or self.config.model,
            answers=parse_answers(raw_answers),
            latency_ms=latency_ms,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cost_usd=(
                float(usage["cost"]) if usage.get("cost") is not None else None
            ),
            provider=payload.get("provider"),
            request_id=payload.get("id"),
            raw_request=body,
            raw_response=payload,
            schema_errors=schema_errors,
            error=None if raw_answers else (
                "Could not recover any valid answer from the model output."
            ),
        )


# --------------------------------------------------------------------------
# Schema + prompt construction
# --------------------------------------------------------------------------


def build_json_schema(questions: dict[str, Question]) -> dict[str, Any]:
    """Derive a strict JSON Schema mirroring Jev's answer shapes."""
    properties: dict[str, Any] = {}
    for key, question in questions.items():
        if isinstance(question, Noul):
            properties[key] = {
                "type": "object",
                "properties": {
                    "noul": {
                        "type": "number",
                        "description": "Probability the statement is true, 0-1.",
                    }
                },
                "required": ["noul"],
                "additionalProperties": False,
            }
        elif isinstance(question, Choice):
            options = question.options
            properties[key] = {
                "type": "object",
                "properties": {
                    "choice": {"type": "string", "enum": options},
                    "confidence": {"type": "number"},
                    "probabilities": {
                        "type": "object",
                        "properties": {
                            opt: {"type": "number"} for opt in options
                        },
                        "required": options,
                        "additionalProperties": False,
                    },
                },
                "required": ["choice", "confidence", "probabilities"],
                "additionalProperties": False,
            }
        else:
            assert isinstance(question, Score)
            properties[key] = {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "number",
                        "description": (
                            f"Position from 0 to {question.max_level}."
                        ),
                    },
                    "confidence": {"type": "number"},
                },
                "required": ["score", "confidence"],
                "additionalProperties": False,
            }

    return {
        "type": "object",
        "properties": properties,
        "required": list(questions.keys()),
        "additionalProperties": False,
    }


def render_prompt(state: Any, questions: dict[str, Question]) -> str:
    """Render state and questions as the user turn of the chat request."""
    lines = ["# Program state", "```json", state_to_text(state), "```", ""]
    lines.append("# Questions")
    for key, question in questions.items():
        lines.append("")
        lines.append(f"## `{key}` ({question.type})")
        lines.append(question.instructions)
        if isinstance(question, Noul):
            if question.true_criteria:
                lines.append(f"- true means: {question.true_criteria}")
            if question.false_criteria:
                lines.append(f"- false means: {question.false_criteria}")
        elif isinstance(question, Choice):
            for opt, desc in question.criteria.items():
                lines.append(f"- `{opt}`: {desc}")
        else:
            assert isinstance(question, Score)
            for index, level in enumerate(question.criteria):
                lines.append(f"- level {index}: {level}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Output validation
# --------------------------------------------------------------------------


def parse_llm_content(
    content: str, questions: dict[str, Question]
) -> tuple[dict[str, Any], list[str]]:
    """Parse and validate model output, collecting every schema violation.

    Returns the salvageable answers plus a list of problems. An empty problem
    list is what Jev achieves structurally on every single call.
    """
    errors: list[str] = []
    data = _extract_json(content)
    if data is None:
        return {}, [
            "Output was not valid JSON, even after attempting to recover a "
            "JSON object from surrounding text."
        ]
    if not isinstance(data, dict):
        return {}, ["Top-level JSON value was not an object."]

    # Some models nest the payload, e.g. {"answers": {...}}.
    if "answers" in data and isinstance(data["answers"], dict) and not (
        set(data.keys()) & set(questions.keys())
    ):
        data = data["answers"]

    cleaned: dict[str, Any] = {}
    for key, question in questions.items():
        if key not in data:
            errors.append(f"`{key}`: missing from the response.")
            continue
        raw = data[key]
        # Tolerate a bare scalar where an object was demanded.
        if not isinstance(raw, dict):
            if isinstance(question, Noul) and isinstance(raw, (int, float)):
                raw = {"noul": raw}
            elif isinstance(question, Choice) and isinstance(raw, str):
                raw = {"choice": raw}
                errors.append(
                    f"`{key}`: returned a bare string instead of the required "
                    "object, so no confidence was reported."
                )
            elif isinstance(question, Score) and isinstance(raw, (int, float)):
                raw = {"score": raw}
                errors.append(
                    f"`{key}`: returned a bare number instead of the required "
                    "object, so no confidence was reported."
                )
            else:
                errors.append(f"`{key}`: expected an object, got {type(raw).__name__}.")
                continue

        if isinstance(question, Noul):
            value = _number(raw.get("noul"))
            if value is None:
                errors.append(f"`{key}`: `noul` was missing or not a number.")
                continue
            if not 0.0 <= value <= 1.0:
                errors.append(
                    f"`{key}`: `noul` was {value}, outside the required 0-1 range."
                )
                value = min(max(value, 0.0), 1.0)
            cleaned[key] = {"type": "noul", "noul": value}

        elif isinstance(question, Choice):
            picked = raw.get("choice")
            if not isinstance(picked, str):
                errors.append(f"`{key}`: `choice` was missing or not a string.")
                continue
            if picked not in question.criteria:
                # This is the failure mode Jev makes structurally impossible:
                # a syntactically valid answer that is not in the option set.
                errors.append(
                    f"`{key}`: chose {picked!r}, which is not one of the "
                    f"{len(question.criteria)} declared options."
                )
                continue
            probabilities = raw.get("probabilities")
            if not isinstance(probabilities, dict):
                probabilities = {}
            else:
                unknown = set(probabilities) - set(question.criteria)
                if unknown:
                    errors.append(
                        f"`{key}`: returned probabilities for undeclared "
                        f"options: {sorted(unknown)}."
                    )
                probabilities = {
                    opt: _number(probabilities.get(opt)) or 0.0
                    for opt in question.criteria
                }
            cleaned[key] = {
                "type": "choice",
                "choice": picked,
                "confidence": _number(raw.get("confidence")),
                "probabilities": probabilities,
            }

        else:
            assert isinstance(question, Score)
            value = _number(raw.get("score"))
            if value is None:
                errors.append(f"`{key}`: `score` was missing or not a number.")
                continue
            if not 0.0 <= value <= question.max_level:
                errors.append(
                    f"`{key}`: `score` was {value}, outside the declared "
                    f"0-{question.max_level} range."
                )
                value = min(max(value, 0.0), float(question.max_level))
            cleaned[key] = {
                "type": "score",
                "score": value,
                "confidence": _number(raw.get("confidence")),
                "legend": {
                    str(i): level for i, level in enumerate(question.criteria)
                },
            }

    extra = set(data.keys()) - set(questions.keys())
    if extra:
        errors.append(f"Response contained undeclared keys: {sorted(extra)}.")

    return cleaned, errors


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_json(content: str) -> Any:
    """Best-effort JSON recovery from a text completion."""
    text = (content or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass

    # Strip a fenced code block if present.
    if "```" in text:
        segments = text.split("```")
        for segment in segments:
            candidate = segment.strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{"):
                try:
                    return json.loads(candidate)
                except ValueError:
                    continue

    # Fall back to the outermost brace pair.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except ValueError:
            return None
    return None
