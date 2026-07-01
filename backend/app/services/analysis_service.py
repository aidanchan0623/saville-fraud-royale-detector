from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.rules.deck_templates import DECK_STYLE_COPY, TRAIT_EXPLANATIONS
from app.rules.expression_selector import ExpressionSelector
from app.rules.fraud_score_templates import CONTRIBUTOR_COPY, TIER_COPY
from app.rules.matchup_rules import label_opponent_core, most_common_loss_core
from app.services.battle_normalizer import (
    NormalizedBattle,
    cards_from_side,
    deck_key,
    deck_names,
    eligible_level_battles,
    eligible_personal_battles,
    material_deck_change,
    normalize_battles,
    normalize_player_tag,
    same_or_minor_variation,
    shared_card_count,
)
from app.services.card_data_service import CardDataService, get_card_service
from app.services.roast_engine import RoastEngine


REPORT_SCHEMA_VERSION = "report-v3"
LEVEL_ADVANTAGE_THRESHOLD = 0.75


def card_name(card: dict[str, Any] | str) -> str:
    return card.get("name", "") if isinstance(card, dict) else str(card)


def unique_ordered(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def as_normalized(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> list[NormalizedBattle]:
    if battles and isinstance(battles[0], NormalizedBattle):
        return battles  # type: ignore[return-value]
    return normalize_battles(player_tag, battles)  # type: ignore[arg-type]


def enrich_card(card: dict[str, Any], card_service: CardDataService | None = None) -> dict[str, Any]:
    service = card_service or get_card_service()
    metadata = service.get(card.get("name", ""))
    icon_urls = card.get("iconUrls") if isinstance(card.get("iconUrls"), dict) else {}
    elixir = card.get("elixir")
    if elixir is None:
        elixir = metadata.get("elixir")
    return {
        **metadata,
        **card,
        "elixir": elixir,
        "type": card.get("type") or metadata.get("type", "unknown"),
        "rarity": card.get("rarity") or metadata.get("rarity", "common"),
        "traits": card.get("traits") or metadata.get("traits", []),
        "metadata_complete": bool(metadata.get("metadata_complete", False)),
        "icon_url": icon_urls.get("medium") or icon_urls.get("evolutionMedium"),
    }


def deck_signature(deck: list[dict[str, Any] | str]) -> str:
    return "|".join(deck_key(deck))


def average_deck_elixir(deck: list[dict[str, Any] | str], card_service: CardDataService | None = None) -> float:
    service = card_service or get_card_service()
    costs: list[float] = []
    for card in deck:
        if isinstance(card, dict):
            cost = card.get("elixir")
            if cost is None:
                cost = service.get(card.get("name", "")).get("elixir")
        else:
            cost = service.get(card).get("elixir")
        if cost is not None:
            costs.append(float(cost))
    return round(sum(costs) / len(costs), 2) if costs else 0.0


def average_card_level(deck: list[dict[str, Any]]) -> float:
    levels = [float(card.get("level")) for card in deck if card.get("level") is not None]
    return round(sum(levels) / len(levels), 2) if levels else 0.0


def deck_similarity(deck_a: list[dict[str, Any] | str], deck_b: list[dict[str, Any] | str]) -> float:
    left = deck_key(deck_a)
    right = deck_key(deck_b)
    if not left and not right:
        return 1.0
    return round(shared_card_count(left, right) / max(len(left), len(right), 1), 3)


def classify_level_disadvantage(player_deck: list[dict[str, Any]], opponent_deck: list[dict[str, Any]]) -> str:
    diff = average_card_level(player_deck) - average_card_level(opponent_deck)
    if diff <= -LEVEL_ADVANTAGE_THRESHOLD:
        return "underlevelled"
    if diff >= LEVEL_ADVANTAGE_THRESHOLD:
        return "overlevelled"
    return "even"


def player_and_opponent(player_tag: str, battle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_battles(player_tag, [battle])[0]
    return normalized.player_side, normalized.opponent_side


def battle_result(player_tag: str, battle: dict[str, Any]) -> str:
    return normalize_battles(player_tag, [battle])[0].result


def result_bucket(result: str) -> str:
    return {"win": "wins", "loss": "losses", "draw": "draws"}.get(result, "draws")


def confidence_from_sample(sample: int, medium: int, high: int) -> str:
    if sample >= high:
        return "high"
    if sample >= medium:
        return "medium"
    return "low"


def calculate_battle_summary(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, Any]:
    normalized = [battle for battle in as_normalized(player_tag, battles) if battle.result != "unknown"]
    summary = {
        "battles_analysed": len(normalized),
        "eligible_battles": sum(1 for battle in normalized if battle.eligible_personal_deck),
        "excluded_battles": sum(1 for battle in normalized if not battle.eligible_personal_deck),
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "win_rate": 0,
        "loss_rate": 0,
        "three_crown_wins": 0,
        "three_crown_losses": 0,
        "close_wins": 0,
        "close_losses": 0,
        "current_streak": {"type": "none", "count": 0},
        "timeline": [],
    }
    results: list[str] = []
    for battle in normalized:
        result = battle.result
        results.append(result)
        summary[result_bucket(result)] += 1
        if result == "win" and battle.player_crowns == 3:
            summary["three_crown_wins"] += 1
        if result == "loss" and battle.opponent_crowns == 3:
            summary["three_crown_losses"] += 1
        if result == "win" and battle.player_crowns - battle.opponent_crowns == 1:
            summary["close_wins"] += 1
        if result == "loss" and battle.opponent_crowns - battle.player_crowns == 1:
            summary["close_losses"] += 1
        summary["timeline"].append(
            {
                "battleTime": battle.battle_time,
                "result": result,
                "playerCrowns": battle.player_crowns,
                "opponentCrowns": battle.opponent_crowns,
                "deck": battle.player_deck_names,
                "eligible": battle.eligible_personal_deck,
            }
        )

    if normalized:
        summary["win_rate"] = round(summary["wins"] / len(normalized) * 100)
        summary["loss_rate"] = round(summary["losses"] / len(normalized) * 100)
        newest_results = list(reversed(results))
        first = newest_results[0]
        count = 0
        for result in newest_results:
            if result != first:
                break
            count += 1
        summary["current_streak"] = {"type": first, "count": count}
    return summary


def cluster_decks(keys: list[tuple[str, ...]]) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for key in keys:
        for cluster in clusters:
            if same_or_minor_variation(cluster["representative"], key):
                cluster["keys"].append(key)
                break
        else:
            clusters.append({"representative": key, "keys": [key]})
    return clusters


def deck_cluster_index(clusters: list[dict[str, Any]], key: tuple[str, ...]) -> int:
    for index, cluster in enumerate(clusters):
        if same_or_minor_variation(cluster["representative"], key):
            return index
    return -1


def card_usage_stats(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, dict[str, Any]]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"used": 0, "wins": 0, "losses": 0, "draws": 0, "signatures": set()})
    for battle in eligible:
        signature = battle.player_deck_key
        for name in unique_ordered(battle.player_deck_names):
            stats[name]["used"] += 1
            stats[name][result_bucket(battle.result)] += 1
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
            "loss_rate": round(values["losses"] / used * 100) if used else 0,
            "deck_variants": len(values["signatures"]),
        }
    return normalized


