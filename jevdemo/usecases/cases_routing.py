"""Demo use cases 1-4: classify an input, then route it.

These are the "smart if-statement" shape TypeSafe describes: structured outputs
slotted into ordinary software as fuzzy decision rules where hand-written logic
would be too brittle.

Question `instructions` and `criteria` are written in English in every interface
language. They are model-facing artefacts, and keeping them fixed means changing
the UI language never silently changes the decision being measured.
"""

from __future__ import annotations

from typing import Any

from ..schema import Choice, DecisionResult, Noul, Score
from .base import Outcome, Sample, UseCase

# ==========================================================================
# 1. Support ticket triage
# ==========================================================================

SUPPORT_QUESTIONS = {
    "department": Choice(
        instructions="Which team should own this ticket?",
        label="Owning team",
        criteria={
            "billing": "Charges, invoices, refunds, subscriptions, or payment failures.",
            "technical": "Something is broken, erroring, or behaving unexpectedly.",
            "account": "Login, password, permissions, seats, or security concerns.",
            "sales": "Pricing questions, upgrades, quotes, or new purchases.",
            "other": "None of the above categories fit this ticket.",
        },
    ),
    "severity": Score(
        instructions="How severe is the problem the customer describes?",
        label="Severity",
        criteria=[
            "Cosmetic or a minor annoyance; nothing is actually blocked.",
            "A feature is degraded but a workaround exists.",
            "Blocking: the customer cannot complete their task at all.",
        ],
    ),
    "frustration": Score(
        instructions="How frustrated does the customer sound?",
        label="Customer frustration",
        criteria=[
            "Calm; simply stating facts.",
            "Frustrated but civil.",
            "Very angry; strong language or threats to leave.",
        ],
    ),
    "churn_risk": Score(
        instructions="How likely does this customer seem to cancel over this issue?",
        label="Churn risk",
        criteria=[
            "No sign of cancellation risk.",
            "Mild dissatisfaction.",
            "Explicitly weighing alternatives or mentioning competitors.",
            "Stating an intention to cancel or already cancelling.",
        ],
    ),
    "refund_requested": Noul(
        instructions="The customer is explicitly asking for a refund or credit.",
        label="Refund requested",
        true_criteria="They ask for money back, a credit, or a reversed charge.",
        false_criteria="They report a problem without asking for money back.",
    ),
    "has_repro": Noul(
        instructions="The customer describes concrete steps that reproduce the problem.",
        label="Reproduction steps present",
        true_criteria="Specific actions, URLs, IDs, or a sequence an engineer could follow.",
        false_criteria="Only a vague description of the symptom.",
    ),
}


def decide_support_triage(result: DecisionResult, state: Any) -> Outcome:
    """Route a ticket. One confidence threshold per action, scaled to its cost."""
    department = result.choice("department")
    department_confidence = result.confidence("department")
    severity = result.score("severity")
    frustration = result.score("frustration")
    churn = result.score("churn_risk")

    trace = [
        f"department={department!r} confidence={department_confidence:.2f}",
        f"severity={severity:.2f} frustration={frustration:.2f} churn_risk={churn:.2f}",
        f"refund_requested={result.noul('refund_requested'):.2f} "
        f"has_repro={result.noul('has_repro'):.2f}",
    ]

    # Floor first: if the classifier is genuinely unsure, nothing automated
    # should fire. This is the branch that makes the rest safe to automate.
    if department_confidence < 0.55:
        trace.append("-> classifier below the 0.55 floor, no automation fired")
        return Outcome("human_review", "warning", trace)

    # Retention outranks topic. An angry enterprise customer talking about
    # cancelling is a retention event first and a support ticket second.
    if churn >= 2.0 or frustration >= 1.8:
        trace.append("-> retention signal outranks topic routing")
        return Outcome("escalate_csm", "warning", trace)

    if department == "technical":
        if severity >= 1.6 and result.noul("has_repro") > 0.6:
            trace.append("-> blocking and reproducible, so engineering is paged")
            return Outcome("escalate_engineering", "error", trace)
        return Outcome("bug_backlog", "info", trace)

    if department == "billing":
        # Refunds move money, so this branch demands a high bar.
        if result.noul("refund_requested") > 0.7 and department_confidence > 0.8:
            trace.append("-> refund intent clear and routing confident")
            return Outcome("refund_flow", "success", trace)
        return Outcome("billing_queue", "info", trace)

    if department == "account":
        return Outcome("account_queue", "info", trace)
    if department == "sales":
        return Outcome("sales_queue", "success", trace)
    return Outcome("general_queue", "info", trace)


