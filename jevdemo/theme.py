"""Runtime light/dark switching for the sidebar control.

Streamlit has no public API for this. `st.set_option` explicitly refuses
`theme.base` ("cannot be set on the fly"), and as of 1.64 the theme is compiled
into emotion class names rather than exposed as CSS custom properties, so
restyling from injected CSS would mean overriding generated class names and
would break on any upgrade.

The internal config module has no such guard, and the frontend does pick up the
new palette on the next rerun — verified by reading the computed background of
`.stApp` before and after a switch (#FFFFFF -> #0E1117 and back). So that is
what this module uses, behind a narrow interface and a graceful fallback.

Two consequences worth knowing:

1. It is a private API. If a future Streamlit release locks it down,
   `apply()` degrades to a no-op and returns False rather than raising, and the
   sidebar explains that the toolbar menu still works.
2. Streamlit config is *process-global*, not per-session. On a shared
   deployment one visitor's choice repaints the app for everyone. That is
   acceptable for a local demo and is called out in the README, but it is the
   reason this is not offered as a general-purpose recipe.
"""

from __future__ import annotations

import streamlit as st
from streamlit import config

LIGHT = "light"
DARK = "dark"
MODES = (LIGHT, DARK)

# Streamlit's own toolbar offers Light/Dark/System. This control only covers the
# two explicit modes, since "System" is already the default before any switch.
_OPTION = "theme.base"

# Palettes are applied here rather than declared as `[theme.light]` /
# `[theme.dark]` in config.toml, and that is a load-bearing detail. Declaring
# both sections makes the frontend choose a palette from its own light/dark
# preference and ignore `theme.base` entirely, which silently breaks this
# control — verified by watching the background stay white while `base` flipped.
# Setting the individual colours alongside `base` keeps one source of truth.
PALETTES: dict[str, dict[str, str]] = {
    LIGHT: {
        "theme.primaryColor": "#4F46E5",
        "theme.backgroundColor": "#FFFFFF",
        "theme.secondaryBackgroundColor": "#F5F5FA",
        "theme.textColor": "#111827",
        "theme.borderColor": "#E4E4EF",
    },
    DARK: {
        # A lighter indigo: #4F46E5 is too dark to read against #0E1117.
        "theme.primaryColor": "#8B85F5",
        "theme.backgroundColor": "#0E1117",
        "theme.secondaryBackgroundColor": "#1B2029",
        "theme.textColor": "#FAFAFA",
        "theme.borderColor": "#2A3038",
    },
}


def current() -> str:
    """The palette currently in effect."""
    try:
        value = config.get_option(_OPTION)
    except Exception:  # noqa: BLE001 - private API, treat any failure as unknown
        return LIGHT
    return value if value in MODES else LIGHT


def apply(mode: str) -> bool:
    """Switch the palette, returning False if the private API is unavailable.

    Callers are expected to rerun afterwards; the frontend only picks up the new
    palette on the next script run.
    """
    if mode not in MODES:
        return False
    try:
        config.set_option(_OPTION, mode)
        for option, value in PALETTES[mode].items():
            config.set_option(option, value)
    except Exception:  # noqa: BLE001 - never take the app down over a colour
        return False
    return True


def sync(desired: str) -> None:
    """Align the live theme with `desired`, rerunning once if it changed.

    The guard matters: rerunning unconditionally would loop forever. After the
    rerun `current()` equals `desired`, so the branch is not taken again.
    """
    if desired not in MODES or current() == desired:
        return
    if apply(desired):
        st.rerun()


def supported() -> bool:
    """Whether switching works in this Streamlit build."""
    try:
        config.get_option(_OPTION)
    except Exception:  # noqa: BLE001
        return False
    return True
