"""Ready-made scenarios for the playground.

Each example is deliberately small and self-explanatory: a short state plus
three or four questions, so the shape of a decision call is obvious at a glance
and quick to modify.

Question rows use the same dict shape the playground editor works with, which
means loading an example simply replaces the editor's contents and everything
stays editable afterwards.

As everywhere else in this app, `instructions` and criteria are English because
they are model-facing; only the example name and blurb are translated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlaygroundExample:
    id: str
    icon: str
    name: dict[str, str]
    blurb: dict[str, str]
    state: Any
    questions: list[dict[str, Any]] = field(default_factory=list)


def _q(
    key: str,
    qtype: str,
    instructions: str,
    *,
    options: str = "",
    levels: str = "",
    true_criteria: str = "",
    false_criteria: str = "",
) -> dict[str, Any]:
    """Build one editor row. `uid` is assigned when the example is loaded."""
    return {
        "key": key,
        "type": qtype,
        "instructions": instructions,
        "options": options,
        "levels": levels,
        "true_criteria": true_criteria,
        "false_criteria": false_criteria,
    }


EXAMPLES: list[PlaygroundExample] = [
    PlaygroundExample(
        id="email_triage",
        icon=":material/mail:",
        name={"en": "Email triage", "zh-TW": "郵件分流"},
        blurb={
            "en": "The smallest useful call: is this urgent, and who handles it?",
            "zh-TW": "最小但實用的呼叫：這封信急不急？該由誰處理？",
        },
        state={
            "from": "facilities@buildingmgmt.com",
            "subject": "Water leak on floor 12 — immediate access needed",
            "body": (
                "We've detected water coming through the ceiling in the 12th "
                "floor server room. We need someone to open the door in the "
                "next 30 minutes or we will have to force entry."
            ),
        },
        questions=[
            _q(
                "urgency",
                "score",
                "How quickly does this email need a response?",
                levels=(
                    "Can wait a week.\n"
                    "Should be answered in a day or two.\n"
                    "Needs a response today.\n"
                    "Needs a response within the hour."
                ),
            ),
            _q(
                "owner",
                "choice",
                "Which team should handle this email?",
                options=(
                    "facilities: Building, access, power, or physical space.\n"
                    "it_ops: Servers, network, or hardware.\n"
                    "security: Access control or an active security concern.\n"
                    "admin: General correspondence."
                ),
            ),
            _q(
                "needs_human_now",
                "noul",
                "Someone must act on this in person rather than by reply.",
                true_criteria="Physical presence or an immediate real-world action is required.",
                false_criteria="A written reply is a sufficient response.",
            ),
        ],
    ),
    PlaygroundExample(
        id="product_review",
        icon=":material/reviews:",
        name={"en": "Product review analysis", "zh-TW": "商品評論分析"},
        blurb={
            "en": "Turn free-text feedback into structured fields you can group by.",
            "zh-TW": "把自由文字的回饋轉換成可分組彙整的結構化欄位。",
        },
        state={
            "product": "Aurora 14in Laptop Stand",
            "rating_given": 2,
            "review": (
                "Looks gorgeous on the desk and the aluminium feels solid. But "
                "the rubber feet came unglued within two weeks and now it "
                "slides every time I type. Support took nine days to reply and "
                "then asked me for the receipt again. Would not buy another."
            ),
        },
        questions=[
            _q(
                "sentiment",
                "score",
                "Overall sentiment of this review.",
                levels=(
                    "Very negative.\n"
                    "Mostly negative.\n"
                    "Mixed.\n"
                    "Mostly positive.\n"
                    "Very positive."
                ),
            ),
            _q(
                "main_complaint",
                "choice",
                "What is the single biggest problem the reviewer describes?",
                options=(
                    "build_quality: Something physically broke or wore out.\n"
                    "support: Poor or slow customer service.\n"
                    "price: Felt too expensive for the value.\n"
                    "shipping: Delivery or packaging problems.\n"
                    "none: No real complaint is made."
                ),
            ),
            _q(
                "mentions_durability",
                "noul",
                "The reviewer comments on how well the product holds up over time.",
                true_criteria="Wear, breakage, or longevity is discussed.",
                false_criteria="Durability is not mentioned.",
            ),
            _q(
                "worth_replying",
                "noul",
                "This review warrants a personal follow-up from the support team.",
                true_criteria="There is an unresolved issue a human could still fix.",
                false_criteria="Nothing actionable remains.",
            ),
        ],
    ),
    PlaygroundExample(
        id="expense_approval",
        icon=":material/receipt_long:",
        name={"en": "Expense approval", "zh-TW": "費用核銷審批"},
        blurb={
            "en": "A policy check where the arithmetic stays in code and only the judgement is asked.",
            "zh-TW": "政策檢查範例：算術留在程式碼中，只把判斷交給模型。",
        },
        state={
            "employee": {"name": "R. Okafor", "department": "Sales", "level": "manager"},
            "expense": {
                "amount_usd": 412.50,
                "merchant": "Nobu Downtown",
                "date": "2026-09-18",
                "category_claimed": "client_entertainment",
                "attendees": ["R. Okafor", "2 prospects from Acme Freight"],
                "note": "Dinner to close the Acme renewal. Receipt attached.",
            },
            "policy_extract": (
                "Client entertainment is reimbursable when at least one external "
                "attendee is named and the purpose is recorded. Meals over $150 "
                "per head require director approval."
            ),
        },
        questions=[
            _q(
                "category_correct",
                "noul",
                "The claimed expense category matches what the expense actually is.",
                true_criteria="The described purpose fits the claimed category.",
                false_criteria="The expense belongs in a different category.",
            ),
            _q(
                "policy_satisfied",
                "noul",
                "The stated policy requirements for this category are met by the evidence given.",
                true_criteria="Every documentation requirement in the policy extract is present.",
                false_criteria="At least one required detail is missing.",
            ),
            _q(
                "business_purpose_clarity",
                "score",
                "How clearly is the business purpose documented?",
                levels=(
                    "No purpose given.\n"
                    "Vague purpose.\n"
                    "Specific, verifiable purpose."
                ),
            ),
            _q(
                "fraud_signal",
                "score",
                "How unusual is this claim relative to a normal business expense?",
                levels=(
                    "Entirely routine.\n"
                    "Slightly unusual but explainable.\n"
                    "Suspicious; warrants review."
                ),
            ),
        ],
    ),
    PlaygroundExample(
        id="chatbot_routing",
        icon=":material/forum:",
        name={"en": "Chatbot turn routing", "zh-TW": "聊天機器人回合路由"},
        blurb={
            "en": "Decide per message whether code, an LLM, or a human should answer.",
            "zh-TW": "逐則訊息判斷該由程式碼、LLM 或真人來回應。",
        },
        state={
            "conversation": [
                {"role": "user", "text": "hi, where's my order #55210?"},
                {"role": "bot", "text": "It shipped on Tuesday and is due Friday."},
                {
                    "role": "user",
                    "text": (
                        "friday is useless, it was a birthday present for "
                        "yesterday. this is the second time. i want to speak to "
                        "an actual person and i want the shipping refunded."
                    ),
                },
            ],
            "customer": {"orders_last_year": 14, "prior_complaints": 1},
        },
        questions=[
            _q(
                "intent",
                "choice",
                "What does the customer want on this latest turn?",
                options=(
                    "order_status: Information about where an order is.\n"
                    "refund_request: Money back or a credit.\n"
                    "complaint: To express dissatisfaction and be heard.\n"
                    "human_handoff: To stop talking to a bot.\n"
                    "other: None of the above."
                ),
            ),
            _q(
                "frustration",
                "score",
                "How frustrated is the customer on this latest turn?",
                levels=(
                    "Calm.\nMildly annoyed.\nClearly frustrated.\nAngry."
                ),
            ),
            _q(
                "asks_for_human",
                "noul",
                "The customer explicitly asks to be transferred to a person.",
                true_criteria="They ask for a human, agent, or representative.",
                false_criteria="No such request is made.",
            ),
            _q(
                "resolvable_by_bot",
                "noul",
                "Everything the customer is asking for can be handled without a person.",
                true_criteria="All requests map to automated actions the bot can take.",
                false_criteria="At least one request needs human discretion.",
            ),
        ],
    ),
    PlaygroundExample(
        id="code_review_risk",
        icon=":material/code:",
        name={"en": "Code change risk", "zh-TW": "程式碼變更風險"},
        blurb={
            "en": "Score a diff so reviewers' attention goes where it is needed.",
            "zh-TW": "為一份 diff 評分，把審查者的注意力導向真正需要的地方。",
        },
        state={
            "pull_request": {
                "title": "Speed up session lookup",
                "files_changed": ["auth/session.py", "auth/cache.py", "tests/test_cache.py"],
                "additions": 84,
                "deletions": 31,
                "description": (
                    "Caches decoded session tokens in memory for 5 minutes to "
                    "avoid re-verifying the signature on every request. Cuts p99 "
                    "auth latency from 40ms to 3ms."
                ),
            },
            "diff_summary": (
                "Adds an in-process TTL cache keyed by the raw token string. "
                "Cache is not invalidated on logout. Signature verification is "
                "skipped entirely on cache hit. New test covers cache hits and "
                "expiry but not logout."
            ),
        },
        questions=[
            _q(
                "touches_security",
                "noul",
                "This change affects authentication, authorisation, or credential handling.",
                true_criteria="Security-relevant logic is modified.",
                false_criteria="The change is unrelated to security.",
            ),
            _q(
                "risk",
                "score",
                "How risky is merging this change as described?",
                levels=(
                    "Trivially safe.\n"
                    "Low risk; well covered.\n"
                    "Moderate risk; needs a careful read.\n"
                    "High risk; could cause a security or correctness incident."
                ),
            ),
            _q(
                "test_coverage",
                "score",
                "How well do the described tests cover the described behaviour change?",
                levels=(
                    "No meaningful tests.\n"
                    "Happy path only.\n"
                    "Main paths plus some edge cases.\n"
                    "Thorough, including failure modes."
                ),
            ),
            _q(
                "needs_senior_review",
                "noul",
                "This change should be reviewed by a senior or domain owner rather than any teammate.",
                true_criteria="The blast radius or subtlety justifies a specialist reviewer.",
                false_criteria="Any competent reviewer could approve it.",
            ),
        ],
    ),
    PlaygroundExample(
        id="applicant_screen",
        icon=":material/badge:",
        name={"en": "Applicant quick screen", "zh-TW": "應徵者快速篩選"},
        blurb={
            "en": "Three independent scores instead of one opaque rating.",
            "zh-TW": "以三個獨立分數取代單一不透明評分。",
        },
        state={
            "role": "Data Engineer — streaming pipelines",
            "application": (
                "Five years at a logistics firm building Airflow batch jobs in "
                "Python; last eighteen months migrating them to Flink for "
                "near-real-time ETA prediction. Ran the on-call rotation for the "
                "pipeline. Comfortable with SQL and Terraform. No formal CS "
                "degree — came in through a bootcamp and stayed."
            ),
        },
        questions=[
            _q(
                "streaming_depth",
                "score",
                "Depth of streaming data experience evidenced here.",
                levels=(
                    "None.\n"
                    "Aware of it only.\n"
                    "Built batch pipelines.\n"
                    "Ran streaming pipelines in production.\n"
                    "Owned high-throughput streaming at scale."
                ),
            ),
            _q(
                "operational_maturity",
                "score",
                "Evidence of operating what they build.",
                levels=(
                    "None.\n"
                    "Some involvement.\n"
                    "Clear ownership of production reliability."
                ),
            ),
            _q(
                "writes_specifically",
                "noul",
                "The application gives concrete, verifiable specifics rather than generic claims.",
                true_criteria="Named tools, durations, and outcomes are given.",
                false_criteria="Mostly buzzwords or unsupported adjectives.",
            ),
        ],
    ),
    PlaygroundExample(
        id="incident_update",
        icon=":material/campaign:",
        name={"en": "Status page update", "zh-TW": "狀態頁公告判斷"},
        blurb={
            "en": "Decide whether to tell customers, and how loudly.",
            "zh-TW": "判斷是否要告知客戶，以及該用多大的力度。",
        },
        state={
            "incident": {
                "started": "2026-09-21T03:10:00Z",
                "symptom": "PDF export failing with a timeout",
                "affected_share_of_requests": 0.06,
                "workaround": "CSV export works normally",
                "internal_status": "root cause identified, fix in staging",
            },
            "support_signal": {"tickets_opened": 4, "social_mentions": 0},
        },
        questions=[
            _q(
                "customer_visible",
                "noul",
                "Customers are likely to notice this themselves.",
                true_criteria="The failure surfaces directly in normal product use.",
                false_criteria="It is internal or effectively invisible to users.",
            ),
            _q(
                "severity",
                "score",
                "How serious is the customer impact?",
                levels=(
                    "Negligible.\n"
                    "Minor inconvenience with a workaround.\n"
                    "A feature is unusable.\n"
                    "Core product is down."
                ),
            ),
            _q(
                "channel",
                "choice",
                "Where should this be communicated?",
                options=(
                    "nowhere: No external communication needed.\n"
                    "status_page_only: A quiet status page note.\n"
                    "status_page_and_email: Status page plus email to affected accounts.\n"
                    "all_channels: Status page, email, and in-app banner."
                ),
            ),
        ],
    ),
    PlaygroundExample(
        id="document_check",
        icon=":material/description:",
        name={"en": "Document completeness check", "zh-TW": "文件完整性檢查"},
        blurb={
            "en": "One noul per required field — the reliable way to check a checklist.",
            "zh-TW": "每個必填欄位各一個 noul —— 這是檢查清單最可靠的做法。",
        },
        state={
            "document_type": "Supplier onboarding form",
            "submitted_text": (
                "Company: Kestrel Components Ltd. Registered in Ireland, company "
                "number 664120. Contact: Aoife Byrne, aoife@kestrel-comp.ie. "
                "We manufacture precision fasteners. Bank details will follow "
                "separately once the NDA is signed. VAT number pending "
                "registration."
            ),
        },
        questions=[
            _q(
                "has_legal_name",
                "noul",
                "A registered legal company name is provided.",
                true_criteria="A full legal entity name appears.",
                false_criteria="Only a trading name or nothing at all.",
            ),
            _q(
                "has_registration_number",
                "noul",
                "A company registration number is provided.",
                true_criteria="A registration or company number appears.",
                false_criteria="No registration number is given.",
            ),
            _q(
                "has_tax_id",
                "noul",
                "A valid tax or VAT identifier is provided.",
                true_criteria="A tax or VAT number is actually stated.",
                false_criteria="It is missing, pending, or promised for later.",
            ),
            _q(
                "has_bank_details",
                "noul",
                "Bank account details are provided.",
                true_criteria="Account details are actually present.",
                false_criteria="They are absent or deferred.",
            ),
            _q(
                "has_named_contact",
                "noul",
                "A named human contact with an email address is provided.",
                true_criteria="Both a person's name and a contact address appear.",
                false_criteria="One or both are missing.",
            ),
        ],
    ),
]


def by_id(example_id: str) -> PlaygroundExample | None:
    for example in EXAMPLES:
        if example.id == example_id:
            return example
    return None