SUPPORT_CASE = UseCase(
    id="support_triage",
    icon=":material/support_agent:",
    title={"en": "Support ticket triage", "zh-TW": "客服工單分流"},
    category={"en": "Classify & route", "zh-TW": "分類與路由"},
    summary={
        "en": (
            "The canonical System One workload. One call answers six questions "
            "about an inbound ticket, and ordinary Python decides where it goes "
            "— including deciding, from the model's own confidence, when *not* "
            "to decide."
        ),
        "zh-TW": (
            "最典型的 System One 工作負載。單次呼叫回答關於一張新進工單的六個問題，"
            "再由普通的 Python 決定它的去向 —— 包括根據模型自身的信賴度，"
            "判斷何時**不應該**自動決定。"
        ),
    },
    why={
        "en": (
            "Triage is a decision, not a document. Nobody reads the model's "
            "prose about the ticket; a queue assignment gets written to a "
            "database. The task also has to finish while the ticket is being "
            "created, which rules out a 10-second call.\n\n"
            "Note the ordering in the code: the confidence floor is checked "
            "*before* any routing branch, and the retention signal outranks the "
            "topic. Both are product decisions that belong in code, not in a "
            "prompt."
        ),
        "zh-TW": (
            "分流是一個決策，而不是一份文件。沒有人會閱讀模型針對工單寫出的敘述；"
            "真正被寫入資料庫的是「該進哪個佇列」。這項任務還必須在工單建立的同時完成，"
            "因此排除了耗時 10 秒的呼叫。\n\n"
            "請注意程式碼中的順序：信賴度下限在**任何**路由分支之前就先檢查，"
            "而留客訊號的優先權高於主題分類。這兩者都是屬於程式碼、而非 prompt 的產品決策。"
        ),
    },
    questions=SUPPORT_QUESTIONS,
    actions={
        "human_review": {
            "en": "Held for a human triager — the model was not confident enough",
            "zh-TW": "保留給人工分流 —— 模型信賴度不足",
        },
        "escalate_csm": {
            "en": "Escalated to the customer success manager as a retention risk",
            "zh-TW": "以留客風險升級至客戶成功經理（CSM）",
        },
        "escalate_engineering": {
            "en": "Paged engineering: blocking bug with reproduction steps",
            "zh-TW": "已呼叫工程團隊：具重現步驟的阻斷性錯誤",
        },
        "bug_backlog": {
            "en": "Filed to the bug backlog",
            "zh-TW": "已歸入錯誤待辦清單",
        },
        "refund_flow": {
            "en": "Started the automated refund flow",
            "zh-TW": "已啟動自動退款流程",
        },
        "billing_queue": {"en": "Routed to the billing queue", "zh-TW": "已路由至帳務佇列"},
        "account_queue": {"en": "Routed to the account team", "zh-TW": "已路由至帳號團隊"},
        "sales_queue": {"en": "Routed to sales", "zh-TW": "已路由至業務團隊"},
        "general_queue": {"en": "Routed to the general queue", "zh-TW": "已路由至一般佇列"},
    },
    decide=decide_support_triage,
    samples=[
        Sample(
            id="duplicate_charge",
            name={"en": "Duplicate charge, refund asked", "zh-TW": "重複收費並要求退款"},
            state={
                "ticket": {
                    "subject": "Charged twice for order A-104",
                    "body": (
                        "Hi, I placed order A-104 last Tuesday and I can see two "
                        "identical charges of $49 on my card, both on the 14th. "
                        "Could you please refund the duplicate one? No rush, I "
                        "know these things happen."
                    ),
                },
                "customer": {"plan": "pro", "tenure_months": 26, "lifetime_value_usd": 1274},
                "order": {
                    "id": "A-104",
                    "charges": [
                        {"amount_usd": 49, "status": "captured", "date": "2026-09-14"},
                        {"amount_usd": 49, "status": "captured", "date": "2026-09-14"},
                    ],
                },
                "refund_policy": "Duplicate charges are always eligible for a full refund.",
            },
            hint={
                "department": "billing",
                "severity": 1.0,
                "frustration": 0.2,
                "churn_risk": 0.1,
                "refund_requested": 0.97,
                "has_repro": 0.72,
            },
        ),
        Sample(
            id="blocking_bug",
            name={"en": "Blocking bug with repro steps", "zh-TW": "具重現步驟的阻斷性錯誤"},
            state={
                "ticket": {
                    "subject": "Checkout returns 500 for all EU customers",
                    "body": (
                        "Since roughly 09:00 UTC today, every checkout attempt "
                        "from an EU billing address fails. Steps: add any item to "
                        "cart, set country to Germany, click Pay. You get a 500 "
                        "and request ID req_8812f. Works fine with a US address. "
                        "This is blocking all our EU revenue."
                    ),
                },
                "customer": {"plan": "enterprise", "tenure_months": 14, "seats": 240},
                "environment": {"region": "eu-central-1", "sdk_version": "4.2.1"},
            },
            hint={
                "department": "technical",
                "severity": 2.0,
                "frustration": 1.1,
                "churn_risk": 0.9,
                "refund_requested": 0.04,
                "has_repro": 0.96,
            },
        ),
        Sample(
            id="churn_threat",
            name={"en": "Angry customer, churn threat", "zh-TW": "憤怒客戶並威脅解約"},
            state={
                "ticket": {
                    "subject": "Third time this month. Done.",
                    "body": (
                        "This is the THIRD outage this month and nobody has "
                        "bothered to explain what is going on. We are already "
                        "trialling a competitor and honestly at this point I am "
                        "ready to move our whole team over. Cancel my renewal "
                        "unless someone gives me a straight answer today."
                    ),
                },
                "customer": {
                    "plan": "enterprise",
                    "tenure_months": 41,
                    "seats": 520,
                    "arr_usd": 96000,
                    "renewal_in_days": 27,
                },
                "history": {"tickets_last_30d": 6, "incidents_last_30d": 3},
            },
            hint={
                "department": "technical",
                "severity": 1.7,
                "frustration": 2.0,
                "churn_risk": 3.0,
                "refund_requested": 0.28,
                "has_repro": 0.1,
            },
        ),
        Sample(
            id="ambiguous",
            name={"en": "Vague message (tests the floor)", "zh-TW": "語意模糊的訊息（測試下限）"},
            state={
                "ticket": {
                    "subject": "question",
                    "body": "hi. it's not working properly. can you check? thanks",
                },
                "customer": {"plan": "free", "tenure_months": 1},
            },
            hint={
                # Pinned low so the offline walkthrough reliably demonstrates
                # the confidence floor rather than a routing branch.
                "department": {"choice": "other", "confidence": 0.31},
                "severity": {"score": 1.0, "confidence": 0.4},
                "frustration": 0.6,
                "churn_risk": 0.4,
                "refund_requested": 0.08,
                "has_repro": 0.03,
            },
        ),
    ],
)


