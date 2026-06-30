import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.analysis_service import (
    AnalysisService,
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
from app.rules.deck_templates import DECK_STYLE_COPY
from app.rules.expression_selector import ExpressionSelector
from app.rules.fraud_score_templates import CONTRIBUTOR_COPY, TIER_COPY
from app.rules.personality_templates import GOBLIN_INTERVENTIONS, PERSONALITY_TEMPLATES
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
            battle(self.main, self.opp, "loss", 14, 13),
            battle(self.alt, self.opp, "loss", 14, 13),
            battle(self.main, self.opp, "win", 14, 13),
            battle(self.alt, self.opp, "loss", 14, 13),
            battle(self.main, self.normal_opp, "win", 14, 13),
            battle(self.alt, self.normal_opp, "loss", 14, 13),
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

    def test_panic_switcher_detection(self):
        behaviour = detect_panic_switching(PLAYER_TAG, self.sample_battles())
        self.assertGreaterEqual(behaviour["changes_after_losses"], 2)
        self.assertGreaterEqual(behaviour["unique_decks"], 2)

    def test_emotional_support_card_detection(self):
        support = detect_emotional_support_card(PLAYER_TAG, self.sample_battles(), min_games=4)
        self.assertTrue(support["detected"])
        self.assertIn(support["card"], {"Mega Knight", "Wizard"})

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
            {"deck_identity_score": 40, "average_elixir": 4.8},
            {"natural_predator": {"matches": 4, "losses": 3}},
            {"overlevelled_fraud_score": 75},
            {"changes_after_losses": 3, "main_deck_games": 5, "main_deck_win_rate": 40},
            {"detected": True},
            {"close_wins": 1, "close_losses": 4},
        )
        self.assertGreater(score["score"], 50)
        self.assertTrue(score["components"])

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
        for key in ("fraud_score", "personality_report", "deck_personality", "roast_report", "roasts"):
            self.assertIn(key, report)

        self.assertEqual(report["roast_report"]["troll_score"], report["fraud_score"]["score"])
        self.assertEqual(report["roast_report"]["score_label"], report["fraud_score"]["tier"])
        self.assertTrue(report["fraud_score"]["contributors"])
        self.assertTrue(report["personality_report"]["scope_note"])
        self.assertTrue(report["deck_personality"]["plain_explanation"])

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
        ]
        traits = detect_deck_traits(heavy_troop_deck, 5.5, "Beatdown-ish")
        labels = {trait["label"] for trait in traits}
        self.assertIn("High elixir commitment", labels)
        self.assertIn("Weak anti-air", labels)
        self.assertIn("No small spell", labels)

    def test_card_icons_use_official_api_icon_urls_when_available(self):
        card = enrich_card({"name": "Mega Knight", "iconUrls": {"medium": "https://example.test/mega-knight.png"}})
        self.assertEqual(card["icon_url"], "https://example.test/mega-knight.png")

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
