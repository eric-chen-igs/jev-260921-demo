"""Bilingual UI strings (English / Traditional Chinese).

Short labels and long-form markdown sections both live here. Use-case specific
copy is co-located with the case definitions in `usecases.py` instead.

Note on scope: only narrative and UI text is translated. The `instructions` and
`criteria` sent to the model stay in English in every language so that switching
the interface language never silently changes the decision being measured.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LANG = "en"

LANGUAGES: dict[str, str] = {
    "en": "English",
    "zh-TW": "繁體中文",
}

STRINGS: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------------- app
    "app.title": {
        "en": "Jev vs LLM",
        "zh-TW": "Jev vs LLM",
    },
    "app.subtitle": {
        "en": "A hands-on comparison of TypeSafe's System One model against general-purpose LLMs.",
        "zh-TW": "以實作方式比較 TypeSafe 的 System One 模型與通用大型語言模型（LLM）。",
    },
    "nav.section_learn": {"en": "Learn", "zh-TW": "了解"},
    "nav.section_try": {"en": "Try it", "zh-TW": "實際試用"},
    "nav.overview": {"en": "What is Jev?", "zh-TW": "什麼是 Jev？"},
    "nav.compare": {"en": "Jev vs LLM", "zh-TW": "Jev 與 LLM 對比"},
    "nav.usecases": {"en": "10 Demo Use Cases", "zh-TW": "10 個示範應用"},
    "nav.playground": {"en": "Playground", "zh-TW": "自由實驗場"},
    "nav.economics": {"en": "Cost & Latency Model", "zh-TW": "成本與延遲估算"},
    # ------------------------------------------------------------ sidebar
    "sidebar.settings": {"en": "Settings", "zh-TW": "設定"},
    "sidebar.api": {"en": "API", "zh-TW": "API"},
    "sidebar.api_key": {"en": "OpenRouter API key", "zh-TW": "OpenRouter API 金鑰"},
    "sidebar.api_key_help": {
        "en": "Kept in this browser session only. Never written to disk by this app.",
        "zh-TW": "僅保存在目前的瀏覽器工作階段中，本應用不會寫入磁碟。",
    },
    "sidebar.api_key_ok": {"en": "Live mode: calls go to the real API.", "zh-TW": "即時模式：將呼叫真實 API。"},
    "sidebar.api_key_missing": {
        "en": "No key set — running in simulated mode.",
        "zh-TW": "尚未設定金鑰 — 目前為模擬模式。",
    },
    "sidebar.get_key": {"en": "Get an OpenRouter key", "zh-TW": "取得 OpenRouter 金鑰"},
    "sidebar.transport": {"en": "Jev transport", "zh-TW": "Jev 傳輸方式"},
    "sidebar.transport_help": {
        "en": "OpenRouter exposes Jev at /api/alpha/decisions. TypeSafe's own API uses /v1/systemone and needs a TypeSafe key instead.",
        "zh-TW": "OpenRouter 透過 /api/alpha/decisions 提供 Jev；TypeSafe 官方 API 則使用 /v1/systemone，需改用 TypeSafe 金鑰。",
    },
    "sidebar.jev_model": {"en": "Jev model", "zh-TW": "Jev 模型"},
    "sidebar.jev_model_help": {
        "en": "jev-latest tracks the newest release. Pin a version if you have tuned thresholds against it.",
        "zh-TW": "jev-latest 會跟隨最新版本；若你已針對特定版本調校門檻值，建議鎖定版本。",
    },
    "sidebar.llm_model": {"en": "Comparison LLM", "zh-TW": "對比用 LLM"},
    "sidebar.llm_model_help": {
        "en": "The LLM is given the identical questions as a strict JSON Schema, so the comparison is not rigged against it.",
        "zh-TW": "LLM 會收到完全相同的問題，並以嚴格 JSON Schema 約束輸出，以確保比較公平。",
    },
    "sidebar.enable_llm": {"en": "Run the LLM side by side", "zh-TW": "同時執行 LLM 對比"},
    "sidebar.enable_llm_help": {
        "en": "Turn this off to exercise Jev alone. LLM calls are far slower and cost real money.",
        "zh-TW": "關閉後只會執行 Jev。LLM 呼叫明顯較慢，且會產生實際費用。",
    },
    "sidebar.language": {"en": "Language", "zh-TW": "語言"},
    "sidebar.appearance": {"en": "Appearance", "zh-TW": "外觀"},
    "sidebar.theme_light": {"en": "Light", "zh-TW": "淺色"},
    "sidebar.theme_dark": {"en": "Dark", "zh-TW": "深色"},
    "sidebar.theme_unsupported": {
        "en": (
            "This Streamlit build does not allow switching the theme from the "
            "app. Use the toolbar menu (top right) → Settings → Appearance."
        ),
        "zh-TW": (
            "此 Streamlit 版本不允許由應用程式內切換主題。"
            "請改用右上角工具列選單 → Settings → Appearance。"
        ),
    },
    "sidebar.region": {"en": "Region", "zh-TW": "地區"},
    "sidebar.show_restricted": {
        "en": "Show models not offered in Hong Kong",
        "zh-TW": "顯示未在香港提供服務的模型",
    },
    "sidebar.show_restricted_help": {
        "en": (
            "Off by default: OpenAI and Anthropic do not list Hong Kong as a "
            "supported territory. Calls still go through OpenRouter rather than "
            "direct, so whether that is acceptable is your compliance call."
        ),
        "zh-TW": (
            "預設關閉：OpenAI 與 Anthropic 均未將香港列為支援地區。"
            "由於呼叫是透過 OpenRouter 而非直接連線，是否可接受屬於你自身的法遵判斷。"
        ),
    },
    "sidebar.hk_filtered": {
        "en": "Showing models available in Hong Kong.",
        "zh-TW": "僅顯示在香港可用的模型。",
    },
    "sidebar.restricted_selected": {
        "en": "This model's vendor does not list Hong Kong as supported.",
        "zh-TW": "此模型的供應商並未將香港列為支援地區。",
    },
    "sidebar.advanced": {"en": "Advanced", "zh-TW": "進階設定"},
    "sidebar.timeout": {"en": "Request timeout (s)", "zh-TW": "請求逾時（秒）"},
    "sidebar.reasoning": {"en": "LLM reasoning effort", "zh-TW": "LLM 推理強度"},
    "sidebar.reasoning_help": {
        "en": "Higher effort usually raises LLM accuracy and sharply raises its latency and cost.",
        "zh-TW": "推理強度越高，LLM 正確率通常越好，但延遲與成本也會大幅上升。",
    },
    "sidebar.temperature": {"en": "LLM temperature", "zh-TW": "LLM temperature"},
    "sidebar.simulated_mode": {"en": "Simulated mode", "zh-TW": "模擬模式"},
    "sidebar.simulated_explain": {
        "en": (
            "Without a key the Jev column is produced locally by a lexical heuristic "
            "so you can still explore the interface. It is **not** Jev, and the LLM "
            "column is unavailable because there is nothing meaningful to fake about "
            "its latency or token bill."
        ),
        "zh-TW": (
            "未設定金鑰時，Jev 欄位由本機的詞彙啟發式規則產生，讓你仍能瀏覽介面。"
            "它**並非** Jev；LLM 欄位則無法使用，因為其延遲與 token 費用無從模擬。"
        ),
    },
    "sidebar.resources": {"en": "Resources", "zh-TW": "參考資源"},
    # ------------------------------------------------------------- common
    "common.run": {"en": "Run decision", "zh-TW": "執行決策"},
    "common.run_again": {"en": "Run again", "zh-TW": "重新執行"},
    "common.running": {"en": "Deciding…", "zh-TW": "正在決策…"},
    "common.jev": {"en": "Jev (System One)", "zh-TW": "Jev（System One）"},
    "common.llm": {"en": "LLM", "zh-TW": "LLM"},
    "common.latency": {"en": "Latency", "zh-TW": "延遲"},
    "common.cost": {"en": "Cost", "zh-TW": "成本"},
    "common.tokens": {"en": "Tokens", "zh-TW": "Token 數"},
    "common.agreement": {"en": "Agreement", "zh-TW": "一致率"},
    "common.speedup": {"en": "Jev speed-up", "zh-TW": "Jev 速度倍率"},
    "common.cheaper": {"en": "Jev cost saving", "zh-TW": "Jev 成本倍率"},
    "common.type_errors": {"en": "Schema violations", "zh-TW": "結構違規數"},
    "common.confidence": {"en": "Confidence", "zh-TW": "信賴度"},
    "common.state": {"en": "Program state", "zh-TW": "程式狀態（state）"},
    "common.state_help": {
        "en": "Anything the model should know. A string, a JSON object, or a list. Text only.",
        "zh-TW": "模型需要知道的內容，可為字串、JSON 物件或陣列，僅支援文字。",
    },
    "common.questions": {"en": "Questions", "zh-TW": "問題（questions）"},
    "common.answers": {"en": "Typed answers", "zh-TW": "型別化答案"},
    "common.raw_request": {"en": "Raw request", "zh-TW": "原始請求"},
    "common.raw_response": {"en": "Raw response", "zh-TW": "原始回應"},
    "common.error": {"en": "Error", "zh-TW": "錯誤"},
    "common.simulated": {"en": "SIMULATED", "zh-TW": "模擬資料"},
    "common.no_run_yet": {
        "en": "Nothing has been run yet. Press the button above.",
        "zh-TW": "尚未執行，請按上方按鈕。",
    },
    "common.question": {"en": "Question", "zh-TW": "問題"},
    "common.agree": {"en": "Agree", "zh-TW": "一致"},
    "common.differs": {"en": "Differs", "zh-TW": "不一致"},
    "common.no_answer": {"en": "no answer returned", "zh-TW": "未回傳答案"},
    "common.gap": {"en": "Gap", "zh-TW": "差距"},
    "common.free": {"en": "free", "zh-TW": "免費"},
    "common.probabilities": {"en": "Probabilities", "zh-TW": "機率分布"},
    "common.level": {"en": "level", "zh-TW": "等級"},
    "common.disabled": {"en": "disabled", "zh-TW": "已停用"},
    "common.none": {"en": "none", "zh-TW": "無"},
    "common.invalid_json": {
        "en": "That is not valid JSON, so it will be sent as a plain string.",
        "zh-TW": "這不是有效的 JSON，將以純字串送出。",
    },
    "common.category": {"en": "Category", "zh-TW": "類別"},
    "common.preset": {"en": "Sample input", "zh-TW": "範例輸入"},
    "common.model_returned": {"en": "Answered by", "zh-TW": "回應模型"},
    # ----------------------------------------------------------- overview
    "overview.heading": {
        "en": "Jev is not a smaller LLM. It is a different primitive.",
        "zh-TW": "Jev 不是更小的 LLM，而是一種不同的基礎元件。",
    },
    "overview.body": {
        "en": """