# ==========================================================================
# 2. Content moderation
# ==========================================================================

MODERATION_QUESTIONS = {
    "harassment": Noul(
        instructions="The content targets a specific person with insults, threats, or degradation.",
        label="Harassment",
        true_criteria="A real individual is being attacked, demeaned, or intimidated.",
        false_criteria="No specific person is targeted, or the tone is not hostile.",
    ),
    "hate_speech": Noul(
        instructions="The content attacks or dehumanises people based on a protected characteristic.",
        label="Hate speech",
        true_criteria="Race, ethnicity, religion, gender, sexuality, or disability is the basis of the attack.",
        false_criteria="No protected characteristic is used as the basis of an attack.",
    ),
    "violence_threat": Noul(
        instructions="The content threatens physical violence against someone.",
        label="Violence threat",
        true_criteria="An intent or desire to physically harm a person or group is expressed.",
        false_criteria="No threat of physical harm is present.",
    ),
    "self_harm": Noul(
        instructions="The author appears to be expressing risk of harming themselves.",
        label="Self-harm risk",
        true_criteria="The author describes their own suicidal thoughts, intent, or self-injury.",
        false_criteria="No first-person indication of self-harm risk.",
    ),
    "sexual_content": Noul(
        instructions="The content is sexually explicit.",
        label="Sexual content",
        true_criteria="Explicit sexual acts or arousal are described.",
        false_criteria="No sexually explicit material.",
    ),
    "scam_spam": Noul(
        instructions="The content is spam, a scam, or a phishing attempt.",
        label="Scam / spam",
        true_criteria="Unsolicited promotion, a financial lure, or a credential-harvesting link.",
        false_criteria="Genuine participation rather than promotion or deception.",
    ),
    "doxxing": Noul(
        instructions="The content exposes private personal information about someone.",
        label="Doxxing",
        true_criteria="A home address, phone number, private email, or identity document is revealed.",
        false_criteria="No private personal information is exposed.",
    ),
    "framing": Choice(
        instructions="What is the author's relationship to any objectionable material quoted here?",
        label="Framing / intent",
        criteria={
            "endorsing": "The author is expressing the objectionable view as their own.",
            "condemning": "The author is quoting or describing it in order to criticise it.",
            "reporting": "The author is neutrally reporting on it as news or documentation.",
            "fiction": "It appears inside clearly fictional or role-played narrative.",
            "educational": "It appears in a clinical, academic, or educational explanation.",
            "not_applicable": "There is no objectionable material to frame.",
        },
    ),
    "severity": Score(
        instructions="Overall severity of the policy problem, if any.",
        label="Severity",
        criteria=[
            "Benign; no policy issue at all.",
            "Rude or low quality, but not a policy violation.",
            "A clear policy violation.",
            "Severe: credible threat, illegal content, or targeted campaign.",
        ],
    ),
}


def decide_moderation(result: DecisionResult, state: Any) -> Outcome:
    """Apply moderation policy. The model scores signals; code owns the policy."""
    severity = result.score("severity")
    framing = result.choice("framing")
    trace = [
        f"severity={severity:.2f} framing={framing!r} "
        f"(confidence={result.confidence('framing'):.2f})",
        " ".join(
            f"{key}={result.noul(key):.2f}"
            for key in (
                "harassment",
                "hate_speech",
                "violence_threat",
                "self_harm",
                "sexual_content",
                "scam_spam",
                "doxxing",
            )
        ),
    ]

    # Self-harm is a support path, never an enforcement path. It is checked
    # first precisely so that no punitive branch can claim it.
    if result.noul("self_harm") > 0.55:
        trace.append("-> routed to wellbeing support, enforcement bypassed entirely")
        return Outcome("self_harm_support", "warning", trace)

    # Credible threats and doxxing carry real-world risk, so they escalate to a
    # human immediately rather than waiting for a severity score.
    if result.noul("violence_threat") > 0.7 or result.noul("doxxing") > 0.7:
        trace.append("-> real-world-harm signal, escalated to the trust & safety team")
        return Outcome("escalate_safety", "error", trace)

    # Quoting hate speech in order to condemn it is the classic false positive.
    # Code can encode that exception once, explicitly and reviewably.
    quoting = framing in ("condemning", "reporting", "educational")
    if quoting and severity < 2.6:
        trace.append(f"-> objectionable material is {framing}, not endorsed; allowed")
        return Outcome("allow_quoting", "success", trace)

    if severity >= 2.6:
        return Outcome("remove", "error", trace)
    if result.noul("scam_spam") > 0.75:
        trace.append("-> spam signal high, visibility limited pending review")
        return Outcome("shadow_limit", "warning", trace)
    if severity >= 1.7:
        return Outcome("remove", "error", trace)
    if severity >= 1.2:
        return Outcome("flag_review", "warning", trace)
    return Outcome("allow", "success", trace)


