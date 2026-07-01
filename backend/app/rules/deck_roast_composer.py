from __future__ import annotations

from typing import Any

from app.rules.expression_selector import ExpressionSelector, format_template
from app.services.battle_normalizer import deck_key, normalize_card_name, shared_card_count


LOCAL_DECK_SNAPSHOT_DATE = "2026-07-01"

META_DECKS = [
    {
        "name": "2.6 Hog Cycle",
        "family": "Hog Cycle",
        "cards": ["Hog Rider", "Musketeer", "Cannon", "Ice Spirit", "Skeletons", "The Log", "Fireball", "Valkyrie"],
    },
    {
        "name": "Classic Log Bait",
        "family": "Log Bait",
        "cards": ["Princess", "Goblin Barrel", "Inferno Tower", "Rocket", "Knight", "The Log", "Goblin Gang", "Ice Spirit"],
    },
    {
        "name": "Royal Giant Lightning",
        "family": "Royal Giant Control",
        "cards": ["Royal Giant", "Lightning", "Fisherman", "Phoenix", "Electro Spirit", "The Log", "Skeletons", "Cannon"],
    },
]

EXACT_META_TEMPLATES = [
    "Ah yes, {deck_name}. You found a proven deck and immediately started acting like you discovered electricity.",
    "This is {deck_name}, which means the cards know what they are doing. Whether you do is a separate investigation.",
    "You copied {deck_name} card for card. Honestly, respect. Why invent a deck when the internet already did your homework?",
    "Bro opened a {family} list, clicked copy, and called it personal growth.",
    "{deck_name}: eight cards with a plan. You are now legally required not to freestyle it.",
    "This is not deck-building. This is downloading {deck_name} and hoping nobody asks follow-up questions.",
    "You brought {deck_name}, so the deck has structure. The pilot is still under review.",
    "The internet made {deck_name} first, and you arrived with the confidence of a co-founder.",
    "{deck_name} is a real deck. Congratulations on outsourcing the hard part.",
    "This is the full {family} package. The cards brought credentials. You brought thumbs.",
    "Eight out of eight cards match {deck_name}. That is not inspiration; that is a screenshot with elixir.",
    "You selected {deck_name} like the deck list owed you rent, and honestly the receipts are clean.",
    "{deck_name} has a plan so obvious even the tower can read it. Please try not to improvise nonsense over it.",
    "You found {deck_name} and said, yeah, I can be trusted with this machinery.",
    "The deck is {deck_name}. The strategy was pre-installed. Do not void the warranty.",
]

META_ADJACENT_TEMPLATES = [
    "You found {deck_name} and immediately started modifying it like a recipe you had never cooked before.",
    "This is basically {family}, except you replaced {missing_cards} with {extra_cards} because apparently peace was never an option.",
    "You were one normal deck list away from {deck_name}, then {extra_cards} happened.",
    "{matched_count}/8 cards match {deck_name}. Close enough to be recognisable, far enough to make the original list sigh.",
    "This is {family} after you let someone edit the deck at 2 a.m.",
    "{matched_cards} are trying to play {family}. {extra_cards} walked in holding a different brief.",
    "You kept the {family} skeleton, then stapled {extra_cards} onto it and called that innovation.",
    "This deck is wearing a {deck_name} jacket with {extra_cards} sticking out of the pockets.",
    "The plan started as {family}. Then the substitutions arrived and the room got quiet.",
    "{matched_count}/8 match with {deck_name}. Not a copy. More like a cover band with questionable drums.",
    "You saw {deck_name} and asked, what if I made this slightly more cursed?",
    "The deck is close to {family}, but {extra_cards} is where the group chat starts yelling.",
    "You changed {missing_cards} into {extra_cards}. That is either adaptation or deck-building with the lights off.",
    "This is {deck_name} with personal edits, which is a dangerous phrase in every strategy game.",
    "The original {family} idea survived. Barely. {extra_cards} is currently being questioned.",
]

