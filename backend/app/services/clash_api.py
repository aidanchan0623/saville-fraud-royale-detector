import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.analysis_service import normalize_player_tag
from app.services.card_data_service import CardDataService, get_card_service


class ClashApiService:
    def __init__(self, card_service: CardDataService | None = None, mock_path: Path | None = None) -> None:
        self.card_service = card_service or get_card_service()
        self.mock_path = mock_path or settings.data_dir / "mock_data.json"
        self._mock_data: dict[str, Any] | None = None

    async def get_player(self, tag: str) -> dict[str, Any]:
        if settings.use_mock_data:
            victim = self._find_mock_victim(tag)
            profile = dict(victim["profile"])
            profile["currentDeck"] = self.card_service.hydrate_deck(victim["currentDeck"], 13)
            return profile

        if not settings.clash_api_key:
            raise HTTPException(status_code=500, detail="CLASH_ROYALE_API_KEY is missing on the backend.")

        encoded = quote(f"#{normalize_player_tag(tag)}", safe="")
        return await self._request(f"/v1/players/{encoded}")

    async def get_battlelog(self, tag: str) -> list[dict[str, Any]]:
        if settings.use_mock_data:
            victim = self._find_mock_victim(tag)
            return self._expand_mock_battles(victim)

        if not settings.clash_api_key:
            raise HTTPException(status_code=500, detail="CLASH_ROYALE_API_KEY is missing on the backend.")

        encoded = quote(f"#{normalize_player_tag(tag)}", safe="")
        payload = await self._request(f"/v1/players/{encoded}/battlelog")
        if not payload:
            raise HTTPException(status_code=404, detail="Battle log is empty or unavailable.")
        return payload

    def list_demo_victims(self) -> list[dict[str, str]]:
        return [
            {
                "key": victim["key"],
                "label": victim["label"],
                "tag": victim["profile"]["tag"],
                "name": victim["profile"]["name"],
            }
            for victim in self._load_mock_data()["victims"]
        ]

    async def _request(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {settings.clash_api_key}"}
        try:
            async with httpx.AsyncClient(base_url=settings.clash_api_base_url, timeout=15) as client:
                response = await client.get(path, headers=headers)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail="Clash Royale API appears unavailable.") from exc

        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="API key rejected. Check token/IP restrictions.")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found. Check the player tag.")
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Clash Royale API rate limit reached.")
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail="Clash Royale API request failed.")
        return response.json()

    def _load_mock_data(self) -> dict[str, Any]:
        if self._mock_data is None:
            with self.mock_path.open("r", encoding="utf-8") as handle:
                self._mock_data = json.load(handle)
        return self._mock_data

    def _find_mock_victim(self, tag_or_key: str) -> dict[str, Any]:
        normalized = normalize_player_tag(tag_or_key)
        lowered = tag_or_key.lower().replace("#", "")
        for victim in self._load_mock_data()["victims"]:
            if normalized == normalize_player_tag(victim["profile"]["tag"]):
                return victim
            if lowered in {victim["key"].lower(), victim["label"].lower().replace(" ", "")}:
                return victim
        raise HTTPException(status_code=404, detail="Demo victim not found.")

    def _expand_mock_battles(self, victim: dict[str, Any]) -> list[dict[str, Any]]:
        battles = []
        start = datetime(2026, 6, 30, 11, 0, tzinfo=timezone.utc)
        profile = victim["profile"]
        for index, item in enumerate(victim["plan"]):
            result, deck_key, opponent_key, crowns, opponent_crowns, player_level, opponent_level = item
            player_deck = self.card_service.hydrate_deck(victim["deckVariants"][deck_key], player_level)
            opponent_deck = self.card_service.hydrate_deck(victim["opponentDecks"][opponent_key], opponent_level)
            battles.append(
                {
                    "type": "PvP",
                    "battleTime": (start - timedelta(minutes=35 * index)).strftime("%Y%m%dT%H%M%S.000Z"),
                    "isLadderTournament": False,
                    "team": [
                        {
                            "tag": profile["tag"],
                            "name": profile["name"],
                            "crowns": crowns,
                            "cards": player_deck,
                        }
                    ],
                    "opponent": [
                        {
                            "tag": f"#OPP{index:03d}",
                            "name": f"Opponent {index + 1}",
                            "crowns": opponent_crowns,
                            "cards": opponent_deck,
                        }
                    ],
                    "mockResult": result,
                }
            )
        return battles