MODERATION_CASE = UseCase(
    id="moderation",
    icon=":material/shield:",
    title={"en": "Content moderation guardrail", "zh-TW": "內容審核防護欄"},
    category={"en": "Classify & route", "zh-TW": "分類與路由"},
    summary={
        "en": (
            "Nine parallel judgements on a single post, then a policy written in "
            "Python. The model never decides what the rules are — it only reports "
            "which signals are present and how strongly."
        ),
        "zh-TW": (
            "對單一則貼文同時做出九項判斷，再交由以 Python 撰寫的政策處理。"
            "模型從不決定規則是什麼 —— 它只回報哪些訊號存在、以及強度如何。"
        ),
    },
    why={
        "en": (
            "Moderation runs on every post, so a 10-second call is not an "
            "option, and at platform volume the per-item cost dominates "
            "everything.\n\n"
            "The more interesting reason is auditability. Policy thresholds "
            "belong in reviewed, diffable, testable code — not buried in a "
            "prompt. Separating *signal detection* from *policy* is what lets "
            "you encode exceptions explicitly: quoting hate speech to condemn "
            "it is allowed, and self-harm routes to support rather than "
            "enforcement. Try the `condemning` sample against the "
            "`endorsing` one to see it work."
        ),
        "zh-TW": (
            "審核會對每一則貼文執行，因此耗時 10 秒的呼叫根本不可行；"
            "而在平台級流量下，單筆成本會壓倒其他一切考量。\n\n"
            "更有意思的理由是「可稽核性」。政策門檻值應該存在於經過審查、可比對差異、"
            "可測試的程式碼中，而不是埋在 prompt 裡。將**訊號偵測**與**政策**分離，"
            "才能明確地寫下例外規則：引用仇恨言論以加以批評是允許的，"
            "而自傷風險會被導向支援資源、而非懲處流程。"
            "可以拿 `condemning`（批評引用）與 `endorsing`（表達認同）兩個範例對照看效果。"
        ),
    },
    questions=MODERATION_QUESTIONS,
    actions={
        "allow": {"en": "Published with no action", "zh-TW": "直接發布，未採取任何動作"},
        "allow_quoting": {
            "en": "Published — objectionable material was quoted, not endorsed",
            "zh-TW": "已發布 —— 可議內容屬引用批評，並非表達認同",
        },
        "flag_review": {
            "en": "Published but queued for human review",
            "zh-TW": "已發布，但排入人工審查佇列",
        },
        "shadow_limit": {
            "en": "Visibility limited pending review (suspected spam)",
            "zh-TW": "已限制曝光並待審查（疑似垃圾訊息）",
        },
        "remove": {"en": "Removed for violating policy", "zh-TW": "因違反政策而移除"},
        "escalate_safety": {
            "en": "Removed and escalated to trust & safety — real-world harm risk",
            "zh-TW": "已移除並升級至信任與安全團隊 —— 存在真實世界傷害風險",
        },
        "self_harm_support": {
            "en": "Kept visible; author shown crisis support resources, no enforcement",
            "zh-TW": "維持顯示；向作者提供危機支援資源，不進行懲處",
        },
    },
    decide=decide_moderation,
    samples=[
        Sample(
            id="benign",
            name={"en": "Benign post", "zh-TW": "正常貼文"},
            state={
                "post": {
                    "text": (
                        "Finally got the migration finished. Took three weekends "
                        "but the query times went from 4s to 200ms. Happy to "
                        "share the index definitions if anyone wants them."
                    ),
                    "author_account_age_days": 830,
                },
            },
            hint={
                "harassment": 0.01, "hate_speech": 0.01, "violence_threat": 0.01,
                "self_harm": 0.01, "sexual_content": 0.01, "scam_spam": 0.03,
                "doxxing": 0.01, "framing": "not_applicable", "severity": 0.0,
            },
        ),
        Sample(
            id="condemning",
            name={"en": "Quoting abuse to condemn it", "zh-TW": "引用惡意言論以加以批評"},
            state={
                "post": {
                    "text": (
                        "I need to show you what landed in my inbox this morning. "
                        "Someone wrote, and I quote, \"people like you should be "
                        "run out of this industry\". This is the third message "
                        "like it this week. Can we please talk about how normal "
                        "this has become in our community?"
                    ),
                    "author_account_age_days": 1450,
                },
            },
            hint={
                "harassment": 0.42, "hate_speech": 0.18, "violence_threat": 0.15,
                "self_harm": 0.02, "sexual_content": 0.01, "scam_spam": 0.01,
                "doxxing": 0.02, "framing": "condemning", "severity": 1.1,
            },
        ),
        Sample(
            id="targeted_harassment",
            name={"en": "Targeted harassment + doxxing", "zh-TW": "針對性騷擾與個資揭露"},
            state={
                "post": {
                    "text": (
                        "everyone should let this clown know exactly what we "
                        "think of him. he works at the office on 14 Maple Street "
                        "and his personal number is on his old resume, go find "
                        "it. make his life difficult."
                    ),
                    "author_account_age_days": 3,
                },
            },
            hint={
                "harassment": 0.95, "hate_speech": 0.12, "violence_threat": 0.48,
                "self_harm": 0.01, "sexual_content": 0.01, "scam_spam": 0.05,
                "doxxing": 0.91, "framing": "endorsing", "severity": 3.0,
            },
        ),
        Sample(
            id="self_harm",
            name={"en": "Author at risk", "zh-TW": "作者處於風險中"},
            state={
                "post": {
                    "text": (
                        "i don't really see the point in any of this anymore. "
                        "been lying awake all week thinking i'd rather just not "
                        "be here. sorry for posting this here, i don't know who "
                        "else to tell."
                    ),
                    "author_account_age_days": 210,
                },
            },
            hint={
                "harassment": 0.01, "hate_speech": 0.01, "violence_threat": 0.02,
                "self_harm": 0.93, "sexual_content": 0.01, "scam_spam": 0.01,
                "doxxing": 0.01, "framing": "not_applicable", "severity": 1.0,
            },
        ),
        Sample(
            id="scam",
            name={"en": "Crypto scam", "zh-TW": "加密貨幣詐騙"},
            state={
                "post": {
                    "text": (
                        "🚨 LAST CHANCE 🚨 I turned $500 into $48,000 in eleven "
                        "days with this bot. Not financial advice 😉 DM me the "
                        "word PROFIT and I'll send the private link, only taking "
                        "20 people today!!"
                    ),
                    "author_account_age_days": 2,
                    "identical_posts_last_hour": 34,
                },
            },
            hint={
                "harassment": 0.01, "hate_speech": 0.01, "violence_threat": 0.01,
                "self_harm": 0.01, "sexual_content": 0.02, "scam_spam": 0.96,
                "doxxing": 0.01, "framing": "endorsing", "severity": 2.2,
            },
        ),
    ],
)