ANCHOR_TITLES: dict[str, list[str]] = {
    "Sparky": [
        "SPARKY'S UNPAID INTERNS",
        "ROLLING POWER STATION HR DEPARTMENT",
        "SIX ELIXIR AND A GROUP CHAT",
        "THE EXTENSION CORD DEFENCE PLAN",
        "SPARKY AND THE QUESTIONABLE STAFFING AGENCY",
        "POWER GRID WITH EMOTIONAL SUPPORT",
        "THE SLOWEST PANIC BUTTON IN THE ARENA",
        "ONE CANNON, SEVEN WITNESSES",
        "SPARKY'S LIABILITY INSURANCE",
        "THE ELECTRIC CART BUSINESS MODEL",
    ],
    "Mega Knight": [
        "EMERGENCY ROOF COLLAPSE PLAN",
        "MEGA KNIGHT CUSTOMER SUPPORT",
        "DROP HIM ON IT AND PRAY",
        "CEILING DAMAGE CONTROL",
        "THE SEVEN ELIXIR COMPLAINT DESK",
        "MEGA KNIGHT'S LOST AND FOUND",
        "AIRBORNE CONCRETE MANAGEMENT",
        "THE JUMP BUTTON BUSINESS MODEL",
        "MIDLANE IMPACT CONSULTING",
        "THE ROOF JUST FILED PAPERWORK",
    ],
    "Witch": [
        "SKELETON GROUP PROJECT",
        "WITCH'S CHILDCARE SERVICE",
        "THE UNIONISED SKELETON PLAN",
        "SUMMON PAPERWORK UNTIL SOMETHING HAPPENS",
        "SKELETON DAYCARE WITH A TOWER PROBLEM",
        "THE BONE ECONOMY",
        "WITCH AND THE UNPAID STAFF",
        "SPLASH DAMAGE PRESCHOOL",
        "THE NECROMANCY MEETING AGENDA",
        "TINY BONES, BIG EXPECTATIONS",
    ],
    "Skeleton Barrel": [
        "AIRBORNE PARCEL DELIVERY",
        "THE SKELETON SHIPPING DEPARTMENT",
        "BARREL LOGISTICS OPERATIONS",
        "GOBLIN AMAZON PRIME",
        "ONE BARREL AND TOO MUCH CONFIDENCE",
        "AIR MAIL WITH BONES INSIDE",
        "THE DROPSHIP HR PROBLEM",
        "SKELETONS BY EXPRESS DELIVERY",
        "THE BALLOONLESS AIRLINE",
        "PARCEL TRACKING SAYS TROUBLE",
    ],
    "Princess": [
        "LONG-RANGE MENACE OPERATIONS",
        "PRINCESS DOING ALL THE HOMEWORK",
        "THE LOG BAIT CUSTOMER SERVICE DESK",
        "DISTANCE-BASED ANNOYANCE",
        "PRINCESS AND THE NOISE COMPLAINTS",
        "POSTCODE RANGE HARASSMENT",
        "THE BRIDGE-SIDE PRESS OFFICE",
        "ONE PRINCESS, SEVEN EXCUSES",
        "THE LONG SHOT LEGAL TEAM",
        "TOWER DAMAGE FROM ANOTHER ZIP CODE",
    ],
    "Inferno Dragon": [
        "LASER LIZARD LEGAL DEFENCE",
        "TANK MELTING INTERN PROGRAM",
        "FLYING HEAT GUN WITH RESPONSIBILITIES",
        "ONE DRAGON, TOO MANY EXPECTATIONS",
        "INFERNO DRAGON'S CUSTOMER ESCALATION TEAM",
        "THE AIRBORNE WELDING DEPARTMENT",
        "LASER LIZARD AND THE SIDE QUESTS",
        "TANK PROBLEM OUTSOURCING",
        "THE HOT BEAM BUSINESS PLAN",
        "DRAGON WITH A JOB DESCRIPTION",
    ],
    "Mini P.E.K.K.A": [
        "PANCAKE ENFORCEMENT UNIT",
        "THE DAMAGE SPREADSHEET DEPARTMENT",
        "SMALL ROBOT, LARGE RESPONSIBILITIES",
        "P.E.K.K.A LITE SUPPORT GROUP",
        "TINY ROBOT WITH BIG HR ISSUES",
        "PANCAKES AND CONSEQUENCES",
        "THE FOUR ELIXIR INCIDENT REPORT",
        "MINI P.E.K.K.A'S NIGHT SHIFT",
        "SMALL METAL PROBLEM SOLVER",
        "THE PANCAKE COLLECTION AGENCY",
    ],
    "Electro Spirit": [
        "ONE-ELIXIR ELECTRICAL CONSULTANT",
        "THE TINY BLUE BUTTON",
        "STATIC ELECTRICITY OPERATIONS",
        "WIFI OUTAGE RESPONSE TEAM",
        "ELECTRO SPIRIT'S IT DEPARTMENT",
        "ONE ELIXIR, TOO MANY RESPONSIBILITIES",
        "THE SPARKY LITTLE MIDDLE MANAGER",
        "STATIC SUPPORT TICKET",
        "THE BLUE BUTTON COVER-UP",
        "ELECTRICAL ASSISTANT TO THE ASSISTANT",
    ],
    "Goblin Gang": [
        "THE BUDGET SECURITY TEAM",
        "SEVEN GOBLINS AND NO PLAN",
        "GROUP PROJECT WITH KNIVES",
        "DISCOUNT CROWD CONTROL",
        "THE CHEAP HEIST CREW",
        "GOBLIN GANG'S HR ORIENTATION",
        "BUDGET DEFENCE WITH POINTY STICKS",
        "THE THREE ELIXIR STAFFING SOLUTION",
        "GOBLIN SECURITY AND QUESTIONABLE BENEFITS",
        "A CROWD CONTROL STARTUP",
    ],
    "Dart Goblin": [
        "UNSUPERVISED BLOWGUN DEPARTMENT",
        "THE LONG-RANGE MENACE",
        "GOBLIN WITH AN HR COMPLAINT",
        "ONE TINY GUY DOING TOO MUCH",
        "DART GOBLIN'S DISTANCE SCAM",
        "THE BLOWGUN CUSTOMER SERVICE DESK",
        "ONE GOBLIN, A VERY LONG STRAW",
        "TINY SNIPER OPERATIONS",
        "THE UNSUPERVISED DART PROGRAM",
        "GOBLIN WORKING REMOTELY",
    ],
}

