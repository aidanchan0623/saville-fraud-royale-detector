import random
from typing import Any

from app.rules.roast_templates import ROAST_TEMPLATES


class RoastEngine:
    def render(
        self,
        rule_id: str,
        title: str,
        evidence: list[str],
        confidence: str,
        relevant_cards: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
        seed: str | int | None = None,
        goblin_mode: bool = False,
    ) -> dict[str, Any]:
        relevant_cards = relevant_cards or []
        metrics = metrics or {}
        templates = ROAST_TEMPLATES.get(rule_id, {}).get("goblin" if goblin_mode else "clean")
        if not templates:
            templates = ["Based on recent deck and matchup patterns, the evidence is suspicious."]
        rng = random.Random(f"{seed}:{rule_id}:{title}:{goblin_mode}")
        text = rng.choice(templates).format(**metrics)
        plain_explanation = metrics.get(
            "plain_explanation",
            "This claim is based on recent deck composition, battle outcomes, card levels, or matchup patterns.",
        )
        return {
            "rule_id": rule_id,
            "title": title,
            "text": text,
            "funny_description": text,
            "plain_language_explanation": plain_explanation,
            "evidence": evidence,
            "confidence": confidence,
            "relevant_cards": relevant_cards,
            "metrics": metrics,
        }