# ==========================================================================
# 3. Inbound lead qualification
# ==========================================================================

LEAD_QUESTIONS = {
    "intent": Choice(
        instructions="What does the sender actually want?",
        label="Intent",
        criteria={
            "demo_request": "They want to see or trial the product.",
            "pricing_question": "They are asking about cost, plans, or quotes.",
            "existing_customer_support": "They are already a customer needing help.",
            "partnership": "They are proposing a partnership or integration.",
            "job_seeker": "They are looking for employment.",
            "vendor_pitch": "They are selling something to us.",
            "spam": "Bulk, automated, or irrelevant outreach.",
        },
    ),
    "company_size": Score(
        instructions="How large does the sender's organisation appear to be?",
        label="Company size",
        criteria=[
            "Individual or side project.",
            "Small team, under about 20 people.",
            "Mid-market, roughly 20 to 500 people.",
            "Enterprise, over about 500 people.",
        ],
    ),
    "timeline": Score(
        instructions="How urgent is the sender's stated timeline?",
        label="Timeline",
        criteria=[
            "No timeline; idle curiosity.",
            "Researching for the future.",
            "Evaluating actively this quarter.",
            "Urgent; needs to decide within weeks.",
        ],
    ),
    "fit": Score(
        instructions="How well does the described need match a data-workflow automation platform?",
        label="Product fit",
        criteria=[
            "No discernible fit.",
            "Weak or tangential fit.",
            "Plausible fit.",
            "Strong fit with a clear use case.",
            "Ideal fit; they describe our core use case precisely.",
        ],
    ),
    "has_budget_signal": Noul(
        instructions="The sender indicates budget exists or has been allocated.",
        label="Budget signal",
        true_criteria="They mention budget, procurement, an existing spend, or a contract.",
        false_criteria="No indication of money being available.",
    ),
    "is_decision_maker": Noul(
        instructions="The sender appears able to authorise a purchase themselves.",
        label="Authority",
        true_criteria="Their role or language implies purchasing authority.",
        false_criteria="They appear to be researching on someone else's behalf.",
    ),
    "competitor_mentioned": Noul(
        instructions="The sender mentions evaluating a competing product.",
        label="Competitive deal",
        true_criteria="A named alternative or an active bake-off is mentioned.",
        false_criteria="No competing product is referenced.",
    ),
}


def decide_lead_routing(result: DecisionResult, state: Any) -> Outcome:
    """Qualify an inbound lead and pick the cheapest adequate sales motion."""
    intent = result.choice("intent")
    confidence = result.confidence("intent")
    fit = result.score("fit")
    size = result.score("company_size")
    timeline = result.score("timeline")

    # A weighted composite beats asking "is this a good lead?", because the
    # weights stay visible and A/B-testable instead of hiding in a prompt.
    qualification = (
        0.40 * (fit / 4)
        + 0.25 * (size / 3)
        + 0.20 * (timeline / 3)
        + 0.15 * result.noul("has_budget_signal")
    )
    trace = [
        f"intent={intent!r} confidence={confidence:.2f}",
        f"fit={fit:.2f}/4 size={size:.2f}/3 timeline={timeline:.2f}/3",
        f"budget={result.noul('has_budget_signal'):.2f} "
        f"authority={result.noul('is_decision_maker'):.2f} "
        f"competitor={result.noul('competitor_mentioned'):.2f}",
        f"composite qualification score = {qualification:.3f}",
    ]
    metrics = {"Qualification score": f"{qualification:.2f} / 1.00"}

    if intent == "spam" and confidence > 0.8:
        return Outcome("discard", "info", trace, metrics)
    if intent == "existing_customer_support":
        trace.append("-> misrouted into the sales inbox, handed to support")
        return Outcome("to_support", "info", trace, metrics)
    if intent in ("job_seeker", "vendor_pitch"):
        return Outcome("auto_reply", "info", trace, metrics)
    if confidence < 0.5:
        return Outcome("sdr_review", "warning", trace, metrics)

    # Competitive enterprise deals are the ones worth interrupting a human for.
    if qualification >= 0.7 and result.noul("competitor_mentioned") > 0.6:
        trace.append("-> qualified and competitive, routed for immediate contact")
        return Outcome("ae_immediate", "error", trace, metrics)
    if qualification >= 0.65 and result.noul("is_decision_maker") > 0.5:
        return Outcome("ae_standard", "success", trace, metrics)
    if qualification >= 0.4:
        return Outcome("sdr_review", "info", trace, metrics)
    if intent in ("pricing_question", "demo_request"):
        trace.append("-> real interest but below the human-touch bar")
        return Outcome("self_serve", "info", trace, metrics)
    return Outcome("nurture", "info", trace, metrics)