ANCHOR_ONE_LINERS: dict[str, list[str]] = {
    "Sparky": [
        "Bro built around {anchor}, then hired {card1} and {card2} like a rolling power station needed unpaid interns.",
        "{anchor} is the main character here, and {card1} is somehow holding the clipboard.",
        "You put {anchor} in charge, then surrounded it with {card1}, {card2}, and a prayer.",
        "{anchor} has one job: make the arena nervous. The rest of this deck looks like shift coverage.",
        "This deck says {anchor} will solve it, and everyone else should please stop the building from catching fire.",
        "{anchor} is expensive, dramatic, and slow, so naturally you gave it {card1} as emotional IT support.",
        "You saw {anchor} and decided the correct support system was {card1}, {card2}, and questionable behaviour.",
        "{anchor} is a power station on wheels. {card1} and {card2} are apparently the safety department.",
        "The whole deck is just trying to buy enough time for {anchor} to remember it has a cannon.",
        "{anchor} is carrying the main plot while {card1} and {card2} argue over who gets blamed first.",
    ],
    "Mega Knight": [
        "You made {anchor} the emergency button, then invited {card1} and {card2} to pretend this was a full strategy.",
        "{anchor} is clearly the plan, which is bold because the plan costs seven elixir and lands on people.",
        "This deck waits for a problem, drops {anchor} on it, and lets {card1} explain the paperwork.",
        "{anchor} is doing roof damage while {card1} and {card2} try to look employed.",
        "You built this like every problem deserves {anchor}, which is funny and financially irresponsible.",
        "{anchor} has the confidence of a full strategy and the subtlety of furniture falling downstairs.",
        "The deck says defence, but {anchor} says somebody is about to get a ceiling inspection.",
        "You paired {anchor} with {card1}, which feels like hiring a bouncer for a library.",
        "{anchor} is the main character. The other seven cards are emergency contacts.",
        "This is {anchor} customer support: loud, expensive, and somehow still asked to fix everything.",
    ],
    "Witch": [
        "{anchor} is running skeleton daycare while {card1} and {card2} pretend the paperwork is normal.",
        "You built around {anchor}, which means every defence arrives with children and a legal issue.",
        "{anchor} brought the skeletons. {card1} brought confusion. {card2} brought whatever this is.",
        "The whole deck looks like {anchor} started a club and nobody checked the guest list.",
        "{anchor} keeps summoning staff because apparently one troop was not enough chaos.",
        "You gave {anchor} a support cast and accidentally built a haunted group project.",
        "{anchor} has a plan. The other cards are mostly there asking if bones count as teamwork.",
        "This deck is {anchor}'s skeleton daycare with {card1} acting like a field trip supervisor.",
        "{anchor} does paperwork by summoning more paperwork.",
        "You placed {anchor} in this lineup and let the skeleton economy handle the details.",
    ],
    "Skeleton Barrel": [
        "{anchor} is delivering skeletons by air mail while {card1} and {card2} pretend this is logistics.",
        "You built around {anchor}, which is just parcel delivery with bones and confidence.",
        "{anchor} has commitment issues but excellent shipping speed.",
        "The deck throws {anchor} at the tower like the arena accepts returns.",
        "You made {anchor} part of the plan, then gave {card1} a completely different department.",
        "{anchor} is airborne nonsense. {card1} and {card2} are the people who signed for the package.",
        "This deck treats {anchor} like a delivery service and the tower like an address with bad luck.",
        "{anchor} handles shipping. {card1} handles complaints. {card2} is just standing there.",
        "You saw {anchor} and thought, yes, my strategy needs skeleton logistics.",
        "The deck has {anchor}, which means somebody confused tower damage with package tracking.",
    ],
    "Princess": [
        "{anchor} is doing tower damage from another postcode while {card1} and {card2} cause local problems.",
        "You built around {anchor}, the only card here that read the long-range employment contract.",
        "{anchor} is the nuisance desk. {card1} and {card2} are the callers on hold.",
        "This deck lets {anchor} do homework from the back while everyone else makes noise up front.",
        "{anchor} has range. The rest of the deck has explanations.",
        "You hired {anchor} for distance-based annoyance and then made {card1} carry a different argument.",
        "{anchor} is trying to play bait. {card1} is trying to start a separate business.",
        "The deck says patience, but {anchor} says I can hit the tower from over here, damn it.",
        "{anchor} is polite from far away and deeply annoying on purpose.",
        "You made {anchor} the press office for whatever nonsense {card1} and {card2} are doing.",
    ],
    "Inferno Dragon": [
        "{anchor} is the laser lizard assigned to every tank problem while {card1} and {card2} handle the side quests.",
        "You built around {anchor}, then expected one dragon to solve an entire department's workload.",
        "{anchor} has a beam and responsibilities. {card1} has questions.",
        "This deck sees a tank and sends {anchor} like a tiny airborne lawsuit.",
        "{anchor} is here to melt problems. The rest of the deck is here to create them.",
        "You gave {anchor} a support cast, but it still looks like the dragon is doing the adult work.",
        "{anchor} is basically a flying heat gun with a project manager badge.",
        "The tank plan is {anchor}. The backup plan is everyone yelling.",
        "{anchor} handles the big targets while {card1} and {card2} pretend they read the meeting notes.",
        "You put {anchor} in this deck like every heavy troop owes you money.",
    ],
    "Mini P.E.K.K.A": [
        "{anchor} is the tiny robot with large responsibilities while {card1} and {card2} stand near the incident.",
        "You built around {anchor}, which is four elixir of damage and zero social skills.",
        "{anchor} has one job: hit something once and make the spreadsheet uncomfortable.",
        "This deck hands every tank problem to {anchor} like pancakes fix infrastructure.",
        "You put {anchor} in charge of consequences, then invited {card1} for morale.",
        "{anchor} is small, angry, and somehow the most professional thing here.",
        "The plan is {anchor} making contact before the opponent reads the fine print.",
        "{anchor} is the enforcement unit. {card1} and {card2} are the questionable witnesses.",
        "You trusted {anchor} with the damage department and honestly that part may be fair.",
        "{anchor} is doing heavy lifting while the rest of the deck debates the definition of support.",
    ],
    "Electro Spirit": [
        "{anchor} costs one elixir and is somehow expected to solve problems created by {card1} and {card2}.",
        "You built around tiny utility and accidentally made {anchor} the electrical consultant.",
        "{anchor} is the blue button. The rest of the deck keeps pressing it and hoping.",
        "This deck gives {anchor} one elixir and several impossible chores.",
        "{anchor} is basically IT support for a plan that keeps unplugging itself.",
        "You put {anchor} here like static electricity can fix deck construction.",
        "{anchor} is small, cheap, and surrounded by cards asking for too much.",
        "The plan includes {anchor}, which means somebody believed in the power of one tiny zap.",
        "{anchor} is the assistant to the assistant regional emergency button.",
        "{anchor} is trying to help, but {card1} and {card2} keep creating adult problems.",
    ],
    "Goblin Gang": [
        "{anchor} is the budget security team, and {card1} looks like it got hired through a friend.",
        "You brought {anchor}, which means defence is being handled by a cheap heist crew.",
        "{anchor} has knives, confidence, and absolutely no HR department.",
        "This deck saw {anchor} and said crowd control can be done on a discount.",
        "{anchor} is a group project where everyone brought a weapon and nobody brought a plan.",
        "You put {anchor} next to {card1}, which feels like a payroll problem.",
        "{anchor} is here to swarm. {card1} is here to make the team look stranger.",
        "The deck uses {anchor} like the arena has a staffing shortage.",
        "{anchor} is not a department. It is several tiny complaints at once.",
        "You hired {anchor} and called it structure. Bold paperwork.",
    ],
    "Dart Goblin": [
        "{anchor} is one tiny guy doing too much while {card1} and {card2} create workplace noise.",
        "You built around {anchor}, a goblin working remotely from unsafe distances.",
        "{anchor} has a blowgun and the confidence of someone who never gets supervised.",
        "This deck lets {anchor} poke from far away while everyone else argues near the bridge.",
        "{anchor} is the long-range menace department and {card1} is whatever HR warned about.",
        "You put {anchor} in the deck like one small goblin can solve scheduling.",
        "{anchor} is doing sniper paperwork with a straw.",
        "The plan asks {anchor} to stay alive, which is already a comedy premise.",
        "{anchor} is tiny, annoying, and somehow carrying more personality than the whole office.",
        "You hired {anchor} for range and forgot to give him adult supervision.",
    ],
}