TypeSafe AI describes **Jev** as their first *System One* model: a class of model
built to make fast, structured decisions that software can consume directly.
The name follows Kahneman's split between fast, intuitive System 1 thinking and
slow, deliberate System 2 reasoning.

The design trade is deliberate and severe. **Jev gives up strings entirely.**
It cannot write prose, code, or a summary. In exchange you get a call that
behaves like a function instead of a conversation:

> unstructured state in → typed probabilistic decisions out

Because the set of possible outputs is declared in advance, the model cannot
return a value outside it. There is no parsing step, no validation step, and no
retry-on-malformed-JSON step, because there is no string to parse.

### The three primitives

The entire API surface is three question types. That is the design, not a
limitation to route around.

| Type | Question it answers | What comes back |
|---|---|---|
| **`noul`** | Is this statement true? | A single calibrated probability, 0-1. The number *is* the belief, so there is no separate confidence. |
| **`choice`** | Which one of these? | One option key from your set (up to 255), plus a probability per option and a confidence. |
| **`score`** | Where on this spectrum? | A continuous position across 2-10 ordered levels you describe, plus a confidence. It may land between levels. |

Every question is answered in **one parallel pass** over the state. A tenth
question costs a few more input tokens and almost no additional time, which
inverts the usual instinct to make a cheap call first and follow up only if
needed. Ask everything up front, then let ordinary code decide what mattered.