LEAD_CASE = UseCase(
    id="lead_routing",
    icon=":material/filter_alt:",
    title={"en": "Inbound lead qualification", "zh-TW": "潛在客戶資格評估"},
    category={"en": "Classify & route", "zh-TW": "分類與路由"},
    summary={
        "en": (
            "Seven signals about an inbound email become one weighted "
            "qualification score, and the score picks the cheapest sales motion "
            "that is good enough."
        ),
        "zh-TW": (
            "將關於一封新進來信的七項訊號轉換為單一加權資格分數，"
            "再由該分數挑選出「足夠好且最省成本」的業務動作。"
        ),
    },
    why={
        "en": (
            "This is the composite-scoring pattern. Rather than asking \"how "
            "good is this lead\" — which hides four judgements inside one "
            "answer — each dimension is scored atomically and combined with "
            "weights the business controls.\n\n"
            "Re-weighting is then a code change you can A/B test, not a prompt "
            "rewrite you have to re-evaluate from scratch."
        ),
        "zh-TW": (
            "這是「複合評分」模式。與其直接問「這個潛在客戶有多好」—— 那會把四個判斷"
            "藏在同一個答案裡 —— 不如把每個維度各自獨立評分，再用業務方可控的權重加以組合。\n\n"
            "如此一來，調整權重就只是一次可做 A/B 測試的程式碼修改，"
            "而不是一次必須從頭重新評估的 prompt 重寫。"
        ),
    },
    questions=LEAD_QUESTIONS,
    actions={
        "ae_immediate": {
            "en": "Routed to an account executive for same-day contact (competitive deal)",
            "zh-TW": "已指派客戶經理當日聯繫（競爭性案件）",
        },
        "ae_standard": {
            "en": "Assigned to an account executive in the normal queue",
            "zh-TW": "已依一般流程指派客戶經理",
        },
        "sdr_review": {
            "en": "Sent to an SDR to qualify manually",
            "zh-TW": "交由業務開發代表（SDR）人工評估",
        },
        "self_serve": {
            "en": "Sent self-serve onboarding and pricing links",
            "zh-TW": "已寄送自助導入與定價連結",
        },
        "nurture": {"en": "Added to the nurture sequence", "zh-TW": "已加入長期培養名單"},
        "to_support": {"en": "Handed to the support team", "zh-TW": "已轉交客服團隊"},
        "auto_reply": {
            "en": "Sent a polite templated reply, no human time spent",
            "zh-TW": "已寄送制式禮貌回覆，未占用人工時間",
        },
        "discard": {"en": "Discarded as spam", "zh-TW": "視為垃圾訊息並丟棄"},
    },
    decide=decide_lead_routing,
    samples=[
        Sample(
            id="enterprise_competitive",
            name={"en": "Enterprise, competitive bake-off", "zh-TW": "大型企業競標評選"},
            state={
                "email": {
                    "from": "priya.raman@northwind-logistics.com",
                    "subject": "Evaluating workflow automation for Q4 rollout",
                    "body": (
                        "Hello — I lead platform engineering at Northwind "
                        "Logistics (about 2,400 staff). We process roughly 40 "
                        "million shipment events a month and currently hand-roll "
                        "the classification rules, which has become "
                        "unmaintainable. I have sign-off on a six-figure budget "
                        "for this fiscal year and need a decision by the end of "
                        "October. We are also trialling Acme Flow — could you "
                        "share how you differ on throughput and cost per event?"
                    ),
                },
            },
            hint={
                "intent": "demo_request", "company_size": 3.0, "timeline": 3.0,
                "fit": 4.0, "has_budget_signal": 0.95,
                "is_decision_maker": 0.9, "competitor_mentioned": 0.97,
            },
        ),
        Sample(
            id="hobbyist",
            name={"en": "Curious hobbyist", "zh-TW": "純粹好奇的個人開發者"},
            state={
                "email": {
                    "from": "dmitri.codes@gmail.com",
                    "subject": "pricing?",
                    "body": (
                        "hey, cool product. i'm building a side project that "
                        "sorts my podcast backlog. is there a free tier? no "
                        "real budget, just tinkering on weekends."
                    ),
                },
            },
            hint={
                "intent": "pricing_question", "company_size": 0.0, "timeline": 0.3,
                "fit": 1.4, "has_budget_signal": 0.03,
                "is_decision_maker": 0.55, "competitor_mentioned": 0.02,
            },
        ),
        Sample(
            id="misrouted_support",
            name={"en": "Existing customer, wrong inbox", "zh-TW": "現有客戶寄錯信箱"},
            state={
                "email": {
                    "from": "ops@brightline.io",
                    "subject": "API returning 403 since this morning",
                    "body": (
                        "We're on the Growth plan (account BL-7741) and all our "
                        "API calls started returning 403 around 06:00. Nothing "
                        "changed on our side. I couldn't find the support address "
                        "so I'm writing here — please advise urgently."
                    ),
                },
            },
            hint={
                "intent": "existing_customer_support", "company_size": 2.0,
                "timeline": 3.0, "fit": 2.0, "has_budget_signal": 0.4,
                "is_decision_maker": 0.3, "competitor_mentioned": 0.01,
            },
        ),
        Sample(
            id="vendor_spam",
            name={"en": "Outbound vendor pitch", "zh-TW": "供應商推銷信"},
            state={
                "email": {
                    "from": "growth@leadgenrocket.biz",
                    "subject": "Quick question re: your outbound",
                    "body": (
                        "Hi there! Noticed you're hiring — I help B2B SaaS teams "
                        "3x their pipeline with our AI SDR platform. Worth a "
                        "quick 15 min? Happy to send over a Loom. Cheers!"
                    ),
                },
            },
            hint={
                "intent": "vendor_pitch", "company_size": 1.0, "timeline": 1.0,
                "fit": 0.2, "has_budget_signal": 0.05,
                "is_decision_maker": 0.6, "competitor_mentioned": 0.05,
            },
        ),
    ],
)


