# Community Meme Taxonomy

This project uses `data/community_meme_taxonomy.json` to score the Community Meme Score portion of the Fraud Score.

## Disclaimer

Community Meme Score reflects recurring player-community jokes about card packages. It is not an objective measure of skill, intelligence, balance, or a player's real ability.

The taxonomy is local and versioned. The app does not scrape forums or social media during player analysis.

## Categories

- `panic_button`: emergency defensive cards that get joked about as a reflex button.
- `midladder_landlord`: mid-ladder comfort cards with a loud community reputation.
- `defensive_spam`: cards that fill lanes or slow the game down in a way some players find annoying.
- `overlevel_bully`: cards that become a meme when ladder levels make them feel louder.
- `bridge_spam`: repeated fast pressure at the bridge.
- `annoyance_engine`: cards that repeatedly force awkward answers.
- `bait_menace`: packages that stress small-spell timing.
- `copy_paste_meta`: recognisable deck packages with a strong community identity.
- `high_elixir_prayer`: heavy commitments where the plan can become hope.
- `tower_pressure_spam`: repeated tower-pressure plans.
- `group_project_deck`: several unrelated meme traits stacked without a clear archetype.

## Current Seeded Cards And Packages

Seed cards include Mega Knight, Royal Recruits, Elite Barbarians, Wizard, Witch, Firecracker, Hog Rider, Electro Giant, P.E.K.K.A, Royal Giant, X-Bow, Mortar, Lava Hound, and Balloon.

Seed packages include:

- Mega Knight + Royal Recruits
- Goblin Barrel + Princess + Goblin Gang
- P.E.K.K.A + Mega Knight
- Royal Giant + Fisherman
- Lava Hound + Balloon

## Responsible Editing

When adding or changing a tag:

1. Use gameplay and deck-package jokes only.
2. Do not use sexuality, race, gender, religion, disability, nationality, appearance, slurs, real-world threats, or personal harassment as insults.
3. Keep source notes honest: these are player-community stereotypes, not objective facts.
4. Add counterpoint context when a card is also a legitimate archetype card.
5. Keep one-card weights modest. Use combination bonuses for clearly supported packages.
6. Update `last_reviewed` when changing a card or package.
7. Run backend tests and the frontend build before committing.

## Adding A Roast Direction

Edit the `roast_directions` array for a card or combination in `data/community_meme_taxonomy.json`.

For example, to personalize Mega Knight + Royal Recruits, find:

```json
{
  "id": "mega_knight_royal_recruits",
  "cards": ["Mega Knight", "Royal Recruits"],
  "roast_directions": [
    "Mega Knight plus Royal Recruits. Bro did not build a deck; bro built a fucking housing estate."
  ]
}
```

Then add another string to that array. Keep it deterministic-friendly: write complete one-liners, not dynamic text that depends on hidden context.
