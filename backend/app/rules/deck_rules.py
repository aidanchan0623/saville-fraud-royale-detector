from collections import Counter
from typing import Any


def _names(deck: list[dict[str, Any]]) -> set[str]:
    return {card.get("name", str(card)) for card in deck}


def _traits(deck: list[dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for card in deck:
        counts.update(card.get("traits", []))
    return counts


def choose_deck_personality(deck: list[dict[str, Any]], average_elixir: float) -> dict[str, Any]:
    names = _names(deck)
    traits = _traits(deck)
    types = Counter(card.get("type", "troop") for card in deck)

    if {"Mega Knight", "Wizard"}.issubset(names):
        return {
            "rule_id": "PANIC_BUTTON_SPECIALIST",
            "title": "PANIC BUTTON SPECIALIST",
            "evidence": ["Current deck contains Mega Knight + Wizard", f"Average elixir: {average_elixir:.1f}"],
            "confidence": "high",
            "relevant_cards": ["Mega Knight", "Wizard"],
        }
    if "Hog Rider" in names and average_elixir <= 3.4:
        return {
            "rule_id": "CARDIO_ADDICT",
            "title": "CARDIO ADDICT",
            "evidence": ["Hog Rider present", f"Low average elixir: {average_elixir:.1f}"],
            "confidence": "high",
            "relevant_cards": ["Hog Rider"],
        }
    if "X-Bow" in names or "Mortar" in names:
        siege = "X-Bow" if "X-Bow" in names else "Mortar"
        return {
            "rule_id": "CIVIL_ENGINEERING_MENACE",
            "title": "CIVIL ENGINEERING MENACE",
            "evidence": [f"{siege} detected", "Siege win condition present"],
            "confidence": "high",
            "relevant_cards": [siege],
        }
    if {"Goblin Barrel", "Princess", "Inferno Tower"}.issubset(names):
        return {
            "rule_id": "TAX_EVASION_SPECIALIST",
            "title": "TAX EVASION SPECIALIST",
            "evidence": ["Goblin Barrel + Princess + Inferno Tower detected"],
            "confidence": "high",
            "relevant_cards": ["Goblin Barrel", "Princess", "Inferno Tower"],
        }
    if {"Elite Barbarians", "Rage"}.issubset(names):
        return {
            "rule_id": "PROBLEM_SOLVER",
            "title": "PROBLEM SOLVER",
            "evidence": ["Elite Barbarians + Rage detected"],
            "confidence": "high",
            "relevant_cards": ["Elite Barbarians", "Rage"],
        }
    if average_elixir >= 4.6:
        return {
            "rule_id": "ELIXIR_INVESTOR",
            "title": "ELIXIR INVESTOR",
            "evidence": [f"Average elixir is {average_elixir:.1f}", "Deck leans expensive"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    if traits["win_condition"] == 0:
        return {
            "rule_id": "IDENTITY_CRISIS",
            "title": "IDENTITY CRISIS",
            "evidence": ["No clear win condition detected in current deck"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    if traits["anti_air"] <= 1:
        return {
            "rule_id": "AIRSPACE_VIOLATION",
            "title": "AIRSPACE VIOLATION",
            "evidence": [f"Only {traits['anti_air']} anti-air option detected"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    if traits["small_spell"] == 0:
        return {
            "rule_id": "LOG_DENIALIST",
            "title": "LOG DENIALIST",
            "evidence": ["No small spell detected"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    if types["building"] > 1:
        return {
            "rule_id": "PROPERTY_DEVELOPER",
            "title": "PROPERTY DEVELOPER",
            "evidence": [f"{types['building']} buildings detected"],
            "confidence": "medium",
            "relevant_cards": [card["name"] for card in deck if card.get("type") == "building"],
        }
    return {
        "rule_id": "RESPECTABLE_CITIZEN",
        "title": "RESPECTABLE CITIZEN",
        "evidence": ["Current deck has a detectable win condition and basic role coverage"],
        "confidence": "low",
        "relevant_cards": [],
    }


def estimate_deck_style(deck: list[dict[str, Any]], average_elixir: float) -> str:
    names = _names(deck)
    traits = _traits(deck)
    if "Hog Rider" in names and average_elixir <= 3.4:
        return "Hog cycle-ish"
    if "X-Bow" in names or "Mortar" in names:
        return "Siege-ish"
    if {"Goblin Barrel", "Princess"}.issubset(names) or traits["bait"] >= 3:
        return "Bait-ish"
    if any(card in names for card in ["Battle Ram", "Bandit", "Royal Ghost", "Ram Rider"]):
        return "Bridge spam-ish"
    if any(card in names for card in ["Golem", "Giant", "Lava Hound"]) and average_elixir >= 4:
        return "Beatdown-ish"
    if traits["control"] >= 2 or "Miner" in names:
        return "Control-ish"
    if {"Mega Knight", "Wizard"}.issubset(names) or {"Elite Barbarians", "Rage"}.issubset(names):
        return "Midladder emergency response unit"
    if traits["win_condition"] == 0:
        return "No coherent archetype detected"
    return "Random bullshit go"


def deck_identity_score(deck: list[dict[str, Any]], style: str) -> int:
    traits = _traits(deck)
    score = 70
    if style == "No coherent archetype detected":
        score -= 35
    if style == "Random bullshit go":
        score -= 25
    if traits["win_condition"] == 0:
        score -= 25
    if traits["small_spell"] == 0:
        score -= 10
    if traits["anti_air"] <= 1:
        score -= 10
    if traits["building"] > 1:
        score -= 5
    return max(0, min(100, score))

