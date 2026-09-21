"""Demo use cases 8-9: decisions inside a real-time control loop.

These are the cases where latency is not a UX nicety but a hard constraint. A
game loop running at 10 Hz has 100 ms per decision; a frontier model's 3-329 s
end-to-end response time is not slow here, it is disqualifying.

Both demos follow the same discipline the community's drone and browser agents
converged on: the loop, the safety rules, and the arithmetic stay in ordinary
code. The model supplies only the tactical judgement in the middle.
"""

from __future__ import annotations

from typing import Any

from ..schema import Choice, DecisionResult, Noul, Question, Score
from .base import Outcome, Sample, UseCase

# ==========================================================================
# 8. Real-time game agent
# ==========================================================================

GAME_QUESTIONS = {
    "action": Choice(
        instructions="Choose the single best action for this tick.",
        label="Next action",
        criteria={
            "attack_nearest": "Fire at the closest visible enemy.",
            "retreat_to_cover": "Break contact and move toward cover or an exit.",
            "grab_health": "Move to collect a nearby health pickup.",
            "grab_ammo": "Move to collect a nearby ammunition pickup.",
            "strafe_left": "Side-step left to dodge incoming fire while staying engaged.",
            "strafe_right": "Side-step right to dodge incoming fire while staying engaged.",
            "advance": "Push forward toward the objective.",
            "hold_position": "Stay put and wait for a better opportunity.",
        },
    ),
    "threat": Score(
        instructions="How dangerous is the player's situation right now?",
        label="Threat level",
        criteria=[
            "No immediate danger.",
            "Enemies present but at a safe distance.",
            "Under fire; taking damage.",
            "Critical: death is imminent without an immediate change.",
        ],
    ),
    "should_disengage": Noul(
        instructions="The player should break off this fight rather than continue it.",
        label="Should disengage",
        true_criteria="Continuing the engagement is likely to get the player killed.",
        false_criteria="The fight is winnable from the current position.",
    ),
    "ammo_sufficient": Noul(
        instructions="The player has enough ammunition for the currently equipped weapon to win this fight.",
        label="Ammo sufficient",
        true_criteria="Enough rounds remain to kill the visible enemies.",
        false_criteria="The player will run dry before the fight ends.",
    ),
}


def decide_game_action(result: DecisionResult, state: Any) -> Outcome:
    """Pick an action, but let hard-coded survival rules overrule the model.

    This mirrors the layering the community's drone agent settled on: the fast
    control loop and the safety reflexes are owned by code, and the model's
    tactical judgement is advisory. Code always keeps the veto.
    """
    player = state.get("player", {}) if isinstance(state, dict) else {}
    pickups = state.get("pickups", []) if isinstance(state, dict) else []
    health = float(player.get("health", 100))
    ammo = sum(
        int(v) for v in (player.get("ammo") or {}).values() if isinstance(v, (int, float))
    )

    proposed = result.choice("action")
    confidence = result.confidence("action")
    threat = result.score("threat")

    trace = [
        f"tick={state.get('tick') if isinstance(state, dict) else '?'} "
        f"health={health:.0f} ammo={ammo}",
        f"model proposes {proposed!r} at confidence {confidence:.2f}",
        f"threat={threat:.2f}/3 disengage={result.noul('should_disengage'):.2f} "
        f"ammo_sufficient={result.noul('ammo_sufficient'):.2f}",
    ]

    medkit_near = any(
        p.get("type") == "medkit" and float(p.get("distance_m", 999)) < 8
        for p in pickups
        if isinstance(p, dict)
    )

    # Safety reflex: code owns survival, not the model. Below 25 health with a
    # medkit in reach, we heal regardless of what was proposed.
    if health < 25 and medkit_near and proposed != "grab_health":
        trace.append("-> SAFETY OVERRIDE: critical health with a medkit in reach")
        return Outcome("grab_health", "error", trace, {"Override": "safety reflex"})

    # Never fire a weapon we cannot feed.
    if proposed == "attack_nearest" and ammo == 0:
        trace.append("-> OVERRIDE: no ammunition, attack is not executable")
        return Outcome("retreat_to_cover", "warning", trace, {"Override": "out of ammo"})

    # Low confidence in a fast loop is cheap to absorb: hold, and the next tick
    # arrives in 100 ms with fresh state.
    if confidence < 0.4:
        trace.append("-> low confidence, holding this tick and re-deciding next tick")
        return Outcome("hold_position", "info", trace, {"Override": "low confidence"})

    if threat >= 2.5 and result.noul("should_disengage") > 0.6:
        trace.append("-> critical threat and disengage advised")
        return Outcome("retreat_to_cover", "warning", trace)

    return Outcome(proposed, "success", trace)


