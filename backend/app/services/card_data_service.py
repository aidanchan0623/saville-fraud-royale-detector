import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


class CardDataService:
    def __init__(self, cards_path: Path | None = None) -> None:
        self.cards_path = cards_path or settings.data_dir / "cards.json"
        self.cards = self._load_cards()
        self.by_name = {card["name"]: card for card in self.cards}
        self.by_key = {_key(card["name"]): card for card in self.cards}

    def _load_cards(self) -> list[dict[str, Any]]:
        with self.cards_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def get(self, name: str) -> dict[str, Any]:
        found = self.by_name.get(name) or self.by_key.get(_key(name))
        if found:
            return {**found, "metadata_complete": True}
        return {
            "name": name,
            "elixir": None,
            "type": "unknown",
            "rarity": "common",
            "traits": [],
            "metadata_complete": False,
        }

    def hydrate_deck(self, names: list[str], level: int = 13) -> list[dict[str, Any]]:
        deck = []
        for name in names:
            card = self.get(name)
            deck.append(
                {
                    "name": card["name"],
                    "level": level,
                    "maxLevel": 14,
                    "elixir": card.get("elixir") or 4,
                    "type": card["type"],
                    "rarity": card["rarity"],
                    "traits": card.get("traits", []),
                    "metadata_complete": card.get("metadata_complete", True),
                }
            )
        return deck


@lru_cache
def get_card_service() -> CardDataService:
    return CardDataService()