### Why calibration is the real product

Jev is trained with **RLCD** (Reinforcement Learning for Calibrated Decisions),
which optimises probabilities against outcomes rather than against human
preference. The claim that follows is the one that changes architecture: higher
confidence really does correspond to higher accuracy, in aggregate.

That is what lets you stop writing one threshold for a whole system and start
writing one per action, scaled to what being wrong costs. A read-only lookup can
fire at 0.5 confidence; moving money should not.

A model that is right 95% of the time but never tells you which 5% it is
guessing on cannot automate anything. One that reliably flags its own
uncertainty can automate the confident majority and escalate the rest.
""",
        "zh-TW": """
TypeSafe AI 將 **Jev** 定位為他們的第一個 *System One* 模型：這類模型專門用來做出
快速、結構化、且能被程式直接使用的決策。命名靈感來自 Kahneman 對「快思」（System 1，
直覺快速）與「慢想」（System 2，刻意推理）的區分。

它的設計取捨非常明確且激烈：**Jev 完全放棄了字串輸出。** 它無法撰寫文章、程式碼或摘要。
作為交換，你得到的是一個行為像「函式」而非「對話」的呼叫：

> 非結構化狀態輸入 → 型別化的機率性決策輸出

由於所有可能的輸出都事先宣告完畢，模型不可能回傳範圍之外的值。因此不需要解析步驟、
不需要驗證步驟，也不需要「JSON 格式錯誤就重試」的步驟 —— 因為根本沒有字串需要解析。

### 三種基礎問題型別

整個 API 介面只有三種問題型別。這是刻意的設計，而不是需要繞過的限制。

| 型別 | 回答的問題 | 回傳內容 |
|---|---|---|
| **`noul`** | 這個陳述為真嗎？ | 單一已校準機率（0-1）。這個數字本身就是信念，因此沒有額外的信賴度欄位。 |
| **`choice`** | 是這幾個選項中的哪一個？ | 你定義的選項鍵之一（最多 255 個），並附上每個選項的機率與整體信賴度。 |
| **`score`** | 落在這個尺度的哪個位置？ | 在你描述的 2-10 個有序等級上的連續位置，並附上信賴度；數值可以落在等級之間。 |

所有問題都在對狀態的**單一次平行運算**中完成。第十個問題只會多花少量輸入 token，
幾乎不增加時間。這顛覆了「先發一個便宜的呼叫、必要時再追問」的慣性做法：
你應該一次問完所有問題，再讓一般程式碼決定哪些答案真正重要。

### 校準才是真正的產品

Jev 使用 **RLCD**（Reinforcement Learning for Calibrated Decisions，校準決策強化學習）
訓練，其最佳化目標是「機率與實際結果的吻合程度」，而非「人類偏好」。由此推導出的主張
才是真正改變系統架構的地方：整體而言，較高的信賴度確實對應較高的正確率。

這讓你不必再為整個系統寫死同一個門檻值，而能**針對每個動作**設定門檻，並依「做錯的代價」
來調整。唯讀查詢可以在信賴度 0.5 就執行；但涉及金流的動作就不該如此。

一個有 95% 機率正確、卻從不告訴你它在哪 5% 上瞎猜的模型，無法自動化任何事情；
而一個能可靠標示自身不確定性的模型，就能自動化有信心的多數案例，並將其餘案例升級處理。
""",
    },
    "overview.table_heading": {
        "en": "Side by side with existing LLMs",
        "zh-TW": "與現有 LLM 的正面比較",
    },
    "overview.table_body": {
        "en": """
The figures below are the ones TypeSafe published at launch. Treat them as
vendor claims: read the caveats section further down before you plan a migration
around them.

