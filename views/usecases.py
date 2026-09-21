"""The ten demo use cases: typed decisions driving real application code."""

from __future__ import annotations

import streamlit as st

from jevdemo import ui
from jevdemo.compare import run_comparison
from jevdemo.i18n import pick
from jevdemo.settings import AppSettings
from jevdemo.usecases import UseCase, registry

CALLOUTS = {
    "success": st.success,
    "warning": st.warning,
    "error": st.error,
    "info": st.info,
}
ICONS = {
    "success": ":material/check_circle:",
    "warning": ":material/warning:",
    "error": ":material/report:",
    "info": ":material/info:",
}


def render(settings: AppSettings) -> None:
    lang = settings.lang
    t = settings.t

    st.title(t("nav.usecases"))
    st.markdown(f"#### {t('usecases.heading')}")
    st.caption(t("usecases.intro"))

    cases = registry()
    with st.expander(f"{t('usecases.pick')} — {len(cases)}"):
        for index, case in enumerate(cases, start=1):
            st.markdown(
                ui.md_safe(
                    f"**{index}. {pick(case.title, lang)}** "
                    f"· :gray-badge[{pick(case.category, lang)}]  \n"
                    f"{pick(case.summary, lang)}"
                )
            )

    case_ids = [case.id for case in cases]
    selected_id = st.selectbox(
        t("usecases.pick"),
        options=case_ids,
        format_func=lambda cid: (
            f"{case_ids.index(cid) + 1}. "
            f"{pick(next(c for c in cases if c.id == cid).title, lang)}"
        ),
        key="usecase_selected",
    )
    case = next(c for c in cases if c.id == selected_id)
    _render_case(case, settings)


def _render_case(case: UseCase, settings: AppSettings) -> None:
    lang = settings.lang
    t = settings.t

    st.divider()
    st.header(f"{pick(case.title, lang)}")
    st.markdown(f":violet-badge[{pick(case.category, lang)}]")
    st.markdown(ui.md_safe(pick(case.summary, lang)))

    with st.expander(t("usecases.why")):
        st.markdown(ui.md_safe(pick(case.why, lang)))

    sample_ids = [s.id for s in case.samples]
    sample_id = st.radio(
        t("common.preset"),
        options=sample_ids,
        format_func=lambda sid: pick(
            case.sample_by_id(sid).name, lang  # type: ignore[union-attr]
        ),
        horizontal=True,
        key=f"uc_sample_{case.id}",
    )
    sample = case.sample_by_id(sample_id)
    assert sample is not None

    with st.expander(t("usecases.edit_state")):
        state = ui.state_editor(
            sample.state, lang, key=f"uc_state_{case.id}_{sample.id}", height=340
        )

    questions = case.questions_for(state)
    with st.expander(f"{t('usecases.questions_asked')} ({len(questions)})"):
        ui.render_questions_reference(questions, lang)

    compare_column, button_column = st.columns([2, 1])
    with compare_column:
        also_compare = st.checkbox(
            t("usecases.compare_toggle"),
            value=False,
            key=f"uc_compare_{case.id}",
            disabled=not settings.llm_available,
            help=None if settings.llm_available else t("sidebar.enable_llm_help"),
        )
    with button_column:
        triggered = st.button(
            t("common.run"),
            type="primary",
            icon=":material/play_arrow:",
            key=f"uc_run_{case.id}",
            width="stretch",
        )

    run_key = f"uc_result_{case.id}"
    if triggered:
        with st.spinner(t("common.running")):
            st.session_state[run_key] = run_comparison(
                settings.jev_client(),
                settings.llm_client(),
                state,
                questions,
                include_llm=also_compare and settings.llm_available,
                simulation_hint=sample.hint,
            )
            st.session_state[run_key + "_questions"] = questions
            st.session_state[run_key + "_state"] = state

    run = st.session_state.get(run_key)
    if run is None:
        st.info(t("common.no_run_yet"), icon=":material/info:")
        return

    questions = st.session_state.get(run_key + "_questions", questions)
    decided_state = st.session_state.get(run_key + "_state", state)

    if not run.jev.ok:
        st.error(f"**{t('common.error')}:** {run.jev.error}")
        return

    st.divider()
    ui.render_result_header(run.jev, lang)
    _render_scale_note(run.jev, lang)

    # The outcome panel: what ordinary code did with the typed answers.
    outcome = case.decide(run.jev, decided_state)
    st.subheader(t("usecases.outcome"))
    callout = CALLOUTS.get(outcome.level, st.info)
    callout(
        f"**{case.action_label(outcome.action, lang)}**  \n`{outcome.action}`",
        icon=ICONS.get(outcome.level, ":material/info:"),
    )

    if outcome.metrics:
        metric_columns = st.columns(len(outcome.metrics))
        for column, (name, value) in zip(
            metric_columns, outcome.metrics.items(), strict=False
        ):
            column.metric(name, value)

    if outcome.trace:
        with st.expander(t("usecases.trace"), expanded=True):
            st.code("\n".join(outcome.trace), language="text")

    with st.expander(t("usecases.decision_code")):
        st.code(case.decide_source(), language="python")

    st.divider()

    if not run.llm.ok:
        # Jev only: a single column is the clearest presentation.
        st.subheader(t("common.answers"))
        ui.render_answers(run.jev, questions, lang)
        ui.render_raw(run.jev, lang)
        return

    # Both engines ran, so compare them aligned row by row.
    ui.render_side_by_side(run, questions, lang)

    st.divider()
    st.subheader(t("compare.per_question"))
    ui.render_delta_table(run, lang)

    # The payoff of the comparison: feed the LLM's answers through the *same*
    # branching code and see whether the application would have acted
    # differently. A disagreement that changes the action is the one that matters.
    llm_outcome = case.decide(run.llm, decided_state)
    same = llm_outcome.action == outcome.action
    st.markdown(f"##### {t('usecases.outcome_compare')}")
    left, right = st.columns(2)
    with left:
        st.caption(t("common.jev"))
        CALLOUTS.get(outcome.level, st.info)(
            f"**{case.action_label(outcome.action, lang)}**  \n`{outcome.action}`",
            icon=ICONS.get(outcome.level, ICONS["info"]),
        )
    with right:
        st.caption(t("common.llm"))
        (st.success if same else st.warning)(
            f"**{case.action_label(llm_outcome.action, lang)}**  \n"
            f"`{llm_outcome.action}`",
            icon=ICONS["success"] if same else ICONS["warning"],
        )
    st.caption(
        t("usecases.same_action") if same else t("usecases.different_action")
    )


def _render_scale_note(result, lang: str) -> None:
    """Project the measured single-call cost out to production volumes."""
    if not result.cost_usd:
        return
    per_thousand = result.cost_usd * 1_000
    per_hour_at_10hz = result.cost_usd * 10 * 3600
    st.caption(
        ui.md_safe(
            f"At this size: **{ui.format_cost(per_thousand)} / 1,000 decisions** · "
            f"**${per_hour_at_10hz:,.2f} / hour** sustained at 10 decisions "
            "per second."
        )
    )
