from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from app.rules.behaviour_rules import choose_behaviour_title
from app.rules.deck_rules import choose_deck_personality, deck_identity_score, estimate_deck_style
from app.rules.matchup_rules import label_opponent_core, most_common_loss_core
from app.services.card_data_service import CardDataService, get_card_service
from app.services.roast_engine import RoastEngine


def normalize_player_tag(tag: str) -> str:
    decoded = unquote(str(tag)).strip().upper()
    decoded = decoded.replace("#", "")
    return re.sub(r"[^A-Z0-9]", "", decoded)


def card_name(card: dict[str, Any] | str) -> str:
    return card.get("name", "") if isinstance(card, dict) else str(card)


def cards_from_side(side: dict[str, Any]) -> list[dict[str, Any]]:
    return [card for card in side.get("cards", []) if isinstance(card, dict)]


def deck_names(deck: list[dict[str, Any] | str]) -> list[str]:
    return [card_name(card) for card in deck]


def deck_signature(deck: list[dict[str, Any] | str]) -> str:
    return "|".join(sorted(deck_names(deck)))


def average_deck_elixir(deck: list[dict[str, Any] | str], card_service: CardDataService | None = None) -> float:
    service = card_service or get_card_service()
    if not deck:
        return 0.0
    total = 0.0
    for card in deck:
        if isinstance(card, dict):
            total += float(card.get("elixir") or service.get(card.get("name", ""))["elixir"])
        else:
            total += float(service.get(card)["elixir"])
    return round(total / len(deck), 2)


def average_card_level(deck: list[dict[str, Any]]) -> float:
    levels = [float(card.get("level", 0)) for card in deck if card.get("level") is not None]
    return round(sum(levels) / len(levels), 2) if levels else 0.0


def deck_similarity(deck_a: list[dict[str, Any] | str], deck_b: list[dict[str, Any] | str]) -> float:
    names_a = set(deck_names(deck_a))
    names_b = set(deck_names(deck_b))
    if not names_a and not names_b:
        return 1.0
    return round(len(names_a & names_b) / max(len(names_a), len(names_b), 1), 3)


def classify_level_disadvantage(player_deck: list[dict[str, Any]], opponent_deck: list[dict[str, Any]]) -> str:
    diff = average_card_level(player_deck) - average_card_level(opponent_deck)
    if diff <= -0.5:
        return "underlevelled"
    if diff >= 0.5:
        return "overlevelled"
    return "even"