def detect_emotional_support_card(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle], min_games: int = 8) -> dict[str, Any]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    baseline_wins = sum(1 for battle in eligible if battle.result == "win")
    baseline_win_rate = round(baseline_wins / len(eligible) * 100) if eligible else 0
    candidates = []
    for stat in card_usage_stats(player_tag, eligible).values():
        if stat["used"] < min_games:
            continue
        if stat["win_rate"] <= baseline_win_rate - 15 and stat["deck_variants"] >= 2:
            score = (baseline_win_rate - stat["win_rate"]) + stat["used"] + stat["deck_variants"] * 2
            candidates.append((score, stat))
    if not candidates:
        return {
            "detected": False,
            "title": "No emotional support card detected.",
            "text": f"Need a card used in at least {min_games} eligible matches with clearly below-baseline results.",
            "confidence": "low",
            "sample_size": len(eligible),
            "evidence": [f"Eligible personal-deck matches: {len(eligible)}", f"Baseline win rate: {baseline_win_rate}%"],
        }
    _, stat = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {
        "detected": True,
        "card": stat["card"],
        "used": stat["used"],
        "wins": stat["wins"],
        "losses": stat["losses"],
        "win_rate": stat["win_rate"],
        "baseline_win_rate": baseline_win_rate,
        "deck_variants": stat["deck_variants"],
        "confidence": confidence_from_sample(stat["used"], 8, 12),
        "sample_size": stat["used"],
        "evidence": [
            f"Used in {stat['used']} eligible personal-deck matches",
            f"Win rate with card: {stat['win_rate']}% versus baseline {baseline_win_rate}%",
            f"Persisted across {stat['deck_variants']} material deck signatures",
        ],
    }


def rank_traumatic_opponent_cards(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle], min_encounters: int = 5) -> list[dict[str, Any]]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    baseline_loss_rate = round(sum(1 for battle in eligible if battle.result == "loss") / len(eligible) * 100) if eligible else 0
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"faced": 0, "wins": 0, "losses": 0, "draws": 0})
    for battle in eligible:
        for name in unique_ordered(battle.opponent_deck_names):
            stats[name]["faced"] += 1
            stats[name][result_bucket(battle.result)] += 1

    ranked = []
    for name, value in stats.items():
        faced = value["faced"]
        losses = value["losses"]
        wins = value["wins"]
        loss_rate = round(losses / faced * 100) if faced else 0
        excess = loss_rate - baseline_loss_rate
        confidence = confidence_from_sample(faced, min_encounters, min_encounters + 4)
        ranked.append(
            {
                "card": name,
                "faced": faced,
                "losses": losses,
                "wins": wins,
                "draws": value["draws"],
                "win_rate_against": round(wins / faced * 100) if faced else 0,
                "loss_rate": loss_rate,
                "baseline_loss_rate": baseline_loss_rate,
                "excess_loss_rate": excess,
                "confidence": confidence if faced >= min_encounters and excess > 0 else "low",
                "evidence": [
                    f"{name} appeared in {faced} eligible matches",
                    f"Loss rate versus {name}: {loss_rate}%",
                    f"Overall eligible loss rate: {baseline_loss_rate}%",
                    f"Excess loss rate: {excess:+d} percentage points",
                ],
            }
        )
    return sorted(ranked, key=lambda item: (item["confidence"] != "low", item["excess_loss_rate"], item["faced"]), reverse=True)


def detect_level_analysis(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, Any]:
    eligible = eligible_level_battles(as_normalized(player_tag, battles))
    losses = {"underlevelled": 0, "even": 0, "overlevelled": 0}
    details = []
    diffs = []
    for battle in eligible:
        if battle.result != "loss":
            continue
        player_average = average_card_level(battle.player_deck)
        opponent_average = average_card_level(battle.opponent_deck)
        diff = round(player_average - opponent_average, 2)
        diffs.append(diff)
        label = classify_level_disadvantage(battle.player_deck, battle.opponent_deck)
        losses[label] += 1
        details.append(
            {
                "battleTime": battle.battle_time,
                "classification": label,
                "player_average_level": player_average,
                "opponent_average_level": opponent_average,
                "level_difference": diff,
            }
        )
    total_losses = sum(losses.values())
    fraud_score = round(losses["overlevelled"] / total_losses * 100) if total_losses else 0
    if total_losses < 5:
        tier = "Insufficient level evidence"
    elif fraud_score <= 20:
        tier = "No level case"
    elif fraud_score <= 40:
        tier = "Mild level suspicion"
    elif fraud_score <= 60:
        tier = "Level advantage pattern"
    elif fraud_score <= 80:
        tier = "Certified level-joke material"
    else:
        tier = "The upgrades have questions"
    return {
        "loss_counts": losses,
        "total_losses_with_levels": total_losses,
        "eligible_level_matches": len(eligible),
        "meaningful_level_advantage_losses": losses["overlevelled"],
        "average_level_difference": round(sum(diffs) / len(diffs), 2) if diffs else 0,
        "confidence": confidence_from_sample(total_losses, 5, 10),
        "percentages": {
            "matchmaking_conspiracy": round(losses["underlevelled"] / total_losses * 100) if total_losses else 0,
            "fair_fight_failure": round(losses["even"] / total_losses * 100) if total_losses else 0,
            "certified_skill_issue": fraud_score,
        },
        "overlevelled_fraud_score": fraud_score,
        "tier": tier,
        "details": details,
        "evidence": [
            f"Eligible level-known losses: {total_losses}",
            f"Meaningful level-advantage losses: {losses['overlevelled']}",
            f"Meaningful advantage threshold: +{LEVEL_ADVANTAGE_THRESHOLD:.2f} average levels",
        ],
    }