GROUP_PROJECT_CONCLUSIONS = [
    "Every card has a job. Nobody agrees what the company does.",
    "This looks like eight cards got assigned to the same group project and three of them opened a different document.",
    "The deck has coworker energy: everyone is present, nobody has read the brief.",
    "It is not random enough to be innocent, but not coordinated enough to look planned.",
    "Somehow this is a strategy and not just a table seating chart gone wrong.",
    "The whole operation feels like a group chat that muted itself.",
    "This deck has a main idea, then immediately starts wandering around the room.",
    "There is a plan in here somewhere, buried under several confident side quests.",
    "The cards are technically coworkers. The team-building day has failed.",
    "This is a deck list with strong opinions and weak meeting discipline.",
]

FALLBACK_ONE_LINERS = [
    "You put {card1}, {card2}, and {card3} together like they all said yeah bro, I can defend that.",
    "{card1} is trying to play Clash Royale. {card2} is doing something else in the corner.",
    "This deck looks like you picked cards while hungry and refused to put anything back.",
    "Who let {card1}, {card2}, and {card3} become coworkers?",
    "You saw these cards in your collection and decided they deserved to meet.",
    "{card1} and {card2} might have a plan. {card3} is here for the plot twist.",
    "This is not a normal archetype. This is a seating arrangement with tower damage.",
    "The deck has eight cards and at least four competing vibes.",
    "{card1} brought confidence, {card2} brought utility, and {card3} brought confusion.",
    "This deck feels custom in the way a sandwich feels custom when every ingredient was a dare.",
]