def player_and_opponent(player_tag: str, battle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_player_tag(player_tag)
    team = battle.get("team", [])
    opponent = battle.get("opponent", [])
    player_side = next((side for side in team if normalize_player_tag(side.get("tag", "")) == normalized), team[0] if team else {})
    opponent_side = opponent[0] if opponent else {}
    return player_side, opponent_side


def battle_result(player_tag: str, battle: dict[str, Any]) -> str:
    player_side, opponent_side = player_and_opponent(player_tag, battle)
    player_crowns = int(player_side.get("crowns", 0))
    opponent_crowns = int(opponent_side.get("crowns", 0))
    if player_crowns > opponent_crowns:
        return "win"
    if player_crowns < opponent_crowns:
        return "loss"
    return "draw"


def result_bucket(result: str) -> str:
    return {"win": "wins", "loss": "losses", "draw": "draws"}[result]


def calculate_battle_summary(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "battles_analysed": len(battles),
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "win_rate": 0,
        "three_crown_wins": 0,
        "three_crown_losses": 0,
        "close_wins": 0,
        "close_losses": 0,
        "current_streak": {"type": "none", "count": 0},
        "timeline": [],
    }
    results: list[str] = []
    for battle in battles:
        player_side, opponent_side = player_and_opponent(player_tag, battle)
        player_crowns = int(player_side.get("crowns", 0))
        opponent_crowns = int(opponent_side.get("crowns", 0))
        result = battle_result(player_tag, battle)
        results.append(result)
        summary[result_bucket(result)] += 1
        if result == "win" and player_crowns == 3:
            summary["three_crown_wins"] += 1
        if result == "loss" and opponent_crowns == 3:
            summary["three_crown_losses"] += 1
        if result == "win" and player_crowns - opponent_crowns == 1:
            summary["close_wins"] += 1
        if result == "loss" and opponent_crowns - player_crowns == 1:
            summary["close_losses"] += 1
        summary["timeline"].append(
            {
                "battleTime": battle.get("battleTime", ""),
                "result": result,
                "playerCrowns": player_crowns,
                "opponentCrowns": opponent_crowns,
                "deck": deck_names(cards_from_side(player_side)),
            }
        )

    if battles:
        summary["win_rate"] = round(summary["wins"] / len(battles) * 100)
        first = results[0]
        count = 0
        for result in results:
            if result != first:
                break
            count += 1
        summary["current_streak"] = {"type": first, "count": count}
    return summary


def card_usage_stats(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"used": 0, "wins": 0, "losses": 0, "draws": 0, "signatures": set()})
    for battle in battles:
        player_side, _ = player_and_opponent(player_tag, battle)
        deck = cards_from_side(player_side)
        signature = deck_signature(deck)
        result = battle_result(player_tag, battle)
        for name in set(deck_names(deck)):
            stats[name]["used"] += 1
            stats[name][result_bucket(result)] += 1
            stats[name]["signatures"].add(signature)
    normalized: dict[str, dict[str, Any]] = {}
    for name, values in stats.items():
        used = values["used"]
        normalized[name] = {
            "card": name,
            "used": used,
            "wins": values["wins"],
            "losses": values["losses"],
            "draws": values["draws"],
            "win_rate": round(values["wins"] / used * 100) if used else 0,
            "deck_variants": len(values["signatures"]),
        }
    return normalized


def detect_emotional_support_card(player_tag: str, battles: list[dict[str, Any]], min_games: int = 4) -> dict[str, Any]:
    candidates = []
    for stat in card_usage_stats(player_tag, battles).values():
        if stat["used"] < min_games:
            continue
        if stat["win_rate"] <= 45 and stat["deck_variants"] >= 2:
            score = (50 - stat["win_rate"]) + stat["used"] * 1.5 + stat["deck_variants"] * 3
            candidates.append((score, stat))
    if not candidates:
        return {
            "detected": False,
            "title": "No emotional support card detected.",
            "text": "The player is either adaptable or has not suffered enough recently.",
            "confidence": "low",
        }
    _, stat = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {
        "detected": True,
        "card": stat["card"],
        "used": stat["used"],
        "wins": stat["wins"],
        "losses": stat["losses"],
        "win_rate": stat["win_rate"],
        "deck_variants": stat["deck_variants"],
        "confidence": "high" if stat["used"] >= 8 else "medium",
        "evidence": [
            f"Used in {stat['used']} of {len(battles)} recent battles",
            f"Win rate when used: {stat['win_rate']}%",
            f"Persisted across {stat['deck_variants']} deck variants",
        ],
    }


def rank_traumatic_opponent_cards(player_tag: str, battles: list[dict[str, Any]], min_encounters: int = 4) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"faced": 0, "wins": 0, "losses": 0, "draws": 0})
    for battle in battles:
        _, opponent_side = player_and_opponent(player_tag, battle)
        result = battle_result(player_tag, battle)
        for name in set(deck_names(cards_from_side(opponent_side))):
            stats[name]["faced"] += 1
            stats[name][result_bucket(result)] += 1

    ranked = []
    for name, value in stats.items():
        faced = value["faced"]
        losses = value["losses"]
        wins = value["wins"]
        loss_rate = round(losses / faced * 100) if faced else 0
        confidence = "high" if faced >= min_encounters else "low"
        if faced >= min_encounters and faced < min_encounters + 3:
            confidence = "medium"
        ranked.append(
            {
                "card": name,
                "faced": faced,
                "losses": losses,
                "wins": wins,
                "draws": value["draws"],
                "win_rate_against": round(wins / faced * 100) if faced else 0,
                "loss_rate": loss_rate,
                "confidence": confidence,
            }
        )
    return sorted(ranked, key=lambda item: (item["loss_rate"], item["faced"]), reverse=True)


