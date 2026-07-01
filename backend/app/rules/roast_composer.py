from __future__ import annotations

from typing import Any

from app.rules.expression_selector import ExpressionSelector, format_template


FAVOURITE_CARD_TEMPLATES = [
    "{card} appeared in {used}/{total} eligible games ({usage_rate}%). At this point it needs a reserved chair and a tax form.",
    "You brought {card} to {used} eligible games like it owed you trophies. The result: {win_rate}% win rate, {delta_label} versus baseline.",
    "{card} is not in the deck. {card} is the deck's emotional foreman, clocking in for {usage_rate}% of the inspected matches.",
    "{card} has survived {used} appearances in the evidence locker. That is not a card choice; that is a lifestyle with elixir attached.",
    "The court sees {card} in {used}/{total} eligible games. Subtlety has been escorted out of the arena.",
    "{card} keeps returning like a bad habit with card art. Usage: {usage_rate}%. Performance: {win_rate}%. Receipts: unfortunately real.",
    "This account has a {card} dependency. It might be genius, it might be bullshit, but it is absolutely documented.",
    "{card} is carrying paperwork in {used} eligible games. The baseline comparison says {delta_label}, so the allegation has numbers now.",
    "You keep putting {card} in the lineup like the rest of the deck is an optional accessory.",
]


FEARED_CARD_TEMPLATES = [
    "{card} appeared in {games} eligible games. You lost {losses}. That is not a hard counter claim; that is a recurring problem with witnesses.",
    "Every time {card} shows up, the loss rate jumps by {excess_label}. The card is not playing Clash Royale; it is collecting evidence.",
    "{card} has turned {games} recorded matchups into a damn case file: {losses} losses, {loss_rate}% loss rate.",
    "The battle log keeps finding {card} near the scene. Baseline loss rate: {baseline_loss_rate}%. Versus this card: {loss_rate}%.",
    "{card} is not confirmed as your owner, but {games} encounters and {losses} losses make the paperwork uncomfortable.",
    "Against {card}, the tower starts making arrangements. Loss rate: {loss_rate}%, which is {excess_label} above your normal damage.",
    "{card} keeps walking into the arena and your results start sweating. That is a detected pattern, not a mythology lecture.",
    "{card} has been bullying this battle log with statistical shoes on: {losses}/{games} losses against it.",
    "The matchup is not declared impossible. It is declared suspicious as hell, with {games} sightings and {excess_label} excess loss rate.",
]


WIN_RATE_TEMPLATES: dict[str, list[str]] = {
    "elite": [
        "{win_rate}% win rate over {total} eligible matches. Annoyingly competent. Please leave some trophies for the rest of the queue.",
        "{wins}-{losses} across eligible matches is strong enough that the report had to put respect in writing, which is disgusting.",
    ],
    "winning": [
        "{win_rate}% win rate. You are winning often enough to keep believing every questionable decision was secretly genius.",
        "{wins} wins from {total} eligible matches. Not flawless, but the ladder cannot laugh you out of court today.",
    ],
    "volatile": [
        "{win_rate}% win rate. Perfectly balanced between smart adaptation and complete bullshit.",
        "{wins}-{losses} in eligible matches. The strategy is alive, but it keeps touching hot stoves.",
    ],
    "concerning": [
        "{win_rate}% win rate. The deck has concerns. The towers have concerns. Frankly, everyone has concerns.",
        "{losses} losses in {total} eligible matches is not a disaster, but it is definitely making eye contact with one.",
    ],
    "catastrophic": [
        "{win_rate}% win rate. This is not a ladder push. This is a public demonstration of stubbornness.",
        "{wins} wins from {total} eligible matches. The sample is large enough for the court to whisper, damn.",
    ],
    "insufficient": [
        "Only {total} eligible matches. Not enough evidence to roast responsibly, though the vibes are still under review.",
        "{total} eligible matches is too tiny for a win-rate conviction. The app refuses to prosecute on pocket lint.",
    ],
}