| | Existing LLMs | System One + Jev |
|---|---|---|
| **Optimised with** | RLHF / RLVR | RLCD (Reinforcement Learning for Calibrated Decisions) |
| **Optimises for** | Human preference: responses raters like | Calibrated decisions: honest probabilities on System One tasks |
| **Inputs** | Unstructured data, emphasis on sequential messages | Unstructured data, emphasis on structured program state |
| **Outputs** | Strings. Flexible enough to be anything, including hallucinations and refusals. Must be parsed and validated. | Type-safe structured values. Possible outputs declared in advance. Never a type error. |
| **Sampling** | Sequential, one token at a time | Parallel, all outputs in a single query |
| **Input cost** | $0.20 - $10 / MTok | $0.042 / MTok |
| **Output cost** | ~5x input tokens | Free |
| **Latency** | 3 s - 329 s | 70 ms - 500 ms |
| **Confidence** | Overconfident and inconsistent, even when asked | Calibrated probability on every output |
| **Can generate text** | Yes | No, never |

### What each one is actually for

**Reach for an LLM when** the output is meant for a human, when you need prose
or code written, when the problem is open-ended, or when correctness is cheaply
verifiable so the model can iterate until tests pass.

**Reach for Jev when** the output is meant for an `if` statement. Classifying,
routing, scoring, extracting a decision, filtering, guardrailing, judging
another model's output, or map-reducing over data too large to send anywhere
expensive. Anything that has to complete inside a request handler.

**The honest answer is usually both.** The cascade pattern uses Jev to decide
which of the rare, hard requests deserve a frontier model, handles the easy
majority in plain code, and escalates whatever Jev flags as uncertain to a human.
""",
        "zh-TW": """
以下數據為 TypeSafe 在發布時公布的內容。請將它們視為**供應商自行提出的主張**：
在據此規劃技術遷移之前，請先閱讀下方的「保留態度」一節。

| | 現有 LLM | System One + Jev |
|---|---|---|
| **訓練最佳化方式** | RLHF / RLVR | RLCD（校準決策強化學習） |
| **最佳化目標** | 人類偏好：評分者喜歡的回答 | 校準決策：在 System One 任務上誠實反映機率 |
| **輸入** | 非結構化資料，偏重連續對話訊息 | 非結構化資料，偏重結構化的程式狀態 |
| **輸出** | 字串。彈性極高，可以是任何東西，也包含幻覺與拒答，且必須經過解析與驗證。 | 型別安全的結構化值。所有可能輸出事先宣告，永不發生型別錯誤。 |
| **取樣方式** | 循序，一次產生一個 token | 平行，單次查詢產生全部輸出 |
| **輸入成本** | 每百萬 token 0.20 - 10 美元 | 每百萬 token 0.042 美元 |
| **輸出成本** | 約為輸入 token 的 5 倍 | 免費 |
| **延遲** | 3 秒 - 329 秒 | 70 毫秒 - 500 毫秒 |
| **信賴度** | 即使明確要求，仍傾向過度自信且不一致 | 每個輸出都附帶已校準的機率 |
| **能否生成文字** | 可以 | 完全不行 |

### 兩者各自的真正用途

**該用 LLM 的時機**：輸出是給人看的、需要撰寫文章或程式碼、問題本身是開放式的，
或正確性可以低成本自動驗證（讓模型反覆迭代到測試通過）。

**該用 Jev 的時機**：輸出是要餵給 `if` 判斷式的。分類、路由、評分、擷取決策、過濾、
防護欄、評判另一個模型的輸出，或是對大到無法送進昂貴模型的資料做 map-reduce。
以及任何必須在單次請求處理時間內完成的工作。

**誠實的答案通常是「兩者並用」。** 所謂 cascade（層疊）模式，就是用 Jev 判斷哪些少數
困難請求值得動用前沿模型、讓一般程式碼處理簡單的多數案例，並將 Jev 標記為不確定的案例
升級給人工處理。
""",
    },
    "overview.caveats_heading": {
        "en": "Read this before you plan a migration",
        "zh-TW": "在規劃遷移前請務必閱讀",
    },
    "overview.caveats_body": {
        "en": """
This demo is an enthusiastic exploration of a new model class, but the numbers
driving it come from the vendor. Four things are worth holding onto.

**1. The benchmark column is not accuracy.** TypeSafe's workflow evaluation has
no ground truth. It builds consensus labels by averaging two frontier models
(GPT-6 Astra and Claude Fable 5.1 at high thinking) and scores everyone against
that average. It measures *agreement with two frontier models*, which is also
why neither appears in the results. TypeSafe notes this biases the reference
toward OpenAI and Anthropic.

On that evaluation Jev scores 67.8%, level with GPT-5.6 Terra at 67.9% and
Claude Sonnet 5 at 67.8%, behind GPT-5.6 Sol at 74.1% and Claude Opus 5 at
73.1% — at roughly 1/200th the cost and 1/50th the latency.

**2. It is self-run.** TypeSafe designed the workflows, built the harness, and
ran the evaluation. No independent reproduction exists yet. Evaluate on your own
traffic before trusting any of it.

**3. "Cannot hallucinate" is narrower than it sounds.** Jev cannot return a
value *outside your schema*. It can absolutely return the *wrong value from
inside* it. The published 0% type-error rate is asserted from the architecture
rather than measured: schema matching is structural, so 0% goes in the chart.
Meanwhile the LLM comparison figure of 45.5% is a single outlier; most models
sit between 0.58% and 13.2%.

**4. The price may move.** TypeSafe cannot prove the pricing is not subsidised.
They say they expect it to fall rather than rise, but that is a forecast.