def detect_panic_switching(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, Any]:
    normalized = as_normalized(player_tag, battles)
    eligible = eligible_personal_battles(normalized)
    keys = [battle.player_deck_key for battle in eligible]
    clusters = cluster_decks(keys)
    cluster_counts = Counter(deck_cluster_index(clusters, key) for key in keys)
    main_cluster, main_count = cluster_counts.most_common(1)[0] if cluster_counts else (-1, 0)
    main_key = clusters[main_cluster]["representative"] if main_cluster >= 0 else tuple()
    main_battles = [battle for battle in eligible if main_cluster >= 0 and deck_cluster_index(clusters, battle.player_deck_key) == main_cluster]
    main_counter = Counter(battle.result for battle in main_battles)
    main_win_rate = round(main_counter["win"] / len(main_battles) * 100) if main_battles else 0
    emergency_battles = [battle for battle in eligible if main_cluster < 0 or deck_cluster_index(clusters, battle.player_deck_key) != main_cluster]
    emergency_counter = Counter(battle.result for battle in emergency_battles)
    emergency_win_rate = round(emergency_counter["win"] / len(emergency_battles) * 100) if emergency_battles else main_win_rate

    post_loss_opportunities = 0
    changes_after_losses = 0
    skipped_after_loss = 0
    for index, battle in enumerate(normalized[:-1]):
        if not battle.eligible_personal_deck or battle.result != "loss":
            continue
        next_battle = normalized[index + 1]
        if not next_battle.eligible_personal_deck:
            skipped_after_loss += 1
            continue
        post_loss_opportunities += 1
        if material_deck_change(battle.player_deck_key, next_battle.player_deck_key):
            changes_after_losses += 1

    major_deck_changes = sum(
        1
        for left, right in zip(eligible, eligible[1:])
        if material_deck_change(left.player_deck_key, right.player_deck_key)
    )
    same_core_rate = round(main_count / len(eligible) * 100) if eligible else 0
    core_similarity_points = [
        round(shared_card_count(left.player_deck_key, right.player_deck_key) / 8 * 100)
        for left, right in zip(eligible, eligible[1:])
        if len(left.player_deck_key) == 8 and len(right.player_deck_key) == 8
    ]
    exact_same_rate = round(sum(1 for key in keys if key == main_key) / len(keys) * 100) if keys else 0
    emergency_worse = bool(emergency_battles and emergency_win_rate <= main_win_rate)
    emergency_much_worse = bool(emergency_battles and emergency_win_rate <= main_win_rate - 15)

    if len(eligible) < 8:
        rule_id = "LIMITED_DATA"
        title = "LIMITED DATA"
    elif post_loss_opportunities >= 3 and changes_after_losses >= 3 and emergency_worse:
        rule_id = "PANIC_SWITCHER"
        title = "PANIC SWITCHER"
    elif major_deck_changes >= 3 and changes_after_losses >= 2 and emergency_much_worse:
        rule_id = "EMOTIONAL_DECK_BUILDER"
        title = "EMOTIONAL DECK BUILDER"
    elif len(eligible) >= 10 and len(clusters) >= 4 and same_core_rate < 60:
        rule_id = "DECK_HOPPER"
        title = "DECK HOPPER"
    elif same_core_rate >= 80:
        rule_id = "ONE_DECK_WARRIOR"
        title = "ONE-DECK WARRIOR"
    elif len(clusters) <= 2:
        rule_id = "STABLE_WITH_MINOR_VARIATIONS"
        title = "STABLE WITH MINOR VARIATIONS"
    else:
        rule_id = "FLEXIBLE_DECK_USER"
        title = "FLEXIBLE DECK USER"

    evidence = [
        f"Eligible personal-deck matches: {len(eligible)}",
        f"Materially distinct deck cores: {len(clusters)}",
        f"Dominant core usage: {main_count} of {len(eligible)} eligible matches ({same_core_rate}%)",
        f"Major deck changes after losses: {changes_after_losses} of {post_loss_opportunities} valid post-loss opportunities",
    ]
    if skipped_after_loss:
        evidence.append(f"Excluded {skipped_after_loss} loss follow-up(s) because the next match was not eligible personal-deck data")
    if rule_id not in {"PANIC_SWITCHER", "EMOTIONAL_DECK_BUILDER"}:
        evidence.append(f"Only {changes_after_losses} verified major post-loss change(s); no panic-switch verdict issued.")

    return {
        "title": title,
        "rule_id": rule_id,
        "classification": rule_id,
        "eligible_battles": len(eligible),
        "excluded_battles": len(normalized) - len(eligible),
        "unique_decks": len(clusters),
        "materially_distinct_deck_cores": len(clusters),
        "exact_same_deck_percentage": exact_same_rate,
        "same_core_percentage": same_core_rate,
        "core_deck_similarity_score": round(sum(core_similarity_points) / len(core_similarity_points)) if core_similarity_points else 100,
        "major_deck_changes": major_deck_changes,
        "post_loss_opportunities": post_loss_opportunities,
        "changes_after_losses": changes_after_losses,
        "main_deck": main_battles[-1].player_deck_names if main_battles else [],
        "main_deck_key": list(main_key),
        "main_deck_games": main_count,
        "main_deck_win_rate": main_win_rate,
        "emergency_deck_games": len(emergency_battles),
        "emergency_deck_win_rate": emergency_win_rate,
        "confidence": confidence_from_sample(len(eligible), 8, 15),
        "evidence": evidence,
    }


