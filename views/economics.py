"""Cost and latency model for the decision layer of a workflow."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from jevdemo.jev_client import JEV_INPUT_USD_PER_MTOK
from jevdemo.settings import AppSettings
from jevdemo.ui import format_cost, format_multiplier, md_safe


def _humanise_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f} s"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    if seconds < 86400:
        return f"{seconds / 3600:.1f} h"
    return f"{seconds / 86400:.1f} days"


def render(settings: AppSettings) -> None:
    t = settings.t

    st.title(t("nav.economics"))
    st.markdown(f"#### {t('economics.heading')}")
    st.caption(t("economics.intro"))

    left, right = st.columns(2)
    with left:
        decisions = st.number_input(
            t("economics.decisions"),
            min_value=1_000,
            max_value=1_000_000_000,
            value=1_000_000,
            step=100_000,
        )
        input_tokens = st.number_input(
            t("economics.state_tokens"), min_value=50, max_value=64_000, value=600, step=50
        )
        llm_output_tokens = st.number_input(
            t("economics.llm_output_tokens"),
            min_value=10,
            max_value=32_000,
            value=180,
            step=10,
        )
    with right:
        llm_input_price = st.number_input(
            t("economics.llm_in_price"),
            min_value=0.001,
            max_value=100.0,
            value=2.0,
            step=0.25,
            format="%.3f",
        )
        llm_output_price = st.number_input(
            t("economics.llm_out_price"),
            min_value=0.001,
            max_value=500.0,
            value=12.0,
            step=0.5,
            format="%.3f",
        )
        jev_latency_ms = st.slider(
            t("economics.jev_latency"), min_value=70, max_value=500, value=180, step=10
        )
        llm_latency_s = st.slider(
            t("economics.llm_latency"), min_value=1.0, max_value=60.0, value=9.0, step=0.5
        )

    # Jev bills input tokens only; output is free.
    jev_cost_each = input_tokens / 1_000_000 * JEV_INPUT_USD_PER_MTOK
    llm_cost_each = (
        input_tokens / 1_000_000 * llm_input_price
        + llm_output_tokens / 1_000_000 * llm_output_price
    )
    jev_total = jev_cost_each * decisions
    llm_total = llm_cost_each * decisions

    jev_seconds = decisions * jev_latency_ms / 1000
    llm_seconds = decisions * llm_latency_s

    st.divider()
    st.subheader(t("economics.monthly_cost"))

    metrics = st.columns(4)
    metrics[0].metric(
        f"{t('common.jev')} — {t('economics.monthly_cost')}", format_cost(jev_total)
    )
    metrics[1].metric(
        f"{t('common.llm')} — {t('economics.monthly_cost')}", format_cost(llm_total)
    )
    metrics[2].metric(
        t("economics.savings"),
        format_cost(llm_total - jev_total),
        delta=f"-{(1 - jev_total / llm_total) * 100:.1f}%" if llm_total else None,
        delta_color="inverse",
    )
    metrics[3].metric(
        t("common.cheaper"),
        format_multiplier(llm_total / jev_total) if jev_total else "—",
    )

    table = pd.DataFrame(
        [
            {
                "Engine": "Jev",
                "Cost / decision": format_cost(jev_cost_each),
                t("economics.monthly_cost"): format_cost(jev_total),
                t("economics.serial_time"): _humanise_duration(jev_seconds),
            },
            {
                "Engine": f"LLM ({settings.llm_model})",
                "Cost / decision": format_cost(llm_cost_each),
                t("economics.monthly_cost"): format_cost(llm_total),
                t("economics.serial_time"): _humanise_duration(llm_seconds),
            },
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(md_safe(t("economics.note")))

    # ------------------------------------------------------------------
    # The cascade
    # ------------------------------------------------------------------
    st.divider()
    st.subheader(t("economics.cascade_heading"))
    st.caption(t("economics.cascade_intro"))

    escalation = st.slider(
        t("economics.escalation"),
        min_value=0,
        max_value=100,
        value=15,
        step=1,
        format="%d%%",
    )
    share = escalation / 100
    cascade_total = jev_total + llm_total * share

    cascade_metrics = st.columns(3)
    cascade_metrics[0].metric(t("economics.cascade_cost"), format_cost(cascade_total))
    cascade_metrics[1].metric(
        t("economics.vs_llm_only"),
        format_cost(llm_total - cascade_total),
        delta=(
            f"-{(1 - cascade_total / llm_total) * 100:.1f}%" if llm_total else None
        ),
        delta_color="inverse",
    )
    cascade_metrics[2].metric(
        t("common.cheaper"),
        format_multiplier(llm_total / cascade_total) if cascade_total else "—",
    )

    curve = pd.DataFrame(
        {
            "escalation_share": [i / 100 for i in range(0, 101, 5)],
            "cascade": [jev_total + llm_total * (i / 100) for i in range(0, 101, 5)],
            "llm_only": [llm_total] * 21,
            "jev_only": [jev_total] * 21,
        }
    ).set_index("escalation_share")
    st.line_chart(curve, height=280)
    st.caption(
        "Every decision pays the Jev call; only the escalated share also pays "
        "the LLM. The crossover point is where routing stops paying for itself "
        "— useful for deciding how conservative your confidence thresholds "
        "can afford to be."
    )
