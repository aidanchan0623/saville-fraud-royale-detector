from typing import Any, Literal

from pydantic import BaseModel, Field


Confidence = Literal["low", "medium", "high"]


class Roast(BaseModel):
    rule_id: str
    title: str
    text: str
    evidence: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"
    relevant_cards: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    player_summary: dict[str, Any]
    battle_summary: dict[str, Any]
    deck_analysis: dict[str, Any]
    matchup_analysis: dict[str, Any]
    level_analysis: dict[str, Any]
    behaviour_analysis: dict[str, Any]
    clutch_analysis: dict[str, Any]
    divorce_recommendation: dict[str, Any]
    roast_report: dict[str, Any]
    roasts: list[Roast]
    disclaimer: str