INSUFFICIENT_EVIDENCE_TEMPLATES = [
    "The evidence locker is light. Bring back more eligible ladder games before we start yelling with confidence.",
    "Suspicion noted. Conviction delayed pending more embarrassing replays.",
    "The sample is too small to establish a pattern of nonsense, which is rude because the jokes were ready.",
    "The court cannot confirm the allegation yet. It has only enough data to raise one eyebrow.",
    "No responsible roast here. The battle log arrived with vibes and forgot the receipts.",
    "The app refuses to frame a card based on crumbs. More eligible matches, then we talk.",
]


FINAL_VERDICT_TEMPLATES = [
    {
        "id": "limited",
        "title": "No Conviction Due to Insufficient Battle Logs",
        "text": "The evidence is too thin for a confident sentence. Suspicion noted; paperwork returned for more ladder games.",
    },
    {
        "id": "loyalist_victim",
        "title": "One-Deck Loyalist, Matchup Victim",
        "text": "The deck loyalty is real, and the matchup pain has receipts. The court respects the commitment while questioning the results.",
    },
    {
        "id": "deck_monogamist",
        "title": "Deck Monogamist With Questionable Results",
        "text": "You stuck with the core. Admirable. Possibly cursed. Definitely documented.",
    },
    {
        "id": "panic",
        "title": "Verified Post-Loss Rebuilder",
        "text": "The deck changes crossed the strict threshold. This was not experimentation; this was emergency construction after impact.",
    },
    {
        "id": "hopper",
        "title": "Flexible To A Fault",
        "text": "The account tried enough deck cores to qualify as a moving service. The report will not call it panic without the loss-timing receipts.",
    },
    {
        "id": "high_elixir",
        "title": "High-Elixir Optimist",
        "text": "The deck spends like confidence is refundable. Sometimes it works; sometimes the elixir economy files a complaint.",
    },
    {
        "id": "signature_crutch",
        "title": "Certified Ladder Nuisance",
        "text": "The favourite card is showing up and producing results. Annoying, effective, and legally admissible.",
    },
    {
        "id": "comfort_pick",
        "title": "Emotionally Attached to Bad Decisions",
        "text": "A repeated card is underperforming against baseline and still getting invited back. That is not loyalty; that is elixir Stockholm syndrome.",
    },
    {
        "id": "suspicious",
        "title": "Statistically Suspicious, Legally Inconclusive",
        "text": "Several patterns smell funny, but the report is keeping the jokes tied to verified numbers.",
    },
    {
        "id": "tactical_soup",
        "title": "Tactical Soup Survivor",
        "text": "The current deck has enough independent issues to make the spoon nervous, but every charge still comes with evidence.",
    },
]


OPENING_TEMPLATES = [
    "Opening charge: {fact}",
    "The court opens with this: {fact}",
    "First allegation on the docket: {fact}",
    "The report bangs the desk and points at this receipt: {fact}",
]


BEHAVIOUR_TEMPLATES = {
    "ONE_DECK_WARRIOR": [
        "Deck loyalty is verified: {main_games}/{eligible} eligible matches used the dominant core. Same deck, same wounds, impressive paperwork.",
        "This is deck monogamy with receipts: {same_core}% dominant-core usage and no panic-switch conviction.",
    ],
    "PANIC_SWITCHER": [
        "{changes} major deck changes followed {opportunities} valid losses. Your emergency deck switch achieved absolutely fuck all unless proven otherwise.",
        "The loss-to-rebuild pipeline crossed the strict threshold: {changes}/{opportunities} post-loss changes.",
    ],
    "DECK_HOPPER": [
        "{unique_decks} materially distinct deck cores in {eligible} eligible matches. The deck history needs a forwarding address.",
        "The account moved between {unique_decks} deck cores. Flexible, yes. Peaceful, absolutely not.",
    ],
    "STABLE_WITH_MINOR_VARIATIONS": [
        "Stable with minor variations: the deck changed, but not enough to call it a meltdown.",
        "The core stayed mostly intact. The court sees testing, not panic shopping.",
    ],
}


