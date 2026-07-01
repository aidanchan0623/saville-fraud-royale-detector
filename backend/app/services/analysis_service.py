from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.rules.deck_templates import DECK_STYLE_COPY, TRAIT_EXPLANATIONS
from app.rules.deck_roast_composer import compose_deck_roast
from app.rules.expression_selector import ExpressionSelector
from app.rules.matchup_rules import label_opponent_core, most_common_loss_core
from app.rules.roast_composer import compose_roast_system
from app.services.battle_normalizer import (
    NormalizedBattle,
    cards_from_side,
    deck_key,
    deck_names,
    eligible_level_battles,
    eligible_personal_battles,
    material_deck_change,
    normalize_battles,
    normalize_card_name,
    normalize_player_tag,
    same_or_minor_variation,
    shared_card_count,
)
from app.services.card_data_service import CardDataService, get_card_service
from app.services.community_meme_service import COMMUNITY_MEME_DISCLAIMER, analyse_community_meme_deck
from app.services.roast_engine import RoastEngine


REPORT_SCHEMA_VERSION = "report-v6"
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


def card_details_from_battles(player_tag: str, name: str, battles: list[dict[str, Any]] | list[NormalizedBattle], card_service: CardDataService | None = None) -> dict[str, Any]:
    service = card_service or get_card_service()
    target = normalize_card_name(name)
    for battle in reversed(as_normalized(player_tag, battles)):
        for card in [*battle.player_deck, *battle.opponent_deck]:
            if normalize_card_name(card.get("name", "")) == target:
                return enrich_card(card, service)
    return enrich_card({"name": name}, service)