GAME_CASE = UseCase(
    id="game_agent",
    icon=":material/sports_esports:",
    title={"en": "Real-time game agent", "zh-TW": "即時遊戲代理"},
    category={"en": "Real-time control", "zh-TW": "即時控制"},
    summary={
        "en": (
            "A symbolic game state goes in, an action comes out, roughly ten "
            "times a second. Hard-coded survival reflexes keep the right to "
            "overrule the model on every tick."
        ),
        "zh-TW": (
            "輸入符號化的遊戲狀態、輸出一個動作，每秒約執行十次。"
            "而寫死的生存反射機制在每一個 tick 都保有推翻模型決定的權力。"
        ),
    },
    why={
        "en": (
            "At 10 Hz you have 100 ms per decision. That single constraint rules "
            "out every frontier model, no matter how much smarter it might be.\n\n"
            "TypeSafe's launch demo of this was a Doom bot, and the engineer's "
            "worry was that ten queries a second would be expensive. It works "
            "out at roughly $7 an hour — lower than the team expected.\n\n"
            "The layering is the lesson, and it is the same one the community's "
            "drone agent documented: a 500 Hz flight controller and a 50 Hz "
            "safety reflex in code, with the model contributing tactical "
            "judgement at 2.5 Hz, advisory only. As that README puts it, the "
            "model cannot be the perception layer and it cannot run at control "
            "rate. Watch the override fire on the *critical health* sample."
        ),
        "zh-TW": (
            "在 10 Hz 之下，每個決策只有 100 毫秒。單單這一個限制，"
            "就排除了所有前沿模型 —— 不論它們可能聰明多少。\n\n"
            "TypeSafe 發布時的示範正是一個 Doom 機器人，當時工程師擔心的是"
            "「每秒十次查詢」會很貴；實際算下來大約每小時 7 美元 —— 低於團隊預期。\n\n"
            "真正的啟示在於分層，而這也正是社群的無人機代理所記錄下的經驗："
            "500 Hz 的飛控與 50 Hz 的安全反射都由程式碼掌管，"
            "模型只在 2.5 Hz 提供戰術判斷，且僅供參考。"
            "如該專案 README 所言：模型不能擔任感知層，也不能在控制頻率上運行。"
            "你可以在「危急血量」範例中看到覆寫機制實際觸發。"
        ),
    },
    questions=GAME_QUESTIONS,
    actions={
        "attack_nearest": {"en": "Fired at the nearest enemy", "zh-TW": "朝最近的敵人開火"},
        "retreat_to_cover": {"en": "Broke contact and moved to cover", "zh-TW": "脫離接觸並移動至掩護"},
        "grab_health": {"en": "Moved to collect the health pickup", "zh-TW": "移動去拾取補血道具"},
        "grab_ammo": {"en": "Moved to collect the ammo pickup", "zh-TW": "移動去拾取彈藥"},
        "strafe_left": {"en": "Strafed left while staying engaged", "zh-TW": "向左橫移並維持交戰"},
        "strafe_right": {"en": "Strafed right while staying engaged", "zh-TW": "向右橫移並維持交戰"},
        "advance": {"en": "Pushed forward toward the objective", "zh-TW": "朝目標推進"},
        "hold_position": {"en": "Held position this tick", "zh-TW": "本 tick 維持原地"},
    },
    decide=decide_game_action,
    samples=[
        Sample(
            id="critical_health",
            name={"en": "Critical health, medkit nearby", "zh-TW": "血量危急、附近有補血包"},
            state={
                "tick": 14822,
                "player": {
                    "health": 18,
                    "armor": 0,
                    "weapon": "shotgun",
                    "ammo": {"shells": 3},
                },
                "enemies": [
                    {"id": "e1", "type": "imp", "distance_m": 9.4, "bearing_deg": -20, "visible": True, "attacking": True},
                    {"id": "e2", "type": "imp", "distance_m": 14.1, "bearing_deg": 35, "visible": True, "attacking": False},
                ],
                "pickups": [
                    {"type": "medkit", "distance_m": 4.2, "bearing_deg": 110, "heals": 25},
                    {"type": "shells", "distance_m": 19.0, "bearing_deg": -80, "amount": 8},
                ],
                "environment": {
                    "in_corridor": True,
                    "cover_available": True,
                    "cover_bearing_deg": 120,
                    "damage_taken_last_second": 11,
                },
            },
            hint={
                "action": "attack_nearest",
                "threat": 2.8,
                "should_disengage": 0.71,
                "ammo_sufficient": 0.38,
            },
        ),
        Sample(
            id="healthy_fight",
            name={"en": "Healthy, winnable fight", "zh-TW": "血量充足、可打贏的戰鬥"},
            state={
                "tick": 9310,
                "player": {
                    "health": 92,
                    "armor": 50,
                    "weapon": "plasma_rifle",
                    "ammo": {"cells": 160},
                },
                "enemies": [
                    {"id": "e1", "type": "zombieman", "distance_m": 12.0, "bearing_deg": 5, "visible": True, "attacking": True},
                ],
                "pickups": [],
                "environment": {
                    "in_corridor": False,
                    "cover_available": True,
                    "cover_bearing_deg": 200,
                    "damage_taken_last_second": 2,
                },
            },
            hint={
                "action": "attack_nearest",
                "threat": 1.2,
                "should_disengage": 0.06,
                "ammo_sufficient": 0.98,
            },
        ),
        Sample(
            id="out_of_ammo",
            name={"en": "Out of ammo under fire", "zh-TW": "彈藥耗盡且遭受攻擊"},
            state={
                "tick": 22140,
                "player": {
                    "health": 64,
                    "armor": 10,
                    "weapon": "shotgun",
                    "ammo": {"shells": 0, "cells": 0},
                },
                "enemies": [
                    {"id": "e1", "type": "cacodemon", "distance_m": 7.1, "bearing_deg": -8, "visible": True, "attacking": True},
                ],
                "pickups": [
                    {"type": "shells", "distance_m": 11.5, "bearing_deg": 160, "amount": 8},
                ],
                "environment": {
                    "in_corridor": True,
                    "cover_available": False,
                    "damage_taken_last_second": 7,
                },
            },
            hint={
                "action": "attack_nearest",
                "threat": 2.4,
                "should_disengage": 0.66,
                "ammo_sufficient": 0.02,
            },
        ),
    ],
)