def template_catalog_counts() -> dict[str, int]:
    return {
        "favourite_card": len(FAVOURITE_CARD_TEMPLATES),
        "feared_card": len(FEARED_CARD_TEMPLATES),
        "win_rate": sum(len(templates) for templates in WIN_RATE_TEMPLATES.values()),
        "insufficient_evidence": len(INSUFFICIENT_EVIDENCE_TEMPLATES),
        "final_verdict": len(FINAL_VERDICT_TEMPLATES),
    }


def signed_pp(value: int | float | None) -> str:
    numeric = int(round(float(value or 0)))
    return f"{numeric:+d} pp"


def confidence_rank(value: str | None) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(value or "low"), 0)


def choose_rendered(selector: ExpressionSelector, templates: list[str], bucket: str, values: dict[str, Any]) -> str:
    return format_template(selector.choose(templates, bucket), values)


def module(
    *,
    module_id: str,
    category: str,
    title: str,
    text: str,
    confidence: str,
    severity: str,
    eligibility_conditions: list[str],
    required_evidence: list[str],
    evidence: list[str],
    linked_cards: list[dict[str, Any]] | None = None,
    score_impact: str | None = None,
) -> dict[str, Any]:
    return {
        "id": module_id,
        "category": category,
        "title": title,
        "text": text,
        "confidence": confidence,
        "confidence_requirement": "Only emitted as a claim when its evidence threshold is satisfied; otherwise emitted as limited evidence.",
        "severity": severity,
        "eligibility_conditions": eligibility_conditions,
        "required_evidence": required_evidence,
        "evidence": evidence,
        "linked_cards": linked_cards or [],
        "score_impact": score_impact or "No direct score impact; the capped Fraud Score is calculated by the existing evidence rules.",
    }


def stat(label: str, value: Any, tone: str = "blue") -> dict[str, Any]:
    return {"label": label, "value": value, "tone": tone}


def win_rate_band(win_rate: int, total: int) -> str:
    if total < 8:
        return "insufficient"
    if win_rate >= 70:
        return "elite"
    if win_rate >= 55:
        return "winning"
    if win_rate >= 45:
        return "volatile"
    if win_rate >= 35:
        return "concerning"
    return "catastrophic"


def gallery_item(
    *,
    item_id: str,
    category: str,
    title: str,
    card: dict[str, Any] | None,
    card_name: str,
    roast: str,
    stats: list[dict[str, Any]],
    evidence: list[str],
    confidence: str,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "category": category,
        "title": title,
        "card": card,
        "card_name": card_name,
        "roast": roast,
        "stats": stats,
        "evidence": evidence,
        "confidence": confidence,
    }


