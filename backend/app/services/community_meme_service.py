from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings
from app.rules.deck_roast_composer import META_DECKS
from app.rules.expression_selector import ExpressionSelector
from app.services.battle_normalizer import normalize_card_name


COMMUNITY_MEME_DISCLAIMER = (
    "Community Meme Score reflects recurring player-community jokes about card packages. "
    "It is not an objective measure of skill."
)
COMMUNITY_MEME_MAX_SCORE = 45


def _card_name(card: dict[str, Any] | str) -> str:
    return card.get("name", "") if isinstance(card, dict) else str(card)


def _deck_names(deck: list[dict[str, Any] | str]) -> list[str]:
    return [name for card in deck if (name := _card_name(card))]


def _name_key(name: str) -> str:
    return normalize_card_name(name)


@lru_cache
def load_community_meme_taxonomy(path: str | Path | None = None) -> dict[str, Any]:
    taxonomy_path = Path(path) if path else settings.data_dir / "community_meme_taxonomy.json"
    with taxonomy_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _matched_meta(deck_names: list[str]) -> dict[str, Any]:
    deck_keys = {_name_key(name) for name in deck_names}
    best = {"style_kind": "custom_signature", "matched_count": 0, "matched_deck_name": None, "family": None}
    for template in META_DECKS:
        template_keys = {_name_key(name) for name in template["cards"]}
        matched = len(deck_keys & template_keys)
        if matched > best["matched_count"]:
            best = {
                "style_kind": "exact_meta" if matched == len(template_keys) == len(deck_keys) else "meta_adjacent" if matched >= 6 else "custom_signature",
                "matched_count": matched,
                "matched_deck_name": template["name"],
                "family": template["family"],
            }
    if best["matched_count"] < 6:
        best["style_kind"] = "custom_signature"
        best["matched_deck_name"] = None
        best["family"] = None
    return best


def _score_band(score: int, taxonomy: dict[str, Any]) -> str:
    for band in taxonomy.get("score_bands", []):
        if int(band.get("min", 0)) <= score <= int(band.get("max", 0)):
            return str(band.get("label", "Community meme evidence"))
    return "Community meme evidence"


def _confidence(score: int, matched_cards: int, matched_combinations: int, deck_size: int) -> str:
    if deck_size < 8 or matched_cards == 0:
        return "low"
    if matched_combinations or score >= 25 or matched_cards >= 3:
        return "high"
    if matched_cards >= 2 or score >= 9:
        return "medium"
    return "low"


