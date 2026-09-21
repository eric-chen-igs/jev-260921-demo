"""The Jev vs LLM side-by-side comparison page."""

from __future__ import annotations

import streamlit as st

from jevdemo import ui
from jevdemo.compare import run_comparison
from jevdemo.i18n import pick
from jevdemo.settings import AppSettings
from jevdemo.usecases import registry

STATE_KEY = "compare_run"


def render(settings: AppSettings) -> None:
    lang = settings.lang
    t = settings.t

    st.title(t("nav.compare"))
    st.markdown(f"#### {t('compare.heading')}")
    st.caption(t("compare.intro"))

    cases = registry()
    case_ids = [case.id for case in cases]
    labels = {case.id: f"{pick(case.title, lang)}" for case in cases}

    selected_id = st.selectbox(
        t("compare.load_case"),
        options=case_ids,
        format_func=lambda cid: labels[cid],
        key="compare_case",
    )
    case = next(c for c in cases if c.id == selected_id)

    sample_ids = [s.id for s in case.samples]
    sample_id = st.radio(
        t("common.preset"),
        options=sample_ids,
        format_func=lambda sid: pick(
            case.sample_by_id(sid).name, lang  # type: ignore[union-attr]
        ),
        horizontal=True,
        key=f"compare_sample_{case.id}",
    )
    sample = case.sample_by_id(sample_id)
    assert sample is not None

    left, right = st.columns([3, 2])
    with left:
        state = ui.state_editor(
            sample.state, lang, key=f"compare_state_{case.id}_{sample.id}", height=300
        )
    with right:
        questions = case.questions_for(state)
        st.markdown(f"**{t('common.questions')}** ({len(questions)})")
        ui.render_questions_reference(questions, lang)

    if not settings.llm_available:
        if not settings.enable_llm:
            st.info(t("compare.llm_disabled"), icon=":material/toggle_off:")
        else:
            st.warning(t("sidebar.simulated_explain"), icon=":material/science:")

    if st.button(t("common.run"), type="primary", icon=":material/play_arrow:"):
        with st.spinner(t("common.running")):
            st.session_state[STATE_KEY] = run_comparison(
                settings.jev_client(),
                settings.llm_client(),
                state,
                questions,
                include_llm=settings.llm_available,
                simulation_hint=sample.hint,
            )
            st.session_state[STATE_KEY + "_questions"] = questions

    run = st.session_state.get(STATE_KEY)
    if run is None:
        st.info(t("common.no_run_yet"), icon=":material/info:")
        return

    questions = st.session_state.get(STATE_KEY + "_questions", questions)

    st.divider()
    if settings.llm_available and run.llm.ok:
        ui.render_comparison_summary(run, lang)
        st.divider()

    jev_column, llm_column = st.columns(2)

    with jev_column:
        st.subheader(t("common.jev"))
        ui.render_result_header(run.jev, lang)
        ui.render_type_safety(run.jev, lang)
        st.markdown(f"**{t('common.answers')}**")
        ui.render_answers(run.jev, questions, lang)
        ui.render_raw(run.jev, lang)

    with llm_column:
        st.subheader(t("common.llm"))
        if not run.llm.ok:
            st.error(f"**{t('common.error', )}:** {run.llm.error}")
        else:
            ui.render_result_header(run.llm, lang)
            ui.render_type_safety(run.llm, lang)
            st.markdown(f"**{t('common.answers')}**")
            ui.render_answers(run.llm, questions, lang)
            ui.render_raw(run.llm, lang)

    if run.deltas:
        st.divider()
        st.subheader(t("compare.per_question"))
        ui.render_delta_table(run, lang)

        disagreements = run.disagreements
        if disagreements:
            st.markdown(f"**{t('compare.disagreements')}**")
            for delta in disagreements:
                st.markdown(
                    f"- `{delta.key}` — {t('common.jev')}: **{delta.jev_display}** · "
                    f"{t('common.llm')}: **{delta.llm_display}**  \n"
                    f"  {delta.label}"
                )
        else:
            st.success(t("compare.all_agree"), icon=":material/handshake:")