# ==========================================================================
# 9. Browser agent action selection
# ==========================================================================


def build_browser_questions(state: Any) -> dict[str, Question]:
    """Build an action space indexed against the current page observation.

    Every observation produces a fresh numbered element table, and the question
    set is rebuilt from it. This is the speculative fan-out pattern applied to
    actions: the operation *and* every possible target are asked in the same
    round trip, and only the target matching the chosen operation is executed.
    Two or three decisions, one network call.
    """
    elements: list[dict[str, Any]] = []
    slots: dict[str, Any] = {}
    if isinstance(state, dict):
        raw = state.get("elements") or []
        if isinstance(raw, list):
            elements = [e for e in raw if isinstance(e, dict)]
        raw_slots = state.get("goal_slots") or {}
        if isinstance(raw_slots, dict):
            slots = raw_slots

    def describe(element: dict[str, Any]) -> str:
        parts = [str(element.get("tag", "element"))]
        if element.get("text"):
            parts.append(f'"{element["text"]}"')
        if element.get("placeholder"):
            parts.append(f'placeholder "{element["placeholder"]}"')
        if element.get("value"):
            parts.append(f'currently "{element["value"]}"')
        return " ".join(parts)

    clickable = {
        str(e.get("index")): describe(e)
        for e in elements
        if e.get("tag") in ("button", "a", "link", "checkbox", "option", "div")
    }
    typeable = {
        str(e.get("index")): describe(e)
        for e in elements
        if e.get("tag") in ("input", "textarea", "combobox")
    }

    questions: dict[str, Question] = {
        "operation": Choice(
            instructions="Which single operation moves us closest to the goal right now?",
            label="Operation",
            criteria={
                "click": "Click an element on the page.",
                "type_text": "Type a value into an input field.",
                "scroll": "Scroll to reveal more of the page.",
                "wait": "Wait: the page is still loading or updating.",
                "done": "The goal has been achieved.",
                "blocked": "Progress is impossible: a captcha, a login wall, or an error.",
            },
        ),
        "page_ready": Noul(
            instructions="The page has finished loading and is ready to be interacted with.",
            label="Page ready",
            true_criteria="Content is fully rendered with no loading indicators.",
            false_criteria="A spinner, skeleton, or partial render is present.",
        ),
    }

    # These are asked unconditionally, even though at most one will be used.
    # Output tokens are free and questions run in parallel, so the extra
    # targets cost a few input tokens and no additional latency.
    if clickable:
        questions["click_target"] = Choice(
            instructions="If the operation is click, which element should be clicked?",
            label="Click target",
            criteria=clickable,
        )
    if typeable:
        questions["type_target"] = Choice(
            instructions="If the operation is type_text, which field should be typed into?",
            label="Type target",
            criteria=typeable,
        )
    if slots:
        questions["type_value"] = Choice(
            instructions=(
                "If the operation is type_text, which piece of the goal should "
                "be typed? Pick the slot, do not invent a value."
            ),
            label="Value to type",
            criteria={
                str(name): f'The goal value "{value}".'
                for name, value in slots.items()
            },
        )
    return questions