def _score_single_deck(deck: list[dict[str, Any] | str], taxonomy: dict[str, Any], deck_label: str, selector: ExpressionSelector) -> dict[str, Any]:
    names = _deck_names(deck)
    name_keys = {_name_key(name): name for name in names}
    cards_by_key = {_name_key(card.get("name", "")): card for card in taxonomy.get("cards", [])}
    combos = taxonomy.get("combinations", [])

    matched_cards = []
    for key, original_name in name_keys.items():
        entry = cards_by_key.get(key)
        if entry:
            matched_cards.append({**entry, "resolved_name": original_name})
    matched_cards = sorted(matched_cards, key=lambda item: int(item.get("meme_weight", 0)), reverse=True)

    categories = []
    base = 0.0
    for index, item in enumerate(matched_cards):
        weight = float(item.get("meme_weight", 0))
        if index == 0:
            base += min(weight, 8)
        elif index == 1:
            base += weight * 0.75
        elif index == 2:
            base += weight * 0.55
        else:
            base += weight * 0.35
        categories.extend(str(category) for category in item.get("categories", []))

    matched_combinations = []
    for combo in combos:
        combo_keys = {_name_key(name) for name in combo.get("cards", [])}
        if combo_keys and combo_keys <= set(name_keys):
            matched_combinations.append(combo)
            base += float(combo.get("bonus", 0))
            categories.append(str(combo.get("category", "combination")))

    meta = _matched_meta(names)
    category_set = set(categories)
    coherent_meta = meta.get("style_kind") == "exact_meta"
    annoying_meta = bool(category_set & {"bait_menace", "copy_paste_meta", "annoyance_engine", "tower_pressure_spam"})
    if coherent_meta and base:
        base *= 0.7 if (matched_combinations and annoying_meta) else 0.55
    elif meta.get("style_kind") == "meta_adjacent" and base:
        base *= 0.85

    group_project = False
    if len(category_set) >= 3 and meta.get("style_kind") == "custom_signature" and len(matched_cards) >= 3:
        base += 6
        group_project = True
        categories.append("group_project_deck")

    score = max(0, min(COMMUNITY_MEME_MAX_SCORE, round(base)))
    top_source = matched_combinations[0] if matched_combinations else matched_cards[0] if matched_cards else None
    directions = top_source.get("roast_directions", []) if top_source else []
    roast = selector.choose(directions, f"community-meme:{deck_label}:{score}") if directions else "No community meme package crossed the evidence line."

    evidence = [
        f"{deck_label.title()} deck cards reviewed: {len(names)}",
        f"Community meme cards matched: {', '.join(item['resolved_name'] for item in matched_cards) if matched_cards else 'none'}",
        f"Community meme packages matched: {', '.join(combo.get('id', 'package') for combo in matched_combinations) if matched_combinations else 'none'}",
    ]
    if meta.get("style_kind") == "exact_meta":
        evidence.append(f"Recognised exact meta deck: {meta.get('matched_deck_name')}; meme weighting reduced for coherent archetype context.")
    elif meta.get("style_kind") == "meta_adjacent":
        evidence.append(f"Meta-adjacent shell detected: {meta.get('family')}; meme weighting reduced slightly.")
    if group_project:
        evidence.append("Group Project Deck bonus applied because several unrelated meme categories were stacked without a recognised exact archetype.")
    evidence.append(taxonomy.get("disclaimer") or COMMUNITY_MEME_DISCLAIMER)

    return {
        "score": score,
        "raw_score": round(base, 2),
        "max_score": COMMUNITY_MEME_MAX_SCORE,
        "label": "Community Meme Deck Score",
        "display_label": "Community Meme Score",
        "confidence": _confidence(score, len(matched_cards), len(matched_combinations), len(names)),
        "sample_size": len(names),
        "matched_card_count": len(matched_cards),
        "matched_cards": [item["resolved_name"] for item in matched_cards],
        "matched_combinations": [combo.get("id", "package") for combo in matched_combinations],
        "categories": sorted(set(categories)),
        "roast": roast,
        "description": "Community meme deck tags with exact-meta dampening and package bonuses.",
        "evidence": evidence,
        "score_receipt": f"Community Meme Score: {score}/{COMMUNITY_MEME_MAX_SCORE} from {len(matched_cards)} meme-tagged card(s) and {len(matched_combinations)} package bonus(es).",
        "band": _score_band(score, taxonomy),
        "deck_label": deck_label,
        "meta_context": meta,
        "disclaimer": taxonomy.get("disclaimer") or COMMUNITY_MEME_DISCLAIMER,
    }


def analyse_community_meme_deck(deck_analysis: dict[str, Any], selector: ExpressionSelector | None = None) -> dict[str, Any]:
    taxonomy = load_community_meme_taxonomy()
    active_selector = selector or ExpressionSelector("community-meme-fallback")
    current_deck = deck_analysis.get("current_deck", [])
    recent = deck_analysis.get("recent_main_deck", {}) or {}
    recent_deck = recent.get("card_details") or recent.get("cards") or []

    scored = [
        _score_single_deck(current_deck, taxonomy, "current", active_selector),
    ]
    if recent_deck and {_name_key(name) for name in _deck_names(recent_deck)} != {_name_key(name) for name in _deck_names(current_deck)}:
        scored.append(_score_single_deck(recent_deck, taxonomy, "recent main", active_selector))

    winner = max(scored, key=lambda item: (item["score"], item["matched_card_count"], item["sample_size"]))
    if len(scored) > 1:
        winner = {
            **winner,
            "compared_decks": [
                {
                    "deck_label": item["deck_label"],
                    "score": item["score"],
                    "matched_cards": item["matched_cards"],
                    "matched_combinations": item["matched_combinations"],
                }
                for item in scored
            ],
        }
    return winner