COMBO_HOOKS = [
    {
        "cards": ["Sparky", "Electro Spirit"],
        "text": "Bro brought a six-elixir cannon and a one-elixir battery. At least the power supply is on theme.",
        "priority": 100,
    },
    {
        "cards": ["Mega Knight", "Witch"],
        "text": "You have Mega Knight dropping from the ceiling while Witch runs skeleton daycare below. This is not defence; this is a family business.",
        "priority": 98,
    },
    {
        "cards": ["Skeleton Barrel", "Princess"],
        "text": "One card delivers skeletons by air mail while Princess shoots from another postcode. Commitment issues, excellent range.",
        "priority": 96,
    },
    {
        "cards": ["Mini P.E.K.K.A", "Inferno Dragon"],
        "text": "You delegated every tank problem to a tiny pancake robot and a laser lizard. Fair enough, honestly.",
        "priority": 95,
    },
    {
        "cards": ["Goblin Gang", "Dart Goblin"],
        "text": "You hired a gang and one guy with a blowgun. That is either defence or a very cheap heist crew.",
        "priority": 94,
    },
    {
        "cards": ["Tesla", "Sparky"],
        "text": "You have Tesla and Sparky in the same deck. The electricity bill must be fucking insane.",
        "priority": 93,
    },
    {
        "cards": ["Electro Spirit", "Ice Spirit"],
        "text": "Two spirits, one elixir each, and somehow both are expected to solve problems created by bigger cards.",
        "priority": 80,
    },
    {
        "cards": ["Mega Knight", "Skeleton Barrel"],
        "text": "Mega Knight is falling through the roof while Skeleton Barrel arrives by air mail. Nobody agreed on a delivery method.",
        "priority": 88,
    },
    {
        "cards": ["Princess", "Goblin Gang"],
        "text": "Princess is filing complaints from the back while Goblin Gang handles the budget security desk.",
        "priority": 70,
    },
    {
        "cards": ["Sparky", "Goblin Gang"],
        "text": "Sparky is the power grid and Goblin Gang is the security team. The budget meeting got weird.",
        "priority": 90,
    },
]

PACKAGE_TITLES = [
    {
        "cards": ["Mega Knight", "Witch"],
        "titles": [
            "MEGA KNIGHT + WITCH: LANDLORD AND TENANTS",
            "CEILING COLLAPSE SKELETON DAYCARE",
            "THE FAMILY BUSINESS WITH SPLASH DAMAGE",
        ],
    },
    {
        "cards": ["Sparky", "Goblin Gang"],
        "titles": [
            "SPARKY + GOBLIN GANG: POWER GRID SECURITY",
            "THE ELECTRIC CART AND THE BUDGET GUARDS",
            "POWER STATION WITH KNIVES",
        ],
    },
    {
        "cards": ["Skeleton Barrel", "Princess"],
        "titles": [
            "SKELETON BARREL + PRINCESS: AIR MAIL COMPLAINTS",
            "LONG-RANGE SHIPPING DEPARTMENT",
            "PARCEL DELIVERY FROM ANOTHER POSTCODE",
        ],
    },
    {
        "cards": ["Inferno Dragon", "Mini P.E.K.K.A"],
        "titles": [
            "TANK PROBLEM DEPARTMENT",
            "LASER LIZARD AND PANCAKE ROBOT",
            "THE MELT IT OR HIT IT PLAN",
        ],
    },
]

