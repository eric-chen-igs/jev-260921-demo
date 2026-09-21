"""Demo use case 10: decompose a fuzzy judgement into weighted dimensions.

The pattern TypeSafe call composite scoring. Asking "how good is this
candidate?" hides four separate judgements inside one answer and gives you no
way to adjust their relative importance afterwards. Scoring each dimension
atomically and combining them in code makes the weights visible, testable, and
A/B-able.
"""

from __future__ import annotations

from typing import Any

from ..schema import DecisionResult, Noul, Score
from .base import Outcome, Sample, UseCase

RESUME_QUESTIONS = {
    "python_depth": Score(
        instructions="Depth of Python experience evidenced in this CV.",
        label="Python depth",
        criteria=[
            "Not mentioned at all.",
            "Mentioned, with no supporting detail.",
            "Used in real projects.",
            "Described as a primary working language.",
            "Deep expertise: performance work, architecture, or library authorship.",
        ],
    ),
    "system_design": Score(
        instructions="Evidence of designing distributed or large-scale systems.",
        label="System design",
        criteria=[
            "No evidence.",
            "Contributed to design discussions.",
            "Designed individual components.",
            "Owned the architecture of a whole system.",
            "Designed at scale across multiple domains or organisations.",
        ],
    ),
    "data_pipeline_experience": Score(
        instructions="Experience building data or streaming pipelines.",
        label="Data pipelines",
        criteria=[
            "None evident.",
            "Incidental exposure.",
            "Built batch pipelines.",
            "Built and operated streaming pipelines in production.",
            "Owned high-throughput pipelines at scale, including their reliability.",
        ],
    ),
    "team_leadership": Score(
        instructions="Experience leading or mentoring engineers.",
        label="Leadership",
        criteria=[
            "None evident.",
            "Informal mentorship.",
            "Led a small project team.",
            "Managed direct reports.",
            "Managed multiple teams or managers.",
        ],
    ),
    "communication": Score(
        instructions="How clearly is the CV itself written and organised?",
        label="Written communication",
        criteria=[
            "Hard to follow; vague or disorganised.",
            "Adequate but generic.",
            "Clear, specific, and quantified.",
        ],
    ),
    "meets_hard_requirement": Noul(
        instructions=(
            "The CV shows at least five years of professional backend software "
            "engineering experience, which is a stated hard requirement for this role."
        ),
        label="Meets hard requirement (5y backend)",
        true_criteria="Dated roles in the CV add up to five or more years of backend work.",
        false_criteria="The evidenced backend experience falls short of five years.",
    ),
    "production_ownership": Noul(
        instructions="The candidate has carried production responsibility, such as on-call or incident ownership.",
        label="Production ownership",
        true_criteria="On-call rotations, incident response, or SLA ownership are described.",
        false_criteria="No evidence of operating what they built.",
    ),
}

# Weights live here, in code, where they can be reviewed and changed
# deliberately. Adjusting the hiring bar is a diff, not a prompt rewrite.
WEIGHTS = {
    "python_depth": 0.25,
    "system_design": 0.25,
    "data_pipeline_experience": 0.20,
    "team_leadership": 0.10,
    "communication": 0.10,
    "production_ownership": 0.10,
}


def decide_resume_screen(result: DecisionResult, state: Any) -> Outcome:
    """Score a CV on six dimensions and combine them with explicit weights.

    One rule is deliberately absent: there is no automated rejection. The model
    can move a CV up the queue, but only a person can end a candidacy. That is a
    policy choice, and putting it in code is what makes it auditable.
    """
    normalised = {
        "python_depth": result.score("python_depth") / 4,
        "system_design": result.score("system_design") / 4,
        "data_pipeline_experience": result.score("data_pipeline_experience") / 4,
        "team_leadership": result.score("team_leadership") / 4,
        "communication": result.score("communication") / 2,
        "production_ownership": result.noul("production_ownership"),
    }
    composite = sum(WEIGHTS[key] * value for key, value in normalised.items())

    trace = [
        f"{key:<26} {value:.2f} x weight {WEIGHTS[key]:.2f} "
        f"= {WEIGHTS[key] * value:.3f}"
        for key, value in normalised.items()
    ]
    trace.append(f"{'composite':<26} {composite:.3f} / 1.000")
    trace.append(
        f"meets_hard_requirement={result.noul('meets_hard_requirement'):.2f}"
    )

    metrics = {
        "Composite score": f"{composite:.2f} / 1.00",
        "Strongest dimension": max(normalised, key=lambda k: normalised[k]),
    }

    # The hard requirement is a stated filter, but a model reading dates off a
    # CV is exactly the arithmetic-on-text task TypeSafe warn is unreliable. So
    # a shortfall routes to a human check rather than acting on its own.
    if result.noul("meets_hard_requirement") < 0.5:
        trace.append(
            "-> hard requirement looks unmet, but date arithmetic is a known "
            "weak spot, so a human verifies rather than the pipeline rejecting"
        )
        return Outcome("verify_requirement", "warning", trace, metrics)

    if composite >= 0.75:
        return Outcome("fast_track", "success", trace, metrics)
    if composite >= 0.55:
        return Outcome("phone_screen", "success", trace, metrics)
    if composite >= 0.35:
        return Outcome("recruiter_review", "info", trace, metrics)
    trace.append("-> low score, placed last in the human review queue, never auto-rejected")
    return Outcome("human_queue", "info", trace, metrics)


