from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import unquote


PERSONAL_DECK_EXCLUSION_KEYWORDS = {
    "2v2",
    "2 vs 2",
    "draft",
    "triple draft",
    "mega draft",
    "predefined",
    "event",
    "challenge",
    "tournament",
    "friendly",
    "clan",
    "boat",
    "duel",
    "touchdown",
    "party",
    "heist",
    "ramp up",
    "sudden death",
    "mirror",
    "capture",
    "rage battle",
}

LEVEL_EXCLUSION_KEYWORDS = PERSONAL_DECK_EXCLUSION_KEYWORDS | {
    "capped",
    "level cap",
    "tournament standard",
    "equalized",
    "equalised",
}

PERSONAL_DECK_ALLOWED_HINTS = {
    "pvp",
    "ladder",
    "path",
    "ranked",
    "league",
    "trophy",
}


def normalize_player_tag(tag: str) -> str:
    decoded = unquote(str(tag)).strip().upper()
    decoded = decoded.replace("#", "")
    return re.sub(r"[^A-Z0-9]", "", decoded)


def normalize_card_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def card_identity(card: dict[str, Any] | str) -> str:
    if isinstance(card, dict):
        identifier = card.get("id")
        if identifier is not None:
            return f"id:{identifier}"
        return f"name:{normalize_card_name(card.get('name', ''))}"
    return f"name:{normalize_card_name(str(card))}"


def deck_key(deck: list[dict[str, Any] | str]) -> tuple[str, ...]:
    return tuple(sorted(card_identity(card) for card in deck if card_identity(card)))


def deck_names(deck: list[dict[str, Any] | str]) -> list[str]:
    return [card.get("name", "") if isinstance(card, dict) else str(card) for card in deck]


def cards_from_side(side: dict[str, Any]) -> list[dict[str, Any]]:
    return [card for card in side.get("cards", []) if isinstance(card, dict)]


def parse_battle_time(value: str) -> datetime:
    if not value:
        return datetime.min
    cleaned = value.replace("Z", "+00:00")
    if len(value) >= 8 and "T" in value and "-" not in value[:8]:
        cleaned = f"{value[:4]}-{value[4:6]}-{value[6:8]}T{value[9:]}"
        cleaned = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return datetime.min


def battle_mode_text(battle: dict[str, Any]) -> str:
    pieces: list[str] = []
    for key in ("type", "challengeTitle", "deckSelection", "gameMode"):
        value = battle.get(key)
        if isinstance(value, dict):
            pieces.extend(str(item) for item in value.values())
        elif value is not None:
            pieces.append(str(value))
    return " ".join(pieces).lower()


def contains_keyword(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


@dataclass(frozen=True)
class NormalizedBattle:
    raw: dict[str, Any]
    original_index: int
    battle_time: str
    chronological_time: datetime
    mode_text: str
    player_side: dict[str, Any] = field(default_factory=dict)
    opponent_side: dict[str, Any] = field(default_factory=dict)
    player_deck: list[dict[str, Any]] = field(default_factory=list)
    opponent_deck: list[dict[str, Any]] = field(default_factory=list)
    player_deck_key: tuple[str, ...] = field(default_factory=tuple)
    opponent_deck_key: tuple[str, ...] = field(default_factory=tuple)
    result: str = "unknown"
    player_crowns: int = 0
    opponent_crowns: int = 0
    eligible_personal_deck: bool = False
    eligible_level: bool = False
    exclusion_reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def player_deck_names(self) -> list[str]:
        return deck_names(self.player_deck)

    @property
    def opponent_deck_names(self) -> list[str]:
        return deck_names(self.opponent_deck)


def find_player_side(player_tag: str, battle: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_player_tag(player_tag)
    for side in battle.get("team", []) or []:
        if normalize_player_tag(side.get("tag", "")) == normalized:
            return side
    return {}


def level_known(deck: list[dict[str, Any]]) -> bool:
    return len(deck) == 8 and all(card.get("level") is not None for card in deck)


def normalize_battle(player_tag: str, battle: dict[str, Any], index: int = 0) -> NormalizedBattle:
    mode_text = battle_mode_text(battle)
    team = battle.get("team", []) or []
    opponents = battle.get("opponent", []) or []
    player_side = find_player_side(player_tag, battle)
    opponent_side = opponents[0] if len(opponents) == 1 else {}
    player_deck = cards_from_side(player_side)
    opponent_deck = cards_from_side(opponent_side)
    reasons: list[str] = []

    if not player_side:
        reasons.append("searched player not found in team")
    if len(team) != 1 or len(opponents) != 1:
        reasons.append("not a standard 1v1 battle")
    if contains_keyword(mode_text, PERSONAL_DECK_EXCLUSION_KEYWORDS):
        reasons.append("mode excluded from personal-deck analysis")
    if len(player_deck) != 8:
        reasons.append("searched player deck incomplete")
    if len(opponent_deck) != 8:
        reasons.append("opponent deck incomplete")
    if mode_text and not contains_keyword(mode_text, PERSONAL_DECK_ALLOWED_HINTS) and "pvp" not in mode_text:
        if "type" in battle:
            reasons.append("mode lacks personal ladder/ranked hint")

    player_crowns = int(player_side.get("crowns", 0) or 0)
    opponent_crowns = int(opponent_side.get("crowns", 0) or 0)
    if player_crowns > opponent_crowns:
        result = "win"
    elif player_crowns < opponent_crowns:
        result = "loss"
    elif player_side:
        result = "draw"
    else:
        result = "unknown"

    eligible_personal_deck = not reasons
    level_reasons = list(reasons)
    if contains_keyword(mode_text, LEVEL_EXCLUSION_KEYWORDS):
        level_reasons.append("mode excluded from level analysis")
    if not level_known(player_deck) or not level_known(opponent_deck):
        level_reasons.append("card levels incomplete")

    return NormalizedBattle(
        raw=battle,
        original_index=index,
        battle_time=str(battle.get("battleTime", "")),
        chronological_time=parse_battle_time(str(battle.get("battleTime", ""))),
        mode_text=mode_text,
        player_side=player_side,
        opponent_side=opponent_side,
        player_deck=player_deck,
        opponent_deck=opponent_deck,
        player_deck_key=deck_key(player_deck),
        opponent_deck_key=deck_key(opponent_deck),
        result=result,
        player_crowns=player_crowns,
        opponent_crowns=opponent_crowns,
        eligible_personal_deck=eligible_personal_deck,
        eligible_level=not level_reasons,
        exclusion_reasons=tuple(dict.fromkeys(level_reasons if not eligible_personal_deck else reasons)),
    )


def normalize_battles(player_tag: str, battles: list[dict[str, Any]]) -> list[NormalizedBattle]:
    normalized = [normalize_battle(player_tag, battle, index) for index, battle in enumerate(battles)]
    return sorted(normalized, key=lambda item: (item.chronological_time, item.original_index))


def eligible_personal_battles(normalized: list[NormalizedBattle]) -> list[NormalizedBattle]:
    return [battle for battle in normalized if battle.eligible_personal_deck]


def eligible_level_battles(normalized: list[NormalizedBattle]) -> list[NormalizedBattle]:
    return [battle for battle in normalized if battle.eligible_level]


def shared_card_count(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    return len(set(left) & set(right))


def material_deck_change(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    return shared_card_count(left, right) <= 5


def same_or_minor_variation(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    return shared_card_count(left, right) >= 6
