"""Shared Streamlit rendering helpers for decision results."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from .compare import ComparisonRun
from .i18n import t
from .schema import Answer, Choice, DecisionResult, Noul, Question, Score

# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------


def format_latency(ms: float | None) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms:.0f} ms"
    return f"{ms / 1000:.2f} s"


def format_cost(usd: float | None) -> str:
    """Format a USD amount, keeping precision where the amount is tiny.

    A single decision can cost a few millionths of a dollar while a monthly
    total runs to thousands, so the precision has to scale with magnitude.
    """
    if usd is None:
        return "—"
    if usd == 0:
        return "$0"
    if usd < 0.01:
        return f"${usd:.6f}"
    if usd < 1:
        return f"${usd:.4f}"
    return f"${usd:,.2f}"


def md_safe(text: str) -> str:
    """Escape dollar signs so Streamlit does not read them as LaTeX delimiters.

    A pair of unescaped `$` in markdown turns everything between them into
    math mode, which silently mangles any prose containing two prices — for
    example "$0.20 to $10 / MTok". None of this app's copy uses LaTeX, so
    escaping every dollar sign is unambiguously the right trade.
    """
    return text.replace("$", r"\$")


def format_multiplier(value: float | None) -> str:
    if value is None:
        return "—"
    if value >= 100:
        return f"{value:,.0f}x"
    if value >= 10:
        return f"{value:.1f}x"
    return f"{value:.2f}x"


# --------------------------------------------------------------------------
# Answer rendering
# --------------------------------------------------------------------------


def render_answer(answer: Answer, question: Question | None, lang: str) -> None:
    """Render a single typed answer with its probability distribution."""
    label = question.display_label() if question else answer.key

    if answer.type == "noul":
        probability = answer.noul or 0.0
        st.markdown(f"**`{answer.key}`** · {label}")
        st.progress(
            min(max(probability, 0.0), 1.0),
            text=f"noul = {probability:.3f}  ({probability:.0%} yes)",
        )

    elif answer.type == "choice":
        st.markdown(f"**`{answer.key}`** · {label}")
        confidence = answer.confidence
        suffix = (
            f" · {t('common.confidence', lang)} {confidence:.0%}"
            if confidence is not None
            else ""
        )
        st.markdown(f"### `{answer.choice}`{suffix}")
        if answer.probabilities:
            _probability_table(answer.probabilities, lang)

    else:  # score
        levels = question.criteria if isinstance(question, Score) else []
        max_level = max(len(levels) - 1, 1) if levels else 1
        score = answer.score or 0.0
        st.markdown(f"**`{answer.key}`** · {label}")
        confidence = answer.confidence
        suffix = (
            f" · {t('common.confidence', lang)} {confidence:.0%}"
            if confidence is not None
            else ""
        )
        st.markdown(f"### {score:.2f} / {max_level}{suffix}")
        st.progress(min(max(score / max_level, 0.0), 1.0))
        if levels:
            nearest = int(round(min(max(score, 0), max_level)))
            st.caption(
                f"→ {t('common.level', lang)} {nearest}: {levels[nearest]}"
            )
        if answer.probabilities:
            legend = answer.legend or {
                str(i): level for i, level in enumerate(levels)
            }
            labelled = {
                f"{key} · {legend.get(key, '')}".strip(" ·"): value
                for key, value in answer.probabilities.items()
            }
            _probability_table(labelled, lang)


def _probability_table(probabilities: dict[str, float], lang: str) -> None:
    frame = pd.DataFrame(
        {
            "option": list(probabilities.keys()),
            "p": [float(v) for v in probabilities.values()],
        }
    ).sort_values("p", ascending=False)
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            "option": st.column_config.TextColumn(t("common.probabilities", lang)),
            "p": st.column_config.ProgressColumn(
                "p", min_value=0.0, max_value=1.0, format="%.3f"
            ),
        },
    )


def render_answers(
    result: DecisionResult, questions: dict[str, Question], lang: str
) -> None:
    """Render every answer in a result, in question declaration order."""
    if not result.ok:
        st.error(f"**{t('common.error', lang)}:** {result.error}")
        return
    if not result.answers:
        st.info(t("common.no_run_yet", lang))
        return
    ordered = [k for k in questions if k in result.answers]
    ordered += [k for k in result.answers if k not in questions]
    for index, key in enumerate(ordered):
        if index:
            st.divider()
        render_answer(result.answers[key], questions.get(key), lang)


# --------------------------------------------------------------------------
# Result metrics
# --------------------------------------------------------------------------


def render_result_header(result: DecisionResult, lang: str) -> None:
    """Latency / cost / token metrics for one engine."""
    if result.simulated:
        st.caption(f":orange-badge[{t('common.simulated', lang)}]")

    left, middle, right = st.columns(3)
    left.metric(t("common.latency", lang), format_latency(result.latency_ms))
    middle.metric(t("common.cost", lang), format_cost(result.cost_usd))
    right.metric(
        t("common.tokens", lang),
        f"{result.input_tokens:,} → {result.output_tokens:,}",
    )
    model_line = f"`{result.model}`"
    if result.provider:
        model_line += f" · {result.provider}"
    st.caption(f"{t('common.model_returned', lang)}: {model_line}")


def render_type_safety(result: DecisionResult, lang: str) -> None:
    """Report schema conformance, the core structural difference between engines."""
    if result.engine == "jev":
        st.success(
            f"**{t('common.type_errors', lang)}: 0** — "
            f"{t('compare.typesafety_note_jev', lang)}",
            icon=":material/verified_user:",
        )
        return

    if result.type_safe:
        st.info(
            f"**{t('common.type_errors', lang)}: 0** — "
            f"{t('compare.typesafety_note_llm_ok', lang)}",
            icon=":material/info:",
        )
        return

    st.warning(
        f"**{t('common.type_errors', lang)}: {len(result.schema_errors)}** — "
        f"{t('compare.typesafety_note_llm_bad', lang)}",
        icon=":material/warning:",
    )
    for problem in result.schema_errors:
        st.caption(f"· {problem}")


def render_raw(result: DecisionResult, lang: str) -> None:
    with st.expander(t("common.raw_request", lang)):
        st.code(
            json.dumps(result.raw_request, indent=2, ensure_ascii=False), language="json"
        )
    if result.raw_response:
        with st.expander(t("common.raw_response", lang)):
            st.code(
                json.dumps(result.raw_response, indent=2, ensure_ascii=False),
                language="json",
            )


# --------------------------------------------------------------------------
# Comparison rendering
# --------------------------------------------------------------------------


def render_comparison_summary(run: ComparisonRun, lang: str) -> None:
    """Headline speed / cost / agreement metrics across both engines."""
    columns = st.columns(4)
    columns[0].metric(t("common.speedup", lang), format_multiplier(run.speedup))
    columns[1].metric(t("common.cheaper", lang), format_multiplier(run.cost_ratio))
    agreement = run.agreement_rate
    columns[2].metric(
        t("common.agreement", lang),
        "—" if agreement is None else f"{agreement:.0%}",
    )
    columns[3].metric(
        t("common.type_errors", lang),
        f"0 / {len(run.llm.schema_errors)}",
        help="Jev / LLM",
    )


def render_delta_table(run: ComparisonRun, lang: str) -> None:
    """Question-by-question comparison of the two engines' answers."""
    if not run.deltas:
        return
    frame = pd.DataFrame(
        [
            {
                t("common.question", lang): f"{delta.key} ({delta.type})",
                t("common.jev", lang): delta.jev_display,
                t("common.llm", lang): delta.llm_display,
                t("common.agree", lang): delta.agrees,
                t("common.gap", lang): (
                    None if delta.gap is None else round(delta.gap, 3)
                ),
            }
            for delta in run.deltas
        ]
    )
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            t("common.agree", lang): st.column_config.CheckboxColumn(
                t("common.agree", lang)
            )
        },
    )
    st.caption(t("compare.agreement_note", lang))