def final_candidates(
    favourite: dict[str, Any],
    feared: dict[str, Any],
    win_rate: dict[str, Any],
    deck_analysis: dict[str, Any],
    behaviour: dict[str, Any],
    fraud_score: dict[str, Any],
    emotional_support: dict[str, Any],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    by_id = {item["id"]: item for item in FINAL_VERDICT_TEMPLATES}
    if win_rate.get("total_eligible_matches", 0) < 8:
        candidates.append(by_id["limited"])
    if behaviour.get("classification") == "PANIC_SWITCHER":
        candidates.append(by_id["panic"])
    if behaviour.get("classification") == "DECK_HOPPER":
        candidates.append(by_id["hopper"])
    if behaviour.get("classification") == "ONE_DECK_WARRIOR" and not feared.get("is_insufficient_evidence"):
        candidates.append(by_id["loyalist_victim"])
    if behaviour.get("classification") == "ONE_DECK_WARRIOR":
        candidates.append(by_id["deck_monogamist"])
    if deck_analysis.get("average_elixir", 0) >= 4.6:
        candidates.append(by_id["high_elixir"])
    if favourite.get("is_true_single_card_favourite") and favourite.get("favourite_card_performance_delta", 0) >= 8:
        candidates.append(by_id["signature_crutch"])
    if emotional_support.get("detected") or (favourite.get("is_true_single_card_favourite") and favourite.get("favourite_card_performance_delta", 0) <= -12):
        candidates.append(by_id["comfort_pick"])
    if deck_analysis.get("structural_issue_count", 0) >= 3:
        candidates.append(by_id["tactical_soup"])
    if fraud_score.get("score", 0) <= 35:
        candidates.append(by_id["suspicious"])
    return candidates or [by_id["suspicious"]]


def compose_roast_system(
    *,
    favourite_card_analysis: dict[str, Any],
    feared_card_analysis: dict[str, Any],
    win_rate_verdict: dict[str, Any],
    deck_analysis: dict[str, Any],
    deck_personality: dict[str, Any],
    behaviour_analysis: dict[str, Any],
    matchup_analysis: dict[str, Any],
    level_analysis: dict[str, Any],
    emotional_support: dict[str, Any],
    fraud_score: dict[str, Any],
    selector: ExpressionSelector,
) -> dict[str, Any]:
    favourite = dict(favourite_card_analysis)
    feared = dict(feared_card_analysis)
    win_rate = dict(win_rate_verdict)
    modules: list[dict[str, Any]] = []
    gallery: list[dict[str, Any]] = []

    fav_values = {
        "card": favourite.get("favourite_card_name") or "the full deck",
        "used": favourite.get("favourite_card_usage_count", 0),
        "total": favourite.get("eligible_match_count", 0),
        "usage_rate": favourite.get("favourite_card_usage_rate", 0),
        "win_rate": favourite.get("favourite_card_win_rate", 0),
        "delta_label": signed_pp(favourite.get("favourite_card_performance_delta", 0)),
    }
    if favourite.get("is_true_single_card_favourite"):
        fav_roast = choose_rendered(selector, FAVOURITE_CARD_TEMPLATES, "composer:favourite", fav_values)
        favourite["roast"] = fav_roast
        severity = "sharp" if abs(favourite.get("favourite_card_performance_delta", 0)) >= 12 else "playful"
        modules.append(
            module(
                module_id="favourite-card-indictment",
                category="favourite_card",
                title="Favourite Card Indictment",
                text=fav_roast,
                confidence=favourite.get("favourite_card_confidence", "low"),
                severity=severity,
                eligibility_conditions=["At least 8 eligible personal-deck matches", "A single card leads usage without a full-deck tie"],
                required_evidence=["eligible_match_count", "usage_count", "usage_rate", "card_win_rate", "player_baseline_win_rate"],
                evidence=favourite.get("evidence", []),
                linked_cards=[favourite["favourite_card"]] if favourite.get("favourite_card") else [],
                score_impact="Comedy-only unless the separate emotional-support threshold also fired.",
            )
        )
        gallery.append(
            gallery_item(
                item_id="favourite-card",
                category="favourite_card",
                title="Favourite Card",
                card=favourite.get("favourite_card"),
                card_name=favourite.get("favourite_card_name", ""),
                roast=fav_roast,
                stats=[
                    stat("Used", f"{fav_values['used']}/{fav_values['total']}", "blue"),
                    stat("Usage", f"{fav_values['usage_rate']}%", "gold"),
                    stat("Win rate", f"{fav_values['win_rate']}%", "green" if favourite.get("favourite_card_performance_delta", 0) >= 0 else "red"),
                    stat("Vs baseline", fav_values["delta_label"], "green" if favourite.get("favourite_card_performance_delta", 0) >= 0 else "red"),
                ],
                evidence=favourite.get("evidence", []),
                confidence=favourite.get("favourite_card_confidence", "low"),
            )
        )
    else:
        limited = favourite.get("favourite_card_reason") or choose_rendered(selector, INSUFFICIENT_EVIDENCE_TEMPLATES, "composer:favourite:limited", fav_values)
        favourite["roast"] = limited
        modules.append(
            module(
                module_id="favourite-card-limited",
                category="limited_evidence",
                title="Favourite Card Evidence Limited",
                text=limited,
                confidence=favourite.get("favourite_card_confidence", "low"),
                severity="light",
                eligibility_conditions=["Favourite-card roast withheld unless usage threshold and single-card distinction are satisfied"],
                required_evidence=["eligible_match_count", "card_usage_counts"],
                evidence=favourite.get("evidence", []),
            )
        )

    feared_values = {
        "card": feared.get("feared_card_name") or feared.get("leading_candidate_name") or "the suspect card",
        "games": feared.get("games_against", 0),
        "losses": feared.get("losses_against", 0),
        "loss_rate": feared.get("loss_rate_against", 0),
        "baseline_loss_rate": feared.get("baseline_loss_rate", 0),
        "excess_label": signed_pp(feared.get("excess_loss_rate", 0)),
    }
    if not feared.get("is_insufficient_evidence"):
        feared_roast = choose_rendered(selector, FEARED_CARD_TEMPLATES, "composer:feared", feared_values)
        feared["roast"] = feared_roast
        modules.append(
            module(
                module_id="feared-card-trauma",
                category="feared_card",
                title="Most Feared Card",
                text=feared_roast,
                confidence=feared.get("feared_card_confidence", "low"),
                severity="sharp" if feared.get("excess_loss_rate", 0) >= 20 else "playful",
                eligibility_conditions=["At least 5 eligible encounters with the opponent card", "Loss rate against card is above baseline"],
                required_evidence=["games_against", "wins_against", "losses_against", "loss_rate_against", "baseline_loss_rate", "excess_loss_rate"],
                evidence=feared.get("evidence", []),
                linked_cards=[feared["feared_card"]] if feared.get("feared_card") else [],
                score_impact="Related matchup weakness can affect the capped Fraud Score through the existing matchup rules.",
            )
        )
        gallery.append(
            gallery_item(
                item_id="feared-card",
                category="feared_card",
                title="Most Feared Card",
                card=feared.get("feared_card"),
                card_name=feared.get("feared_card_name", ""),
                roast=feared_roast,
                stats=[
                    stat("Faced", feared_values["games"], "blue"),
                    stat("Lost", f"{feared_values['losses']}/{feared_values['games']}", "red"),
                    stat("Loss rate", f"{feared_values['loss_rate']}%", "red"),
                    stat("Excess loss", feared_values["excess_label"], "gold"),
                ],
                evidence=feared.get("evidence", []),
                confidence=feared.get("feared_card_confidence", "low"),
            )
        )
    else:
        limited = feared.get("evidence_summary") or choose_rendered(selector, INSUFFICIENT_EVIDENCE_TEMPLATES, "composer:feared:limited", feared_values)
        feared["roast"] = limited
        modules.append(
            module(
                module_id="feared-card-limited",
                category="limited_evidence",
                title="Feared Card Evidence Limited",
                text=limited,
                confidence=feared.get("feared_card_confidence", "low"),
                severity="light",
                eligibility_conditions=["Feared-card claim withheld unless 5 encounters and excess loss rate are present"],
                required_evidence=["games_against", "baseline_loss_rate", "excess_loss_rate"],
                evidence=feared.get("evidence", []),
                linked_cards=[feared["leading_candidate"]] if feared.get("leading_candidate") else [],
            )
        )

    band = win_rate_band(int(win_rate.get("win_rate", 0)), int(win_rate.get("total_eligible_matches", 0)))
    win_values = {
        "win_rate": win_rate.get("win_rate", 0),
        "wins": win_rate.get("wins", 0),
        "losses": win_rate.get("losses", 0),
        "total": win_rate.get("total_eligible_matches", 0),
    }
    win_roast = choose_rendered(selector, WIN_RATE_TEMPLATES[band], f"composer:win-rate:{band}", win_values)
    win_rate["band"] = band
    win_rate["roast"] = win_roast
    modules.append(
        module(
            module_id="win-rate-verdict",
            category="win_rate" if band != "insufficient" else "limited_evidence",
            title="Win Rate Verdict",
            text=win_roast,
            confidence=win_rate.get("confidence", "low"),
            severity="sharp" if band in {"concerning", "catastrophic"} else "playful",
            eligibility_conditions=["Uses eligible personal-deck matches only", "Low-win-rate roasts require visible sample size"],
            required_evidence=["total_eligible_matches", "wins", "losses", "win_rate"],
            evidence=win_rate.get("evidence", []),
            score_impact="Win rate is shown as context; score changes still come from specific evidence-backed contributors.",
        )
    )

    classification = behaviour_analysis.get("classification", "")
    behaviour_templates = BEHAVIOUR_TEMPLATES.get(classification)
    if behaviour_templates:
        behaviour_text = choose_rendered(
            selector,
            behaviour_templates,
            f"composer:behaviour:{classification}",
            {
                "main_games": behaviour_analysis.get("main_deck_games", 0),
                "eligible": behaviour_analysis.get("eligible_battles", 0),
                "same_core": behaviour_analysis.get("same_core_percentage", 0),
                "changes": behaviour_analysis.get("changes_after_losses", 0),
                "opportunities": behaviour_analysis.get("post_loss_opportunities", 0),
                "unique_decks": behaviour_analysis.get("materially_distinct_deck_cores", behaviour_analysis.get("unique_decks", 0)),
            },
        )
        category = "panic_switching" if classification == "PANIC_SWITCHER" else "deck_hopper" if classification == "DECK_HOPPER" else "deck_loyalty"
        modules.append(
            module(
                module_id=f"behaviour-{classification.lower()}",
                category=category,
                title=behaviour_analysis.get("title", "Deck Behaviour"),
                text=behaviour_text,
                confidence=behaviour_analysis.get("confidence", "low"),
                severity="sharp" if classification == "PANIC_SWITCHER" else "playful",
                eligibility_conditions=["Strict deck-switch classifier supplied this classification"],
                required_evidence=["eligible_battles", "materially_distinct_deck_cores", "post_loss_opportunities", "changes_after_losses"],
                evidence=behaviour_analysis.get("evidence", []),
                linked_cards=[{"name": name} for name in behaviour_analysis.get("main_deck", [])[:3]],
                score_impact="Only strict panic/deck-hopper evidence can contribute to deck-switching score.",
            )
        )

    if emotional_support.get("detected"):
        text = f"{emotional_support.get('card')} keeps returning with a {emotional_support.get('win_rate')}% win rate against a {emotional_support.get('baseline_win_rate')}% baseline. That is comfort-pick behavior with receipts."
        modules.append(
            module(
                module_id="emotional-support-card",
                category="emotional_support_card",
                title="Emotional Support Card",
                text=text,
                confidence=emotional_support.get("confidence", "low"),
                severity="sharp",
                eligibility_conditions=["Card used in at least 8 eligible matches", "Card performs at least 15 pp below baseline across multiple deck variants"],
                required_evidence=["used", "win_rate", "baseline_win_rate", "deck_variants"],
                evidence=emotional_support.get("evidence", []),
                linked_cards=[emotional_support["card_details"]] if emotional_support.get("card_details") else [{"name": emotional_support.get("card", "")}],
                score_impact="Can contribute to the capped deck-switching score group.",
            )
        )
        gallery.append(
            gallery_item(
                item_id="emotional-support-card",
                category="emotional_support_card",
                title="Emotional Support Card",
                card=emotional_support.get("card_details"),
                card_name=emotional_support.get("card", ""),
                roast=text,
                stats=[
                    stat("Used", emotional_support.get("used", 0), "blue"),
                    stat("Win rate", f"{emotional_support.get('win_rate', 0)}%", "red"),
                    stat("Baseline", f"{emotional_support.get('baseline_win_rate', 0)}%", "gold"),
                    stat("Variants", emotional_support.get("deck_variants", 0), "blue"),
                ],
                evidence=emotional_support.get("evidence", []),
                confidence=emotional_support.get("confidence", "low"),
            )
        )

    best = favourite.get("best_signature_card")
    if best and best.get("card_name") != favourite.get("favourite_card_name"):
        text = f"{best.get('card_name')} quietly posted a {best.get('win_rate')}% win rate over {best.get('used')} eligible uses. The side character brought receipts."
        gallery.append(
            gallery_item(
                item_id="best-signature-card",
                category="favourite_card_performance",
                title="Best Signature Card",
                card=best.get("card"),
                card_name=best.get("card_name", ""),
                roast=text,
                stats=[
                    stat("Used", best.get("used", 0), "blue"),
                    stat("Win rate", f"{best.get('win_rate', 0)}%", "green"),
                    stat("Vs baseline", signed_pp(best.get("delta", 0)), "green"),
                ],
                evidence=best.get("evidence", []),
                confidence=best.get("confidence", "low"),
            )
        )

    if level_analysis.get("total_losses_with_levels", 0) >= 5 and level_analysis.get("meaningful_level_advantage_losses", 0):
        modules.append(
            module(
                module_id="overlevelled-losses",
                category="overlevelled_loss",
                title="Overlevelled Losses",
                text=f"{level_analysis.get('meaningful_level_advantage_losses')} losses came with meaningful average level advantage. The upgrades arrived; the result still filed a complaint.",
                confidence=level_analysis.get("confidence", "low"),
                severity="sharp",
                eligibility_conditions=["At least 5 eligible level-known losses", "Player average level exceeded opponent by threshold"],
                required_evidence=["total_losses_with_levels", "meaningful_level_advantage_losses", "average_level_difference"],
                evidence=level_analysis.get("evidence", []),
                score_impact="Can contribute through the capped level-advantage score group.",
            )
        )

    if deck_analysis.get("structural_issue_count", 0):
        issue_names = ", ".join(issue.get("label", "") for issue in deck_analysis.get("structural_issues", [])[:3])
        modules.append(
            module(
                module_id="current-deck-issues",
                category="current_deck_issue",
                title="Current Deck Under Review",
                text=f"Current deck issue list: {issue_names}. The deck may still win, but it is doing so while carrying questionable luggage.",
                confidence=deck_personality.get("confidence", "low"),
                severity="playful",
                eligibility_conditions=["Current deck metadata has enough resolved card roles"],
                required_evidence=["structural_issues", "deck_identity_score", "average_elixir"],
                evidence=deck_personality.get("evidence", []),
                linked_cards=deck_analysis.get("current_deck", [])[:3],
                score_impact="Only specific structural issues add capped deck-construction score.",
            )
        )

    if not deck_analysis.get("current_matches_recent_main_deck", True):
        modules.append(
            module(
                module_id="recent-main-deck-mismatch",
                category="recent_main_deck_issue",
                title="Current Deck Differs From Recent Main",
                text="The current deck is not the recent main deck, so the report keeps historical blame on the old paperwork instead of inventing new drama.",
                confidence="medium",
                severity="light",
                eligibility_conditions=["Current deck and recent main deck differ materially"],
                required_evidence=["current_deck_key", "recent_main_deck.key"],
                evidence=["Current deck differs from the recent main deck. Historical results may reflect a previous deck."],
            )
        )

    predator = matchup_analysis.get("natural_predator", {})
    if predator.get("core_cards"):
        modules.append(
            module(
                module_id="feared-card-core",
                category="feared_card_core",
                title="Recurring Opponent Core",
                text=f"The recurring opponent core showed up in {predator.get('matches')} eligible matches with a {predator.get('loss_rate', 0)}% loss rate. Not a hard-counter claim, but the arena keeps leaving fingerprints.",
                confidence=predator.get("confidence", "low"),
                severity="sharp" if predator.get("excess_loss_rate", 0) >= 20 else "playful",
                eligibility_conditions=["Opponent card core appears in enough eligible matches", "Core loss rate exceeds baseline"],
                required_evidence=["core_cards", "matches", "losses", "loss_rate", "baseline_loss_rate"],
                evidence=predator.get("evidence", []),
                linked_cards=[{"name": name} for name in predator.get("core_cards", [])],
                score_impact="Related matchup weakness can contribute through the capped matchup score group.",
            )
        )

    final_choice = selector.choose(
        final_candidates(favourite, feared, win_rate, deck_analysis, behaviour_analysis, fraud_score, emotional_support),
        "composer:final-verdict",
    )
    final_text = format_template(final_choice["text"], {"score": fraud_score.get("score", 0), "deck_type": deck_personality.get("title", "")})
    modules.append(
        module(
            module_id="final-verdict",
            category="final_verdict",
            title=final_choice["title"],
            text=final_text,
            confidence=fraud_score.get("confidence", "low"),
            severity="dramatic",
            eligibility_conditions=["Combines only modules already selected by evidence gates"],
            required_evidence=["fraud_score", "behaviour_classification", "eligible_match_count"],
            evidence=(fraud_score.get("score_receipts") or win_rate.get("evidence", []))[:8],
            score_impact="Summarizes existing score contributors without adding new points.",
        )
    )

    opening_facts: list[tuple[int, str, list[str]]] = []
    if favourite.get("is_true_single_card_favourite") and confidence_rank(favourite.get("favourite_card_confidence")) >= 1:
        opening_facts.append((70 + abs(int(favourite.get("favourite_card_performance_delta", 0))), f"{favourite.get('favourite_card_name')} appeared in {favourite.get('favourite_card_usage_count')}/{favourite.get('eligible_match_count')} eligible games with a {favourite.get('favourite_card_win_rate')}% win rate.", favourite.get("evidence", [])))
    if not feared.get("is_insufficient_evidence") and confidence_rank(feared.get("feared_card_confidence")) >= 1:
        opening_facts.append((80 + max(0, int(feared.get("excess_loss_rate", 0))), f"{feared.get('feared_card_name')} produced a {feared.get('loss_rate_against')}% loss rate against you, {signed_pp(feared.get('excess_loss_rate'))} above baseline.", feared.get("evidence", [])))
    if int(win_rate.get("total_eligible_matches", 0)) >= 8:
        opening_facts.append((50 + abs(50 - int(win_rate.get("win_rate", 0))), f"eligible win rate sits at {win_rate.get('win_rate')}% over {win_rate.get('total_eligible_matches')} matches.", win_rate.get("evidence", [])))
    if behaviour_analysis.get("classification") == "PANIC_SWITCHER":
        opening_facts.append((95, f"{behaviour_analysis.get('changes_after_losses')} major deck changes followed {behaviour_analysis.get('post_loss_opportunities')} valid losses.", behaviour_analysis.get("evidence", [])))
    if not opening_facts:
        opening_facts.append((1, "the evidence is limited, so the report is roasting carefully instead of inventing nonsense.", win_rate.get("evidence", [])))

    _, opening_fact, opening_evidence = sorted(opening_facts, key=lambda item: item[0], reverse=True)[0]
    opening_charge = choose_rendered(selector, OPENING_TEMPLATES, "composer:opening", {"fact": opening_fact})

    narrative = {
        "opening_charge": opening_charge,
        "opening_evidence": opening_evidence,
        "favourite_card_indictment": favourite.get("roast", ""),
        "feared_card_trauma": feared.get("roast", ""),
        "win_rate_verdict": win_rate.get("roast", ""),
        "deck_personality": deck_personality.get("roast", ""),
        "final_title": final_choice["title"],
        "final_verdict": final_text,
        "arc": [
            "Opening charge",
            "Favourite-card indictment",
            "Feared-card trauma report",
            "Win-rate verdict",
            "Deck personality",
            "Final verdict",
        ],
    }

    return {
        "favourite_card_analysis": favourite,
        "feared_card_analysis": feared,
        "win_rate_verdict": win_rate,
        "roast_narrative": narrative,
        "roast_modules": modules,
        "card_evidence_gallery": gallery,
    }