ANCHOR_PRIORITY = [
    "Sparky",
    "Mega Knight",
    "Witch",
    "Skeleton Barrel",
    "Princess",
    "Inferno Dragon",
    "Mini P.E.K.K.A",
    "Electro Spirit",
    "Goblin Gang",
    "Dart Goblin",
    "Hog Rider",
    "Royal Giant",
    "Balloon",
    "Golem",
    "Giant",
    "Lava Hound",
    "X-Bow",
    "Mortar",
]


def deck_roast_catalog_counts() -> dict[str, Any]:
    return {
        "exact_meta": len(EXACT_META_TEMPLATES),
        "meta_adjacent": len(META_ADJACENT_TEMPLATES),
        "anchor_title_categories": {anchor: len(templates) for anchor, templates in ANCHOR_TITLES.items()},
        "anchor_one_liner_categories": {anchor: len(templates) for anchor, templates in ANCHOR_ONE_LINERS.items()},
        "group_project": len(GROUP_PROJECT_CONCLUSIONS),
        "fallback": len(FALLBACK_ONE_LINERS),
        "combo_hooks": len(COMBO_HOOKS),
        "package_title_groups": sum(len(item["titles"]) for item in PACKAGE_TITLES),
    }


def card_name(card: dict[str, Any] | str) -> str:
    return card.get("name", "") if isinstance(card, dict) else str(card)


def name_set(cards: list[dict[str, Any] | str]) -> set[str]:
    return {card_name(card) for card in cards if card_name(card)}


