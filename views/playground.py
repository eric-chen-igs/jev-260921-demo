"""Freeform playground: compose an arbitrary decision call and send it.

The flow is deliberately stepped — state, then questions, then run — because the
main thing newcomers get wrong is treating this like a chat prompt. Seeing
"program state" and "typed questions" as two separate inputs is most of the
conceptual work.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import streamlit as st

from jevdemo import ui
from jevdemo.compare import run_comparison
from jevdemo.i18n import pick
from jevdemo.playground_examples import EXAMPLES, by_id
from jevdemo.schema import Choice, Noul, Question, Score
from jevdemo.settings import AppSettings

QUESTIONS_KEY = "pg_questions"
STATE_KEY = "pg_state_value"
RUN_KEY = "pg_run"
LOADED_KEY = "pg_loaded_example"

TYPE_LABELS = {
    "noul": {"en": "noul · yes/no probability", "zh-TW": "noul · 是非機率"},
    "choice": {"en": "choice · pick one", "zh-TW": "choice · 單選"},
    "score": {"en": "score · rate on a scale", "zh-TW": "score · 尺度評分"},
}

BLANK_ROW = {
    "instructions": "",
    "options": "",
    "levels": "",
    "true_criteria": "",
    "false_criteria": "",
}


# --------------------------------------------------------------------------
# Row helpers
# --------------------------------------------------------------------------


def _row(qtype: str, key: str) -> dict[str, Any]:
    return {"uid": uuid.uuid4().hex[:8], "key": key, "type": qtype, **BLANK_ROW}


def _load_example(example_id: str) -> None:
    """Replace the editor contents with a named example."""
    example = by_id(example_id)
    if example is None:
        return
    st.session_state[STATE_KEY] = example.state
    st.session_state[QUESTIONS_KEY] = [
        {**BLANK_ROW, **row, "uid": uuid.uuid4().hex[:8]}
        for row in example.questions
    ]
    st.session_state[LOADED_KEY] = example_id
    # Editor widgets are keyed by uid, so stale widget state must go or the old
    # text would be restored on top of the freshly loaded rows.
    for widget_key in [
        k
        for k in st.session_state
        if k.startswith(("pg_key_", "pg_type_", "pg_instr_", "pg_opts_", "pg_lvls_", "pg_true_", "pg_false_"))
    ]:
        del st.session_state[widget_key]
    st.session_state.pop("pg_state_box", None)
    st.session_state.pop(RUN_KEY, None)


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


def _build_questions(
    specs: list[dict[str, Any]],
) -> tuple[dict[str, Question], list[str]]:
    """Turn editor rows into Question objects, reporting any problems."""
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


# --------------------------------------------------------------------------
# View
# --------------------------------------------------------------------------


def render(settings: AppSettings) -> None:
    lang = settings.lang
    t = settings.t

    st.title(t("nav.playground"))
    st.markdown(f"#### {t('playground.heading')}")
    st.caption(t("playground.intro"))

    # Seed from the first example so the page is never empty on arrival.
    if QUESTIONS_KEY not in st.session_state:
        _load_example(EXAMPLES[0].id)

    _render_example_picker(settings)

    with st.expander(t("playground.type_primer")):
        st.markdown(t("playground.type_primer_body"))

    # -- Step 1: state -----------------------------------------------------
    st.subheader(t("playground.step_state"))
    st.caption(t("playground.step_state_help"))
    state = ui.state_editor(
        st.session_state.get(STATE_KEY, ""), lang, key="pg_state_box", height=240
    )
    st.session_state[STATE_KEY] = state

    # -- Step 2: questions -------------------------------------------------
    specs: list[dict[str, Any]] = st.session_state[QUESTIONS_KEY]
    st.subheader(f"{t('playground.step_questions')} ({len(specs)})")
    st.caption(t("playground.step_questions_help"))

    _render_add_buttons(settings, specs)
    remove_uid = _render_question_rows(settings, specs)
    if remove_uid is not None:
        st.session_state[QUESTIONS_KEY] = [s for s in specs if s["uid"] != remove_uid]
        st.rerun()

    # -- Step 3: run -------------------------------------------------------
    questions, problems = _build_questions(specs)
    st.subheader(t("playground.step_run"))

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

    if st.button(
        t("common.run"),
        type="primary",
        icon=":material/play_arrow:",
        disabled=bool(problems),
    ):
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

    if not run.llm.ok:
        ui.render_result_header(run.jev, lang)
        ui.render_type_safety(run.jev, lang)
        st.markdown(f"##### {t('common.answers')}")
        ui.render_answers(run.jev, answered, lang)
        ui.render_raw(run.jev, lang)
        return

    ui.render_side_by_side(run, answered, lang)
    if run.deltas:
        st.divider()
        st.subheader(t("compare.per_question"))
        ui.render_delta_table(run, lang)


def _render_example_picker(settings: AppSettings) -> None:
    """A one-click library of ready-made scenarios."""
    lang = settings.lang
    t = settings.t

    with st.container(border=True):
        st.markdown(f"**{t('playground.examples')}**")
        ids = [example.id for example in EXAMPLES]
        picked = st.selectbox(
            t("playground.pick_example"),
            options=ids,
            format_func=lambda eid: pick(by_id(eid).name, lang),  # type: ignore[union-attr]
            key="pg_example_pick",
            label_visibility="collapsed",
        )
        example = by_id(picked)
        if example is not None:
            st.caption(pick(example.blurb, lang))

        load_column, clear_column = st.columns([1, 1])
        if load_column.button(
            t("playground.load_example"),
            icon=":material/download:",
            width="stretch",
            type="secondary",
        ):
            _load_example(picked)
            st.rerun()
        if clear_column.button(
            t("playground.clear"), icon=":material/delete_sweep:", width="stretch"
        ):
            st.session_state[QUESTIONS_KEY] = [_row("noul", "question_1")]
            st.session_state[STATE_KEY] = ""
            st.session_state.pop("pg_state_box", None)
            st.session_state.pop(RUN_KEY, None)
            st.rerun()

        if st.session_state.get(LOADED_KEY) == picked:
            st.caption(f":green-badge[{t('playground.loaded')}]")


def _render_add_buttons(settings: AppSettings, specs: list[dict[str, Any]]) -> None:
    """Add a question of a given type directly, rather than add-then-switch."""
    t = settings.t
    columns = st.columns(3)
    specs_count = len(specs)
    for column, (qtype, icon, label_key) in zip(
        columns,
        [
            ("noul", ":material/help:", "playground.add_noul"),
            ("choice", ":material/list:", "playground.add_choice"),
            ("score", ":material/linear_scale:", "playground.add_score"),
        ],
        strict=True,
    ):
        if column.button(
            t(label_key), icon=icon, width="stretch", key=f"pg_add_{qtype}"
        ):
            specs.append(_row(qtype, f"question_{specs_count + 1}"))
            st.rerun()


def _render_question_rows(
    settings: AppSettings, specs: list[dict[str, Any]]
) -> str | None:
    """Draw one editable card per question. Returns a uid to remove, if any."""
    lang = settings.lang
    t = settings.t
    remove_uid: str | None = None

    for position, spec in enumerate(specs, start=1):
        uid = spec["uid"]
        with st.container(border=True):
            head, type_column, remove_column = st.columns([3, 2.2, 1])
            spec["key"] = head.text_input(
                f"{position}. {t('playground.key')}",
                value=spec["key"],
                key=f"pg_key_{uid}",
                placeholder="urgency",
            )
            spec["type"] = type_column.selectbox(
                t("playground.type"),
                options=["noul", "choice", "score"],
                index=["noul", "choice", "score"].index(spec["type"]),
                format_func=lambda v: pick(TYPE_LABELS[v], lang),
                key=f"pg_type_{uid}",
            )
            with remove_column:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button(
                    "",
                    key=f"pg_rm_{uid}",
                    icon=":material/delete:",
                    help=t("playground.remove"),
                    disabled=len(specs) <= 1,
                ):
                    remove_uid = uid

            spec["instructions"] = st.text_area(
                t("playground.instructions"),
                value=spec["instructions"],
                key=f"pg_instr_{uid}",
                height=68,
                placeholder=pick(
                    {
                        "en": "Write it as a plain statement or question about the state.",
                        "zh-TW": "以一句關於狀態的直述句或問句來撰寫。",
                    },
                    lang,
                ),
            )

            if spec["type"] == "choice":
                spec["options"] = st.text_area(
                    t("playground.options"),
                    value=spec["options"],
                    key=f"pg_opts_{uid}",
                    height=120,
                    placeholder="billing: Payment or subscription issues.\ntechnical: Bugs or integration problems.\nother: Anything else.",
                )
                st.caption(t("playground.options_help"))
            elif spec["type"] == "score":
                spec["levels"] = st.text_area(
                    t("playground.levels"),
                    value=spec["levels"],
                    key=f"pg_lvls_{uid}",
                    height=120,
                    placeholder="Can wait for the next release\nShould be fixed this week\nBlocking revenue right now",
                )
                st.caption(t("playground.levels_help"))
            else:
                true_column, false_column = st.columns(2)
                spec["true_criteria"] = true_column.text_area(
                    t("playground.true_criteria"),
                    value=spec["true_criteria"],
                    key=f"pg_true_{uid}",
                    height=68,
                    placeholder="What makes this statement true.",
                )
                spec["false_criteria"] = false_column.text_area(
                    t("playground.false_criteria"),
                    value=spec["false_criteria"],
                    key=f"pg_false_{uid}",
                    height=68,
                    placeholder="What makes it false.",
                )
                st.caption(t("playground.noul_help"))

    return remove_uid