def decide_browser_action(result: DecisionResult, state: Any) -> Outcome:
    """Execute only the branch matching the chosen operation."""
    operation = result.choice("operation")
    confidence = result.confidence("operation")
    slots = state.get("goal_slots", {}) if isinstance(state, dict) else {}

    trace = [
        f"url={state.get('url') if isinstance(state, dict) else '?'}",
        f"operation={operation!r} confidence={confidence:.2f} "
        f"page_ready={result.noul('page_ready'):.2f}",
        "speculative targets returned in the same call: "
        f"click_target={result.choice('click_target') or '-'} "
        f"type_target={result.choice('type_target') or '-'} "
        f"type_value={result.choice('type_value') or '-'}",
    ]

    if result.noul("page_ready") < 0.4 and operation not in ("wait", "blocked"):
        trace.append("-> page is not ready, waiting instead of acting on a stale DOM")
        return Outcome("wait", "info", trace, {"Override": "page not ready"})

    if operation == "blocked":
        return Outcome("blocked", "error", trace)
    if operation == "done":
        return Outcome("done", "success", trace)
    if operation == "wait":
        return Outcome("wait", "info", trace)
    if operation == "scroll":
        return Outcome("scroll", "info", trace)

    if operation == "click":
        target = result.choice("click_target")
        if not target:
            trace.append("-> no click target available, falling back to scroll")
            return Outcome("scroll", "warning", trace)
        trace.append(f"-> executing CLICK on element {target}")
        return Outcome("click", "success", trace, {"Element": f"#{target}"})

    if operation == "type_text":
        target = result.choice("type_target")
        slot = result.choice("type_value")
        if not target or not slot:
            trace.append("-> missing a target or a value slot, waiting")
            return Outcome("wait", "warning", trace)
        # Jev picks the slot; the literal string comes from our own goal state.
        # The model never generates the text that gets typed.
        value = slots.get(slot, "")
        trace.append(f"-> executing TYPE {value!r} into element {target}")
        return Outcome(
            "type_text", "success", trace,
            {"Element": f"#{target}", "Value": str(value)},
        )

    return Outcome("wait", "warning", trace)