def by_name(cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {card.get("name", ""): card for card in cards if card.get("name")}


def card_lookup(cards: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    lookup = by_name(cards)
    return [lookup[name] for name in names if name in lookup]


def compact_join(values: list[str]) -> str:
    values = [value for value in values if value]
    if not values:
        return "nothing obvious"
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def format_values(values: dict[str, Any]) -> dict[str, Any]:
    return {key: compact_join(value) if isinstance(value, list) else value for key, value in values.items()}


def match_meta_deck(cards: list[dict[str, Any]]) -> dict[str, Any]:
    current_names = name_set(cards)
    best: dict[str, Any] | None = None
    for meta in META_DECKS:
        meta_names = set(meta["cards"])
        matched = sorted(current_names & meta_names)
        extra = sorted(current_names - meta_names)
        missing = sorted(meta_names - current_names)
        candidate = {
            **meta,
            "matched_count": len(matched),
            "matched_cards": matched,
            "extra_cards": extra,
            "missing_cards": missing,
        }
        if best is None or candidate["matched_count"] > best["matched_count"]:
            best = candidate
    if not best:
        return {"style_kind": "custom_signature", "matched_count": 0}
    if best["matched_count"] == 8:
        return {**best, "style_kind": "exact_meta"}
    if best["matched_count"] >= 6:
        return {**best, "style_kind": "meta_adjacent"}
    return {**best, "style_kind": "custom_signature"}


def pick_package(deck_names: set[str], selector: ExpressionSelector) -> tuple[list[str], str] | None:
    available = [item for item in PACKAGE_TITLES if set(item["cards"]).issubset(deck_names)]
    if not available:
        return None
    selected = selector.choose(available, "deck-roast:package")
    return selected["cards"], selector.choose(selected["titles"], f"deck-roast:package-title:{','.join(selected['cards'])}")


def pick_anchor(cards: list[dict[str, Any]]) -> str:
    names = name_set(cards)
    for anchor in ANCHOR_PRIORITY:
        if anchor in names:
            return anchor
    win_condition = next((card for card in cards if "win_condition" in card.get("traits", [])), None)
    if win_condition:
        return win_condition.get("name", "")
    costly = sorted(cards, key=lambda card: (card.get("elixir") or 0, card.get("name", "")), reverse=True)
    return costly[0].get("name", "") if costly else "The Deck"


def support_names(cards: list[dict[str, Any]], anchors: list[str]) -> list[str]:
    names = [card.get("name", "") for card in cards if card.get("name") not in anchors]
    return names[:7]


def pick_combo(deck_names: set[str], selector: ExpressionSelector) -> dict[str, Any] | None:
    hooks = [hook for hook in COMBO_HOOKS if set(hook["cards"]).issubset(deck_names)]
    if not hooks:
        return None
    hooks = sorted(hooks, key=lambda item: item["priority"], reverse=True)
    top_priority = hooks[0]["priority"]
    top_hooks = [hook for hook in hooks if hook["priority"] == top_priority]
    return selector.choose(top_hooks, f"deck-roast:combo:{top_priority}")


def deck_difference_line(current_cards: list[dict[str, Any]], recent_cards: list[dict[str, Any]], recent_uses: int, eligible_matches: int) -> str:
    if not recent_cards:
        return "No recent main deck had enough eligible receipts, so this roast is about what you brought today."
    current_key = deck_key(current_cards)
    recent_key = deck_key(recent_cards)
    current_names = name_set(current_cards)
    recent_names = name_set(recent_cards)
    shared = shared_card_count(current_key, recent_key)
    added = sorted(current_names - recent_names)
    removed = sorted(recent_names - current_names)
    if current_key == recent_key:
        return f"Yep, this is the same nonsense you have been committing to for {recent_uses} of {eligible_matches} eligible games."
    if shared >= 6 and added and removed:
        return f"You kept the main idea but changed {compact_join(removed[:2])} into {compact_join(added[:2])}, which is either adaptation or boredom with buttons."
    return "This is not the deck you were mainly using recently. New chapter, same questionable confidence."


def mentioned_card_names(text: str, deck_names: list[str], anchors: list[str], fallback: list[str]) -> list[str]:
    mentioned = []
    lowered = text.lower()
    for name in [*anchors, *deck_names]:
        if name and name.lower() in lowered and name not in mentioned:
            mentioned.append(name)
    for name in fallback:
        if name not in mentioned:
            mentioned.append(name)
        if len(mentioned) >= 4:
            break
    return mentioned[:5]


def compose_deck_roast(
    *,
    cards: list[dict[str, Any]],
    estimated_style: str,
    traits: list[dict[str, Any]],
    average_elixir: float,
    selector: ExpressionSelector,
    deck_role: str,
    recent_main_cards: list[dict[str, Any]] | None = None,
    recent_main_uses: int = 0,
    eligible_matches: int = 0,
    performance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not cards:
        return {
            "headline": "NO DECK, NO DRAMA",
            "one_liner": "The app cannot roast an empty deck without inventing nonsense.",
            "main_roast": "Bring eight cards and the court will resume bullying responsibly.",
            "supporting_roast": "No deck cards were available.",
            "style_kind": "insufficient_data",
            "anchor_cards": [],
            "mentioned_cards": [],
            "tone": "friendly_roast",
            "confidence": "low",
            "evidence_summary": "No canonical eight-card deck was available.",
            "evidence": ["No deck cards available for deck roast."],
        }

    names = [card.get("name", "") for card in cards if card.get("name")]
    deck_names = set(names)
    metadata_complete = all(card.get("metadata_complete", True) for card in cards)
    meta_match = match_meta_deck(cards)
    style_kind = meta_match.get("style_kind", "custom_signature")
    evidence = [
        f"Deck role: {deck_role}",
        f"Detected deck style: {estimated_style}",
        f"Average elixir: {average_elixir}",
        f"Known card metadata: {sum(1 for card in cards if card.get('metadata_complete', True))}/{len(cards)}",
    ]
    if traits:
        evidence.extend(f"{trait.get('label')}: {trait.get('explanation')}" for trait in traits[:5])

    if style_kind == "exact_meta":
        values = format_values(
            {
                "deck_name": meta_match["name"],
                "family": meta_match["family"],
                "matched_count": meta_match["matched_count"],
                "matched_cards": meta_match["matched_cards"][:4],
            }
        )
        one_liner = format_template(selector.choose(EXACT_META_TEMPLATES, f"deck-roast:exact:{meta_match['name']}"), values)
        headline = f"{meta_match['name'].upper()}: YES, THE INTERNET MADE THIS FIRST"
        main = f"{one_liner} The list is an exact 8/8 local match, so the deck gets credit and you get supervision."
        anchor_names = meta_match["matched_cards"][:3]
        evidence.extend(
            [
                f"Exact popular deck match: {meta_match['name']}",
                "Matched cards: 8/8",
                f"Local snapshot date: {LOCAL_DECK_SNAPSHOT_DATE}",
            ]
        )
        mentioned = meta_match["matched_cards"]
        confidence = "high"
        evidence_summary = f"Exact 8/8 match with {meta_match['name']} ({meta_match['family']})."
    elif style_kind == "meta_adjacent":
        values = format_values(
            {
                "deck_name": meta_match["name"],
                "family": meta_match["family"],
                "matched_count": meta_match["matched_count"],
                "matched_cards": meta_match["matched_cards"][:4],
                "missing_cards": meta_match["missing_cards"][:2],
                "extra_cards": meta_match["extra_cards"][:2],
            }
        )
        one_liner = format_template(selector.choose(META_ADJACENT_TEMPLATES, f"deck-roast:adjacent:{meta_match['name']}"), values)
        headline = f"{meta_match['family'].upper()}: YOU TRIED TO IMPROVE IT"
        main = f"{one_liner} Substitution receipt: {compact_join(meta_match['missing_cards'][:2])} became {compact_join(meta_match['extra_cards'][:2])}."
        anchor_names = meta_match["matched_cards"][:3]
        evidence.extend(
            [
                f"Recognised deck-family match: {meta_match['name']}",
                f"Matched cards: {meta_match['matched_count']}/8",
                f"Missing from template: {compact_join(meta_match['missing_cards'])}",
                f"Added instead: {compact_join(meta_match['extra_cards'])}",
                f"Local snapshot date: {LOCAL_DECK_SNAPSHOT_DATE}",
            ]
        )
        mentioned = [*meta_match["matched_cards"][:3], *meta_match["extra_cards"][:2]]
        confidence = "medium"
        evidence_summary = f"{meta_match['matched_count']}/8 match with {meta_match['name']}; substitutions are shown in receipts."
    else:
        package = pick_package(deck_names, selector)
        if package:
            anchor_names, headline = package
        else:
            anchor = pick_anchor(cards)
            anchor_names = [anchor] if anchor else []
            title_templates = ANCHOR_TITLES.get(anchor, [])
            headline = selector.choose(title_templates, f"deck-roast:title:{anchor}") if title_templates else "CUSTOM DECK GROUP PROJECT"

        anchor = anchor_names[0] if anchor_names else pick_anchor(cards)
        supports = support_names(cards, anchor_names)
        while len(supports) < 3:
            supports.append(anchor)
        combo = pick_combo(deck_names, selector)
        one_liner_templates = ANCHOR_ONE_LINERS.get(anchor, FALLBACK_ONE_LINERS)
        values = {
            "anchor": anchor,
            "card1": supports[0],
            "card2": supports[1],
            "card3": supports[2],
            "style": estimated_style,
            "average_elixir": average_elixir,
        }
        one_liner = format_template(selector.choose(one_liner_templates, f"deck-roast:one-liner:{anchor}"), values)
        conclusion = selector.choose(GROUP_PROJECT_CONCLUSIONS, "deck-roast:conclusion")
        if combo:
            main = f"{combo['text']} {conclusion}"
            mentioned = mentioned_card_names(f"{combo['text']} {one_liner}", names, combo["cards"], [anchor, *supports])
        else:
            fallback = format_template(selector.choose(FALLBACK_ONE_LINERS, f"deck-roast:fallback:{anchor}"), values)
            main = f"{one_liner} {conclusion if one_liner != fallback else ''}".strip()
            mentioned = mentioned_card_names(main, names, anchor_names, [anchor, *supports])
        if estimated_style not in {"Unclassified deck style", "No coherent archetype detected"}:
            style_kind = "archetype_family"
            evidence_summary = f"Detected {estimated_style} with custom card-specific anchor copy."
        else:
            style_kind = "custom_signature"
            evidence_summary = "Custom-signature deck roast built from actual cards and local role metadata."
        confidence = "medium" if metadata_complete else "low"

    supporting = deck_difference_line(cards, recent_main_cards or [], recent_main_uses, eligible_matches)
    if performance and performance.get("games"):
        supporting = f"{supporting} Performance receipt: {performance.get('win_rate', 0)}% win rate over {performance.get('games')} eligible games."

    mentioned_cards = card_lookup(cards, mentioned_card_names(f"{headline} {one_liner} {main}", names, anchor_names, mentioned if "mentioned" in locals() else names[:3]))
    anchor_cards = card_lookup(cards, anchor_names)
    return {
        "headline": headline,
        "one_liner": one_liner,
        "main_roast": main,
        "supporting_roast": supporting,
        "style_kind": style_kind,
        "anchor_cards": anchor_cards,
        "mentioned_cards": mentioned_cards,
        "tone": "friendly_roast",
        "confidence": confidence,
        "evidence_summary": evidence_summary,
        "evidence": evidence,
        "deck_match": {
            "style_kind": style_kind,
            "matched_deck_name": meta_match.get("name"),
            "family": meta_match.get("family"),
            "matched_count": meta_match.get("matched_count", 0),
            "matched_cards": meta_match.get("matched_cards", []),
            "missing_cards": meta_match.get("missing_cards", []),
            "extra_cards": meta_match.get("extra_cards", []),
            "snapshot_date": LOCAL_DECK_SNAPSHOT_DATE if style_kind in {"exact_meta", "meta_adjacent"} else None,
        },
    }