# ==========================================================================
# 4. On-call alert triage
# ==========================================================================

ALERT_QUESTIONS = {
    "category": Choice(
        instructions="What is the most likely underlying cause of this alert?",
        label="Likely cause",
        criteria={
            "deploy_regression": "A recent deployment introduced the problem.",
            "dependency_outage": "An upstream or third-party service is failing.",
            "capacity": "Resource exhaustion: CPU, memory, disk, or connections.",
            "data_quality": "Malformed or unexpected input data is causing failures.",
            "infrastructure": "Host, network, or cloud-provider level failure.",
            "flaky_monitor": "The monitor itself is unreliable; the service is fine.",
        },
    ),
    "severity": Score(
        instructions="How much user-visible impact is this having right now?",
        label="User impact",
        criteria=[
            "None; purely internal signal.",
            "Degraded performance that users may not notice.",
            "Clearly user-visible errors affecting some traffic.",
            "Full outage of a critical path.",
        ],
    ),
    "is_actionable": Noul(
        instructions="There is a concrete action a responder could take right now.",
        label="Actionable",
        true_criteria="A specific remediation is implied by the evidence.",
        false_criteria="Nothing to do; informational or already self-recovering.",
    ),
    "deploy_correlated": Noul(
        instructions="The onset of the problem lines up with a recent deployment.",
        label="Deploy correlated",
        true_criteria="The timeline places a deploy immediately before the onset.",
        false_criteria="No deployment near the onset time.",
    ),
    "self_recovering": Noul(
        instructions="The metrics suggest the system is already recovering on its own.",
        label="Self-recovering",
        true_criteria="Error rates are trending back toward normal without intervention.",
        false_criteria="The problem is steady or worsening.",
    ),
    "runbook_covers": Noul(
        instructions="The attached runbook covers this exact failure mode.",
        label="Runbook applies",
        true_criteria="The runbook describes this symptom and a remediation for it.",
        false_criteria="The runbook does not address this situation.",
    ),
}


def decide_alert_triage(result: DecisionResult, state: Any) -> Outcome:
    """Decide whether to wake a human at 3am. Bias hard against false pages."""
    category = result.choice("category")
    severity = result.score("severity")
    trace = [
        f"category={category!r} confidence={result.confidence('category'):.2f}",
        f"severity={severity:.2f}/3 actionable={result.noul('is_actionable'):.2f}",
        f"deploy_correlated={result.noul('deploy_correlated'):.2f} "
        f"self_recovering={result.noul('self_recovering'):.2f} "
        f"runbook_covers={result.noul('runbook_covers'):.2f}",
    ]

    if category == "flaky_monitor" and result.confidence("category") > 0.7:
        trace.append("-> monitor is the problem, not the service")
        return Outcome("suppress_and_file", "info", trace)
    if result.noul("is_actionable") < 0.35:
        trace.append("-> nothing actionable, so paging would only cost sleep")
        return Outcome("suppress", "info", trace)
    if result.noul("self_recovering") > 0.7 and severity < 2.0:
        trace.append("-> recovering on its own and impact is limited")
        return Outcome("watch", "info", trace)

    # An automated rollback is a big hammer, so it needs several signals to
    # agree before it fires unattended.
    if (
        category == "deploy_regression"
        and result.noul("deploy_correlated") > 0.8
        and severity >= 2.0
        and result.confidence("category") > 0.75
    ):
        trace.append("-> deploy correlation strong and impact high, rolling back")
        return Outcome("auto_rollback", "error", trace)

    if severity >= 2.5:
        return Outcome("page_now", "error", trace)
    if severity >= 1.5:
        if result.noul("runbook_covers") > 0.7:
            trace.append("-> runbook applies, so automation can attempt it first")
            return Outcome("auto_runbook", "warning", trace)
        return Outcome("page_now", "warning", trace)
    return Outcome("ticket", "info", trace)


