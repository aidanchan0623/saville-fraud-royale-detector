import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.analysis_service import (
    average_deck_elixir,
    calculate_battle_summary,
    calculate_troll_score,
    classify_level_disadvantage,
    deck_similarity,
    detect_emotional_support_card,
    detect_panic_switching,
    normalize_player_tag,
    rank_traumatic_opponent_cards,
)
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


if __name__ == "__main__":
    unittest.main()