def detect_level_analysis(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, Any]:
    losses = {"underlevelled": 0, "even": 0, "overlevelled": 0}
    details = []
    for battle in battles:
        if battle_result(player_tag, battle) != "loss":
            continue
        player_side, opponent_side = player_and_opponent(player_tag, battle)
        player_deck = cards_from_side(player_side)
        opponent_deck = cards_from_side(opponent_side)
        label = classify_level_disadvantage(player_deck, opponent_deck)
        losses[label] += 1
        details.append(
            {
                "battleTime": battle.get("battleTime", ""),
                "classification": label,
                "player_average_level": average_card_level(player_deck),
                "opponent_average_level": average_card_level(opponent_deck),
            }
        )
    total_losses = sum(losses.values())
    fraud_score = round(losses["overlevelled"] / total_losses * 100) if total_losses else 0
    if fraud_score <= 20:
        tier = "Innocent citizen"
    elif fraud_score <= 40:
        tier = "Mild suspect"
    elif fraud_score <= 60:
        tier = "Suspicious behaviour"
    elif fraud_score <= 80:
        tier = "Certified fraud"
    else:
        tier = "The cards deserve a new owner"
    return {
        "loss_counts": losses,
        "total_losses_with_levels": total_losses,
        "percentages": {
            "matchmaking_conspiracy": round(losses["underlevelled"] / total_losses * 100) if total_losses else 0,
            "fair_fight_failure": round(losses["even"] / total_losses * 100) if total_losses else 0,
            "certified_skill_issue": fraud_score,
        },
        "overlevelled_fraud_score": fraud_score,
        "tier": tier,
        "details": details,
    }


def detect_panic_switching(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, Any]:
    signatures = []
    results = []
    deck_results: dict[str, Counter] = defaultdict(Counter)
    deck_labels: dict[str, list[str]] = {}
    for battle in battles:
        player_side, _ = player_and_opponent(player_tag, battle)
        deck = cards_from_side(player_side)
        signature = deck_signature(deck)
        result = battle_result(player_tag, battle)
        signatures.append(signature)
        results.append(result)
        deck_results[signature][result] += 1
        deck_labels[signature] = deck_names(deck)

    exact_repeats = sum(1 for left, right in zip(signatures, signatures[1:]) if left == right)
    comparisons = max(len(signatures) - 1, 1)
    exact_same_rate = round(exact_repeats / comparisons * 100)
    changes_after_losses = 0
    major_changes = 0
    similarity_points = []
    for newer_index in range(len(battles) - 1):
        older_signature = signatures[newer_index + 1]
        newer_signature = signatures[newer_index]
        older_deck = deck_labels[older_signature]
        newer_deck = deck_labels[newer_signature]
        similarity = deck_similarity(older_deck, newer_deck)
        similarity_points.append(similarity)
        changed_at_least_three = similarity <= 0.625
        if changed_at_least_three:
            major_changes += 1
        if results[newer_index + 1] == "loss" and changed_at_least_three:
            changes_after_losses += 1

    main_signature, main_count = Counter(signatures).most_common(1)[0] if signatures else ("", 0)
    main_counter = deck_results[main_signature]
    main_games = sum(main_counter.values())
    main_win_rate = round(main_counter["win"] / main_games * 100) if main_games else 0
    emergency_counter = Counter()
    for signature, counter in deck_results.items():
        if signature != main_signature:
            emergency_counter.update(counter)
    emergency_games = sum(emergency_counter.values())
    emergency_win_rate = round(emergency_counter["win"] / emergency_games * 100) if emergency_games else 0
    rule_id, title = choose_behaviour_title(len(battles), len(set(signatures)), exact_same_rate / 100, changes_after_losses)
    return {
        "title": title,
        "rule_id": rule_id,
        "unique_decks": len(set(signatures)),
        "exact_same_deck_percentage": exact_same_rate,
        "core_deck_similarity_score": round((sum(similarity_points) / len(similarity_points) * 100) if similarity_points else 100),
        "major_deck_changes": major_changes,
        "changes_after_losses": changes_after_losses,
        "main_deck": deck_labels.get(main_signature, []),
        "main_deck_games": main_count,
        "main_deck_win_rate": main_win_rate,
        "emergency_deck_games": emergency_games,
        "emergency_deck_win_rate": emergency_win_rate,
        "evidence": [
            f"Used {len(set(signatures))} unique deck signatures",
            f"Changed at least 3 cards after {changes_after_losses} losses",
            f"Main deck win rate: {main_win_rate}%",
            f"Emergency deck win rate: {emergency_win_rate}%",
        ],
    }


