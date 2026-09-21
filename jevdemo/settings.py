"""Sidebar settings menu and the app-wide configuration object it produces."""

from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st

from . import theme
from .i18n import DEFAULT_LANG, LANGUAGES, t
from .jev_client import JEV_MODEL_CHOICES, JevClient, JevConfig
from .llm_client import (
    DEFAULT_LLM_MODEL,
    LLMClient,
    LLMConfig,
    llm_model_choices,
    llm_option,
)

REASONING_EFFORTS = ["default", "none", "low", "medium", "high"]


@dataclass
class AppSettings:
    lang: str
    api_key: str
    transport: str
    jev_model: str
    llm_model: str
    enable_llm: bool
    timeout: float
    reasoning_effort: str
    temperature: float
    theme_mode: str = theme.LIGHT

    @property
    def simulated(self) -> bool:
        return not self.api_key

    @property
    def llm_available(self) -> bool:
        return self.enable_llm and bool(self.api_key)

    def jev_client(self) -> JevClient:
        return JevClient(
            JevConfig(
                api_key=self.api_key,
                model=self.jev_model,
                transport="simulated" if self.simulated else self.transport,
                timeout=self.timeout,
            )
        )

    def llm_client(self) -> LLMClient:
        return LLMClient(
            LLMConfig(
                api_key=self.api_key,
                model=self.llm_model,
                timeout=max(self.timeout, 120.0),
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
            )
        )

    def t(self, key: str, **kwargs: str) -> str:
        return t(key, self.lang, **kwargs)


def _default_api_key() -> str:
    """Seed the key field from secrets or the environment, if either is set."""
    try:
        secret = st.secrets.get("OPENROUTER_API_KEY")  # type: ignore[union-attr]
        if secret:
            return str(secret)
    except Exception:
        # st.secrets raises when no secrets file exists, which is the norm here.
        pass
    return os.environ.get("OPENROUTER_API_KEY", "")


def _format_llm_option(model_id: str) -> str:
    """Label a model with its vendor, flagging anything unavailable in HK."""
    option = llm_option(model_id)
    if option is None:
        return model_id
    marker = "" if option.available_in_hk else "  ⚠"
    return f"{model_id}  ·  {option.vendor}{marker}"