def card_details_from_player_context(player_tag: str, name: str, current_deck: list[dict[str, Any]], battles: list[dict[str, Any]] | list[NormalizedBattle], card_service: CardDataService | None = None) -> dict[str, Any]:
    service = card_service or get_card_service()
    target = normalize_card_name(name)
    for card in current_deck:
        if normalize_card_name(card.get("name", "")) == target:
            return enrich_card(card, service)
    return card_details_from_battles(player_tag, name, battles, service)


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
    bucket_order = ("overlevelled", "even", "underlevelled")
    bucket_labels = {"overlevelled": "Overlevelled", "even": "Even level", "underlevelled": "Underlevelled"}
    buckets: dict[str, dict[str, Any]] = {
        key: {"wins": 0, "losses": 0, "draws": 0, "diffs": []}
        for key in bucket_order
    }
    details = []
    diffs: list[float] = []
    win_diffs: list[float] = []
    loss_diffs: list[float] = []
    for battle in eligible:
        player_average = average_card_level(battle.player_deck)
        opponent_average = average_card_level(battle.opponent_deck)
        diff = round(player_average - opponent_average, 2)
        diffs.append(diff)
        label = classify_level_disadvantage(battle.player_deck, battle.opponent_deck)
        buckets[label][result_bucket(battle.result)] += 1
        buckets[label]["diffs"].append(diff)
        if battle.result == "win":
            win_diffs.append(diff)
        elif battle.result == "loss":
            loss_diffs.append(diff)
        details.append(
            {
                "battleTime": battle.battle_time,
                "classification": label,
                "result": battle.result,
                "player_average_level": player_average,
                "opponent_average_level": opponent_average,
                "level_difference": diff,
            }
        )
    losses = {key: int(buckets[key]["losses"]) for key in bucket_order}
    wins = {key: int(buckets[key]["wins"]) for key in bucket_order}
    draws = {key: int(buckets[key]["draws"]) for key in bucket_order}
    total_losses = sum(losses.values())
    sample_size = len(eligible)
    fraud_score = round(losses["overlevelled"] / total_losses * 100) if total_losses else 0
    level_chart = []
    for key in bucket_order:
        matches = wins[key] + losses[key] + draws[key]
        level_chart.append(
            {
                "key": key,
                "label": bucket_labels[key],
                "wins": wins[key],
                "losses": losses[key],
                "draws": draws[key],
                "matches": matches,
                "win_rate": round(wins[key] / matches * 100) if matches else 0,
                "average_level_difference": round(sum(buckets[key]["diffs"]) / len(buckets[key]["diffs"]), 2) if buckets[key]["diffs"] else 0,
            }
        )
    over_matches = wins["overlevelled"] + losses["overlevelled"] + draws["overlevelled"]
    even_matches = wins["even"] + losses["even"] + draws["even"]
    under_matches = wins["underlevelled"] + losses["underlevelled"] + draws["underlevelled"]
    over_win_rate = round(wins["overlevelled"] / over_matches * 100) if over_matches else 0
    even_win_rate = round(wins["even"] / even_matches * 100) if even_matches else 0
    under_win_rate = round(wins["underlevelled"] / under_matches * 100) if under_matches else 0

    if sample_size < 5:
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
    if sample_size < 5:
        level_roast = "Not enough level-known 1v1 matches to judge whether upgrades are carrying."
    elif over_matches and losses["overlevelled"] >= wins["overlevelled"] and losses["overlevelled"] >= 2:
        level_roast = "You brought extra levels and still found a way to make it difficult. That is genuinely impressive."
    elif over_matches >= 3 and over_win_rate >= 60:
        level_roast = "Your cards arrived with a height advantage and the confidence of a private-school bully."
    elif under_matches >= 3 and under_win_rate > 50:
        level_roast = "The deck is doing unpaid overtime. Respectfully, the cards are carrying."
    else:
        level_roast = "No level excuse detected. This one is between you and the deck."
    return {
        "loss_counts": losses,
        "win_counts": wins,
        "draw_counts": draws,
        "result_counts": {
            key: {"wins": wins[key], "losses": losses[key], "draws": draws[key]}
            for key in bucket_order
        },
        "total_losses_with_levels": total_losses,
        "eligible_level_matches": sample_size,
        "level_known_sample_size": sample_size,
        "meaningful_level_advantage_losses": losses["overlevelled"],
        "meaningful_level_advantage_wins": wins["overlevelled"],
        "average_level_difference": round(sum(diffs) / len(diffs), 2) if diffs else 0,
        "average_level_difference_in_wins": round(sum(win_diffs) / len(win_diffs), 2) if win_diffs else 0,
        "average_level_difference_in_losses": round(sum(loss_diffs) / len(loss_diffs), 2) if loss_diffs else 0,
        "overlevelled_win_rate": over_win_rate,
        "even_level_win_rate": even_win_rate,
        "underlevelled_win_rate": under_win_rate,
        "level_reliance_chart": level_chart,
        "level_chart_visible": sample_size >= 5,
        "level_reliance_roast": level_roast,
        "confidence": confidence_from_sample(sample_size, 5, 12),
        "percentages": {
            "matchmaking_conspiracy": round(losses["underlevelled"] / total_losses * 100) if total_losses else 0,
            "fair_fight_failure": round(losses["even"] / total_losses * 100) if total_losses else 0,
            "certified_skill_issue": fraud_score,
        },
        "overlevelled_fraud_score": fraud_score,
        "tier": tier,
        "details": details,
        "evidence": [
            f"Eligible level-known 1v1 matches: {sample_size}",
            f"Eligible level-known losses: {total_losses}",
            f"Meaningful level-advantage losses: {losses['overlevelled']}",
            f"Overlevelled record: {wins['overlevelled']}-{losses['overlevelled']}-{draws['overlevelled']}",
            f"Even-level record: {wins['even']}-{losses['even']}-{draws['even']}",
            f"Underlevelled record: {wins['underlevelled']}-{losses['underlevelled']}-{draws['underlevelled']}",
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
    signature_to_card_deck = {battle.player_deck_key: [enrich_card(card, card_service) for card in battle.player_deck] for battle in eligible}
    recent_main_deck = signature_to_deck.get(common_key, [])
    recent_main_card_deck = signature_to_card_deck.get(common_key, [])
    current_matches_recent = bool(current_key and common_key and same_or_minor_variation(current_key, common_key))
    current_exact_recent = bool(current_key and common_key and current_key == common_key)
    current_recent_shared = shared_card_count(current_key, common_key) if current_key and common_key else 0
    current_names = {card.get("name", "") for card in current_deck}
    recent_names = set(recent_main_deck)
    current_recent_added = sorted(current_names - recent_names)
    current_recent_removed = sorted(recent_names - current_names)

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
        "recent_main_deck": {"cards": recent_main_deck, "card_details": recent_main_card_deck, "uses": common_count, "key": list(common_key)},
        "current_matches_recent_main_deck": current_matches_recent,
        "current_exact_recent_main_deck": current_exact_recent,
        "current_recent_shared_cards": current_recent_shared,
        "current_recent_added_cards": current_recent_added,
        "current_recent_removed_cards": current_recent_removed,
        "eligible_battle_history": {
            "eligible_matches": len(eligible),
            "excluded_matches": len(normalized) - len(eligible),
            "note": "Only eligible personal-deck battles count as receipts; party modes and weird formats stay out of the argument.",
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


def analyse_favourite_card(
    player_tag: str,
    battles: list[dict[str, Any]] | list[NormalizedBattle],
    deck_analysis: dict[str, Any],
    card_service: CardDataService,
    min_games: int = 8,
) -> dict[str, Any]:
    normalized = as_normalized(player_tag, battles)
    eligible = eligible_personal_battles(normalized)
    total = len(eligible)
    wins = sum(1 for battle in eligible if battle.result == "win")
    baseline_win_rate = round(wins / total * 100) if total else 0
    usage = sorted(
        card_usage_stats(player_tag, eligible).values(),
        key=lambda item: (item["used"], item["win_rate"], item["wins"]),
        reverse=True,
    )
    evidence_base = [f"Eligible personal-deck matches: {total}", f"Player baseline win rate: {baseline_win_rate}%"]
    if not usage:
        return {
            "detected": False,
            "favourite_card": None,
            "favourite_card_name": None,
            "eligible_match_count": total,
            "player_baseline_win_rate": baseline_win_rate,
            "favourite_card_usage_count": 0,
            "favourite_card_usage_rate": 0,
            "favourite_card_win_rate": 0,
            "favourite_card_performance_delta": 0,
            "favourite_card_confidence": "low",
            "favourite_card_reason": "No eligible personal-deck cards were found, so the report refuses to invent a favourite.",
            "is_true_single_card_favourite": False,
            "is_full_deck_loyalist_case": False,
            "evidence": evidence_base,
        }

    top = usage[0]
    top_count = top["used"]
    second_count = usage[1]["used"] if len(usage) > 1 else 0
    tied_top = [item for item in usage if item["used"] == top_count]
    top_eight = usage[:8]
    top_eight_spread = max((item["used"] for item in top_eight), default=0) - min((item["used"] for item in top_eight), default=0)
    full_deck_loyalist = bool(len(tied_top) >= 6 or (len(top_eight) >= 8 and top_eight_spread <= 1 and top_count >= min_games))
    usage_rate = round(top_count / total * 100) if total else 0
    delta = top["win_rate"] - baseline_win_rate
    common_evidence = [
        *evidence_base,
        f"Most-used card candidate: {top['card']} in {top_count} of {total} eligible matches ({usage_rate}%)",
        f"Candidate win rate: {top['win_rate']}% versus baseline {baseline_win_rate}% ({delta:+d} percentage points)",
        f"Second-most usage count: {second_count}",
    ]

    best_signature = None
    best_candidates = [
        stat
        for stat in usage
        if stat["used"] >= max(5, min_games - 3) and stat["win_rate"] >= baseline_win_rate + 8
    ]
    if best_candidates:
        best = sorted(best_candidates, key=lambda item: (item["win_rate"] - baseline_win_rate, item["used"]), reverse=True)[0]
        best_signature = {
            "card_name": best["card"],
            "card": card_details_from_player_context(player_tag, best["card"], deck_analysis.get("current_deck", []), normalized, card_service),
            "used": best["used"],
            "wins": best["wins"],
            "losses": best["losses"],
            "win_rate": best["win_rate"],
            "delta": best["win_rate"] - baseline_win_rate,
            "confidence": confidence_from_sample(best["used"], 5, 10),
            "evidence": [
                f"{best['card']} appeared in {best['used']} eligible matches",
                f"Win rate with {best['card']}: {best['win_rate']}% versus baseline {baseline_win_rate}%",
            ],
        }

    if total < min_games:
        return {
            "detected": False,
            "favourite_card": None,
            "favourite_card_name": top["card"],
            "eligible_match_count": total,
            "player_baseline_win_rate": baseline_win_rate,
            "favourite_card_usage_count": top_count,
            "favourite_card_usage_rate": usage_rate,
            "favourite_card_win_rate": top["win_rate"],
            "favourite_card_performance_delta": delta,
            "favourite_card_confidence": "low",
            "favourite_card_reason": f"Only {total} eligible personal-deck matches; a strong favourite-card roast needs at least {min_games}.",
            "is_true_single_card_favourite": False,
            "is_full_deck_loyalist_case": False,
            "best_signature_card": best_signature,
            "evidence": common_evidence,
        }

    if full_deck_loyalist:
        return {
            "detected": False,
            "favourite_card": None,
            "favourite_card_name": None,
            "eligible_match_count": total,
            "player_baseline_win_rate": baseline_win_rate,
            "favourite_card_usage_count": top_count,
            "favourite_card_usage_rate": usage_rate,
            "favourite_card_win_rate": top["win_rate"],
            "favourite_card_performance_delta": delta,
            "favourite_card_confidence": "medium",
            "favourite_card_reason": "No single main character detected. This player is committed to the entire eight-card group chat.",
            "is_true_single_card_favourite": False,
            "is_full_deck_loyalist_case": True,
            "best_signature_card": best_signature,
            "evidence": [
                *common_evidence,
                f"{len(tied_top)} cards tied for top usage" if len(tied_top) >= 6 else f"Top eight card usage spread is only {top_eight_spread} match",
            ],
        }

    meaningful_single_card = top_count >= min_games and usage_rate >= 45 and (top_count > second_count or usage_rate >= 75)
    if not meaningful_single_card:
        return {
            "detected": False,
            "favourite_card": None,
            "favourite_card_name": top["card"],
            "eligible_match_count": total,
            "player_baseline_win_rate": baseline_win_rate,
            "favourite_card_usage_count": top_count,
            "favourite_card_usage_rate": usage_rate,
            "favourite_card_win_rate": top["win_rate"],
            "favourite_card_performance_delta": delta,
            "favourite_card_confidence": "low",
            "favourite_card_reason": "Top card usage did not separate enough from the rest of the deck to frame a true single-card favourite.",
            "is_true_single_card_favourite": False,
            "is_full_deck_loyalist_case": False,
            "best_signature_card": best_signature,
            "evidence": common_evidence,
        }

    if delta >= 10:
        reason = f"{top['card']} is a high-usage card performing above baseline by {delta:+d} percentage points."
    elif delta <= -10:
        reason = f"{top['card']} is a high-usage card performing below baseline by {delta:+d} percentage points."
    else:
        reason = f"{top['card']} is a high-usage card with results close to baseline."

    return {
        "detected": True,
        "favourite_card": card_details_from_player_context(player_tag, top["card"], deck_analysis.get("current_deck", []), normalized, card_service),
        "favourite_card_name": top["card"],
        "favourite_card_usage_count": top_count,
        "favourite_card_usage_rate": usage_rate,
        "favourite_card_win_rate": top["win_rate"],
        "player_baseline_win_rate": baseline_win_rate,
        "favourite_card_performance_delta": delta,
        "favourite_card_confidence": confidence_from_sample(top_count, min_games, min_games + 4),
        "favourite_card_reason": reason,
        "is_true_single_card_favourite": True,
        "is_full_deck_loyalist_case": False,
        "eligible_match_count": total,
        "best_signature_card": best_signature,
        "evidence": common_evidence,
    }


def analyse_feared_card(
    player_tag: str,
    battles: list[dict[str, Any]] | list[NormalizedBattle],
    card_service: CardDataService,
    min_encounters: int = 5,
) -> dict[str, Any]:
    normalized = as_normalized(player_tag, battles)
    eligible = eligible_personal_battles(normalized)
    ranked = rank_traumatic_opponent_cards(player_tag, eligible, min_encounters=min_encounters)
    baseline_loss_rate = round(sum(1 for battle in eligible if battle.result == "loss") / len(eligible) * 100) if eligible else 0
    base = {
        "feared_card": None,
        "feared_card_name": None,
        "feared_card_image": None,
        "games_against": 0,
        "wins_against": 0,
        "losses_against": 0,
        "loss_rate_against": 0,
        "baseline_loss_rate": baseline_loss_rate,
        "excess_loss_rate": 0,
        "feared_card_confidence": "low",
        "evidence_summary": f"Need at least {min_encounters} eligible encounters and an above-baseline loss rate before naming a feared card.",
        "is_insufficient_evidence": True,
        "evidence": [f"Eligible personal-deck matches: {len(eligible)}", f"Baseline loss rate: {baseline_loss_rate}%"],
    }
    if not ranked:
        return base

    leading = ranked[0]
    leading_card = card_details_from_battles(player_tag, leading["card"], normalized, card_service)
    sufficient = next((item for item in ranked if item["faced"] >= min_encounters and item["excess_loss_rate"] > 0), None)
    if not sufficient:
        reason = (
            f"The court cannot confirm that {leading['card']} owns you yet. "
            f"It appeared in {leading['faced']} eligible matches with {leading['excess_loss_rate']:+d} pp excess loss rate."
        )
        return {
            **base,
            "leading_candidate": leading_card,
            "leading_candidate_name": leading["card"],
            "games_against": leading["faced"],
            "wins_against": leading["wins"],
            "losses_against": leading["losses"],
            "loss_rate_against": leading["loss_rate"],
            "excess_loss_rate": leading["excess_loss_rate"],
            "evidence_summary": reason,
            "evidence": [
                *base["evidence"],
                *leading.get("evidence", []),
                f"Minimum encounters for a feared-card claim: {min_encounters}",
            ],
        }

    card = card_details_from_battles(player_tag, sufficient["card"], normalized, card_service)
    return {
        "feared_card": card,
        "feared_card_name": sufficient["card"],
        "feared_card_image": card.get("icon_url"),
        "games_against": sufficient["faced"],
        "wins_against": sufficient["wins"],
        "losses_against": sufficient["losses"],
        "loss_rate_against": sufficient["loss_rate"],
        "baseline_loss_rate": sufficient["baseline_loss_rate"],
        "excess_loss_rate": sufficient["excess_loss_rate"],
        "feared_card_confidence": sufficient["confidence"],
        "evidence_summary": (
            f"{sufficient['card']} appeared in {sufficient['faced']} eligible matches; "
            f"loss rate was {sufficient['loss_rate']}% versus {sufficient['baseline_loss_rate']}% baseline."
        ),
        "is_insufficient_evidence": False,
        "evidence": [
            *sufficient.get("evidence", []),
            "This is a detected recurring problem, not a hard-counter claim.",
        ],
    }


def analyse_win_rate_verdict(
    player_tag: str,
    battles: list[dict[str, Any]] | list[NormalizedBattle],
    behaviour_analysis: dict[str, Any],
) -> dict[str, Any]:
    eligible = eligible_personal_battles(as_normalized(player_tag, battles))
    total = len(eligible)
    wins = sum(1 for battle in eligible if battle.result == "win")
    losses = sum(1 for battle in eligible if battle.result == "loss")
    draws = sum(1 for battle in eligible if battle.result == "draw")
    win_rate = round(wins / total * 100) if total else 0
    loss_rate = round(losses / total * 100) if total else 0
    close_wins = sum(1 for battle in eligible if battle.result == "win" and battle.player_crowns - battle.opponent_crowns == 1)
    close_losses = sum(1 for battle in eligible if battle.result == "loss" and battle.opponent_crowns - battle.player_crowns == 1)
    close_total = close_wins + close_losses
    close_game_win_rate = round(close_wins / close_total * 100) if close_total else None
    trend = "insufficient chronological data"
    trend_delta = 0
    if total >= 10:
        midpoint = total // 2
        older = eligible[:midpoint]
        newer = eligible[midpoint:]
        older_rate = round(sum(1 for battle in older if battle.result == "win") / len(older) * 100) if older else 0
        newer_rate = round(sum(1 for battle in newer if battle.result == "win") / len(newer) * 100) if newer else 0
        trend_delta = newer_rate - older_rate
        if trend_delta >= 12:
            trend = "improving"
        elif trend_delta <= -12:
            trend = "declining"
        else:
            trend = "stable"

    evidence = [
        f"Eligible personal-deck matches: {total}",
        f"Wins/losses/draws: {wins}/{losses}/{draws}",
        f"Eligible win rate: {win_rate}%",
    ]
    if close_game_win_rate is not None:
        evidence.append(f"Close-game win rate: {close_game_win_rate}% from {close_total} close games")
    if behaviour_analysis.get("main_deck_games", 0):
        evidence.append(f"Main deck win rate: {behaviour_analysis.get('main_deck_win_rate', 0)}% over {behaviour_analysis.get('main_deck_games', 0)} games")
    if behaviour_analysis.get("emergency_deck_games", 0):
        evidence.append(f"Replacement deck win rate: {behaviour_analysis.get('emergency_deck_win_rate', 0)}% over {behaviour_analysis.get('emergency_deck_games', 0)} games")
    if total >= 10:
        evidence.append(f"Recent-half trend delta: {trend_delta:+d} percentage points")

    return {
        "total_eligible_matches": total,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "close_wins": close_wins,
        "close_losses": close_losses,
        "close_game_win_rate": close_game_win_rate,
        "main_deck_win_rate": behaviour_analysis.get("main_deck_win_rate"),
        "main_deck_games": behaviour_analysis.get("main_deck_games"),
        "replacement_deck_win_rate": behaviour_analysis.get("emergency_deck_win_rate"),
        "replacement_deck_games": behaviour_analysis.get("emergency_deck_games"),
        "confidence": confidence_from_sample(total, 8, 15),
        "trend": trend,
        "trend_delta": trend_delta,
        "evidence": evidence,
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


def _score_group(
    key: str,
    label: str,
    score: int,
    max_score: int,
    confidence: str,
    sample_size: int,
    evidence: list[str],
    description: str,
    roast: str,
    raw_score: float | int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    applied = max(0, min(max_score, int(round(score))))
    return {
        "key": key,
        "group": key,
        "label": label,
        "raw_score": raw_score if raw_score is not None else score,
        "raw_candidate_points": raw_score if raw_score is not None else score,
        "score": applied,
        "points": applied,
        "applied_points": applied,
        "max_score": max_score,
        "max_points": max_score,
        "confidence": confidence if confidence in {"low", "medium", "high"} else "low",
        "sample_size": sample_size,
        "evidence": evidence,
        "evidence_count": len(evidence),
        "description": description,
        "roast": roast,
        "excluded": False,
        **(extra or {}),
    }


def calculate_performance_loss_component(
    battle_summary: dict[str, Any],
    win_rate_verdict: dict[str, Any] | None,
    clutch_analysis: dict[str, Any],
) -> dict[str, Any]:
    verdict = win_rate_verdict or {}
    total = int(verdict.get("total_eligible_matches") or battle_summary.get("eligible_battles") or battle_summary.get("battles_analysed") or 0)
    wins = int(verdict.get("wins") if verdict.get("wins") is not None else battle_summary.get("wins", 0))
    losses = int(verdict.get("losses") if verdict.get("losses") is not None else battle_summary.get("losses", 0))
    draws = int(verdict.get("draws") if verdict.get("draws") is not None else battle_summary.get("draws", 0))
    win_rate = int(verdict.get("win_rate") if verdict.get("win_rate") is not None else battle_summary.get("win_rate", 0))
    loss_rate = int(verdict.get("loss_rate") if verdict.get("loss_rate") is not None else battle_summary.get("loss_rate", 0))
    close_wins = int(verdict.get("close_wins") if verdict.get("close_wins") is not None else clutch_analysis.get("close_wins", 0))
    close_losses = int(verdict.get("close_losses") if verdict.get("close_losses") is not None else clutch_analysis.get("close_losses", 0))
    close_total = close_wins + close_losses

    if total < 8:
        score = min(5, round((losses / max(total, 1)) * 5))
        roast = "Not enough losses to prosecute responsibly."
    elif win_rate >= 60:
        score = min(4, max(0, round((100 - win_rate) / 10)))
        roast = "Annoyingly, the nonsense is working."
    elif win_rate >= 50:
        score = 5 + round((59 - win_rate) / 9 * 4)
        roast = "The deck is getting away with it often enough to become dangerous."
    elif win_rate >= 40:
        score = 10 + round((49 - win_rate) / 9 * 7)
        roast = "The deck remains legally playable, but the towers have concerns."
    elif win_rate >= 30:
        score = 18 + round((39 - win_rate) / 9 * 6)
        roast = "This is less ladder progression and more stubborn field research."
    elif total >= 10:
        score = 25 + round((29 - min(win_rate, 29)) / 29 * 5)
        roast = "The replay evidence suggests you are conducting a long-term experiment into losing with confidence."
    else:
        score = 20 + round((29 - min(win_rate, 29)) / 29 * 4)
        roast = "The win rate is bad, but the court wants a bigger sample before yelling properly."

    if total >= 8 and close_total >= 5 and close_losses > close_wins:
        score += min(3, round((close_losses - close_wins) / close_total * 5))
    score = min(30, score)
    confidence = confidence_from_sample(total, 8, 15)
    evidence = [
        f"Eligible personal-deck record: {wins}-{losses}-{draws}",
        f"Eligible personal-deck matches: {total}",
        f"Win rate: {win_rate}% / loss rate: {loss_rate}%",
        f"Close-game record: {close_wins}-{close_losses}",
    ]
    if verdict.get("main_deck_win_rate") is not None:
        evidence.append(f"Recent main-deck win rate: {verdict.get('main_deck_win_rate')}% across {verdict.get('main_deck_games', 0)} matches")
    return _score_group(
        "performance_loss",
        "Performance / Loss Score",
        score,
        30,
        confidence,
        total,
        evidence,
        "Eligible personal-deck results, loss rate, main-deck performance, and close-game evidence.",
        roast,
        raw_score=score,
    )


def calculate_level_reliance_component(level_analysis: dict[str, Any]) -> dict[str, Any]:
    sample = int(level_analysis.get("level_known_sample_size") or level_analysis.get("eligible_level_matches") or 0)
    chart = level_analysis.get("level_reliance_chart") or []
    by_key = {item.get("key"): item for item in chart if isinstance(item, dict)}
    over = by_key.get("overlevelled", {})
    even = by_key.get("even", {})
    under = by_key.get("underlevelled", {})
    over_matches = int(over.get("matches", 0) or 0)
    even_matches = int(even.get("matches", 0) or 0)
    under_matches = int(under.get("matches", 0) or 0)
    over_wins = int(over.get("wins", level_analysis.get("meaningful_level_advantage_wins", 0)) or 0)
    over_losses = int(over.get("losses", level_analysis.get("meaningful_level_advantage_losses", 0)) or 0)
    over_win_rate = int(over.get("win_rate", level_analysis.get("overlevelled_win_rate", 0)) or 0)
    non_over_matches = even_matches + under_matches
    non_over_wins = int(even.get("wins", 0) or 0) + int(under.get("wins", 0) or 0)
    non_over_win_rate = round(non_over_wins / non_over_matches * 100) if non_over_matches else 0
    total_wins = over_wins + non_over_wins

    if sample < 5:
        score = min(5, over_losses * 2 + over_wins)
    elif over_matches < 2:
        score = min(5, over_losses * 2)
    else:
        score = min(6, round(over_matches / max(sample, 1) * 6))
        if float(over.get("average_level_difference", 0) or 0) >= 1:
            score += 4
        if over_win_rate >= non_over_win_rate + 15 and over_wins:
            score += min(8, max(3, round((over_win_rate - non_over_win_rate) / 5)))
        if total_wins and over_wins / total_wins >= 0.6:
            score += 4
        if over_losses >= 2:
            score += min(7, 3 + over_losses * 2)
        if over_losses and over_win_rate < 50:
            score += 3
    score = min(25, score)
    confidence = "low" if sample < 5 or over_matches < 2 else confidence_from_sample(sample, 5, 12)
    roast = level_analysis.get("level_reliance_roast") or "No level excuse detected. This one is between you and the deck."
    evidence = [
        *level_analysis.get("evidence", []),
        f"Overlevelled win rate: {over_win_rate}%",
        f"Even/underlevelled combined win rate: {non_over_win_rate}%",
        f"Average level difference in wins: {level_analysis.get('average_level_difference_in_wins', 0)}",
        f"Average level difference in losses: {level_analysis.get('average_level_difference_in_losses', 0)}",
    ]
    return _score_group(
        "level_reliance",
        "Level-Reliance Score",
        score,
        25,
        confidence,
        sample,
        evidence,
        "Eligible level-known standard 1v1 matches only, split into overlevelled, even, and underlevelled records.",
        roast,
        raw_score=score,
    )


def calculate_troll_score(
    battle_summary: dict[str, Any],
    deck_analysis: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    clutch_analysis: dict[str, Any],
    win_rate_verdict: dict[str, Any] | None = None,
    selector: ExpressionSelector | None = None,
) -> dict[str, Any]:
    active_selector = selector or ExpressionSelector("fraud-score")
    community = analyse_community_meme_deck(deck_analysis, active_selector)
    community_group = _score_group(
        "community_meme",
        "Community Meme Deck Score",
        community["score"],
        45,
        community["confidence"],
        community["sample_size"],
        community["evidence"],
        "Local community-meme taxonomy with sensible stacking, package bonuses, and exact-meta dampening.",
        community["roast"],
        raw_score=community.get("raw_score", community["score"]),
        extra={
            "display_label": "Community Meme Score",
            "matched_cards": community.get("matched_cards", []),
            "matched_combinations": community.get("matched_combinations", []),
            "categories": community.get("categories", []),
            "band": community.get("band"),
            "disclaimer": community.get("disclaimer", COMMUNITY_MEME_DISCLAIMER),
        },
    )
    performance_group = calculate_performance_loss_component(battle_summary, win_rate_verdict, clutch_analysis)
    level_group = calculate_level_reliance_component(level_analysis)
    score_groups = [community_group, performance_group, level_group]
    score = min(100, sum(group["score"] for group in score_groups))
    label = "Community score pending"
    if score <= 14:
        label = "LEGALLY BORING"
    elif score <= 29:
        label = "MILD SUSPECT"
    elif score <= 44:
        label = "COMMUNITY SIDE-EYE"
    elif score <= 59:
        label = "MID-LADDER ALLEGATIONS"
    elif score <= 74:
        label = "CERTIFIED COMMUNITY MENACE"
    elif score <= 89:
        label = "PANIC-BUTTON PROFESSIONAL"
    else:
        label = "PUBLIC NUISANCE DECK"
    return {
        "score": score,
        "label": label,
        "components": score_groups,
        "score_groups": score_groups,
        "group_caps": {"community_meme": 45, "performance_loss": 30, "level_reliance": 25},
        "score_formula": {
            "community_meme": "0-45",
            "performance_loss": "0-30",
            "level_reliance": "0-25",
            "total": "min(100, Community Meme Deck Score + Performance / Loss Score + Level-Reliance Score)",
        },
    }


FRAUD_TIER_BANDS = [
    {
        "key": "legally_boring",
        "min": 0,
        "max": 14,
        "title": "LEGALLY BORING",
        "description": "This deck has avoided serious allegations. Unfortunately, it may actually be normal.",
        "headlines": [
            "The evidence tried to start drama, but the deck was mostly normal.",
            "The court looked for a scandal and found paperwork.",
        ],
    },
    {
        "key": "mild_suspect",
        "min": 15,
        "max": 29,
        "title": "MILD SUSPECT",
        "description": "A few choices deserve a raised eyebrow, not a full hearing.",
        "headlines": [
            "A few cards are acting suspicious, but nobody is calling the tower police yet.",
            "There is smoke, but it might just be Wizard asking for attention.",
        ],
    },
    {
        "key": "community_side_eye",
        "min": 30,
        "max": 44,
        "title": "COMMUNITY SIDE-EYE",
        "description": "The deck has entered the group chat and nobody is pretending to be surprised.",
        "headlines": [
            "The deck walked into the room and the group chat immediately got louder.",
            "This is not illegal. It is just very noticeable.",
        ],
    },
    {
        "key": "mid_ladder_allegations",
        "min": 45,
        "max": 59,
        "title": "MID-LADDER ALLEGATIONS",
        "description": "Several cards appear to have been selected during a stressful moment.",
        "headlines": [
            "Several choices here look like they were made during tower panic.",
            "The allegations are mid-ladder, but the receipts brought shoes.",
        ],
    },
    {
        "key": "certified_community_menace",
        "min": 60,
        "max": 74,
        "title": "CERTIFIED COMMUNITY MENACE",
        "description": "The deck does not violate any rules. It does, however, violate several social agreements.",
        "headlines": [
            "The app cannot ban this deck, but it did sigh heavily.",
            "This is legal gameplay with suspicious community side effects.",
        ],
    },
    {
        "key": "panic_button_professional",
        "min": 75,
        "max": 89,
        "title": "PANIC-BUTTON PROFESSIONAL",
        "description": "You have assembled enough emergency cards to make normal decision-making optional.",
        "headlines": [
            "Two panic buttons and no shame would be the polite summary.",
            "The deck saw normal interaction and filed for emergency powers.",
        ],
    },
    {
        "key": "public_nuisance_deck",
        "min": 90,
        "max": 100,
        "title": "PUBLIC NUISANCE DECK",
        "description": "The app cannot ban this deck, but it has submitted a strongly worded complaint.",
        "headlines": [
            "The deck is legal, but several towers have requested a welfare check.",
            "This is a public nuisance deck with a battle-log alibi.",
        ],
    },
]


def fraud_tier_for_score(score: int, confidence: str) -> dict[str, Any]:
    if confidence == "low":
        return {
            "key": "insufficient_evidence",
            "title": "INSUFFICIENT EVIDENCE, SUSPICIOUS VIBES",
            "description": "The battle log is too short for a conviction, but the deck has been noted.",
            "headlines": [
                "The court lacks evidence, but the vibes have been photographed.",
                "The battle log is short; the suspicion is not.",
            ],
        }
    for band in FRAUD_TIER_BANDS:
        if band["min"] <= score <= band["max"]:
            return band
    return FRAUD_TIER_BANDS[-1]


def fraud_tier_key(score: int) -> str:
    return fraud_tier_for_score(score, "medium")["key"]


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
    score_groups = list(troll_score.get("score_groups") or troll_score.get("components") or [])
    contributors = []
    for component in score_groups:
        contributors.append(
            {
                "key": component.get("key", component.get("group", component.get("label", "score_component"))),
                "label": component["label"],
                "group": component["group"],
                "raw_score": component.get("raw_score", component.get("raw_candidate_points", component.get("points", 0))),
                "raw_candidate_points": component.get("raw_candidate_points", component.get("raw_score", component.get("points", 0))),
                "applied_points": component.get("applied_points", component.get("points", 0)),
                "points": component.get("applied_points", component.get("points", 0)),
                "score": component.get("score", component.get("points", 0)),
                "max_score": component.get("max_score", component.get("max_points", 0)),
                "max_points": component.get("max_points", component.get("max_score", 0)),
                "description": component.get("description") or "Evidence-backed score contributor.",
                "evidence": component.get("evidence", []),
                "evidence_count": len(component.get("evidence", [])),
                "sample_size": component.get("sample_size", 0),
                "confidence": component.get("confidence", "low"),
                "excluded": component.get("excluded", False),
                "roast": component.get("roast", "The evidence filed a small but readable complaint."),
                "display_label": component.get("display_label", component.get("label")),
                "matched_cards": component.get("matched_cards", []),
                "matched_combinations": component.get("matched_combinations", []),
                "categories": component.get("categories", []),
                "band": component.get("band"),
            }
        )
    positive = [item for item in contributors if item["points"] > 0]
    if battle_summary.get("eligible_battles", battle_summary.get("battles_analysed", 0)) < 8:
        confidence = "low"
    else:
        confidence_values = [item["confidence"] for item in positive]
        confidence = "low" if not confidence_values else "medium" if "low" in confidence_values or "medium" in confidence_values else "high"
    tier_copy = fraud_tier_for_score(score, confidence)
    headline = selector.choose(tier_copy["headlines"], f"fraud:{tier_copy['key']}:headline")
    receipts = [evidence for contributor in contributors for evidence in contributor["evidence"]]
    return {
        "score": score,
        "tier": tier_copy["title"],
        "tier_key": tier_copy["key"],
        "tier_description": tier_copy["description"],
        "headline_roast": headline,
        "confidence": confidence,
        "overall_confidence_note": f"Overall confidence: {confidence.title()} - based on {battle_summary.get('eligible_battles', 0)} eligible personal-deck matches with per-claim thresholds applied.",
        "contributors": contributors,
        "score_groups": contributors,
        "score_receipts": receipts,
        "group_caps": troll_score.get("group_caps", {}),
        "score_formula": troll_score.get("score_formula", {}),
        "score_summary": f"{contributors[0]['label']} {contributors[0]['points']}/{contributors[0]['max_points']}, {contributors[1]['label']} {contributors[1]['points']}/{contributors[1]['max_points']}, {contributors[2]['label']} {contributors[2]['points']}/{contributors[2]['max_points']}" if len(contributors) >= 3 else "",
    }


def build_deck_personality(deck_analysis: dict[str, Any], selector: ExpressionSelector) -> dict[str, Any]:
    style = deck_analysis["estimated_deck_style"]
    copy = DECK_STYLE_COPY.get(style, {"plain": "Local deck style evidence is limited.", "roasts": ["The deck is custom enough that the receipts need to do the talking."]})
    traits = deck_analysis.get("structural_issues", [])
    issue_count = deck_analysis.get("structural_issue_count", 0)
    evidence = list(deck_analysis["personality_rule"].get("evidence", []))
    evidence.extend([f"{trait['label']}: {trait['explanation']}" for trait in traits])
    if not deck_analysis.get("current_matches_recent_main_deck", True):
        evidence.append("Current deck differs from the recent main deck. Historical results may reflect a previous deck.")
    current_roast = compose_deck_roast(
        cards=deck_analysis.get("current_deck", []),
        estimated_style=style,
        traits=traits,
        average_elixir=deck_analysis.get("average_elixir", 0),
        selector=selector,
        deck_role="current_deck",
        recent_main_cards=deck_analysis.get("recent_main_deck", {}).get("card_details", []),
        recent_main_uses=deck_analysis.get("recent_main_deck", {}).get("uses", 0),
        eligible_matches=deck_analysis.get("eligible_battle_history", {}).get("eligible_matches", 0),
    )
    recent_cards = deck_analysis.get("recent_main_deck", {}).get("card_details", [])
    recent_roast = None
    if recent_cards and not deck_analysis.get("current_exact_recent_main_deck", False):
        recent_average = average_deck_elixir(recent_cards)
        recent_style = safe_estimate_deck_style(recent_cards, recent_average)
        recent_roast = compose_deck_roast(
            cards=recent_cards,
            estimated_style=recent_style,
            traits=detect_deck_traits(recent_cards, recent_average, recent_style),
            average_elixir=recent_average,
            selector=selector,
            deck_role="recent_main_deck",
            recent_main_cards=recent_cards,
            recent_main_uses=deck_analysis.get("recent_main_deck", {}).get("uses", 0),
            eligible_matches=deck_analysis.get("eligible_battle_history", {}).get("eligible_matches", 0),
        )
    evidence.extend(current_roast.get("evidence", []))
    return {
        "title": current_roast["headline"],
        "style": style,
        "plain_explanation": current_roast["one_liner"],
        "roast": current_roast["main_roast"],
        "supporting_roast": current_roast["supporting_roast"],
        "traits": traits,
        "evidence": evidence,
        "confidence": current_roast.get("confidence", deck_analysis["personality_rule"].get("confidence", "medium")),
        "current_matches_recent_main_deck": deck_analysis.get("current_matches_recent_main_deck", False),
        "current_deck_roast": current_roast,
        "recent_main_deck_roast": recent_roast,
        "legacy_plain_explanation": copy["plain"],
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
        if emotional_support.get("detected"):
            emotional_support = {
                **emotional_support,
                "card_details": card_details_from_player_context(
                    player_tag,
                    emotional_support["card"],
                    deck_analysis.get("current_deck", []),
                    normalized,
                    self.card_service,
                ),
            }
        main_character = analyse_main_character(player_tag, normalized)
        clutch_analysis = analyse_clutch(battle_summary)
        divorce = recommend_deck_divorce(player_tag, normalized, deck_analysis["current_deck"])
        favourite_card_analysis = analyse_favourite_card(player_tag, normalized, deck_analysis, self.card_service)
        feared_card_analysis = analyse_feared_card(player_tag, normalized, self.card_service)
        win_rate_verdict = analyse_win_rate_verdict(player_tag, normalized, behaviour_analysis)
        troll_score = calculate_troll_score(battle_summary, deck_analysis, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, clutch_analysis, win_rate_verdict, selector)
        fraud_score = build_fraud_score(troll_score, battle_summary, deck_analysis, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, clutch_analysis, selector)
        deck_personality = build_deck_personality(deck_analysis, selector)
        personality_report = build_personality_report(deck_analysis, battle_summary, matchup_analysis, level_analysis, behaviour_analysis, emotional_support, main_character, fraud_score, selector, goblin_mode)
        roast_system = compose_roast_system(
            favourite_card_analysis=favourite_card_analysis,
            feared_card_analysis=feared_card_analysis,
            win_rate_verdict=win_rate_verdict,
            deck_analysis=deck_analysis,
            deck_personality=deck_personality,
            behaviour_analysis=behaviour_analysis,
            matchup_analysis=matchup_analysis,
            level_analysis=level_analysis,
            emotional_support=emotional_support,
            fraud_score=fraud_score,
            selector=selector,
        )
        favourite_card_analysis = roast_system["favourite_card_analysis"]
        feared_card_analysis = roast_system["feared_card_analysis"]
        win_rate_verdict = roast_system["win_rate_verdict"]

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
        narrative = roast_system["roast_narrative"]
        title = narrative.get("final_title") or f"{personality_report['title']} - {fraud_score['tier']}".strip()
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
            "favourite_card_analysis": favourite_card_analysis,
            "feared_card_analysis": feared_card_analysis,
            "win_rate_verdict": win_rate_verdict,
            "roast_narrative": narrative,
            "roast_modules": roast_system["roast_modules"],
            "card_evidence_gallery": roast_system["card_evidence_gallery"],
            "fraud_score": fraud_score,
            "personality_report": personality_report,
            "roast_report": {
                "title": title,
                "troll_score": fraud_score["score"],
                "score_label": fraud_score["tier"],
                "headline_roast": narrative.get("opening_charge") or fraud_score["headline_roast"],
                "evidence": fraud_score["score_receipts"] or narrative.get("opening_evidence") or headline_roast["evidence"],
                "score_breakdown": fraud_score["contributors"],
            },
            "roasts": roasts,
            "disclaimer": "Results are based on eligible public battle-log deck, crown, level, and matchup data. Draft, 2v2, event, capped, and incomplete-deck modes are excluded from personal-deck behavioural claims.",
        }


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_card_service(), RoastEngine())