RESUME_CASE = UseCase(
    id="resume_scoring",
    icon=":material/scoreboard:",
    title={"en": "CV screening by composite score", "zh-TW": "以複合分數篩選履歷"},
    category={"en": "Score at scale", "zh-TW": "大規模評分"},
    summary={
        "en": (
            "Six dimensions scored independently, then combined with weights "
            "that live in code. No automated rejection: the model can raise a CV "
            "up the queue, but only a person can end a candidacy."
        ),
        "zh-TW": (
            "六個維度各自獨立評分，再以存在於程式碼中的權重加以組合。"
            "不進行自動拒絕：模型可以把履歷往前排，但只有人才能終止一位候選人的申請。"
        ),
    },
    why={
        "en": (
            "Decomposition is the whole technique. \"Rate this candidate 1-10\" "
            "buries several unrelated judgements in one number and leaves you no "
            "lever to adjust them. Six atomic scores plus a weight vector gives "
            "you a lever per dimension, and re-weighting becomes a diff you can "
            "A/B test rather than a prompt you have to re-evaluate from scratch.\n\n"
            "Two constraints in the code deserve attention, because screening "
            "affects people's livelihoods.\n\n"
            "First, **no automated rejection.** Every path ends in a human "
            "queue; the score only changes the order. Encoding that in code "
            "rather than trusting a threshold is what makes it auditable.\n\n"
            "Second, the **hard requirement is not trusted to the model.** "
            "Counting years from dated roles is arithmetic on text, which "
            "TypeSafe explicitly list as unreliable. So a shortfall routes to a "
            "human check instead of acting on its own — the right shape for any "
            "question where the model's known weakness meets a consequential "
            "outcome."
        ),
        "zh-TW": (
            "「拆解」就是這個技巧的全部。「給這位候選人打 1 到 10 分」會把數個互不相關的判斷"
            "埋進同一個數字，讓你完全沒有調整的槓桿。六個原子化分數搭配一組權重向量，"
            "則讓你對每個維度都有一根槓桿；調整權重因此變成一次可做 A/B 測試的程式碼差異，"
            "而不是一段必須從頭重新評估的 prompt。\n\n"
            "程式碼中有兩個限制值得注意，因為履歷篩選會影響他人的生計。\n\n"
            "第一，**不進行自動拒絕。** 所有路徑最終都會進入人工佇列；分數只影響排序。"
            "把這件事寫進程式碼、而不是信賴某個門檻值，正是它能被稽核的原因。\n\n"
            "第二，**硬性條件不交給模型判斷。** 從帶日期的工作經歷推算年資屬於"
            "「對文字做算術」，而 TypeSafe 明確將此列為不可靠項目。因此當條件看似未達成時，"
            "流程會交由人工確認、而非自行處置 ——"
            "任何「模型已知弱項」與「後果重大的結果」交會之處，都該採用這種形狀的設計。"
        ),
    },
    questions=RESUME_QUESTIONS,
    actions={
        "fast_track": {
            "en": "Fast-tracked straight to a hiring-manager interview",
            "zh-TW": "已快速通關，直接安排與招募主管面談",
        },
        "phone_screen": {
            "en": "Advanced to a phone screen",
            "zh-TW": "已進入電話初談階段",
        },
        "recruiter_review": {
            "en": "Placed in the standard recruiter review queue",
            "zh-TW": "已排入標準招募人員審閱佇列",
        },
        "human_queue": {
            "en": "Placed last in the human review queue — never auto-rejected",
            "zh-TW": "排在人工審閱佇列末位 —— 絕不自動拒絕",
        },
        "verify_requirement": {
            "en": "Flagged for a human to verify the years-of-experience requirement",
            "zh-TW": "已標記，待人工確認年資條件",
        },
    },
    decide=decide_resume_screen,
    samples=[
        Sample(
            id="strong",
            name={"en": "Strong senior backend CV", "zh-TW": "資深後端的優秀履歷"},
            state={
                "role": "Senior Backend Engineer — Data Platform (5+ years required)",
                "cv": (
                    "Amara Osei — Senior Software Engineer\n\n"
                    "Helio Data (2021-2026, 5 yrs) — Tech lead for the ingestion "
                    "platform. Designed and owned a Kafka-based streaming "
                    "pipeline processing 1.2M events/sec at p99 of 40ms. Cut "
                    "infrastructure spend 38% by rewriting the partitioner in "
                    "Python with a C extension. Ran the on-call rotation for the "
                    "platform and led incident response for two Sev-1 outages. "
                    "Mentored four engineers, two of whom were promoted.\n\n"
                    "Corvid Analytics (2018-2021, 3 yrs) — Built batch ETL in "
                    "Python and Airflow across 40+ sources. Authored an "
                    "internal schema-migration library now used by six teams.\n\n"
                    "Skills: Python (primary, 8 yrs), Go, Kafka, Postgres, "
                    "Kubernetes, Terraform.\n"
                    "Talks: 'Backpressure Without Tears', PyCon 2024."
                ),
            },
            hint={
                "python_depth": 4.0, "system_design": 3.6,
                "data_pipeline_experience": 4.0, "team_leadership": 2.4,
                "communication": 2.0, "meets_hard_requirement": 0.97,
                "production_ownership": 0.96,
            },
        ),
        Sample(
            id="junior",
            name={"en": "Promising but junior", "zh-TW": "有潛力但資歷較淺"},
            state={
                "role": "Senior Backend Engineer — Data Platform (5+ years required)",
                "cv": (
                    "Tom Brennan — Software Engineer\n\n"
                    "Lumen Retail (2024-2026, 2 yrs) — Backend engineer on the "
                    "orders team. Wrote Python services with FastAPI, added "
                    "Redis caching that improved response times. Participated in "
                    "design reviews for a new pricing service.\n\n"
                    "Internship, Vellum Tech (2023, 6 months) — Built an "
                    "internal dashboard in React.\n\n"
                    "BSc Computer Science, 2023.\n"
                    "Skills: Python, FastAPI, Postgres, some Docker. Keen to "
                    "learn distributed systems."
                ),
            },
            hint={
                "python_depth": 2.2, "system_design": 1.0,
                "data_pipeline_experience": 0.8, "team_leadership": 0.2,
                "communication": 1.6, "meets_hard_requirement": 0.04,
                "production_ownership": 0.18,
            },
        ),
        Sample(
            id="vague",
            name={"en": "Buzzword-heavy, low signal", "zh-TW": "術語堆砌、資訊量低"},
            state={
                "role": "Senior Backend Engineer — Data Platform (5+ years required)",
                "cv": (
                    "Dynamic, results-oriented technology professional with "
                    "extensive experience leveraging cutting-edge solutions to "
                    "drive synergistic outcomes across the full stack. Proven "
                    "track record of thought leadership in cloud, AI, big data, "
                    "blockchain, and agile transformation. Passionate about "
                    "scalable enterprise architecture and stakeholder alignment.\n\n"
                    "Various roles, 2015-present. References available on request.\n"
                    "Skills: Python, Java, C++, Go, Rust, SQL, NoSQL, AWS, GCP, "
                    "Azure, Kubernetes, Docker, Kafka, Spark, TensorFlow."
                ),
            },
            hint={
                "python_depth": 1.0, "system_design": 0.9,
                "data_pipeline_experience": 0.8, "team_leadership": 1.0,
                "communication": 0.3, "meets_hard_requirement": 0.44,
                "production_ownership": 0.15,
            },
        ),
    ],
)


CASES = [RESUME_CASE]