def analyse_matchups(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, Any]:
    traumatic_cards = rank_traumatic_opponent_cards(player_tag, battles)
    losses = [battle for battle in battles if battle_result(player_tag, battle) == "loss"]
    loss_decks = [deck_names(cards_from_side(player_and_opponent(player_tag, battle)[1])) for battle in losses]
    core, core_loss_count = most_common_loss_core(loss_decks)
    core_matches = []
    for battle in battles:
        _, opponent_side = player_and_opponent(player_tag, battle)
        opponent_names = set(deck_names(cards_from_side(opponent_side)))
        if core and set(core).issubset(opponent_names):
            core_matches.append(battle)
    core_losses = sum(1 for battle in core_matches if battle_result(player_tag, battle) == "loss")
    natural_predator = {
        "label": label_opponent_core(core) if core else "No recurring predator detected",
        "core_cards": core,
        "losses": core_losses,
        "matches": len(core_matches),
        "confidence": "high" if len(core_matches) >= 6 else "medium" if len(core_matches) >= 3 else "low",
    }
    one_match = next((item for item in traumatic_cards if item["faced"] == 1 and item["losses"] == 1), None)
    complaint_without_proof = next((item for item in traumatic_cards if 1 < item["faced"] < 4 and item["loss_rate"] >= 60), None)
    return {
        "traumatic_cards": traumatic_cards[:8],
        "who_hurt_you": next((item for item in traumatic_cards if item["faced"] >= 4), traumatic_cards[0] if traumatic_cards else None),
        "one_match_trauma": one_match,
        "complaint_without_proof": complaint_without_proof,
        "natural_predator": natural_predator,
        "loss_core_count": core_loss_count,
    }


def analyse_deck(player: dict[str, Any], player_tag: str, battles: list[dict[str, Any]], card_service: CardDataService) -> dict[str, Any]:
    current_deck = player.get("currentDeck") or cards_from_side(player_and_opponent(player_tag, battles[0])[0])
    average_elixir = average_deck_elixir(current_deck, card_service)
    type_counts = Counter(card.get("type", "troop") for card in current_deck)
    style = estimate_deck_style(current_deck, average_elixir)
    identity = deck_identity_score(current_deck, style)
    usage = card_usage_stats(player_tag, battles)
    most_used = sorted(usage.values(), key=lambda item: item["used"], reverse=True)[:8]
    signatures = Counter()
    signature_to_deck = {}
    for battle in battles:
        player_side, _ = player_and_opponent(player_tag, battle)
        deck = cards_from_side(player_side)
        signature = deck_signature(deck)
        signatures[signature] += 1
        signature_to_deck[signature] = deck_names(deck)
    common_signature, common_count = signatures.most_common(1)[0] if signatures else ("", 0)
    personality = choose_deck_personality(current_deck, average_elixir)
    return {
        "current_deck": current_deck,
        "average_elixir": average_elixir,
        "composition": {
            "troops": type_counts["troop"],
            "spells": type_counts["spell"],
            "buildings": type_counts["building"],
        },
        "most_used_cards": most_used,
        "most_common_deck": {
            "cards": signature_to_deck.get(common_signature, []),
            "uses": common_count,
        },
        "estimated_deck_style": style,
        "deck_identity_score": identity,
        "personality_rule": personality,
    }


