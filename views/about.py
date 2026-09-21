"""The "What is Jev?" page: explains the model class and compares it to LLMs."""

from __future__ import annotations

import streamlit as st

from jevdemo.settings import AppSettings
from jevdemo.ui import md_safe

CURL_EXAMPLE = """\
curl https://openrouter.ai/api/alpha/decisions \\
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "typesafe/jev-latest",
    "state": {
      "ticket": "My checkout page shows a blank screen after I click Pay.",
      "customer_tier": "enterprise"
    },
    "questions": {
      "team": {
        "type": "choice",
        "instructions": "Which team should own this ticket?",
        "criteria": {
          "payments": "Checkout, billing, or payment processing issues.",
          "frontend": "Rendering, layout, or browser compatibility issues.",
          "account":  "Login, permissions, or profile issues."
        }
      },
      "urgency": {
        "type": "score",
        "instructions": "How urgent is this ticket?",
        "criteria": [
          "Can wait for the next release",
          "Should be fixed this week",
          "Blocking revenue right now"
        ]
      },
      "is_bug": {
        "type": "noul",
        "instructions": "Is the customer reporting a software defect?",
        "criteria": {
          "true":  "The customer describes broken or unexpected behaviour.",
          "false": "The customer is asking a question or requesting a feature."
        }
      }
    }
  }'
"""

RESPONSE_EXAMPLE = """\
{
  "id": "gen-dec-1789738314-X5e5eKGQdvR9rblyX250",
  "model": "typesafe/jev-1.13-20260917",
  "provider": "TypeSafe",
  "answers": {
    "team": {
      "type": "choice",
      "choice": "payments",
      "confidence": 0.75,
      "probabilities": { "payments": 0.84, "frontend": 0.16, "account": 0.0 }
    },
    "urgency": {
      "type": "score",
      "score": 1.99,
      "confidence": 0.99,
      "probabilities": { "0": 0.0, "1": 0.01, "2": 0.99 },
      "legend": {
        "0": "Can wait for the next release",
        "1": "Should be fixed this week",
        "2": "Blocking revenue right now"
      }
    },
    "is_bug": { "type": "noul", "noul": 0.96 }
  },
  "usage": { "input_tokens": 476, "output_tokens": 70, "cost": 0.000019992 }
}
"""

CONSUMING_EXAMPLE = '''\
# The answers are already typed, so this is just ordinary Python.
# No parsing, no validation, no retry-on-malformed-JSON.
answers = response["answers"]

if answers["is_bug"]["noul"] > 0.7:
    team = answers["team"]

    # One threshold per action, scaled to what being wrong costs.
    if team["confidence"] < 0.55:
        route_to_human(ticket)                    # the floor: genuinely unsure
    elif answers["urgency"]["score"] > 1.5:
        page_oncall(ticket, team=team["choice"])   # expensive, so a higher bar
    else:
        enqueue(ticket, team=team["choice"])
else:
    reply_with_docs(ticket)
'''


def render(settings: AppSettings) -> None:
    t = settings.t

    st.title(t("nav.overview"))
    st.markdown(f"#### {t('overview.heading')}")
    st.markdown(md_safe(t("overview.body")))

    st.divider()
    st.header(t("overview.table_heading"))
    st.markdown(md_safe(t("overview.table_body")))

    st.divider()
    st.header(t("overview.wire_heading"))
    st.markdown(md_safe(t("overview.wire_body")))

    request_tab, response_tab, code_tab = st.tabs(
        ["Request", "Response", "Consuming the answers"]
    )
    with request_tab:
        st.code(CURL_EXAMPLE, language="bash")
    with response_tab:
        st.code(RESPONSE_EXAMPLE, language="json")
    with code_tab:
        st.code(CONSUMING_EXAMPLE, language="python")

    st.divider()
    st.header(t("overview.caveats_heading"))
    st.markdown(md_safe(t("overview.caveats_body")))

    st.divider()
    st.subheader(t("overview.sources"))
    st.markdown(
        "- [Introducing System One Models & Jev — TypeSafe AI]"
        "(https://typesafe.ai/blog/introducing-system-one-models-and-jev)\n"
        "- [Jev Latest on OpenRouter](https://openrouter.ai/~typesafe/jev-latest)\n"
        "- [OpenRouter OpenAPI specification](https://openrouter.ai/openapi.json)"
        " — the `POST /api/alpha/decisions` schema this app is built against\n\n"
        "Figures quoted on this page are TypeSafe's own published numbers and are"
        " summarised here rather than reproduced. Content was rephrased for"
        " compliance with licensing restrictions."
    )
