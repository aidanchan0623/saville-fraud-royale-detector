ROAST_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "PANIC_BUTTON_SPECIALIST": {
        "clean": [
            "You do not build pushes. You wait until the screen becomes stressful, then deploy emotional support Mega Knight.",
            "Your deck has one emergency protocol: make something expensive land on the problem."
        ],
        "goblin": [
            "Your deck is a crime scene with a jump button.",
            "What the hell is this plan besides panic, splash damage, and vibes?"
        ],
    },
    "CARDIO_ADDICT": {
        "clean": [
            "Your entire battle plan is sending Hog Rider on unpaid overtime until someone gives up.",
            "You are conducting a cardiovascular study on one pig."
        ],
        "goblin": [
            "That Hog Rider has done more cardio than your win condition has done thinking.",
            "You pressed Hog so often the bridge should start charging rent."
        ],
    },
    "CIVIL_ENGINEERING_MENACE": {
        "clean": [
            "You did not come here to fight. You came here to submit a construction project.",
            "Your opponent wanted a battle. You brought zoning permits."
        ],
        "goblin": [
            "You are playing city planning with tower damage attached.",
            "This is not a duel. It is a damn infrastructure proposal."
        ],
    },
    "TAX_EVASION_SPECIALIST": {
        "clean": [
            "You believe honest tower damage is for people without creativity.",
            "Your strategy is sending tiny accountants to audit the tower."
        ],
        "goblin": [
            "Your tower damage has offshore accounts.",
            "This deck does not attack. It commits statistically suspicious paperwork."
        ],
    },
    "PROBLEM_SOLVER": {
        "clean": [
            "When faced with a tactical problem, you solve it by making two angry men run faster.",
            "Your deck is what happens when patience leaves the chat."
        ],
        "goblin": [
            "Your plan is two angry men and a damn speed boost.",
            "This is not macro. This is button-mashing with witnesses."
        ],
    },
    "ELIXIR_INVESTOR": {
        "clean": [
            "You save elixir so patiently that your opponent has time to graduate before your push begins.",
            "Your deck costs more than your tactical awareness can comfortably finance."
        ],
        "goblin": [
            "Your deck is expensive enough to need a loan officer.",
            "You spent all that elixir and still bought confusion."
        ],
    },
    "IDENTITY_CRISIS": {
        "clean": [
            "Your deck wants to be beatdown, cycle, bait, and bridge spam. It has achieved unemployment in all four industries.",
            "No coherent archetype detected. The deck meeting ended without minutes."
        ],
        "goblin": [
            "Random nonsense detected. The spreadsheet is scared.",
            "This deck is eight cards looking for adult supervision."
        ],
    },
    "AIRSPACE_VIOLATION": {
        "clean": [
            "Your anti-air policy appears to be hoping Balloon respects your personal boundaries.",
            "The sky is not defended. It is merely being observed."
        ],
        "goblin": [
            "Your air defense is a strongly worded letter.",
            "Balloon sees this deck and starts laughing before overtime."
        ],
    },
    "LOG_DENIALIST": {
        "clean": [
            "You saw small-spell bait and decided the tower should process that emotionally.",
            "The deck has no small spell, which is a bold way to outsource regret."
        ],
        "goblin": [
            "No small spell. Absolutely unserious behaviour.",
            "This deck looked at bait and said, damn, let the tower figure it out."
        ],
    },
    "PROPERTY_DEVELOPER": {
        "clean": [
            "You are less interested in winning than in creating affordable housing for defensive structures.",
            "The deck has multiple buildings and a suspicious interest in real estate."
        ],
        "goblin": [
            "You brought a property portfolio to a duel.",
            "Your win condition appears to be urban development."
        ],
    },
    "EMOTIONAL_SUPPORT_CARD": {
        "clean": [
            "You have not kept {card} because it wins. You kept it because it feels like family.",
            "{card} keeps showing up with a {win_rate}% win rate, which is loyalty with receipts."
        ],
        "goblin": [
            "{card} is not a strategy. It is a comfort object with a damage stat.",
            "The {card} relationship is statistically embarrassing."
        ],
    },
    "WHO_HURT_YOU": {
        "clean": [
            "{card} is not your counter. At this point, {card} is your landlord.",
            "The battle log keeps finding {card} near the scene of the incident."
        ],
        "goblin": [
            "{card} saw the matchup and filed ownership papers.",
            "{card} has been farming this account like it found a coupon."
        ],
    },
    "NATURAL_PREDATOR": {
        "clean": [
            "Your deck sees this matchup and immediately begins writing its will.",
            "This enemy core keeps appearing in losses with uncomfortable confidence."
        ],
        "goblin": [
            "This matchup walks in and your deck starts looking for the exit.",
            "Statistically, this enemy shell has been eating your lunch."
        ],
    },
    "OVERLEVELLED_FRAUD": {
        "clean": [
            "You lost {overlevelled_losses} matches while having higher average card levels. The upgrades did their part.",
            "The cards showed up upgraded. The result did not."
        ],
        "goblin": [
            "You lost {overlevelled_losses} overlevelled games. The credit card did its part.",
            "The levels were there. The excuses are now under review."
        ],
    },
    "PANIC_SWITCHER": {
        "clean": [
            "You changed decks after {changes_after_losses} recent losses. This is not adaptation. This is grief bargaining.",
            "The emergency decks are not an escape plan. They are the same problem in a new outfit."
        ],
        "goblin": [
            "You swapped decks after losses like the cards were the only suspects.",
            "This deck history is panic shopping with battle buttons."
        ],
    },
    "ONE_DECK_WARRIOR": {
        "clean": [
            "Loyalty is admirable. So is noticing when something is not working.",
            "You keep returning to the same deck with the emotional strength of a lighthouse."
        ],
        "goblin": [
            "You are committed. The win rate is less committed back.",
            "Same deck, same wounds, impressive paperwork."
        ],
    },
    "MAIN_CHARACTER_SYNDROME": {
        "clean": [
            "You built your identity around {card}, and the evidence is currently doing a slow nod.",
            "{card} appears in {used} of {total} decks. Subtlety has left the arena."
        ],
        "goblin": [
            "{card} is the main character and the plot is currently mid.",
            "This account has a {card} dependency and the battle log has receipts."
        ],
    },
    "CLUTCH_REPORT": {
        "clean": [
            "The final minute is not currently your friend.",
            "Close games keep arriving, and the exits are not always graceful."
        ],
        "goblin": [
            "Overtime has been looking at you funny.",
            "The close-game record is doing damage without elixir."
        ],
    },
    "DECK_DIVORCE": {
        "clean": [
            "This relationship has had enough chances.",
            "Consider counselling without {card}; the recent results are politely alarming."
        ],
        "goblin": [
            "{card} and this deck may need separate lawyers.",
            "The {card} experiment has entered its statistically embarrassing era."
        ],
    },
    "RESPECTABLE_CITIZEN": {
        "clean": [
            "The report tried to be dramatic, but the evidence is annoyingly reasonable.",
            "A few suspicious moments, but nothing the court can fully enjoy."
        ],
        "goblin": [
            "Low fraud detected. Disappointing for comedy, healthy for trophies.",
            "The battle log brought receipts, and most of them are boringly competent."
        ],
    },
}

