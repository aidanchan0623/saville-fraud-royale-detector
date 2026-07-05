from typing import Any, Literal

from pydantic import BaseModel, Field


Confidence = Literal["low", "medium", "high"]


class Roast(BaseModel):
    rule_id: str
    title: str
    text: str
    funny_description: str | None = None
    plain_language_explanation: str | None = None
    evidence: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"
    relevant_cards: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class StructuredEvidence(BaseModel):
    id: str
    title: str
    observation: str
    sample_size: int = 0
    confidence: Confidence = "low"
    score_impact: int = 0
    roast_key: str
    roast_text: str
    receipts: list[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    schema_version: str
    player_summary: dict[str, Any]
    battle_summary: dict[str, Any]
    deck_analysis: dict[str, Any]
    deck_personality: dict[str, Any]
    matchup_analysis: dict[str, Any]
    level_analysis: dict[str, Any]
    behaviour_analysis: dict[str, Any]
    clutch_analysis: dict[str, Any]
    divorce_recommendation: dict[str, Any]
    favourite_card_analysis: dict[str, Any]
    feared_card_analysis: dict[str, Any]
    win_rate_verdict: dict[str, Any]
    roast_narrative: dict[str, Any]
    roast_modules: list[dict[str, Any]]
    card_evidence_gallery: list[dict[str, Any]]
    structured_evidence: list[StructuredEvidence] = Field(default_factory=list)
    fraud_score: dict[str, Any]
    personality_report: dict[str, Any]
    roast_report: dict[str, Any]
    roasts: list[Roast]
    disclaimer: str
