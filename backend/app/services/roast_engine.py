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
        return {
            "rule_id": rule_id,
            "title": title,
            "text": text,
            "evidence": evidence,
            "confidence": confidence,
            "relevant_cards": relevant_cards,
            "metrics": metrics,
        }