BROWSER_CASE = UseCase(
    id="browser_agent",
    icon=":material/ads_click:",
    title={"en": "Browser agent action picker", "zh-TW": "瀏覽器代理動作選擇"},
    category={"en": "Real-time control", "zh-TW": "即時控制"},
    summary={
        "en": (
            "Each observation turns the page into a numbered element table. One "
            "call picks the operation *and* every candidate target at once; code "
            "executes only the branch that matches."
        ),
        "zh-TW": (
            "每次觀察都會把頁面轉換成一份編號的元素表。單次呼叫同時選出操作類型"
            "**以及**所有候選目標，再由程式碼只執行相符的那個分支。"
        ),
    },
    why={
        "en": (
            "This is speculative fan-out applied to actions, and it is the trick "
            "behind the launch-week browser agent that booked a real flight in "
            "7.1 seconds for $0.0039, page loads included.\n\n"
            "Asking for the click target, the type target, and the value slot "
            "unconditionally looks wasteful until you remember two things: "
            "questions are answered in parallel, so the extra ones add almost no "
            "time, and output tokens are free, so they add almost no cost. "
            "Waiting for a second round trip to ask \"and what should I click?\" "
            "would cost far more than asking up front and discarding the answer.\n\n"
            "The `type_value` question is the interesting constraint. Jev cannot "
            "generate text, so it does not write the string to type — it "
            "*selects which slot of our own goal state* to type. The literal "
            "value always comes from our code, which is exactly why nothing can "
            "be hallucinated into a form field."
        ),
        "zh-TW": (
            "這是把「推測式扇出」（speculative fan-out）套用在動作上，"
            "也正是發布週那個瀏覽器代理背後的訣竅 ——"
            "它在 7.1 秒內、花費 0.0039 美元（含頁面載入時間）完成了真實的機票預訂。\n\n"
            "無條件詢問點擊目標、輸入目標與值欄位，乍看之下很浪費，"
            "但別忘了兩件事：問題是平行回答的，因此多問幾題幾乎不增加時間；"
            "而輸出 token 免費，因此幾乎不增加成本。"
            "若為了問「那我該點哪裡？」而多等一次往返，代價遠高於一次問完再丟棄不用的答案。\n\n"
            "`type_value` 這個問題體現了一個有趣的限制。Jev 無法生成文字，"
            "所以它並不撰寫要輸入的字串 —— 它是**從我們自己的目標狀態中挑選要填入哪個欄位**。"
            "實際的字面值永遠來自我們的程式碼，這正是為什麼不可能有幻覺內容被填進表單。"
        ),
    },
    questions_builder=build_browser_questions,
    actions={
        "click": {"en": "Clicked the selected element", "zh-TW": "已點擊選定的元素"},
        "type_text": {"en": "Typed a goal value into the selected field", "zh-TW": "已將目標值輸入選定欄位"},
        "scroll": {"en": "Scrolled to reveal more of the page", "zh-TW": "已捲動頁面以顯示更多內容"},
        "wait": {"en": "Waited for the page to settle", "zh-TW": "等待頁面穩定"},
        "done": {"en": "Goal achieved, loop exited", "zh-TW": "目標達成，結束迴圈"},
        "blocked": {"en": "Blocked — handed to a human", "zh-TW": "受阻 —— 轉交人工處理"},
    },
    decide=decide_browser_action,
    samples=[
        Sample(
            id="flight_search",
            name={"en": "Flight search, empty form", "zh-TW": "機票搜尋、表單為空"},
            state={
                "goal": "Book the cheapest direct flight from Zurich to London on 14 October 2026",
                "goal_slots": {
                    "origin": "Zurich",
                    "destination": "London",
                    "depart_date": "2026-10-14",
                },
                "url": "https://www.example-flights.com/",
                "step": 1,
                "elements": [
                    {"index": 1, "tag": "input", "placeholder": "Where from?", "value": ""},
                    {"index": 2, "tag": "input", "placeholder": "Where to?", "value": ""},
                    {"index": 3, "tag": "input", "placeholder": "Departure date", "value": ""},
                    {"index": 4, "tag": "button", "text": "Search flights"},
                    {"index": 5, "tag": "checkbox", "text": "Direct flights only"},
                    {"index": 6, "tag": "a", "text": "Sign in"},
                    {"index": 7, "tag": "button", "text": "Accept all cookies"},
                ],
                "loading_indicators": [],
            },
            hint={
                "operation": "type_text",
                "page_ready": 0.94,
                "click_target": "7",
                "type_target": "1",
                "type_value": "origin",
            },
        ),
        Sample(
            id="results_page",
            name={"en": "Results loaded, ready to filter", "zh-TW": "結果已載入、準備套用篩選"},
            state={
                "goal": "Book the cheapest direct flight from Zurich to London on 14 October 2026",
                "goal_slots": {
                    "origin": "Zurich",
                    "destination": "London",
                    "depart_date": "2026-10-14",
                },
                "url": "https://www.example-flights.com/search?from=ZRH&to=LON&date=2026-10-14",
                "step": 6,
                "elements": [
                    {"index": 1, "tag": "checkbox", "text": "Direct flights only"},
                    {"index": 2, "tag": "button", "text": "Sort: Cheapest"},
                    {"index": 3, "tag": "button", "text": "Sort: Fastest"},
                    {"index": 4, "tag": "div", "text": "ZRH 07:10 → LCY 08:05 · direct · CHF 118"},
                    {"index": 5, "tag": "div", "text": "ZRH 11:40 → LHR 12:35 · 1 stop · CHF 96"},
                    {"index": 6, "tag": "div", "text": "ZRH 18:20 → LGW 19:20 · direct · CHF 134"},
                    {"index": 7, "tag": "button", "text": "Select"},
                ],
                "loading_indicators": [],
            },
            hint={
                "operation": "click",
                "page_ready": 0.96,
                "click_target": "1",
                "type_target": None,
                "type_value": "destination",
            },
        ),
        Sample(
            id="still_loading",
            name={"en": "Page still loading", "zh-TW": "頁面仍在載入"},
            state={
                "goal": "Book the cheapest direct flight from Zurich to London on 14 October 2026",
                "goal_slots": {
                    "origin": "Zurich",
                    "destination": "London",
                    "depart_date": "2026-10-14",
                },
                "url": "https://www.example-flights.com/search?from=ZRH&to=LON&date=2026-10-14",
                "step": 5,
                "elements": [
                    {"index": 1, "tag": "div", "text": "Searching 480 airlines…"},
                    {"index": 2, "tag": "button", "text": "Cancel search"},
                ],
                "loading_indicators": ["progress_bar", "skeleton_rows"],
            },
            hint={
                "operation": "wait",
                "page_ready": 0.05,
                "click_target": "2",
                "type_target": None,
                "type_value": "origin",
            },
        ),
        Sample(
            id="captcha",
            name={"en": "Blocked by a captcha", "zh-TW": "遭 CAPTCHA 阻擋"},
            state={
                "goal": "Book the cheapest direct flight from Zurich to London on 14 October 2026",
                "goal_slots": {
                    "origin": "Zurich",
                    "destination": "London",
                    "depart_date": "2026-10-14",
                },
                "url": "https://www.example-flights.com/challenge",
                "step": 7,
                "elements": [
                    {"index": 1, "tag": "div", "text": "Verify you are human"},
                    {"index": 2, "tag": "checkbox", "text": "I'm not a robot"},
                    {"index": 3, "tag": "div", "text": "Select all squares containing a bus"},
                ],
                "loading_indicators": [],
            },
            hint={
                "operation": "blocked",
                "page_ready": 0.9,
                "click_target": "2",
                "type_target": None,
                "type_value": "origin",
            },
        ),
    ],
)


CASES = [GAME_CASE, BROWSER_CASE]