### Where Jev is known to be weak

TypeSafe publish a "jaggedness" page, which is unusually candid for a launch.

- **It reads literally.** Negations, scoping words, and implied conditions land
  at face value. If you catch yourself explaining what you *really meant*, that
  explanation was the missing half of your instruction.
- **It is not a calculator.** Counting is unreliable and the error grows with
  the size of the thing counted. Iterate in code and ask one `noul` per item.
- **Dates are text, not ordered quantities.** Which came first, how far apart,
  whether one falls in a window: all unreliable. Extract with a `choice` over
  enumerated values, then order and compare in code.
- **Context rot is real.** Accuracy falls as the state fills with material the
  question does not need. Retrieve and filter first, then send only the fields
  the question actually uses.
- **State is not treated as hostile.** Text engineered to argue for its own
  classification can move the answer. If user-controlled content goes into
  state, that is your threat model to handle.
- **It does not generate.** If you need a value extracted from free text, get
  candidates with a regex or a generative model and let Jev pick among them.

The meta-rule from their docs is good design advice regardless of model: do not
ask the model something code can compute exactly, and do not hide several
judgements inside one question.
""",
        "zh-TW": """
這個示範專案對一個新模型類別抱持高度興趣，但驅動它的數據來自供應商本身。
有四件事必須放在心上。

**1. 那個基準分數欄位並不是「正確率」。** TypeSafe 的 workflow 評測沒有標準答案。
它以兩個前沿模型（GPT-6 Astra 與 Claude Fable 5.1，皆開啟高強度推理）的平均值建立
共識標籤，再用該平均值為所有模型打分。因此它衡量的是**與兩個前沿模型的一致程度**，
這也是為什麼這兩個模型本身不出現在結果中。TypeSafe 也指出，這讓參考答案偏向
OpenAI 與 Anthropic。

在該評測中，Jev 得分 67.8%，與 GPT-5.6 Terra（67.9%）和 Claude Sonnet 5（67.8%）
持平，落後於 GPT-5.6 Sol（74.1%）與 Claude Opus 5（73.1%）—— 但成本約為 1/200，
延遲約為 1/50。

**2. 這是供應商自行執行的評測。** 工作流程、測試框架與實際執行全由 TypeSafe 完成，
目前尚無獨立第三方複現。在信任任何數據之前，請先用你自己的真實流量進行評估。

**3.「不會產生幻覺」的範圍比字面上更窄。** Jev 不可能回傳**你的 schema 之外**的值，
但它完全有可能回傳 schema **之內的錯誤值**。公布的 0% 型別錯誤率是從架構推導而來，
而非實測：由於 schema 相符是結構性保證，所以直接在圖表填入 0%。另一方面，LLM 對照組
的 45.5% 是單一極端值，大多數模型落在 0.58% 到 13.2% 之間。

**4. 價格可能變動。** TypeSafe 無法證明目前定價沒有補貼。他們表示預期價格會下降而非上升，
但那僅是預測。

### Jev 已知的弱項

TypeSafe 公開了一個名為「jaggedness」（能力不平整）的頁面，對一個新產品發布而言相當坦誠。

- **它照字面理解。** 否定詞、限定範圍的詞語與隱含條件都會被字面採納。如果你發現自己正在
  解釋「我真正的意思是……」，那段解釋就是你指令中缺少的另一半。
- **它不是計算機。** 計數並不可靠，且誤差會隨被計數對象的數量增加而放大。請在程式碼中
  逐項迭代，對每個項目各問一個 `noul`。
- **日期對它而言是文字，不是有序數值。** 誰先誰後、相隔多久、是否落在某區間，全都不可靠。
  請用 `choice` 在列舉值中擷取，再於程式碼中排序與比較。
- **context rot（脈絡腐化）是真實存在的。** 當狀態塞滿問題不需要的內容時，正確率會下降。
  請先檢索並過濾，只送出問題真正需要的欄位。
- **它不會把狀態視為潛在惡意輸入。** 刻意設計、為自己爭取特定分類的文字可能影響答案。
  若使用者可控的內容會進入狀態，這就是你必須自行處理的威脅模型。
- **它不做生成。** 若你需要從自由文字中擷取某個值，請先用正規表達式或生成式模型取得候選項，
  再讓 Jev 從中挑選。

他們文件中的總則，不論用哪個模型都是好的設計建議：不要問模型可以由程式碼精確算出的事情，
也不要把多個判斷藏在同一個問題裡。
""",
    },
    "overview.wire_heading": {
        "en": "What a call actually looks like",
        "zh-TW": "一次呼叫的實際樣貌",
    },
    "overview.wire_body": {
        "en": """
Jev is reachable two ways. This app supports both, selectable in the sidebar.

| | OpenRouter | TypeSafe first-party |
|---|---|---|
| Endpoint | `POST https://openrouter.ai/api/alpha/decisions` | `POST https://api.typesafe.ai/v1/systemone` |
| Model slug | `typesafe/jev-latest` | `jev-latest` |
| Credential | OpenRouter key | TypeSafe key (early access, waitlisted) |

The body, the three question types, and the answer shapes are otherwise
identical. One difference worth knowing: OpenRouter requires **both** the `true`
and `false` descriptions on a `noul` whenever `criteria` is present at all,
while TypeSafe's API treats each side as independently optional. This app
normalises that for you, so the same question definition works on both.
""",
        "zh-TW": """
Jev 有兩種呼叫途徑，本應用皆支援，可於側邊欄切換。