def analyse_matchups(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, Any]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    baseline_loss_rate = round(sum(1 for battle in eligible if battle.result == "loss") / len(eligible) * 100) if eligible else 0
    traumatic_cards = rank_traumatic_opponent_cards(player_tag, eligible)
    losses = [battle for battle in eligible if battle.result == "loss"]
    loss_decks = [battle.opponent_deck_names for battle in losses]
    core, core_loss_count = most_common_loss_core(loss_decks)
    core_matches = []
    for battle in eligible:
        opponent_names = set(battle.opponent_deck_names)
        if core and set(core).issubset(opponent_names):
            core_matches.append(battle)
    core_losses = sum(1 for battle in core_matches if battle.result == "loss")
    core_loss_rate = round(core_losses / len(core_matches) * 100) if core_matches else 0
    core_excess = core_loss_rate - baseline_loss_rate
    natural_predator = {
        "label": f"Potential {label_opponent_core(core)}" if len(core_matches) >= 4 and core_excess > 0 else "No recurring opponent core with enough evidence",
        "core_cards": core if len(core_matches) >= 4 and core_excess > 0 else [],
        "losses": core_losses,
        "matches": len(core_matches),
        "loss_rate": core_loss_rate,
        "baseline_loss_rate": baseline_loss_rate,
        "excess_loss_rate": core_excess,
        "confidence": confidence_from_sample(len(core_matches), 4, 8) if core_excess > 0 else "low",
        "evidence": [
            f"Core faced in {len(core_matches)} eligible matches",
            f"Loss rate versus core: {core_loss_rate}%",
            f"Overall eligible loss rate: {baseline_loss_rate}%",
            f"Excess loss rate: {core_excess:+d} percentage points",
        ],
    }
    who_hurt_you = next((item for item in traumatic_cards if item["faced"] >= 5 and item["excess_loss_rate"] > 0), None)
    return {
        "traumatic_cards": traumatic_cards[:8],
        "who_hurt_you": who_hurt_you,
        "one_match_trauma": None,
        "complaint_without_proof": next((item for item in traumatic_cards if 2 <= item["faced"] < 5 and item["excess_loss_rate"] > 0), None),
        "natural_predator": natural_predator,
        "loss_core_count": core_loss_count,
        "baseline_loss_rate": baseline_loss_rate,
        "confidence": confidence_from_sample(len(eligible), 8, 15),
    }


def safe_estimate_deck_style(deck: list[dict[str, Any]], average_elixir: float) -> str:
    names = {card.get("name", "") for card in deck}
    traits = Counter(trait for card in deck for trait in card.get("traits", []))
    unknown_count = sum(1 for card in deck if not card.get("metadata_complete", True))
    if unknown_count >= 3:
        return "Unclassified deck style"
    if "Hog Rider" in names and average_elixir <= 3.4:
        return "Hog cycle-ish"
    if "X-Bow" in names or "Mortar" in names:
        return "Siege-ish"
    if {"Goblin Barrel", "Princess"}.issubset(names) or traits["bait"] >= 3:
        return "Bait-ish"
    if any(card in names for card in ["Battle Ram", "Bandit", "Royal Ghost", "Ram Rider"]):
        return "Bridge spam-ish"
    if any(card in names for card in ["Golem", "Giant", "Lava Hound"]) and average_elixir >= 4:
        return "Beatdown-ish"
    if traits["control"] >= 2 or "Miner" in names:
        return "Control-ish"
    if {"Mega Knight", "Wizard"}.issubset(names) or {"Elite Barbarians", "Rage"}.issubset(names):
        return "Midladder emergency response unit"
    return "Unclassified deck style"


def detect_deck_traits(deck: list[dict[str, Any]], average_elixir: float, style: str) -> list[dict[str, str]]:
    known = [card for card in deck if card.get("metadata_complete", True)]
    unknown_count = len(deck) - len(known)
    traits = Counter(trait for card in known for trait in card.get("traits", []))
    types = Counter(card.get("type", "unknown") for card in known)
    costs = [float(card.get("elixir")) for card in known if card.get("elixir") is not None]
    labels: list[str] = []
    if unknown_count:
        labels.append("Incomplete card metadata")
    if costs and average_elixir >= 4.6:
        labels.append("High elixir commitment")
    if len(known) >= 6 and traits["anti_air"] <= 1:
        labels.append("Weak anti-air")
    if len(known) >= 6 and traits["small_spell"] == 0:
        labels.append("No small spell")
    if types["building"] > 1:
        labels.append("Defensive building reliance")
    if traits["splash"] >= 3:
        labels.append("Heavy splash dependency")
    if len(known) >= 6 and traits["win_condition"] == 0:
        labels.append("No clear win condition")
    if len(known) >= 6 and "building_damage" not in traits and "tank_killer" not in traits and traits["win_condition"] <= 1:
        labels.append("No reliable building answer")
    if sum(1 for cost in costs if cost >= 5) >= 3:
        labels.append("Too many expensive cards")
    if traits["splash"] >= 3 or traits["swarm"] >= 3 or traits["cycle"] >= 4:
        labels.append("Too many duplicate roles")
    if types["spell"] == 0 and len(known) >= 6:
        labels.append("No spells")
    if types["building"] == 0 and len(known) >= 6:
        labels.append("No buildings")
    if not labels:
        labels.append("Readable role coverage")
    return [{"label": label, "explanation": TRAIT_EXPLANATIONS.get(label, "Detected from central card-role metadata.")} for label in labels[:5]]


def deck_identity_score(deck: list[dict[str, Any]], style: str) -> int:
    issue_labels = {trait["label"] for trait in detect_deck_traits(deck, average_deck_elixir(deck), style)}
    score = 75
    penalties = {
        "No clear win condition": 18,
        "No small spell": 8,
        "Weak anti-air": 8,
        "Too many duplicate roles": 7,
        "Too many expensive cards": 7,
        "No reliable building answer": 6,
        "Incomplete card metadata": 0,
    }
    for label, penalty in penalties.items():
        if label in issue_labels:
            score -= penalty
    return max(0, min(100, score))