def _init_state() -> None:
    defaults = {
        "lang": DEFAULT_LANG,
        "api_key": _default_api_key(),
        "transport": "openrouter",
        "jev_model": os.environ.get("JEV_MODEL", JEV_MODEL_CHOICES[0]),
        "llm_model": os.environ.get("COMPARE_LLM_MODEL", DEFAULT_LLM_MODEL),
        "enable_llm": True,
        "timeout": 60.0,
        "reasoning_effort": "default",
        "temperature": 0.0,
        "theme_mode": theme.current(),
        "show_restricted_models": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_sidebar() -> AppSettings:
    """Draw the settings menu and return the resulting configuration."""
    _init_state()

    with st.sidebar:
        # Language first, so the rest of the menu reflects the choice
        # immediately on this same run.
        # No `index=` here: the value is owned by session_state via the key,
        # and passing both makes Streamlit warn about a conflicting default.
        lang = st.radio(
            t("sidebar.language", st.session_state["lang"]),
            options=list(LANGUAGES.keys()),
            format_func=lambda code: LANGUAGES[code],
            horizontal=True,
            key="lang",
        )

        theme_labels = {
            theme.LIGHT: f":material/light_mode: {t('sidebar.theme_light', lang)}",
            theme.DARK: f":material/dark_mode: {t('sidebar.theme_dark', lang)}",
        }
        theme_mode = st.radio(
            t("sidebar.appearance", lang),
            options=list(theme.MODES),
            format_func=lambda mode: theme_labels[mode],
            horizontal=True,
            key="theme_mode",
        )
        if theme.supported():
            # Repaints on the rerun this triggers; no-ops once already in sync.
            theme.sync(theme_mode)
        else:
            st.caption(t("sidebar.theme_unsupported", lang))

        st.divider()
        st.subheader(t("sidebar.api", lang))

        api_key = st.text_input(
            t("sidebar.api_key", lang),
            type="password",
            help=t("sidebar.api_key_help", lang),
            key="api_key",
            placeholder="sk-or-v1-…",
        ).strip()

        if api_key:
            st.success(t("sidebar.api_key_ok", lang), icon=":material/check_circle:")
        else:
            st.warning(t("sidebar.api_key_missing", lang), icon=":material/science:")
        st.caption(f"[{t('sidebar.get_key', lang)}](https://openrouter.ai/keys)")

        transport = st.selectbox(
            t("sidebar.transport", lang),
            options=["openrouter", "typesafe"],
            format_func=lambda v: (
                "OpenRouter · /api/alpha/decisions"
                if v == "openrouter"
                else "TypeSafe · /v1/systemone"
            ),
            help=t("sidebar.transport_help", lang),
            key="transport",
        )

        jev_model = st.selectbox(
            t("sidebar.jev_model", lang),
            options=JEV_MODEL_CHOICES,
            help=t("sidebar.jev_model_help", lang),
            key="jev_model",
            accept_new_options=True,
        )

        st.divider()
        st.subheader(t("common.llm", lang))

        enable_llm = st.toggle(
            t("sidebar.enable_llm", lang),
            help=t("sidebar.enable_llm_help", lang),
            key="enable_llm",
        )

        show_restricted = st.checkbox(
            t("sidebar.show_restricted", lang),
            help=t("sidebar.show_restricted_help", lang),
            key="show_restricted_models",
            disabled=not enable_llm,
        )
        options = llm_model_choices(include_restricted=show_restricted)

        # A previously chosen restricted model must stay in `options`, or
        # Streamlit would silently reset the widget when the filter re-engages.
        if st.session_state.get("llm_model") not in options:
            options = [*options, st.session_state["llm_model"]]

        llm_model = st.selectbox(
            t("sidebar.llm_model", lang),
            options=options,
            format_func=_format_llm_option,
            help=t("sidebar.llm_model_help", lang),
            key="llm_model",
            accept_new_options=True,
            disabled=not enable_llm,
        )

        selected = llm_option(llm_model)
        if selected is not None and not selected.available_in_hk:
            st.warning(
                t("sidebar.restricted_selected", lang),
                icon=":material/travel_explore:",
            )
            if selected.note:
                st.caption(selected.note.get(lang) or selected.note.get("en", ""))
        elif not show_restricted:
            st.caption(t("sidebar.hk_filtered", lang))

        with st.expander(t("sidebar.advanced", lang)):
            reasoning_effort = st.selectbox(
                t("sidebar.reasoning", lang),
                options=REASONING_EFFORTS,
                help=t("sidebar.reasoning_help", lang),
                key="reasoning_effort",
            )
            temperature = st.slider(
                t("sidebar.temperature", lang),
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                key="temperature",
            )
            timeout = st.slider(
                t("sidebar.timeout", lang),
                min_value=10.0,
                max_value=300.0,
                step=10.0,
                key="timeout",
            )

        if not api_key:
            st.divider()
            st.caption(f"**{t('sidebar.simulated_mode', lang)}**")
            st.caption(t("sidebar.simulated_explain", lang))

        st.divider()
        st.caption(f"**{t('sidebar.resources', lang)}**")
        st.caption(
            "· [Introducing System One Models & Jev]"
            "(https://typesafe.ai/blog/introducing-system-one-models-and-jev)  \n"
            "· [Jev on OpenRouter](https://openrouter.ai/~typesafe/jev-latest)"
        )

    return AppSettings(
        lang=lang,
        api_key=api_key,
        transport=transport,
        jev_model=jev_model,
        llm_model=llm_model,
        enable_llm=enable_llm,
        timeout=float(timeout),
        reasoning_effort=reasoning_effort,
        temperature=float(temperature),
        theme_mode=theme_mode,
    )