| | OpenRouter | TypeSafe 官方 |
|---|---|---|
| 端點 | `POST https://openrouter.ai/api/alpha/decisions` | `POST https://api.typesafe.ai/v1/systemone` |
| 模型代號 | `typesafe/jev-latest` | `jev-latest` |
| 憑證 | OpenRouter 金鑰 | TypeSafe 金鑰（早期存取，需排隊候補） |

除此之外，請求主體、三種問題型別與答案結構完全相同。一個值得注意的差異：只要 `noul`
出現 `criteria` 欄位，OpenRouter 就要求**同時**提供 `true` 與 `false` 的描述，
而 TypeSafe 的 API 則允許兩者各自獨立選填。本應用已為你統一處理，
因此同一份問題定義在兩邊都能運作。
""",
    },
    "overview.sources": {"en": "Sources", "zh-TW": "資料來源"},
    # ------------------------------------------------------------ compare
    "compare.heading": {
        "en": "Same state, same questions, two engines",
        "zh-TW": "相同狀態、相同問題、兩種引擎",
    },
    "compare.intro": {
        "en": (
            "Both engines receive the identical question set. The LLM gets it as a "
            "strict JSON Schema, which is the most favourable way to extract typed "
            "decisions from a chat model. Latency is measured end to end from this "
            "machine, and cost comes from the provider's own billing field rather "
            "than a price table."
        ),
        "zh-TW": (
            "兩種引擎會收到完全相同的問題集。LLM 端以嚴格 JSON Schema 約束輸出，"
            "這是從對話模型取得型別化決策最有利的方式。延遲為本機端到端實測，"
            "成本則取自服務供應商回傳的計費欄位，而非price table 推估。"
        ),
    },
    "compare.load_case": {"en": "Start from a use case", "zh-TW": "從示範情境載入"},
    "compare.custom": {"en": "Custom (edit below)", "zh-TW": "自訂（於下方編輯）"},
    "compare.per_question": {"en": "Question-by-question", "zh-TW": "逐題對照"},
    "compare.disagreements": {
        "en": "Disagreements worth a look",
        "zh-TW": "值得關注的分歧",
    },
    "compare.all_agree": {
        "en": "Both engines agreed on every question.",
        "zh-TW": "兩種引擎在所有問題上都一致。",
    },
    "compare.agreement_note": {
        "en": (
            "Agreement is not correctness — neither column is ground truth. A "
            "disagreement is an invitation to look at the input and decide which "
            "answer you would have written."
        ),
        "zh-TW": (
            "一致並不等於正確 —— 兩邊都不是標準答案。出現分歧時，"
            "正是你該回頭檢視輸入、並判斷自己會寫下哪個答案的時機。"
        ),
    },
    "compare.llm_disabled": {
        "en": "The LLM column is switched off in the sidebar.",
        "zh-TW": "LLM 欄位已在側邊欄停用。",
    },
    "compare.typesafety_note_jev": {
        "en": "Structurally guaranteed: the output space is the schema.",
        "zh-TW": "結構性保證：輸出空間即為 schema 本身。",
    },
    "compare.typesafety_note_llm_ok": {
        "en": "Validated clean on this run. Not guaranteed on the next one.",
        "zh-TW": "本次執行驗證通過，但無法保證下一次也如此。",
    },
    "compare.typesafety_note_llm_bad": {
        "en": "Violations found while validating the model's output:",
        "zh-TW": "驗證模型輸出時發現以下違規：",
    },
    # ----------------------------------------------------------- usecases
    "usecases.heading": {
        "en": "Ten things that get easier when decisions are typed",
        "zh-TW": "當決策具備型別後，這十件事會變得更容易",
    },
    "usecases.intro": {
        "en": (
            "Each demo is a small working app. It builds a state object, asks Jev a "
            "set of typed questions, and then runs **ordinary Python** over the "
            "answers to reach an outcome. The code that does the branching is shown "
            "with every demo, because that is the actual point: the interesting "
            "logic stays in your codebase, reviewable and testable, and the model "
            "only supplies the judgements code finds hard to phrase."
        ),
        "zh-TW": (
            "每個示範都是一個可運作的小型應用：它建立狀態物件、向 Jev 提出一組型別化問題，"
            "然後以**普通的 Python 程式碼**處理答案並得出結果。每個示範都會一併展示分支邏輯的"
            "程式碼，因為這正是重點所在：真正重要的邏輯留在你的程式庫中，可審查、可測試，"
            "模型只負責提供那些難以用程式碼描述的判斷。"
        ),
    },
    "usecases.pick": {"en": "Pick a demo", "zh-TW": "選擇示範"},
    "usecases.why": {"en": "Why this suits Jev", "zh-TW": "為什麼這適合用 Jev"},
    "usecases.outcome": {"en": "What the app did", "zh-TW": "應用實際執行的動作"},
    "usecases.decision_code": {
        "en": "The branching code, verbatim",
        "zh-TW": "分支邏輯程式碼（原始內容）",
    },
    "usecases.questions_asked": {
        "en": "Questions asked in this call",
        "zh-TW": "本次呼叫提出的問題",
    },
    "usecases.compare_toggle": {
        "en": "Also run the LLM for comparison",
        "zh-TW": "同時執行 LLM 以進行比較",
    },
    "usecases.edit_state": {
        "en": "Edit the state before running",
        "zh-TW": "執行前編輯狀態",
    },
    "usecases.trace": {"en": "Decision trace", "zh-TW": "決策軌跡"},
    "usecases.outcome_compare": {
        "en": "What the same code did with each engine's answers",
        "zh-TW": "同一段程式碼在兩種引擎答案下的實際結果",
    },
    "usecases.same_action": {
        "en": (
            "Both engines led the application to the same action, so the "
            "differences above were not decision-relevant here."
        ),
        "zh-TW": (
            "兩種引擎都讓應用程式採取相同動作，"
            "因此上方的差異在本案例中並不影響決策結果。"
        ),
    },
    "usecases.different_action": {
        "en": (
            "The two engines led the application to different actions. This is "
            "the kind of disagreement worth investigating — read the state and "
            "decide which action you would have wanted."
        ),
        "zh-TW": (
            "兩種引擎讓應用程式採取了不同動作。這正是值得深入檢視的分歧 ——"
            "請回頭閱讀輸入狀態，並判斷你希望系統採取哪一個動作。"
        ),
    },
    # --------------------------------------------------------- playground
    "playground.heading": {"en": "Build your own decision call", "zh-TW": "自行建構決策呼叫"},
    "playground.intro": {
        "en": (
            "Write any state, define any mix of the three question types, and send "
            "it. This is the fastest way to find out whether a decision in your own "
            "product is a good fit."
        ),
        "zh-TW": (
            "自由撰寫任何狀態、定義三種問題型別的任意組合並送出。"
            "這是最快的方式，用來判斷你自己產品中的某個決策是否適合交給 Jev。"
        ),
    },
    "playground.examples": {
        "en": "Start from an example",
        "zh-TW": "從範例開始",
    },
    "playground.pick_example": {"en": "Example", "zh-TW": "範例"},
    "playground.load_example": {"en": "Load example", "zh-TW": "載入範例"},
    "playground.loaded": {"en": "loaded", "zh-TW": "已載入"},
    "playground.clear": {"en": "Start blank", "zh-TW": "清空重來"},
    "playground.step_state": {"en": "1 · Program state", "zh-TW": "1 · 程式狀態"},
    "playground.step_state_help": {
        "en": (
            "Everything the model is allowed to know. It cannot look anything "
            "up, so whatever you leave out simply does not exist as far as the "
            "answers are concerned."
        ),
        "zh-TW": (
            "模型被允許知道的全部內容。它無法自行查找任何資料，"
            "因此你沒放進來的東西，對答案而言就等於不存在。"
        ),
    },
    "playground.step_questions": {"en": "2 · Questions", "zh-TW": "2 · 問題"},
    "playground.step_questions_help": {
        "en": (
            "All of these are answered in one call, in parallel. Adding a fourth "
            "or tenth question costs a few input tokens and almost no extra time."
        ),
        "zh-TW": (
            "這些問題會在單次呼叫中平行回答完畢。"
            "增加第四個甚至第十個問題，只多花少量輸入 token，幾乎不增加時間。"
        ),
    },
    "playground.step_run": {"en": "3 · Send it", "zh-TW": "3 · 送出"},
    "playground.type_primer": {
        "en": "Which question type should I use?",
        "zh-TW": "我該使用哪一種問題型別？",
    },
    "playground.type_primer_body": {
        "en": (
            "- **`noul`** — a yes/no judgement, returned as one probability "
            "between 0 and 1. Use it for anything you would write as an `if`. "
            "Checking a checklist? One `noul` per item beats one question asking "
            "for a count.\n"
            "- **`choice`** — exactly one option from a set you name, up to 255 "
            "of them. Your code branches on the option key, so name the keys the "
            "way you would name enum members. Include an explicit `other` so the "
            "model can say nothing fits instead of picking the closest wrong "
            "thing.\n"
            "- **`score`** — a position across 2-10 ordered levels you describe "
            "in words. The answer can land between levels, which is what lets "
            "your code apply its own thresholds.\n\n"
            "Two rules that save time: never ask the model something your code "
            "can compute exactly, and never hide two judgements inside one "
            "question."
        ),
        "zh-TW": (
            "- **`noul`** —— 是非判斷，回傳一個 0 到 1 之間的機率。凡是你會寫成 `if` "
            "的條件都適合用它。要檢查一份清單？為每個項目各問一個 `noul`，"
            "遠勝於用一個問題要求模型計數。\n"
            "- **`choice`** —— 從你指定的集合中選出恰好一個選項，最多 255 個。"
            "你的程式碼會依選項鍵分支，所以請像命名 enum 成員那樣命名這些鍵。"
            "建議明確加入 `other`，讓模型能表達「都不符合」，"
            "而不是硬挑一個最接近但錯誤的答案。\n"
            "- **`score`** —— 在你用文字描述的 2 到 10 個有序等級上的位置。"
            "答案可以落在等級之間，這正是讓你的程式碼能套用自訂門檻值的關鍵。\n\n"
            "兩條能省下大量時間的原則：絕不要問模型你的程式碼可以精確算出的事情，"
            "也絕不要把兩個判斷藏在同一個問題裡。"
        ),
    },
    "playground.add_noul": {"en": "Add yes/no", "zh-TW": "新增是非題"},
    "playground.add_choice": {"en": "Add pick-one", "zh-TW": "新增單選題"},
    "playground.add_score": {"en": "Add rating", "zh-TW": "新增評分題"},
    "playground.remove": {"en": "Remove", "zh-TW": "移除"},
    "playground.options_help": {
        "en": "One per line. The key before the colon is what your code branches on.",
        "zh-TW": "每行一個。冒號前的鍵值就是你的程式碼用來分支的依據。",
    },
    "playground.levels_help": {
        "en": "One per line, lowest first. Level numbering starts at 0.",
        "zh-TW": "每行一個，由低至高。等級編號從 0 開始。",
    },
    "playground.noul_help": {
        "en": "Both descriptions are optional, but spelling them out sharply improves the answer.",
        "zh-TW": "兩側描述皆為選填，但把它們清楚寫出來能明顯改善答案品質。",
    },
    "playground.key": {"en": "Key (your code branches on this)", "zh-TW": "鍵值（程式碼依此分支）"},
    "playground.type": {"en": "Type", "zh-TW": "型別"},
    "playground.instructions": {"en": "Instructions", "zh-TW": "問題敘述（instructions）"},
    "playground.true_criteria": {"en": "What `true` means", "zh-TW": "`true` 代表什麼"},
    "playground.false_criteria": {"en": "What `false` means", "zh-TW": "`false` 代表什麼"},
    "playground.options": {
        "en": "Options, one per line as `key: description`",
        "zh-TW": "選項，每行一個，格式為 `key: 說明`",
    },
    "playground.levels": {
        "en": "Levels, one per line, lowest first",
        "zh-TW": "等級，每行一個，由低至高",
    },
    "playground.no_questions": {
        "en": "Add at least one question to run.",
        "zh-TW": "請至少新增一個問題才能執行。",
    },
    "playground.generated": {"en": "Generated request body", "zh-TW": "產生的請求主體"},
    # ---------------------------------------------------------- economics
    "economics.heading": {
        "en": "What this costs at your volume",
        "zh-TW": "在你的流量規模下的成本",
    },
    "economics.intro": {
        "en": (
            "A model for the decision layer of a workflow, using published list "
            "prices. Adjust the inputs to match your own traffic. This is "
            "arithmetic on vendor pricing, not a benchmark."
        ),
        "zh-TW": (
            "以公開定價估算工作流程中「決策層」的成本模型。請依你自己的流量調整輸入值。"
            "這只是基於供應商定價的算術推估，並非實測基準。"
        ),
    },
    "economics.decisions": {"en": "Decisions per month", "zh-TW": "每月決策次數"},
    "economics.state_tokens": {
        "en": "Input tokens per decision",
        "zh-TW": "每次決策的輸入 token 數",
    },
    "economics.llm_output_tokens": {
        "en": "LLM output tokens per decision",
        "zh-TW": "LLM 每次決策的輸出 token 數",
    },
    "economics.llm_in_price": {
        "en": "LLM input price ($/MTok)",
        "zh-TW": "LLM 輸入價格（美元/百萬 token）",
    },
    "economics.llm_out_price": {
        "en": "LLM output price ($/MTok)",
        "zh-TW": "LLM 輸出價格（美元/百萬 token）",
    },
    "economics.jev_latency": {"en": "Jev latency (ms)", "zh-TW": "Jev 延遲（毫秒）"},
    "economics.llm_latency": {"en": "LLM latency (s)", "zh-TW": "LLM 延遲（秒）"},
    "economics.monthly_cost": {"en": "Monthly cost", "zh-TW": "每月成本"},
    "economics.serial_time": {
        "en": "Serial time to process the month",
        "zh-TW": "以序列方式處理當月所需時間",
    },
    "economics.savings": {"en": "Monthly saving with Jev", "zh-TW": "改用 Jev 的每月節省"},
    "economics.cascade_heading": {
        "en": "The cascade is usually the real answer",
        "zh-TW": "cascade（層疊）通常才是真正的答案",
    },
    "economics.cascade_intro": {
        "en": (
            "You rarely replace an LLM outright. You put Jev in front of it to "
            "decide which requests actually need one. Set the share of traffic that "
            "still escalates:"
        ),
        "zh-TW": (
            "你很少會完全取代 LLM，而是把 Jev 放在前面，用來判斷哪些請求真的需要 LLM。"
            "請設定仍需升級處理的流量比例："
        ),
    },
    "economics.escalation": {"en": "Share escalated to the LLM", "zh-TW": "升級至 LLM 的流量比例"},
    "economics.cascade_cost": {"en": "Cascade monthly cost", "zh-TW": "cascade 每月成本"},
    "economics.vs_llm_only": {"en": "vs LLM for everything", "zh-TW": "相較於全部交由 LLM"},
    "economics.note": {
        "en": (
            "Jev bills input tokens only, at $0.042/MTok, with output free. That is "
            "why asking ten questions instead of three barely moves the bill, and "
            "why a wide `choice` costs almost nothing extra."
        ),
        "zh-TW": (
            "Jev 僅就輸入 token 計費（每百萬 token 0.042 美元），輸出免費。"
            "這正是為什麼把問題從三個增加到十個幾乎不影響帳單，"
            "以及為什麼選項眾多的 `choice` 幾乎不會增加額外成本。"
        ),
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Look up a localised string, falling back to English then the key itself."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def pick(values: dict[str, Any], lang: str = DEFAULT_LANG) -> Any:
    """Select a language variant from an inline `{"en": ..., "zh-TW": ...}` map."""
    if not isinstance(values, dict):
        return values
    return values.get(lang) or values.get(DEFAULT_LANG) or next(iter(values.values()), "")
