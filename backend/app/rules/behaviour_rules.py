def choose_behaviour_title(total_battles: int, unique_decks: int, exact_same_rate: float, changes_after_losses: int) -> tuple[str, str]:
    if changes_after_losses >= 3 and changes_after_losses >= max(2, total_battles * 0.18):
        return "PANIC_SWITCHER", "PANIC SWITCHER"
    if unique_decks >= max(4, total_battles // 4):
        return "PANIC_SWITCHER", "DECK HOPPER"
    if exact_same_rate >= 0.8:
        return "ONE_DECK_WARRIOR", "ONE-DECK WARRIOR"
    return "PANIC_SWITCHER", "EMOTIONAL DECK BUILDER"

