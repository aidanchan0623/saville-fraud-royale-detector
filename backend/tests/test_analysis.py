import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.analysis_service import (
    AnalysisService,
    REPORT_SCHEMA_VERSION,
    analyse_favourite_card,
    analyse_feared_card,
    analyse_win_rate_verdict,
    average_deck_elixir,
    build_fraud_score,
    build_deck_personality,
    calculate_battle_summary,
    calculate_troll_score,
    classify_level_disadvantage,
    deck_similarity,
    detect_deck_traits,
    detect_emotional_support_card,
    enrich_card,
    detect_panic_switching,
    normalize_player_tag,
    rank_traumatic_opponent_cards,
)
from app.services.battle_normalizer import deck_key, material_deck_change, normalize_battles
from app.models.schemas import ReportResponse
from app.rules.deck_templates import DECK_STYLE_COPY
from app.rules.deck_roast_composer import compose_deck_roast, deck_roast_catalog_counts
from app.rules.expression_selector import ExpressionSelector
from app.rules.fraud_score_templates import CONTRIBUTOR_COPY, TIER_COPY
from app.rules.personality_templates import GOBLIN_INTERVENTIONS, PERSONALITY_TEMPLATES
from app.rules.roast_composer import template_catalog_counts
from app.services.card_data_service import get_card_service
from app.services.roast_engine import RoastEngine


PLAYER_TAG = "#TEST01"


def deck(names, level=13):
    return get_card_service().hydrate_deck(names, level)