ALERT_CASE = UseCase(
    id="alert_triage",
    icon=":material/notifications_active:",
    title={"en": "On-call alert triage", "zh-TW": "值班告警分流"},
    category={"en": "Classify & route", "zh-TW": "分類與路由"},
    summary={
        "en": (
            "Read an alert plus recent deploys and metrics, then decide whether "
            "it justifies waking someone — or whether automation can handle it."
        ),
        "zh-TW": (
            "讀取告警內容以及近期部署與指標，判斷它是否值得叫醒某個人 ——"
            "或者自動化流程是否足以處理。"
        ),
    },
    why={
        "en": (
            "Alert fatigue is a judgement problem wearing a threshold costume. "
            "Static rules cannot weigh \"error rate doubled\" against \"but a "
            "deploy landed 90 seconds earlier and it is already recovering\", so "
            "teams end up paging on everything and trusting nothing.\n\n"
            "Notice how much the code refuses to do. Suppression is checked "
            "before escalation, and the automated rollback demands four "
            "independent signals — including the model's own confidence — before "
            "it fires unattended. The expensive, irreversible action gets the "
            "highest bar."
        ),
        "zh-TW": (
            "告警疲勞其實是一個披著「門檻值」外衣的判斷問題。靜態規則無法權衡"
            "「錯誤率翻倍」與「但 90 秒前剛部署、而且已經在自行恢復」這兩件事，"
            "於是團隊最後對所有事情都發出呼叫，卻對任何告警都不再信任。\n\n"
            "請注意程式碼「拒絕做」的事情有多少：抑制判斷排在升級之前，"
            "而自動回滾需要四個獨立訊號同時成立 —— 其中包含模型自身的信賴度 ——"
            "才會在無人監督下執行。代價最高、最難復原的動作，門檻也設得最高。"
        ),
    },
    questions=ALERT_QUESTIONS,
    actions={
        "page_now": {"en": "Paged the on-call engineer", "zh-TW": "已呼叫值班工程師"},
        "auto_rollback": {
            "en": "Triggered an automatic rollback of the suspect deploy",
            "zh-TW": "已自動回滾可疑的部署版本",
        },
        "auto_runbook": {
            "en": "Ran the documented runbook automatically, notified the channel",
            "zh-TW": "已自動執行既有 runbook，並通知頻道",
        },
        "watch": {
            "en": "Held under observation — recovering without intervention",
            "zh-TW": "持續觀察中 —— 系統正在自行恢復",
        },
        "ticket": {"en": "Filed a low-priority ticket", "zh-TW": "已建立低優先度工單"},
        "suppress": {
            "en": "Suppressed — nothing actionable to do",
            "zh-TW": "已抑制 —— 無可執行的處理動作",
        },
        "suppress_and_file": {
            "en": "Suppressed and filed a task to fix the monitor itself",
            "zh-TW": "已抑制，並建立修復該監控項目的任務",
        },
    },
    decide=decide_alert_triage,
    samples=[
        Sample(
            id="deploy_regression",
            name={"en": "Deploy regression, clear outage", "zh-TW": "部署造成的明確服務中斷"},
            state={
                "alert": {
                    "name": "checkout_5xx_rate_high",
                    "fired_at": "2026-09-21T02:14:33Z",
                    "message": "5xx rate on POST /checkout is 31% (threshold 2%)",
                },
                "metrics": {
                    "error_rate_before": 0.004,
                    "error_rate_now": 0.31,
                    "trend_last_5min": "flat at elevated level",
                    "affected_requests_per_min": 4200,
                },
                "recent_deploys": [
                    {
                        "service": "checkout-api",
                        "version": "v2026.9.21-a4f",
                        "deployed_at": "2026-09-21T02:13:02Z",
                        "changes": "refactor payment intent creation",
                    }
                ],
                "runbook": (
                    "checkout_5xx_rate_high: verify recent deploys first. If a "
                    "deploy landed within 5 minutes of onset, roll back before "
                    "further investigation."
                ),
            },
            hint={
                "category": "deploy_regression", "severity": 3.0,
                "is_actionable": 0.96, "deploy_correlated": 0.97,
                "self_recovering": 0.04, "runbook_covers": 0.93,
            },
        ),
        Sample(
            id="flaky_monitor",
            name={"en": "Flapping monitor", "zh-TW": "抖動的監控項目"},
            state={
                "alert": {
                    "name": "disk_usage_warning_worker_17",
                    "fired_at": "2026-09-21T02:20:11Z",
                    "message": "Disk usage 81% (threshold 80%)",
                },
                "metrics": {
                    "times_fired_last_24h": 47,
                    "times_resolved_within_60s": 46,
                    "current_usage": 0.81,
                    "trend_last_5min": "oscillating between 79% and 82%",
                },
                "recent_deploys": [],
                "runbook": (
                    "disk_usage_warning: worker nodes rotate large temp files "
                    "during batch windows; brief spikes above 80% are expected."
                ),
            },
            hint={
                "category": "flaky_monitor", "severity": 0.2,
                "is_actionable": 0.12, "deploy_correlated": 0.02,
                "self_recovering": 0.92, "runbook_covers": 0.81,
            },
        ),
        Sample(
            id="dependency",
            name={"en": "Third-party degradation", "zh-TW": "第三方服務降級"},
            state={
                "alert": {
                    "name": "email_delivery_latency_high",
                    "fired_at": "2026-09-21T02:31:00Z",
                    "message": "p95 send latency 45s (threshold 10s)",
                },
                "metrics": {
                    "queue_depth": 18400,
                    "queue_depth_trend": "growing 300/min",
                    "our_error_rate": 0.001,
                    "upstream_provider_status": "degraded per provider status page",
                },
                "recent_deploys": [],
                "runbook": (
                    "email_delivery_latency_high: if the provider reports "
                    "degradation, no local action helps. Messages queue durably "
                    "and drain automatically."
                ),
            },
            hint={
                "category": "dependency_outage", "severity": 1.6,
                "is_actionable": 0.38, "deploy_correlated": 0.02,
                "self_recovering": 0.35, "runbook_covers": 0.88,
            },
        ),
    ],
)


CASES = [SUPPORT_CASE, MODERATION_CASE, LEAD_CASE, ALERT_CASE]
