from collections import Counter
from itertools import combinations
from typing import Any


def label_opponent_core(cards: list[str]) -> str:
    names = set(cards)
    if {"Mega Knight", "Inferno Tower"}.issubset(names):
        return "Mega Knight control-ish"
    if {"Goblin Barrel", "Princess"}.issubset(names) or {"Princess", "Inferno Tower"}.issubset(names):
        return "Inferno Tower bait-ish"
    if {"Lava Hound", "Balloon"}.issubset(names) or {"Balloon", "Baby Dragon"}.issubset(names):
        return "Heavy air pressure"
    if "Tornado" in names:
        return "Tornado control"
    if {"Tesla", "X-Bow"}.issubset(names) or {"Inferno Tower", "Knight"}.issubset(names):
        return "Building defence shell"
    if "Golem" in names or "Giant" in names:
        return "Giant beatdown-ish"
    return "Recurring opponent shell"


def most_common_loss_core(loss_decks: list[list[str]]) -> tuple[list[str], int]:
    counts: Counter[tuple[str, ...]] = Counter()
    for deck in loss_decks:
        for combo in combinations(sorted(set(deck)), 3):
            counts[combo] += 1
    if not counts:
        return [], 0
    core, count = counts.most_common(1)[0]
    return list(core), count