def battle(player_cards, opponent_cards, result="loss", player_level=13, opponent_level=13):
    crowns = {
        "win": (2, 1),
        "loss": (1, 2),
        "draw": (1, 1),
        "three_loss": (0, 3),
    }[result]
    return {
        "type": "PvP",
        "battleTime": "20260630T120000.000Z",
        "team": [{"tag": PLAYER_TAG, "name": "Tester", "crowns": crowns[0], "cards": deck(player_cards, player_level)}],
        "opponent": [{"tag": "#OPP", "name": "Opponent", "crowns": crowns[1], "cards": deck(opponent_cards, opponent_level)}],
    }


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.main = ["Mega Knight", "Wizard", "Elite Barbarians", "Rage", "Valkyrie", "Fireball", "Arrows", "Skeleton Army"]
        self.alt = ["Mega Knight", "Wizard", "Balloon", "Baby Dragon", "Firecracker", "Zap", "Bats", "Cannon"]
        self.opp = ["Mega Knight", "Firecracker", "Inferno Tower", "Miner", "Zap", "Bats", "Knight", "Wall Breakers"]
        self.normal_opp = ["Hog Rider", "Musketeer", "Cannon", "Ice Spirit", "Skeletons", "The Log", "Fireball", "Valkyrie"]

    def sample_battles(self):
        return [
            {**battle(self.main, self.opp, "loss", 14, 13), "battleTime": "20260630T120000.000Z"},
            {**battle(self.alt, self.opp, "loss", 14, 13), "battleTime": "20260630T120100.000Z"},
            {**battle(self.main, self.opp, "win", 14, 13), "battleTime": "20260630T120200.000Z"},
            {**battle(self.alt, self.opp, "loss", 14, 13), "battleTime": "20260630T120300.000Z"},
            {**battle(self.main, self.normal_opp, "win", 14, 13), "battleTime": "20260630T120400.000Z"},
            {**battle(self.alt, self.normal_opp, "loss", 14, 13), "battleTime": "20260630T120500.000Z"},
        ]

    def sample_player(self):
        return {
            "tag": PLAYER_TAG,
            "name": "Local Tester",
            "arena": {"name": "Test Arena"},
            "trophies": 6500,
            "expLevel": 44,
            "clan": {"name": "Unit Test Clan"},
            "currentDeck": deck(self.main, 14),
        }

    def build_sample_report(self, seed="fixed", goblin_mode=False):
        service = AnalysisService(get_card_service(), RoastEngine())
        return service.build_report(self.sample_player(), self.sample_battles(), seed=seed, goblin_mode=goblin_mode)

    def deck_with_anchor(self, anchor, index=0):
        pool = [
            "Knight",
            "Musketeer",
            "Cannon",
            "Ice Spirit",
            "Skeletons",
            "The Log",
            "Valkyrie",
            "Hog Rider",
            "Miner",
            "Wall Breakers",
            "Bomb Tower",
            "Phoenix",
            "Baby Dragon",
            "Zap",
            "Firecracker",
            "Mini P.E.K.K.A",
        ]
        cards = [anchor]
        cursor = index
        while len(cards) < 8:
            candidate = pool[cursor % len(pool)]
            cursor += 1
            if candidate not in cards:
                cards.append(candidate)
        return cards

    def compose_deck_copy(self, names, seed="deck-copy", recent=None, uses=0, eligible=0):
        cards = deck(names)
        style = "Unclassified deck style"
        average = average_deck_elixir(cards)
        traits = detect_deck_traits(cards, average, style)
        return compose_deck_roast(
            cards=cards,
            estimated_style=style,
            traits=traits,
            average_elixir=average,
            selector=ExpressionSelector(seed),
            deck_role="current_deck",
            recent_main_cards=deck(recent) if recent else cards,
            recent_main_uses=uses or eligible,
            eligible_matches=eligible or uses or 12,
        )

    def test_player_tag_normalization(self):
        self.assertEqual(normalize_player_tag(" %23abc-123 "), "ABC123")
        self.assertEqual(normalize_player_tag("#mid001"), "MID001")

    def test_battle_summary(self):
        summary = calculate_battle_summary(PLAYER_TAG, self.sample_battles())
        self.assertEqual(summary["battles_analysed"], 6)
        self.assertEqual(summary["wins"], 2)
        self.assertEqual(summary["losses"], 4)
        self.assertEqual(summary["win_rate"], 33)
        self.assertEqual(summary["close_losses"], 4)

    def test_average_deck_elixir(self):
        self.assertAlmostEqual(average_deck_elixir(deck(["Hog Rider", "Ice Spirit", "Skeletons", "The Log"])), 2.0)

    def test_deck_similarity(self):
        near = ["Mega Knight", "Wizard", "Balloon", "Rage", "Valkyrie", "Fireball", "Baby Dragon", "Skeleton Army"]
        self.assertEqual(deck_similarity(self.main, self.main), 1.0)
        self.assertEqual(deck_similarity(self.main, near), 0.75)
        self.assertFalse(material_deck_change(deck_key(deck(self.main, 13)), deck_key(deck(list(reversed(self.main)), 14))))

    def test_panic_switcher_detection(self):
        behaviour = detect_panic_switching(PLAYER_TAG, self.sample_battles())
        self.assertEqual(behaviour["classification"], "LIMITED_DATA")
        self.assertNotIn(behaviour["classification"], {"PANIC_SWITCHER", "EMOTIONAL_DECK_BUILDER"})

    def test_emotional_support_card_detection(self):
        support = detect_emotional_support_card(PLAYER_TAG, self.sample_battles(), min_games=4)
        self.assertFalse(support["detected"])

    def test_traumatic_opponent_card_ranking(self):
        ranked = rank_traumatic_opponent_cards(PLAYER_TAG, self.sample_battles(), min_encounters=4)
        first_cards = {item["card"] for item in ranked[:4]}
        self.assertIn("Mega Knight", first_cards)
        mega = next(item for item in ranked if item["card"] == "Mega Knight")
        self.assertEqual(mega["faced"], 4)
        self.assertEqual(mega["losses"], 3)

    def test_level_disadvantage_classification(self):
        self.assertEqual(classify_level_disadvantage(deck(self.main, 12), deck(self.opp, 13)), "underlevelled")
        self.assertEqual(classify_level_disadvantage(deck(self.main, 13), deck(self.opp, 13)), "even")
        self.assertEqual(classify_level_disadvantage(deck(self.main, 14), deck(self.opp, 13)), "overlevelled")

    def test_troll_score_calculation(self):
        score = calculate_troll_score(
            {"win_rate": 33, "losses": 4, "three_crown_losses": 1},
            {
                "deck_identity_score": 40,
                "average_elixir": 4.8,
                "structural_issues": [
                    {"label": "No clear win condition", "explanation": "No tower plan"},
                    {"label": "No small spell", "explanation": "No cheap answer"},
                    {"label": "Weak anti-air", "explanation": "Limited air answers"},
                ],
                "structural_issue_count": 3,
            },
            {"natural_predator": {"matches": 4, "losses": 3, "excess_loss_rate": 30, "evidence": ["Pattern"], "confidence": "medium"}},
            {"overlevelled_fraud_score": 75, "total_losses_with_levels": 5, "meaningful_level_advantage_losses": 4, "evidence": ["Level pattern"], "confidence": "medium"},
            {"classification": "PANIC_SWITCHER", "changes_after_losses": 3, "post_loss_opportunities": 3, "main_deck_games": 5, "main_deck_win_rate": 40, "evidence": ["Switching"], "confidence": "medium"},
            {"detected": True},
            {"close_wins": 1, "close_losses": 4, "evidence": ["Close games"], "confidence": "medium"},
        )
        self.assertGreater(score["score"], 40)
        self.assertTrue(score["components"])
        deck_points = sum(item["applied_points"] for item in score["components"] if item["group"] == "deck_construction")
        self.assertLessEqual(deck_points, 15)

    def test_rule_engine_output_structure(self):
        roast = RoastEngine().render(
            "PANIC_SWITCHER",
            "PANIC SWITCHER",
            ["Changed deck after losses"],
            "high",
            ["Mega Knight"],
            {"changes_after_losses": 5},
            seed="fixed",
        )
        self.assertEqual(roast["rule_id"], "PANIC_SWITCHER")
        self.assertEqual(roast["confidence"], "high")
        self.assertIn("text", roast)
        self.assertIn("evidence", roast)
        self.assertIn("funny_description", roast)
        self.assertIn("plain_language_explanation", roast)

    def test_report_has_new_sections_and_compatible_legacy_fields(self):
        report = self.build_sample_report()
        self.assertEqual(report["schema_version"], REPORT_SCHEMA_VERSION)
        for key in (
            "fraud_score",
            "personality_report",
            "deck_personality",
            "roast_report",
            "roasts",
            "favourite_card_analysis",
            "feared_card_analysis",
            "win_rate_verdict",
            "roast_narrative",
            "roast_modules",
            "card_evidence_gallery",
        ):
            self.assertIn(key, report)

        self.assertEqual(report["roast_report"]["troll_score"], report["fraud_score"]["score"])
        self.assertEqual(report["roast_report"]["score_label"], report["fraud_score"]["tier"])
        self.assertTrue(report["fraud_score"]["contributors"])
        self.assertTrue(report["personality_report"]["scope_note"])
        self.assertTrue(report["deck_personality"]["plain_explanation"])
        self.assertTrue(report["roast_narrative"]["opening_charge"])
        self.assertTrue(any(module["category"] == "final_verdict" for module in report["roast_modules"]))

    def test_response_model_preserves_new_report_sections(self):
        serialized = ReportResponse.model_validate(self.build_sample_report()).model_dump()
        self.assertEqual(serialized["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertIn("fraud_score", serialized)
        self.assertIn("personality_report", serialized)
        self.assertIn("deck_personality", serialized)
        self.assertIn("favourite_card_analysis", serialized)
        self.assertIn("feared_card_analysis", serialized)
        self.assertIn("win_rate_verdict", serialized)
        self.assertIn("card_evidence_gallery", serialized)
        self.assertIn("plain_language_explanation", serialized["roasts"][0])

    def test_report_has_no_duplicate_roast_rule_ids(self):
        report = self.build_sample_report()
        rule_ids = [roast["rule_id"] for roast in report["roasts"]]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))

    def test_report_output_is_deterministic_with_same_seed(self):
        first = self.build_sample_report(seed="repeatable")
        second = self.build_sample_report(seed="repeatable")
        self.assertEqual(first["fraud_score"], second["fraud_score"])
        self.assertEqual(first["personality_report"], second["personality_report"])
        self.assertEqual(first["deck_personality"], second["deck_personality"])

    def test_report_copy_varies_across_seed_values(self):
        first = self.build_sample_report(seed="alpha")
        second = self.build_sample_report(seed="bravo")
        first_copy = (
            first["fraud_score"]["headline_roast"],
            first["personality_report"]["summary"],
            first["deck_personality"]["roast"],
        )
        second_copy = (
            second["fraud_score"]["headline_roast"],
            second["personality_report"]["summary"],
            second["deck_personality"]["roast"],
        )
        self.assertNotEqual(first_copy, second_copy)

    def test_template_catalog_has_multiple_variants_per_category(self):
        counts = template_catalog_counts()
        self.assertGreaterEqual(counts["favourite_card"], 8)
        self.assertGreaterEqual(counts["feared_card"], 8)
        self.assertGreaterEqual(counts["win_rate"], 8)
        self.assertGreaterEqual(counts["insufficient_evidence"], 6)
        self.assertGreaterEqual(counts["final_verdict"], 8)
        self.assertGreaterEqual(len(PERSONALITY_TEMPLATES), 30)
        self.assertGreaterEqual(len(GOBLIN_INTERVENTIONS), 5)
        for copy in TIER_COPY.values():
            self.assertGreaterEqual(len(copy["labels"]), 5)
            self.assertGreaterEqual(len(copy["descriptions"]), 12)
            self.assertGreaterEqual(len(copy["headlines"]), 5)
        for copy in CONTRIBUTOR_COPY.values():
            self.assertGreaterEqual(len(copy["roasts"]), 3)
            self.assertTrue(copy["description"])
        for copy in DECK_STYLE_COPY.values():
            self.assertGreaterEqual(len(copy["roasts"]), 3)
            self.assertTrue(copy["plain"])

    def test_deck_roast_catalog_has_required_variety(self):
        counts = deck_roast_catalog_counts()
        self.assertGreaterEqual(counts["exact_meta"], 15)
        self.assertGreaterEqual(counts["meta_adjacent"], 15)
        self.assertGreaterEqual(counts["group_project"], 10)
        self.assertGreaterEqual(counts["fallback"], 10)
        self.assertGreaterEqual(counts["combo_hooks"], 8)
        for anchor, count in counts["anchor_title_categories"].items():
            self.assertGreaterEqual(count, 10, anchor)
        for anchor, count in counts["anchor_one_liner_categories"].items():
            self.assertGreaterEqual(count, 10, anchor)

    def test_custom_sparky_deck_roast_is_card_specific(self):
        names = ["Electro Spirit", "Knight", "Goblin Gang", "Sparky", "Tesla", "Arrows", "Dart Goblin", "Ice Spirit"]
        roast = self.compose_deck_copy(names, seed="sparky-case")
        combined = " ".join([roast["headline"], roast["one_liner"], roast["main_roast"]])
        self.assertEqual(roast["style_kind"], "custom_signature")
        self.assertNotIn("Unclassified", roast["headline"])
        self.assertIn("Sparky", combined)
        self.assertTrue(any(card in combined for card in ["Electro Spirit", "Tesla", "Goblin Gang", "Dart Goblin", "Ice Spirit"]))
        self.assertTrue(roast["mentioned_cards"])

    def test_custom_mega_witch_barrel_deck_roast_mentions_real_combo(self):
        names = ["Skeleton Barrel", "Mini P.E.K.K.A", "Princess", "The Log", "Bats", "Witch", "Mega Knight", "Inferno Dragon"]
        roast = self.compose_deck_copy(names, seed="mega-witch-case")
        combined = " ".join([roast["headline"], roast["one_liner"], roast["main_roast"]])
        self.assertEqual(roast["style_kind"], "custom_signature")
        self.assertTrue(any(card in combined for card in ["Mega Knight", "Witch", "Skeleton Barrel", "Inferno Dragon", "Mini P.E.K.K.A"]))
        self.assertNotIn("Unclassified", roast["headline"])

    def test_exact_meta_deck_roast_names_copy_and_match_count(self):
        names = ["Hog Rider", "Musketeer", "Cannon", "Ice Spirit", "Skeletons", "The Log", "Fireball", "Valkyrie"]
        roast = self.compose_deck_copy(names, seed="exact-meta")
        self.assertEqual(roast["style_kind"], "exact_meta")
        self.assertIn("2.6 Hog Cycle", roast["one_liner"] + roast["headline"] + roast["evidence_summary"])
        self.assertEqual(roast["deck_match"]["matched_count"], 8)
        self.assertIn("8/8", roast["evidence_summary"])

    def test_meta_adjacent_deck_roast_mentions_substitutions(self):
        names = ["Hog Rider", "Musketeer", "Tesla", "Ice Spirit", "Goblin Gang", "The Log", "Fireball", "Valkyrie"]
        roast = self.compose_deck_copy(names, seed="meta-adjacent")
        combined = " ".join([roast["headline"], roast["one_liner"], roast["main_roast"], roast["evidence_summary"]])
        self.assertEqual(roast["style_kind"], "meta_adjacent")
        self.assertEqual(roast["deck_match"]["matched_count"], 6)
        self.assertIn("Hog Cycle", combined)
        self.assertTrue(any(card in combined for card in ["Tesla", "Goblin Gang"]))

    def test_deck_roast_context_line_changes_when_current_deck_differs(self):
        current = ["Electro Spirit", "Knight", "Goblin Gang", "Sparky", "Tesla", "Arrows", "Dart Goblin", "Ice Spirit"]
        recent = ["Hog Rider", "Musketeer", "Cannon", "Ice Spirit", "Skeletons", "The Log", "Fireball", "Valkyrie"]
        roast = self.compose_deck_copy(current, seed="deck-diff", recent=recent, uses=10, eligible=12)
        self.assertIn("not the deck", roast["supporting_roast"].lower())

    def test_fraud_score_contributors_are_rich_and_plain_language(self):
        report = self.build_sample_report()
        contributors = report["fraud_score"]["contributors"]
        self.assertTrue(contributors)
        for contributor in contributors:
            self.assertIn("label", contributor)
            self.assertIn("points", contributor)
            self.assertIn("description", contributor)
            self.assertIn("evidence", contributor)
            self.assertTrue(contributor["description"])

        for roast in report["roasts"]:
            self.assertTrue(roast["plain_language_explanation"])
            self.assertTrue(roast["funny_description"])

    def test_personality_report_is_evidence_scoped_not_a_real_diagnosis(self):
        report = self.build_sample_report()
        personality = report["personality_report"]
        self.assertIn("battle-log", personality["scope_note"])
        self.assertIn("not a real psychological diagnosis", personality["scope_note"])
        self.assertGreaterEqual(len(personality["evidence"]), 5)

    def test_low_battle_sample_reduces_fraud_score_confidence(self):
        report = self.build_sample_report()
        self.assertLess(report["battle_summary"]["battles_analysed"], 10)
        self.assertEqual(report["fraud_score"]["confidence"], "low")

    def test_goblin_mode_copy_avoids_hard_prohibited_phrases(self):
        report = self.build_sample_report(goblin_mode=True)
        rendered = " ".join(
            [report["personality_report"]["intervention_tip"]]
            + [roast["text"] for roast in report["roasts"]]
        ).lower()
        prohibited = ["kill yourself", "kys", "self-harm", "racial slur", "homophobic slur"]
        for phrase in prohibited:
            self.assertNotIn(phrase, rendered)

    def test_deck_personality_traits_reflect_detected_deck_shape(self):
        heavy_troop_deck = [
            {"name": "Mega Knight", "type": "troop", "elixir": 7, "traits": ["splash"]},
            {"name": "Wizard", "type": "troop", "elixir": 5, "traits": ["splash", "anti_air"]},
            {"name": "Elite Barbarians", "type": "troop", "elixir": 6, "traits": []},
            {"name": "Valkyrie", "type": "troop", "elixir": 4, "traits": ["splash"]},
            {"name": "Knight", "type": "troop", "elixir": 3, "traits": []},
            {"name": "Mini P.E.K.K.A", "type": "troop", "elixir": 4, "traits": ["tank_killer"]},
            {"name": "Giant", "type": "troop", "elixir": 5, "traits": ["win_condition"]},
            {"name": "Skeleton Army", "type": "troop", "elixir": 3, "traits": ["swarm"]},
        ]
        traits = detect_deck_traits(heavy_troop_deck, 5.5, "Beatdown-ish")
        labels = {trait["label"] for trait in traits}
        self.assertIn("High elixir commitment", labels)
        self.assertIn("Weak anti-air", labels)
        self.assertIn("No small spell", labels)

    def test_player_second_in_2v2_is_identified_but_excluded(self):
        teammate = {"tag": "#TEAMMATE", "name": "Wrong", "crowns": 0, "cards": deck(self.alt)}
        searched = {"tag": PLAYER_TAG, "name": "Tester", "crowns": 1, "cards": deck(self.main)}
        two_v_two = {
            "type": "2v2",
            "battleTime": "20260630T120000.000Z",
            "team": [teammate, searched],
            "opponent": [
                {"tag": "#A", "name": "A", "crowns": 2, "cards": deck(self.opp)},
                {"tag": "#B", "name": "B", "crowns": 2, "cards": deck(self.normal_opp)},
            ],
        }
        normalized = normalize_battles(PLAYER_TAG, [two_v_two])[0]
        self.assertEqual(normalized.player_deck_names, self.main)
        self.assertFalse(normalized.eligible_personal_deck)

    def test_newest_first_logs_are_sorted_before_post_loss_logic(self):
        old_loss = {**battle(self.main, self.opp, "loss"), "battleTime": "20260630T120000.000Z"}
        new_after_loss = {**battle(self.alt, self.opp, "win"), "battleTime": "20260630T120100.000Z"}
        normalized = normalize_battles(PLAYER_TAG, [new_after_loss, old_loss])
        self.assertEqual([item.battle_time for item in normalized], ["20260630T120000.000Z", "20260630T120100.000Z"])

    def test_draft_and_event_modes_are_excluded(self):
        draft = {**battle(self.main, self.opp, "win"), "type": "tripleDraft"}
        event = {**battle(self.main, self.opp, "win"), "type": "event"}
        normalized = normalize_battles(PLAYER_TAG, [draft, event])
        self.assertTrue(all(not item.eligible_personal_deck for item in normalized))

    def test_one_main_deck_with_one_card_tests_is_stable(self):
        one_swap = ["Mega Knight", "Wizard", "Elite Barbarians", "Rage", "Valkyrie", "Fireball", "Arrows", "Knight"]
        battles = []
        for index in range(10):
            cards = one_swap if index in {3, 7} else self.main
            battles.append({**battle(cards, self.opp, "win" if index % 2 else "loss"), "battleTime": f"20260630T12{index:02d}00.000Z"})
        behaviour = detect_panic_switching(PLAYER_TAG, battles)
        self.assertIn(behaviour["classification"], {"ONE_DECK_WARRIOR", "STABLE_WITH_MINOR_VARIATIONS"})
        self.assertNotIn(behaviour["classification"], {"PANIC_SWITCHER", "EMOTIONAL_DECK_BUILDER"})

    def test_true_repeated_post_loss_major_switcher_is_classified(self):
        deck_c = ["Hog Rider", "Musketeer", "Cannon", "Ice Spirit", "Skeletons", "The Log", "Fireball", "Valkyrie"]
        deck_d = ["Giant", "Wizard", "Baby Dragon", "Lightning", "Mini P.E.K.K.A", "Zap", "Bats", "Tombstone"]
        sequence = [
            (self.main, "loss"),
            (self.alt, "loss"),
            (deck_c, "loss"),
            (deck_d, "loss"),
            (self.main, "win"),
            (self.alt, "loss"),
            (deck_c, "win"),
            (deck_d, "loss"),
        ]
        battles = [{**battle(cards, self.opp, result), "battleTime": f"20260630T12{index:02d}00.000Z"} for index, (cards, result) in enumerate(sequence)]
        behaviour = detect_panic_switching(PLAYER_TAG, battles)
        self.assertEqual(behaviour["classification"], "PANIC_SWITCHER")

    def test_card_icons_use_official_api_icon_urls_when_available(self):
        card = enrich_card({"name": "Mega Knight", "iconUrls": {"medium": "https://example.test/mega-knight.png"}})
        self.assertEqual(card["icon_url"], "https://example.test/mega-knight.png")

    def test_missing_card_metadata_and_image_have_fallback_fields(self):
        card = enrich_card({"name": "Mystery Soup"})
        self.assertFalse(card["metadata_complete"])
        self.assertIsNone(card["icon_url"])
        self.assertEqual(card["type"], "unknown")

    def test_favourite_card_uses_only_eligible_personal_history(self):
        battles = []
        for index in range(10):
            battles.append({**battle(self.deck_with_anchor("Fireball", index), self.normal_opp, "win" if index % 2 else "loss"), "battleTime": f"20260630T12{index:02d}00.000Z"})
        for index in range(8):
            excluded = {**battle(self.deck_with_anchor("Hog Rider", index), self.opp, "win"), "type": "tripleDraft", "battleTime": f"20260630T13{index:02d}00.000Z"}
            battles.append(excluded)
        analysis = analyse_favourite_card(PLAYER_TAG, battles, {"current_deck": deck(self.deck_with_anchor("Fireball"))}, get_card_service())
        self.assertTrue(analysis["is_true_single_card_favourite"])
        self.assertEqual(analysis["favourite_card_name"], "Fireball")
        self.assertEqual(analysis["eligible_match_count"], 10)

    def test_true_one_deck_player_gets_no_fake_single_card_favourite(self):
        battles = [{**battle(self.main, self.normal_opp, "win" if index % 2 else "loss"), "battleTime": f"20260630T12{index:02d}00.000Z"} for index in range(10)]
        analysis = analyse_favourite_card(PLAYER_TAG, battles, {"current_deck": deck(self.main)}, get_card_service())
        self.assertFalse(analysis["is_true_single_card_favourite"])
        self.assertTrue(analysis["is_full_deck_loyalist_case"])
        self.assertIsNone(analysis["favourite_card"])
        self.assertIn("entire eight-card group chat", analysis["favourite_card_reason"])

    def test_favourite_card_delta_uses_player_baseline(self):
        battles = []
        for index in range(12):
            result = "win" if index < 8 else "loss"
            battles.append({**battle(self.deck_with_anchor("Fireball", index), self.normal_opp, result), "battleTime": f"20260630T12{index:02d}00.000Z"})
        for index in range(3):
            battles.append({**battle(self.deck_with_anchor("Hog Rider", index), self.opp, "loss"), "battleTime": f"20260630T13{index:02d}00.000Z"})
        analysis = analyse_favourite_card(PLAYER_TAG, battles, {"current_deck": deck(self.deck_with_anchor("Fireball"))}, get_card_service())
        self.assertEqual(analysis["player_baseline_win_rate"], 53)
        self.assertEqual(analysis["favourite_card_win_rate"], 67)
        self.assertEqual(analysis["favourite_card_performance_delta"], 14)

    def test_feared_card_requires_minimum_sample_size(self):
        battles = []
        for index in range(4):
            battles.append({**battle(self.main, self.opp, "loss"), "battleTime": f"20260630T12{index:02d}00.000Z"})
        for index in range(4):
            battles.append({**battle(self.main, self.normal_opp, "win"), "battleTime": f"20260630T13{index:02d}00.000Z"})
        analysis = analyse_feared_card(PLAYER_TAG, battles, get_card_service())
        self.assertTrue(analysis["is_insufficient_evidence"])
        self.assertEqual(analysis["games_against"], 4)

    def test_feared_card_compares_against_baseline_loss_rate(self):
        battles = []
        for index in range(5):
            result = "win" if index == 0 else "loss"
            battles.append({**battle(self.main, self.opp, result), "battleTime": f"20260630T12{index:02d}00.000Z"})
        for index in range(5):
            result = "loss" if index == 0 else "win"
            battles.append({**battle(self.main, self.normal_opp, result), "battleTime": f"20260630T13{index:02d}00.000Z"})
        analysis = analyse_feared_card(PLAYER_TAG, battles, get_card_service())
        self.assertFalse(analysis["is_insufficient_evidence"])
        self.assertEqual(analysis["feared_card_name"], "Mega Knight")
        self.assertEqual(analysis["baseline_loss_rate"], 50)
        self.assertEqual(analysis["loss_rate_against"], 80)
        self.assertEqual(analysis["excess_loss_rate"], 30)

    def test_insufficient_samples_emit_limited_evidence_not_false_claims(self):
        favourite = analyse_favourite_card(PLAYER_TAG, self.sample_battles(), {"current_deck": deck(self.main)}, get_card_service())
        feared = analyse_feared_card(PLAYER_TAG, self.sample_battles(), get_card_service())
        self.assertFalse(favourite["is_true_single_card_favourite"])
        self.assertTrue(feared["is_insufficient_evidence"])
        self.assertIn("needs at least", favourite["favourite_card_reason"])

    def test_panic_roast_module_requires_strict_panic_classification(self):
        report = self.build_sample_report()
        self.assertNotEqual(report["behaviour_analysis"]["classification"], "PANIC_SWITCHER")
        self.assertNotIn("panic_switching", {module["category"] for module in report["roast_modules"]})

    def test_win_rate_verdict_uses_eligible_matches_only(self):
        battles = [
            {**battle(self.main, self.normal_opp, "win"), "battleTime": "20260630T120000.000Z"},
            {**battle(self.main, self.normal_opp, "loss"), "battleTime": "20260630T120100.000Z"},
            {**battle(self.main, self.normal_opp, "win"), "type": "tripleDraft", "battleTime": "20260630T120200.000Z"},
        ]
        behaviour = detect_panic_switching(PLAYER_TAG, battles)
        verdict = analyse_win_rate_verdict(PLAYER_TAG, battles, behaviour)
        self.assertEqual(verdict["total_eligible_matches"], 2)
        self.assertEqual(verdict["wins"], 1)
        self.assertEqual(verdict["losses"], 1)

    def test_builders_keep_mock_and_live_report_contract_compatible(self):
        selector = ExpressionSelector("contract")
        battle_summary = {
            "battles_analysed": 12,
            "wins": 3,
            "losses": 9,
            "draws": 0,
            "win_rate": 25,
            "three_crown_losses": 2,
            "close_wins": 1,
            "close_losses": 5,
        }
        deck_analysis = {
            "current_deck": deck(self.main, 14),
            "average_elixir": 4.25,
            "deck_identity_score": 40,
            "estimated_deck_style": "Midladder emergency response unit",
            "personality_rule": {"evidence": ["Expensive splash-heavy deck"], "confidence": "medium"},
        }
        matchup_analysis = {"natural_predator": {"label": "Recurring counter shell", "matches": 5, "losses": 4}}
        level_analysis = {"loss_counts": {"overlevelled": 4}, "overlevelled_fraud_score": 44}
        behaviour_analysis = {"changes_after_losses": 3, "unique_decks": 3, "main_deck_games": 6, "main_deck_win_rate": 33}
        emotional_support = {"detected": False, "evidence": []}
        clutch_analysis = {"close_wins": 1, "close_losses": 5}
        troll_score = calculate_troll_score(
            battle_summary,
            deck_analysis,
            matchup_analysis,
            level_analysis,
            behaviour_analysis,
            emotional_support,
            clutch_analysis,
        )
        fraud_score = build_fraud_score(
            troll_score,
            battle_summary,
            deck_analysis,
            matchup_analysis,
            level_analysis,
            behaviour_analysis,
            emotional_support,
            clutch_analysis,
            selector,
        )
        deck_personality = build_deck_personality(deck_analysis, selector)
        self.assertIn("score", fraud_score)
        self.assertIn("contributors", fraud_score)
        self.assertIn("plain_explanation", deck_personality)
        self.assertIn("traits", deck_personality)


if __name__ == "__main__":
    unittest.main()