def render_questions_reference(questions: dict[str, Question], lang: str) -> None:
    """Show the exact question definitions being sent to the model."""
    for key, question in questions.items():
        with st.expander(f"`{key}` · {question.type} — {question.display_label()}"):
            st.markdown(f"**instructions:** {question.instructions}")
            if isinstance(question, Noul):
                if question.true_criteria:
                    st.markdown(f"- `true`: {question.true_criteria}")
                if question.false_criteria:
                    st.markdown(f"- `false`: {question.false_criteria}")
            elif isinstance(question, Choice):
                for option, description in question.criteria.items():
                    st.markdown(f"- `{option}`: {description}")
            elif isinstance(question, Score):
                for index, level in enumerate(question.criteria):
                    st.markdown(f"- level `{index}`: {level}")


def state_editor(
    state: Any, lang: str, *, key: str, height: int = 260
) -> Any:
    """Editable state box that parses JSON when possible, else sends a string."""
    as_text = (
        state if isinstance(state, str) else json.dumps(state, indent=2, ensure_ascii=False)
    )
    edited = st.text_area(
        t("common.state", lang),
        value=as_text,
        height=height,
        key=key,
        help=t("common.state_help", lang),
    )
    stripped = edited.strip()
    if stripped.startswith(("{", "[")):
        try:
            return json.loads(stripped)
        except ValueError:
            st.caption(f":orange[{t('common.invalid_json', lang)}]")
    return edited