def analyse_deck(player: dict[str, Any], player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle], card_service: CardDataService) -> dict[str, Any]:
    normalized = as_normalized(player_tag, battles)
    eligible = eligible_personal_battles(normalized)
    current_deck = [enrich_card(card, card_service) for card in (player.get("currentDeck") or (eligible[-1].player_deck if eligible else []))]
    current_key = deck_key(current_deck)
    average_elixir = average_deck_elixir(current_deck, card_service)
    type_counts = Counter(card.get("type", "unknown") for card in current_deck)
    style = safe_estimate_deck_style(current_deck, average_elixir)
    identity = deck_identity_score(current_deck, style)
    traits = detect_deck_traits(current_deck, average_elixir, style)
    issue_count = sum(1 for trait in traits if trait["label"] not in {"Readable role coverage", "Incomplete card metadata"})

    usage = card_usage_stats(player_tag, eligible)
    most_used = sorted(usage.values(), key=lambda item: item["used"], reverse=True)[:8]
    key_counts = Counter(battle.player_deck_key for battle in eligible)
    common_key, common_count = key_counts.most_common(1)[0] if key_counts else (tuple(), 0)
    signature_to_deck = {battle.player_deck_key: battle.player_deck_names for battle in eligible}
    recent_main_deck = signature_to_deck.get(common_key, [])
    current_matches_recent = bool(current_key and common_key and same_or_minor_variation(current_key, common_key))

    if issue_count >= 4:
        personality_rule = {
            "rule_id": "IDENTITY_CRISIS",
            "title": "TACTICAL SOUP",
            "evidence": [f"{issue_count} independent structural issues detected in the current deck"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    elif issue_count:
        personality_rule = {
            "rule_id": "RESPECTABLE_CITIZEN",
            "title": "CURRENT DECK UNDER REVIEW",
            "evidence": [f"{issue_count} structural issue(s) detected in the current deck"],
            "confidence": "medium",
            "relevant_cards": [],
        }
    else:
        personality_rule = {
            "rule_id": "RESPECTABLE_CITIZEN",
            "title": "CURRENT DECK CHECK",
            "evidence": ["No severe current-deck structural issue crossed the evidence threshold"],
            "confidence": "low" if not current_deck else "medium",
            "relevant_cards": [],
        }

    return {
        "current_deck": current_deck,
        "current_deck_key": list(current_key),
        "average_elixir": average_elixir,
        "composition": {
            "troops": type_counts["troop"],
            "spells": type_counts["spell"],
            "buildings": type_counts["building"],
            "unknown": type_counts["unknown"],
        },
        "most_used_cards": most_used,
        "most_common_deck": {"cards": recent_main_deck, "uses": common_count},
        "recent_main_deck": {"cards": recent_main_deck, "uses": common_count, "key": list(common_key)},
        "current_matches_recent_main_deck": current_matches_recent,
        "eligible_battle_history": {
            "eligible_matches": len(eligible),
            "excluded_matches": len(normalized) - len(eligible),
            "note": "Current deck is judged separately from eligible recent battle history.",
        },
        "estimated_deck_style": style,
        "deck_identity_score": identity,
        "structural_issues": traits,
        "structural_issue_count": issue_count,
        "metadata_unknown_count": sum(1 for card in current_deck if not card.get("metadata_complete", True)),
        "personality_rule": personality_rule,
    }


def analyse_main_character(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle]) -> dict[str, Any]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    usage = sorted(card_usage_stats(player_tag, eligible).values(), key=lambda item: item["used"], reverse=True)
    if not usage:
        return {"detected": False, "title": "No main character detected", "evidence": ["No eligible personal-deck matches found"], "confidence": "low"}
    top_count = usage[0]["used"]
    tied = [item for item in usage if item["used"] == top_count]
    if len(tied) >= 6:
        return {
            "detected": False,
            "title": "No single main character detected",
            "text": "This player is genuinely loyal to a full deck core, so no one card gets framed as the entire personality.",
            "confidence": "medium",
            "evidence": [f"{len(tied)} cards tied as most-used across {top_count} eligible matches"],
        }
    top = usage[0]
    return {
        "detected": True,
        "card": top["card"],
        "used": top["used"],
        "total": len(eligible),
        "usage_rate": round(top["used"] / len(eligible) * 100) if eligible else 0,
        "win_rate": top["win_rate"],
        "confidence": confidence_from_sample(top["used"], 8, 12),
        "evidence": [f"Appeared in {top['used']} of {len(eligible)} eligible decks", f"Win rate when present: {top['win_rate']}%"],
    }


def analyse_clutch(summary: dict[str, Any]) -> dict[str, Any]:
    close_wins = summary["close_wins"]
    close_losses = summary["close_losses"]
    close_total = close_wins + close_losses
    three_crown_losses = summary["three_crown_losses"]
    if close_total < 5:
        rating = "Insufficient close-game evidence"
    elif close_wins >= close_losses + 3:
        rating = "Ice in veins"
    elif close_wins >= close_losses:
        rating = "Mildly composed"
    elif three_crown_losses >= max(2, summary["losses"] // 3):
        rating = "Crown donation service"
    else:
        rating = "Late-game wobble"
    return {
        "rating": rating,
        "close_wins": close_wins,
        "close_losses": close_losses,
        "three_crown_losses": three_crown_losses,
        "three_crown_wins": summary["three_crown_wins"],
        "confidence": confidence_from_sample(close_total, 5, 10),
        "evidence": [f"Close games: {close_total}", f"Close wins/losses: {close_wins}/{close_losses}"],
    }


def recommend_deck_divorce(player_tag: str, battles: list[dict[str, Any]] | list[NormalizedBattle], current_deck: list[dict[str, Any]]) -> dict[str, Any]:
    usage = card_usage_stats(player_tag, battles)
    current_names = {card["name"] for card in current_deck}
    candidates = []
    for name, stat in usage.items():
        if name not in current_names or stat["used"] < 8:
            continue
        if stat["win_rate"] <= 40:
            candidates.append((40 - stat["win_rate"] + stat["used"], stat))
    if not candidates:
        return {"detected": False, "title": "No divorce recommendation.", "text": "No current-deck card has enough poor eligible evidence for a benching joke.", "confidence": "low"}
    _, stat = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {
        "detected": True,
        "card": stat["card"],
        "used": stat["used"],
        "win_rate": stat["win_rate"],
        "confidence": confidence_from_sample(stat["used"], 8, 12),
        "evidence": [f"Used in {stat['used']} eligible battles", f"Win rate when used: {stat['win_rate']}%"],
    }


def add_candidate(candidates: list[dict[str, Any]], group: str, label: str, points: int, evidence: list[str], sample_size: int, confidence: str, excluded: bool = False, description: str | None = None) -> None:
    candidates.append(
        {
            "group": group,
            "label": label,
            "raw_candidate_points": points,
            "points": points,
            "evidence": evidence,
            "sample_size": sample_size,
            "confidence": confidence,
            "excluded": excluded,
            "description": description or "Detected from eligible battle-log evidence.",
        }
    )


def apply_group_caps(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    caps = {
        "deck_construction": 15,
        "deck_switching": 12,
        "level_advantage": 20,
        "matchup_weakness": 15,
        "close_game": 10,
    }
    used = Counter()
    applied = []
    for candidate in candidates:
        group = candidate["group"]
        remaining = caps.get(group, candidate["raw_candidate_points"]) - used[group]
        applied_points = 0 if candidate["excluded"] else max(0, min(candidate["raw_candidate_points"], remaining))
        used[group] += applied_points
        applied.append({**candidate, "applied_points": applied_points, "points": applied_points})
    return applied


def calculate_troll_score(
    battle_summary: dict[str, Any],
    deck_analysis: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    clutch_analysis: dict[str, Any],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for issue in deck_analysis.get("structural_issues", []):
        label = issue.get("label", "")
        points = {
            "No clear win condition": 10,
            "No small spell": 7,
            "Weak anti-air": 6,
            "Too many duplicate roles": 5,
            "Too many expensive cards": 5,
            "No reliable building answer": 4,
        }.get(label, 0)
        if points:
            add_candidate(candidates, "deck_construction", label, points, [issue.get("explanation", label)], 1, deck_analysis.get("personality_rule", {}).get("confidence", "low"))
    if deck_analysis.get("deck_identity_score", 100) < 55 and deck_analysis.get("structural_issue_count", 0) >= 3:
        add_candidate(candidates, "deck_construction", "Multiple current-deck structural issues", 8, [f"Structural issues detected: {deck_analysis.get('structural_issue_count', 0)}"], 1, "medium")

    classification = behaviour_analysis.get("classification")
    if classification == "PANIC_SWITCHER":
        add_candidate(candidates, "deck_switching", "Verified panic switching", 12, behaviour_analysis.get("evidence", []), behaviour_analysis.get("post_loss_opportunities", 0), behaviour_analysis.get("confidence", "low"))
    elif classification == "DECK_HOPPER":
        add_candidate(candidates, "deck_switching", "Verified deck hopping", 10, behaviour_analysis.get("evidence", []), behaviour_analysis.get("eligible_battles", 0), behaviour_analysis.get("confidence", "low"))
    elif behaviour_analysis.get("changes_after_losses", 0):
        add_candidate(candidates, "deck_switching", "Possible post-loss deck changes", 5, behaviour_analysis.get("evidence", []), behaviour_analysis.get("post_loss_opportunities", 0), "low", excluded=behaviour_analysis.get("changes_after_losses", 0) < 3)

    if level_analysis.get("total_losses_with_levels", 0) >= 5 and level_analysis.get("meaningful_level_advantage_losses", 0):
        add_candidate(candidates, "level_advantage", "Lost with meaningful level advantage", min(20, round(level_analysis["overlevelled_fraud_score"] * 0.2)), level_analysis.get("evidence", []), level_analysis.get("total_losses_with_levels", 0), level_analysis.get("confidence", "low"))

    predator = matchup_analysis.get("natural_predator", {})
    if predator.get("matches", 0) >= 4 and predator.get("excess_loss_rate", 0) > 0:
        add_candidate(candidates, "matchup_weakness", "Detected matchup pattern", min(15, max(4, round(predator["excess_loss_rate"] / 3))), predator.get("evidence", []), predator.get("matches", 0), predator.get("confidence", "low"))

    close_total = clutch_analysis.get("close_wins", 0) + clutch_analysis.get("close_losses", 0)
    if close_total >= 5 and clutch_analysis.get("close_losses", 0) > clutch_analysis.get("close_wins", 0):
        add_candidate(candidates, "close_game", "Close-game losses", min(10, round(clutch_analysis["close_losses"] / close_total * 10)), clutch_analysis.get("evidence", []), close_total, clutch_analysis.get("confidence", "low"))

    if emotional_support.get("detected"):
        add_candidate(candidates, "deck_switching", "Emotional support card detected", 6, emotional_support.get("evidence", []), emotional_support.get("sample_size", 0), emotional_support.get("confidence", "low"))

    components = apply_group_caps(candidates)
    score = min(100, sum(component["applied_points"] for component in components if not component.get("excluded")))
    label = "Respectable citizen" if score <= 20 else "Mildly fraudulent" if score <= 40 else "Questionable gameplay" if score <= 60 else "Midladder incident" if score <= 80 else "National emergency"
    return {"score": score, "label": label, "components": components, "group_caps": {"deck_construction": 15, "deck_switching": 12, "level_advantage": 20, "matchup_weakness": 15, "close_game": 10}}


def fraud_tier_key(score: int) -> str:
    if score <= 20:
        return "respectable"
    if score <= 40:
        return "mild"
    if score <= 60:
        return "questionable"
    if score <= 80:
        return "high"
    return "extreme"


def build_fraud_score(
    troll_score: dict[str, Any],
    battle_summary: dict[str, Any],
    deck_analysis: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    clutch_analysis: dict[str, Any],
    selector: ExpressionSelector,
) -> dict[str, Any]:
    score = int(troll_score["score"])
    tier_key = fraud_tier_key(score)
    tier_copy = TIER_COPY[tier_key]
    contributors = []
    for component in sorted(troll_score["components"], key=lambda item: item.get("applied_points", item.get("points", 0)), reverse=True):
        copy = CONTRIBUTOR_COPY.get(component["label"], {})
        contributors.append(
            {
                "label": component["label"],
                "group": component["group"],
                "raw_candidate_points": component["raw_candidate_points"],
                "applied_points": component.get("applied_points", component.get("points", 0)),
                "points": component.get("applied_points", component.get("points", 0)),
                "description": component.get("description") or copy.get("description") or "Evidence-backed score contributor.",
                "evidence": component.get("evidence", []),
                "evidence_count": len(component.get("evidence", [])),
                "sample_size": component.get("sample_size", 0),
                "confidence": component.get("confidence", "low"),
                "excluded": component.get("excluded", False),
                "roast": selector.choose(copy.get("roasts", ["The evidence filed a small but readable complaint."]), f"fraud:contributor:{component['label']}"),
            }
        )
    if not contributors:
        contributors.append(
            {
                "label": "Evidence stayed boring",
                "group": "none",
                "raw_candidate_points": 0,
                "applied_points": 0,
                "points": 0,
                "description": "No major contributor crossed the evidence threshold.",
                "evidence": ["No score components crossed the threshold"],
                "evidence_count": 1,
                "sample_size": battle_summary.get("eligible_battles", 0),
                "confidence": "low",
                "excluded": False,
                "roast": "Suspicion noted; conviction denied due to insufficient battle logs.",
            }
        )
    confidence_values = [item["confidence"] for item in contributors if item["points"] > 0]
    confidence = "low" if not confidence_values or "low" in confidence_values else "medium" if "medium" in confidence_values else "high"
    return {
        "score": score,
        "tier": selector.choose(tier_copy["labels"], f"fraud:{tier_key}:label"),
        "tier_key": tier_key,
        "tier_description": selector.choose(tier_copy["descriptions"], f"fraud:{tier_key}:description"),
        "headline_roast": selector.choose(tier_copy["headlines"], f"fraud:{tier_key}:headline"),
        "confidence": confidence,
        "overall_confidence_note": f"Overall confidence: {confidence.title()} - based on {battle_summary.get('eligible_battles', 0)} eligible personal-deck matches with per-claim thresholds applied.",
        "contributors": contributors[:7],
        "score_receipts": [evidence for contributor in contributors for evidence in contributor["evidence"]],
        "group_caps": troll_score.get("group_caps", {}),
    }


def build_deck_personality(deck_analysis: dict[str, Any], selector: ExpressionSelector) -> dict[str, Any]:
    style = deck_analysis["estimated_deck_style"]
    copy = DECK_STYLE_COPY.get(style, {"plain": "This current deck does not cleanly match a known archetype, which is not automatically a problem.", "roasts": ["Unclassified is not guilty. The court has learned restraint."]})
    traits = deck_analysis.get("structural_issues", [])
    issue_count = deck_analysis.get("structural_issue_count", 0)
    if issue_count >= 4:
        title = "Tactical Soup"
        roast = "Multiple independent current-deck issues crossed the threshold. The spoon is evidence-based."
    elif style == "Unclassified deck style":
        title = "Unclassified Deck Style"
        roast = "The deck dodged the archetype label, but the app refuses to call that a crime by itself."
    else:
        title = style
        roast = selector.choose(copy["roasts"], f"deck:{style}:roast")
    evidence = list(deck_analysis["personality_rule"].get("evidence", []))
    evidence.extend([f"{trait['label']}: {trait['explanation']}" for trait in traits])
    if not deck_analysis.get("current_matches_recent_main_deck", True):
        evidence.append("Current deck differs from the recent main deck. Historical results may reflect a previous deck.")
    return {
        "title": title,
        "style": style,
        "plain_explanation": copy["plain"],
        "roast": roast,
        "traits": traits,
        "evidence": evidence,
        "confidence": deck_analysis["personality_rule"].get("confidence", "medium"),
        "current_matches_recent_main_deck": deck_analysis.get("current_matches_recent_main_deck", False),
    }


def build_personality_report(
    deck_analysis: dict[str, Any],
    battle_summary: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    main_character: dict[str, Any],
    fraud_score: dict[str, Any],
    selector: ExpressionSelector,
    goblin_mode: bool,
) -> dict[str, Any]:
    classification = behaviour_analysis.get("classification")
    eligible = behaviour_analysis.get("eligible_battles", 0)
    if classification == "ONE_DECK_WARRIOR":
        title = "Deck Monogamist"
        summary = f"You used the same core deck in {behaviour_analysis['main_deck_games']} of {eligible} eligible matches. This is either disciplined mastery or a long-term relationship that has stopped making both parties happy."
        diagnosis = "Deck loyalty is well supported."
    elif classification == "PANIC_SWITCHER":
        title = "Verified Post-Loss Rebuilder"
        summary = f"{behaviour_analysis['changes_after_losses']} major deck changes followed {behaviour_analysis['post_loss_opportunities']} valid losses. The court can confirm a deck-switching incident."
        diagnosis = "Panic-switch evidence crossed the threshold."
    elif classification == "DECK_HOPPER":
        title = "Flexible To A Fault"
        summary = f"You used {behaviour_analysis['materially_distinct_deck_cores']} materially distinct deck cores in {eligible} eligible matches, and no single core dominated the case file."
        diagnosis = "Deck-hopping evidence is supported."
    elif classification == "LIMITED_DATA":
        title = "Insufficient Evidence Enjoyer"
        summary = f"Only {eligible} eligible personal-deck matches were found. Suspicion noted; conviction denied due to insufficient battle logs."
        diagnosis = "Limited eligible sample."
    elif classification == "STABLE_WITH_MINOR_VARIATIONS":
        title = "Stable With Receipts"
        summary = f"You have one clear main deck with minor variations. Only {behaviour_analysis['changes_after_losses']} eligible major deck variation(s) followed losses, so no emotional crisis verdict was issued."
        diagnosis = "Normal deck testing, not chaos."
    else:
        title = "Flexible Deck User"
        summary = f"You used multiple meaningful deck cores across {eligible} eligible matches, but the changes were not strongly tied to losses."
        diagnosis = "Flexible, not convicted."

    traits = [
        {"label": "Deck Loyalty", "value": f"{behaviour_analysis.get('same_core_percentage', 0)}% dominant-core usage"},
        {"label": "Deck Switching", "value": f"{behaviour_analysis.get('changes_after_losses', 0)} post-loss major changes"},
        {"label": "Evidence Sample", "value": f"{eligible} eligible matches"},
    ]
    if emotional_support.get("detected"):
        traits.append({"label": "Comfort Pick", "value": emotional_support["card"]})
    intervention = "Fix the loudest verified pattern first; the unverified drama can wait."
    if goblin_mode and classification == "PANIC_SWITCHER":
        intervention = "Try losing once without rebuilding the entire company."
    evidence = [
        *behaviour_analysis.get("evidence", []),
        f"Fraud Score tier: {fraud_score['tier']}",
        f"Eligible level-known losses: {level_analysis.get('total_losses_with_levels', 0)}",
        f"Matchup baseline loss rate: {matchup_analysis.get('baseline_loss_rate', 0)}%",
    ]
    return {
        "section_title": "Evidence-Based Personality Report",
        "title": title,
        "summary": summary,
        "traits": traits[:4],
        "diagnosis": diagnosis,
        "intervention_tip": intervention,
        "evidence": evidence,
        "confidence": fraud_score["confidence"],
        "scope_note": "This is a deck personality summary based only on eligible recent battle-log behaviour, not a real psychological diagnosis.",
    }


def dedupe_roasts(roasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for roast in roasts:
        rule_id = roast.get("rule_id")
        if rule_id in seen:
            continue
        seen.add(rule_id)
        unique.append(roast)
    return unique


@dataclass
class AnalysisService:
    card_service: CardDataService
    roast_engine: RoastEngine

    def build_report(self, player: dict[str, Any], battles: list[dict[str, Any]], seed: str | int | None = None, goblin_mode: bool = False) -> dict[str, Any]:
        player_tag = player.get("tag", "")
        selector = ExpressionSelector(seed or player_tag)
        normalized = normalize_battles(player_tag, battles)
        battle_summary = calculate_battle_summary(player_tag, normalized)
        deck_analysis = analyse_deck(player, player_tag, normalized, self.card_service)
        matchup_analysis = analyse_matchups(player_tag, normalized)
        level_analysis = detect_level_analysis(player_tag, normalized)
        behaviour_analysis = detect_panic_switching(player_tag, normalized)
        emotional_support = detect_emotional_support_card(player_tag, normalized)
        main_character = analyse_main_character(player_tag, normalized)
        clutch_analysis = analyse_clutch(battle_summary)
        divorce = recommend_deck_divorce(player_tag, normalized, deck_analysis["current_deck"])
        troll_score = calculate_troll_score(battle_summary, deck_analysis, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, clutch_analysis)
        fraud_score = build_fraud_score(troll_score, battle_summary, deck_analysis, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, clutch_analysis, selector)
        deck_personality = build_deck_personality(deck_analysis, selector)
        personality_report = build_personality_report(deck_analysis, battle_summary, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, main_character, fraud_score, selector, goblin_mode)

        roasts = [
            self.roast_engine.render(
                behaviour_analysis["rule_id"],
                behaviour_analysis["title"],
                behaviour_analysis["evidence"],
                behaviour_analysis["confidence"],
                behaviour_analysis["main_deck"],
                {"plain_explanation": "This classification uses only eligible standard personal-deck battles sorted oldest to newest."},
                seed or player_tag,
                goblin_mode,
            ),
            self.roast_engine.render(
                deck_analysis["personality_rule"]["rule_id"],
                deck_analysis["personality_rule"]["title"],
                deck_personality["evidence"],
                deck_personality["confidence"],
                deck_analysis["personality_rule"].get("relevant_cards", []),
                {"plain_explanation": deck_personality["plain_explanation"]},
                seed or player_tag,
                goblin_mode,
            ),
        ]
        if emotional_support.get("detected"):
            roasts.append(self.roast_engine.render("EMOTIONAL_SUPPORT_CARD", "EMOTIONAL SUPPORT CARD", emotional_support["evidence"], emotional_support["confidence"], [emotional_support["card"]], {"card": emotional_support["card"], "win_rate": emotional_support["win_rate"]}, seed or player_tag, goblin_mode))
        hurt = matchup_analysis.get("who_hurt_you")
        if hurt and hurt.get("faced", 0) >= 5:
            roasts.append(self.roast_engine.render("WHO_HURT_YOU", "DETECTED MATCHUP PATTERN", hurt["evidence"], hurt["confidence"], [hurt["card"]], {"card": hurt["card"]}, seed or player_tag, goblin_mode))
        predator = matchup_analysis["natural_predator"]
        if predator["core_cards"]:
            roasts.append(self.roast_engine.render("NATURAL_PREDATOR", "POTENTIAL NATURAL PREDATOR", predator["evidence"], predator["confidence"], predator["core_cards"], {}, seed or player_tag, goblin_mode))
        if level_analysis["total_losses_with_levels"] >= 5 and level_analysis["meaningful_level_advantage_losses"]:
            roasts.append(
                self.roast_engine.render(
                    "OVERLEVELLED_FRAUD",
                    "OVERLEVELLED FRAUD SCORE",
                    level_analysis["evidence"],
                    level_analysis["confidence"],
                    [],
                    {
                        "overlevelled_losses": level_analysis["meaningful_level_advantage_losses"],
                        "plain_explanation": "This only counts eligible level-known losses where the player averaged at least 0.75 card levels above the opponent.",
                    },
                    seed or player_tag,
                    goblin_mode,
                )
            )
        roasts.append(self.roast_engine.render("CLUTCH_REPORT", f"CLUTCH RATING: {clutch_analysis['rating'].upper()}", clutch_analysis["evidence"], clutch_analysis["confidence"], [], {}, seed or player_tag, goblin_mode))
        if divorce.get("detected"):
            roasts.append(self.roast_engine.render("DECK_DIVORCE", "DECK DIVORCE RECOMMENDATION", divorce["evidence"], divorce["confidence"], [divorce["card"]], {"card": divorce["card"]}, seed or player_tag, goblin_mode))

        roasts = dedupe_roasts(roasts)
        headline_roast = roasts[0] if roasts else {"evidence": []}
        title = f"{personality_report['title']} - {fraud_score['tier']}".strip()
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
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
            "deck_personality": deck_personality,
            "matchup_analysis": matchup_analysis,
            "level_analysis": level_analysis,
            "behaviour_analysis": behaviour_analysis,
            "clutch_analysis": clutch_analysis,
            "divorce_recommendation": divorce,
            "fraud_score": fraud_score,
            "personality_report": personality_report,
            "roast_report": {
                "title": title,
                "troll_score": fraud_score["score"],
                "score_label": fraud_score["tier"],
                "headline_roast": fraud_score["headline_roast"],
                "evidence": fraud_score["score_receipts"] or headline_roast["evidence"],
                "score_breakdown": fraud_score["contributors"],
            },
            "roasts": roasts,
            "disclaimer": "Results are based on eligible public battle-log deck, crown, level, and matchup data. Draft, 2v2, event, capped, and incomplete-deck modes are excluded from personal-deck behavioural claims.",
        }


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_card_service(), RoastEngine())
