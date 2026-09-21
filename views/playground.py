"""Freeform playground: compose an arbitrary decision call and send it."""

from __future__ import annotations

import json
import uuid
from typing import Any

import streamlit as st

from jevdemo import ui
from jevdemo.compare import run_comparison
from jevdemo.schema import Choice, Noul, Question, Score
from jevdemo.settings import AppSettings

QUESTIONS_KEY = "pg_questions"
RUN_KEY = "pg_run"

DEFAULT_STATE = {
    "email": {
        "from": "priya.raman@northwind-logistics.com",
        "subject": "Evaluating workflow automation for Q4",
        "body": (
            "We process about 40 million shipment events a month and currently "
            "hand-roll the classification rules. I have sign-off on a six-figure "
            "budget and need to decide by the end of October. We're also "
            "trialling a competitor."
        ),
    }
}


def _seed_questions() -> list[dict[str, Any]]:
    return [
        {
            "uid": uuid.uuid4().hex[:8],
            "key": "intent",
            "type": "choice",
            "instructions": "What does the sender actually want?",
            "options": (
                "demo_request: They want to see or trial the product.\n"
                "pricing_question: They are asking about cost or plans.\n"
                "partnership: They are proposing a partnership.\n"
                "spam: Bulk, automated, or irrelevant outreach."
            ),
            "levels": "",
            "true_criteria": "",
            "false_criteria": "",
        },
        {
            "uid": uuid.uuid4().hex[:8],
            "key": "urgency",
            "type": "score",
            "instructions": "How urgent is the sender's stated timeline?",
            "options": "",
            "levels": (
                "No timeline; idle curiosity.\n"
                "Researching for the future.\n"
                "Evaluating actively this quarter.\n"
                "Urgent; needs to decide within weeks."
            ),
            "true_criteria": "",
            "false_criteria": "",
        },
        {
            "uid": uuid.uuid4().hex[:8],
            "key": "has_budget",
            "type": "noul",
            "instructions": "The sender indicates budget exists or has been allocated.",
            "options": "",
            "levels": "",
            "true_criteria": "They mention budget, procurement, or an existing spend.",
            "false_criteria": "No indication of money being available.",
        },
    ]


def _parse_options(raw: str) -> dict[str, str]:
    """Parse `key: description` lines into a choice criteria map."""
    criteria: dict[str, str] = {}
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, description = line.split(":", 1)
            key, description = key.strip(), description.strip()
        else:
            key, description = line, line
        if key:
            criteria[key] = description or key
    return criteria


