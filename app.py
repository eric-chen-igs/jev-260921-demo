"""Jev vs LLM — a Streamlit demo of TypeSafe's System One model.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from jevdemo.i18n import t
from jevdemo.settings import render_sidebar
from views import about, compare, economics, playground, usecases

st.set_page_config(
    page_title="Jev vs LLM — TypeSafe System One Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    settings = render_sidebar()
    lang = settings.lang

    # Pages are declared in code rather than as a `pages/` directory so their
    # titles can follow the selected language.
    pages = {
        t("nav.section_learn", lang): [
            st.Page(
                lambda: about.render(settings),
                title=t("nav.overview", lang),
                icon=":material/lightbulb:",
                url_path="overview",
                default=True,
            ),
            st.Page(
                lambda: economics.render(settings),
                title=t("nav.economics", lang),
                icon=":material/savings:",
                url_path="economics",
            ),
        ],
        t("nav.section_try", lang): [
            st.Page(
                lambda: usecases.render(settings),
                title=t("nav.usecases", lang),
                icon=":material/apps:",
                url_path="use-cases",
            ),
            st.Page(
                lambda: compare.render(settings),
                title=t("nav.compare", lang),
                icon=":material/compare_arrows:",
                url_path="compare",
            ),
            st.Page(
                lambda: playground.render(settings),
                title=t("nav.playground", lang),
                icon=":material/science:",
                url_path="playground",
            ),
        ],
    }

    st.navigation(pages).run()


if __name__ == "__main__":
    main()