def analyse_main_character(player_tag: str, battles: list[dict[str, Any]]) -> dict[str, Any]:
    usage = sorted(card_usage_stats(player_tag, battles).values(), key=lambda item: item["used"], reverse=True)
    if not usage:
        return {}
    top = usage[0]
    return {
        "card": top["card"],
        "used": top["used"],
        "total": len(battles),
        "usage_rate": round(top["used"] / len(battles) * 100) if battles else 0,
        "win_rate": top["win_rate"],
        "persists_despite_poor_performance": top["win_rate"] < 50 and top["used"] >= max(5, len(battles) // 2),
        "evidence": [
            f"Appeared in {top['used']} of {len(battles)} recent decks",
            f"Win rate when present: {top['win_rate']}%",
        ],
    }


def analyse_clutch(summary: dict[str, Any]) -> dict[str, Any]:
    close_wins = summary["close_wins"]
    close_losses = summary["close_losses"]
    three_crown_losses = summary["three_crown_losses"]
    if close_wins >= close_losses + 3:
        rating = "Ice in veins"
    elif close_wins >= close_losses:
        rating = "Mildly composed"
    elif three_crown_losses >= max(2, summary["losses"] // 3):
        rating = "Crown donation service"
    else:
        rating = "Panic at the bridge"
    return {
        "rating": rating,
        "close_wins": close_wins,
        "close_losses": close_losses,
        "three_crown_losses": three_crown_losses,
        "three_crown_wins": summary["three_crown_wins"],
    }


def recommend_deck_divorce(player_tag: str, battles: list[dict[str, Any]], current_deck: list[dict[str, Any]]) -> dict[str, Any]:
    usage = card_usage_stats(player_tag, battles)
    current_names = {card["name"] for card in current_deck}
    candidates = []
    for name, stat in usage.items():
        if name not in current_names or stat["used"] < 5:
            continue
        if stat["win_rate"] <= 45:
            card = next((item for item in current_deck if item["name"] == name), None)
            overlap = []
            if card:
                traits = set(card.get("traits", []))
                for other in current_deck:
                    if other["name"] == name:
                        continue
                    shared = traits & set(other.get("traits", []))
                    if "splash" in shared or "anti_air" in shared or card.get("type") == other.get("type"):
                        overlap.append(other["name"])
            score = (50 - stat["win_rate"]) + stat["used"] + len(overlap)
            candidates.append((score, stat, overlap[:3]))
    if not candidates:
        return {
            "detected": False,
            "title": "No divorce recommendation.",
            "text": "Against all odds, your deck is at least internally committed to its mistakes.",
            "confidence": "low",
        }
    _, stat, overlap = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {
        "detected": True,
        "card": stat["card"],
        "used": stat["used"],
        "win_rate": stat["win_rate"],
        "overlaps_with": overlap,
        "confidence": "medium" if stat["used"] < 10 else "high",
        "evidence": [
            f"Used in {stat['used']} battles",
            f"Win rate when used: {stat['win_rate']}%",
            f"Overlaps with: {', '.join(overlap) if overlap else 'no obvious role overlap'}",
        ],
    }


def calculate_troll_score(
    battle_summary: dict[str, Any],
    deck_analysis: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    clutch_analysis: dict[str, Any],
) -> dict[str, Any]:
    components = []
    win_rate = battle_summary["win_rate"]
    if win_rate < 50:
        components.append({"label": "Poor overall win rate", "points": min(18, round((50 - win_rate) * 0.7))})
    overlevelled_points = round(level_analysis["overlevelled_fraud_score"] * 0.18)
    if overlevelled_points:
        components.append({"label": "Lost while overlevelled", "points": min(18, overlevelled_points)})
    panic_points = min(16, behaviour_analysis["changes_after_losses"] * 3)
    if panic_points:
        components.append({"label": "Repeated panic deck changes", "points": panic_points})
    if emotional_support.get("detected"):
        components.append({"label": "Emotional support card detected", "points": 12})
    if deck_analysis["deck_identity_score"] < 55:
        components.append({"label": "Deck identity crisis", "points": 15})
    close_total = clutch_analysis["close_wins"] + clutch_analysis["close_losses"]
    if close_total and clutch_analysis["close_losses"] > clutch_analysis["close_wins"]:
        components.append({"label": "Close-loss ratio", "points": min(10, round(clutch_analysis["close_losses"] / close_total * 10))})
    if battle_summary["losses"]:
        three_loss_points = min(8, round(battle_summary["three_crown_losses"] / battle_summary["losses"] * 8))
        if three_loss_points:
            components.append({"label": "Three-crown loss ratio", "points": three_loss_points})
    predator = matchup_analysis["natural_predator"]
    if predator["matches"] >= 4 and predator["losses"] >= 3:
        components.append({"label": "Weak against a recurring matchup", "points": min(14, predator["losses"] * 2)})
    if deck_analysis["average_elixir"] >= 4.6 and win_rate < 50:
        components.append({"label": "High elixir with poor results", "points": 8})
    if behaviour_analysis["main_deck_games"] >= 5 and behaviour_analysis["main_deck_win_rate"] < 45:
        components.append({"label": "Repeated low-performing deck usage", "points": 9})

    total = min(100, sum(item["points"] for item in components))
    if total <= 20:
        label = "Respectable citizen"
    elif total <= 40:
        label = "Mildly fraudulent"
    elif total <= 60:
        label = "Questionable gameplay"
    elif total <= 80:
        label = "Midladder incident"
    else:
        label = "National emergency"
    return {"score": total, "label": label, "components": components}


@dataclass
class AnalysisService:
    card_service: CardDataService
    roast_engine: RoastEngine

    def build_report(
        self,
        player: dict[str, Any],
        battles: list[dict[str, Any]],
        seed: str | int | None = None,
        goblin_mode: bool = False,
    ) -> dict[str, Any]:
        player_tag = player.get("tag", "")
        battle_summary = calculate_battle_summary(player_tag, battles)
        deck_analysis = analyse_deck(player, player_tag, battles, self.card_service)
        matchup_analysis = analyse_matchups(player_tag, battles)
        level_analysis = detect_level_analysis(player_tag, battles)
        behaviour_analysis = detect_panic_switching(player_tag, battles)
        emotional_support = detect_emotional_support_card(player_tag, battles)
        main_character = analyse_main_character(player_tag, battles)
        clutch_analysis = analyse_clutch(battle_summary)
        divorce = recommend_deck_divorce(player_tag, battles, deck_analysis["current_deck"])
        troll_score = calculate_troll_score(
            battle_summary,
            deck_analysis,
            matchup_analysis,
            level_analysis,
            behaviour_analysis,
            emotional_support,
            clutch_analysis,
        )

        roasts = []
        roasts.append(
            self.roast_engine.render(
                **deck_analysis["personality_rule"],
                metrics={"average_elixir": deck_analysis["average_elixir"]},
                seed=seed or player_tag,
                goblin_mode=goblin_mode,
            )
        )
        if emotional_support.get("detected"):
            roasts.append(
                self.roast_engine.render(
                    "EMOTIONAL_SUPPORT_CARD",
                    "EMOTIONAL SUPPORT CARD",
                    emotional_support["evidence"],
                    emotional_support["confidence"],
                    [emotional_support["card"]],
                    {"card": emotional_support["card"], "win_rate": emotional_support["win_rate"]},
                    seed or player_tag,
                    goblin_mode,
                )
            )
        hurt = matchup_analysis.get("who_hurt_you")
        if hurt:
            roasts.append(
                self.roast_engine.render(
                    "WHO_HURT_YOU",
                    "WHO HURT YOU?",
                    [
                        f"Faced {hurt['card']} {hurt['faced']} times",
                        f"Lost {hurt['losses']} of those matches",
                        f"Win rate against it: {hurt['win_rate_against']}%",
                    ],
                    hurt["confidence"],
                    [hurt["card"]],
                    {"card": hurt["card"]},
                    seed or player_tag,
                    goblin_mode,
                )
            )
        predator = matchup_analysis["natural_predator"]
        if predator["core_cards"]:
            roasts.append(
                self.roast_engine.render(
                    "NATURAL_PREDATOR",
                    "NATURAL PREDATOR",
                    [
                        f"Lost {predator['losses']} of {predator['matches']} recent battles against this card core",
                        f"Core cards: {', '.join(predator['core_cards'])}",
                    ],
                    predator["confidence"],
                    predator["core_cards"],
                    {},
                    seed or player_tag,
                    goblin_mode,
                )
            )
        roasts.append(
            self.roast_engine.render(
                "OVERLEVELLED_FRAUD",
                "BLAME ALLOCATION",
                [
                    f"Underlevelled losses: {level_analysis['loss_counts']['underlevelled']}",
                    f"Even-level losses: {level_analysis['loss_counts']['even']}",
                    f"Overlevelled losses: {level_analysis['loss_counts']['overlevelled']}",
                ],
                "high" if level_analysis["total_losses_with_levels"] >= 5 else "medium",
                [],
                {"overlevelled_losses": level_analysis["loss_counts"]["overlevelled"]},
                seed or player_tag,
                goblin_mode,
            )
        )
        roasts.append(
            self.roast_engine.render(
                behaviour_analysis["rule_id"],
                behaviour_analysis["title"],
                behaviour_analysis["evidence"],
                "high" if behaviour_analysis["changes_after_losses"] >= 4 else "medium",
                behaviour_analysis["main_deck"],
                {"changes_after_losses": behaviour_analysis["changes_after_losses"]},
                seed or player_tag,
                goblin_mode,
            )
        )
        if main_character:
            roasts.append(
                self.roast_engine.render(
                    "MAIN_CHARACTER_SYNDROME",
                    "MAIN CHARACTER SYNDROME",
                    main_character["evidence"],
                    "high" if main_character["used"] >= 10 else "medium",
                    [main_character["card"]],
                    {"card": main_character["card"], "used": main_character["used"], "total": main_character["total"]},
                    seed or player_tag,
                    goblin_mode,
                )
            )
        roasts.append(
            self.roast_engine.render(
                "CLUTCH_REPORT",
                f"CLUTCH RATING: {clutch_analysis['rating'].upper()}",
                [
                    f"Close wins: {clutch_analysis['close_wins']}",
                    f"Close losses: {clutch_analysis['close_losses']}",
                    f"Three-crown losses: {clutch_analysis['three_crown_losses']}",
                ],
                "medium",
                [],
                {},
                seed or player_tag,
                goblin_mode,
            )
        )
        if divorce.get("detected"):
            roasts.append(
                self.roast_engine.render(
                    "DECK_DIVORCE",
                    "DECK DIVORCE RECOMMENDATION",
                    divorce["evidence"],
                    divorce["confidence"],
                    [divorce["card"]],
                    {"card": divorce["card"]},
                    seed or player_tag,
                    goblin_mode,
                )
            )

        headline_roast = max(roasts, key=lambda item: (len(item["evidence"]), item["confidence"] == "high"))
        title = f"{headline_roast['title']} {troll_score['label'].upper()}".strip()

        return {
            "player_summary": {
                "name": player.get("name", "Unknown Player"),
                "tag": player.get("tag", player_tag),
                "arena": player.get("arena", {}).get("name", "Unknown Arena"),
                "trophies": player.get("trophies"),
                "player_level": player.get("expLevel"),
                "clan": player.get("clan", {}).get("name", "No clan"),
                "battles_analysed": battle_summary["battles_analysed"],
            },
            "battle_summary": battle_summary,
            "deck_analysis": {**deck_analysis, "emotional_support_card": emotional_support, "main_character": main_character},
            "matchup_analysis": matchup_analysis,
            "level_analysis": level_analysis,
            "behaviour_analysis": behaviour_analysis,
            "clutch_analysis": clutch_analysis,
            "divorce_recommendation": divorce,
            "roast_report": {
                "title": title,
                "troll_score": troll_score["score"],
                "score_label": troll_score["label"],
                "headline_roast": headline_roast["text"],
                "evidence": headline_roast["evidence"],
                "score_breakdown": troll_score["components"],
            },
            "roasts": roasts,
            "disclaimer": "Results are based on recent public battle-log deck, crown, level, and matchup data. The Clash Royale API does not provide replay footage, card placements, elixir spending, timing, or card-cast counts.",
        }


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_card_service(), RoastEngine())