def _parse_levels(raw: str) -> list[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _build_questions(specs: list[dict[str, Any]]) -> tuple[dict[str, Question], list[str]]:
    """Turn the editor rows into Question objects, reporting any problems."""
    questions: dict[str, Question] = {}
    problems: list[str] = []
    for index, spec in enumerate(specs, start=1):
        key = (spec.get("key") or "").strip()
        instructions = (spec.get("instructions") or "").strip()
        if not key:
            problems.append(f"Question {index}: a key is required.")
            continue
        if not instructions:
            problems.append(f"`{key}`: instructions are required.")
            continue
        if key in questions:
            problems.append(f"`{key}`: duplicate key.")
            continue

        qtype = spec.get("type")
        if qtype == "choice":
            criteria = _parse_options(spec.get("options", ""))
            if len(criteria) < 2:
                problems.append(f"`{key}`: a choice needs at least two options.")
                continue
            if len(criteria) > 255:
                problems.append(f"`{key}`: a choice supports at most 255 options.")
                continue
            questions[key] = Choice(instructions=instructions, criteria=criteria)
        elif qtype == "score":
            levels = _parse_levels(spec.get("levels", ""))
            if len(levels) < 2:
                problems.append(f"`{key}`: a score needs at least two levels.")
                continue
            if len(levels) > 10:
                problems.append(f"`{key}`: a score supports at most ten levels.")
                continue
            questions[key] = Score(instructions=instructions, criteria=levels)
        else:
            questions[key] = Noul(
                instructions=instructions,
                true_criteria=(spec.get("true_criteria") or "").strip() or None,
                false_criteria=(spec.get("false_criteria") or "").strip() or None,
            )
    return questions, problems


def render(settings: AppSettings) -> None:
    lang = settings.lang
    t = settings.t

    st.title(t("nav.playground"))
    st.markdown(f"#### {t('playground.heading')}")
    st.caption(t("playground.intro"))

    st.session_state.setdefault(QUESTIONS_KEY, _seed_questions())
    specs: list[dict[str, Any]] = st.session_state[QUESTIONS_KEY]

    state = ui.state_editor(DEFAULT_STATE, lang, key="pg_state", height=260)

    st.subheader(f"{t('common.questions')} ({len(specs)})")

    remove_uid: str | None = None
    for spec in specs:
        uid = spec["uid"]
        with st.container(border=True):
            head, type_column, remove_column = st.columns([3, 2, 1])
            spec["key"] = head.text_input(
                t("playground.key"), value=spec["key"], key=f"pg_key_{uid}"
            )
            spec["type"] = type_column.selectbox(
                t("playground.type"),
                options=["noul", "choice", "score"],
                index=["noul", "choice", "score"].index(spec["type"]),
                key=f"pg_type_{uid}",
            )
            with remove_column:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button(
                    t("playground.remove"),
                    key=f"pg_rm_{uid}",
                    icon=":material/delete:",
                    disabled=len(specs) <= 1,
                ):
                    remove_uid = uid

            spec["instructions"] = st.text_area(
                t("playground.instructions"),
                value=spec["instructions"],
                key=f"pg_instr_{uid}",
                height=68,
            )

            if spec["type"] == "choice":
                spec["options"] = st.text_area(
                    t("playground.options"),
                    value=spec["options"],
                    key=f"pg_opts_{uid}",
                    height=120,
                )
            elif spec["type"] == "score":
                spec["levels"] = st.text_area(
                    t("playground.levels"),
                    value=spec["levels"],
                    key=f"pg_lvls_{uid}",
                    height=120,
                )
            else:
                true_column, false_column = st.columns(2)
                spec["true_criteria"] = true_column.text_area(
                    t("playground.true_criteria"),
                    value=spec["true_criteria"],
                    key=f"pg_true_{uid}",
                    height=68,
                )
                spec["false_criteria"] = false_column.text_area(
                    t("playground.false_criteria"),
                    value=spec["false_criteria"],
                    key=f"pg_false_{uid}",
                    height=68,
                )

    if remove_uid is not None:
        st.session_state[QUESTIONS_KEY] = [
            s for s in specs if s["uid"] != remove_uid
        ]
        st.rerun()

    add_column, run_column = st.columns([1, 1])
    if add_column.button(t("playground.add"), icon=":material/add:", width="stretch"):
        specs.append(
            {
                "uid": uuid.uuid4().hex[:8],
                "key": f"question_{len(specs) + 1}",
                "type": "noul",
                "instructions": "",
                "options": "",
                "levels": "",
                "true_criteria": "",
                "false_criteria": "",
            }
        )
        st.rerun()

    questions, problems = _build_questions(specs)
    triggered = run_column.button(
        t("common.run"),
        type="primary",
        icon=":material/play_arrow:",
        disabled=not questions or bool(problems),
        width="stretch",
    )

    for problem in problems:
        st.warning(problem, icon=":material/warning:")
    if not questions:
        st.info(t("playground.no_questions"), icon=":material/info:")
        return

    with st.expander(t("playground.generated")):
        st.code(
            json.dumps(
                {
                    "model": settings.jev_model,
                    "state": state,
                    "questions": {k: q.to_wire() for k, q in questions.items()},
                },
                indent=2,
                ensure_ascii=False,
            ),
            language="json",
        )

    if triggered:
        with st.spinner(t("common.running")):
            st.session_state[RUN_KEY] = run_comparison(
                settings.jev_client(),
                settings.llm_client(),
                state,
                questions,
                include_llm=settings.llm_available,
            )
            st.session_state[RUN_KEY + "_questions"] = questions

    run = st.session_state.get(RUN_KEY)
    if run is None:
        st.info(t("common.no_run_yet"), icon=":material/info:")
        return

    answered = st.session_state.get(RUN_KEY + "_questions", questions)

    st.divider()
    if settings.llm_available and run.llm.ok:
        ui.render_comparison_summary(run, lang)
        st.divider()

    jev_column, llm_column = st.columns(2)
    with jev_column:
        st.subheader(t("common.jev"))
        ui.render_result_header(run.jev, lang)
        ui.render_type_safety(run.jev, lang)
        ui.render_answers(run.jev, answered, lang)
        ui.render_raw(run.jev, lang)
    with llm_column:
        st.subheader(t("common.llm"))
        if not run.llm.ok:
            st.caption(run.llm.error or t("common.disabled"))
        else:
            ui.render_result_header(run.llm, lang)
            ui.render_type_safety(run.llm, lang)
            ui.render_answers(run.llm, answered, lang)
            ui.render_raw(run.llm, lang)

    if run.deltas:
        st.divider()
        st.subheader(t("compare.per_question"))
        ui.render_delta_table(run, lang)
