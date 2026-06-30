import random
import re
from typing import Any


OVERUSED_WORDS = {
    "suspicious",
    "emotional",
    "fraudulent",
    "chaotic",
    "midladder",
    "statistically embarrassing",
}


class ExpressionSelector:
    def __init__(self, seed: str | int | None = None) -> None:
        self.seed = str(seed or random.random())
        self.used_ids: set[str] = set()
        self.used_texts: set[str] = set()
        self.word_counts: dict[str, int] = {}

    def choose(self, variants: list[Any], bucket: str, prefer_index: int | None = None) -> Any:
        if not variants:
            raise ValueError(f"No expression variants provided for {bucket}")
        indexed = list(enumerate(variants))
        rng = random.Random(f"{self.seed}:{bucket}:{len(self.used_ids)}")
        rng.shuffle(indexed)
        if prefer_index is not None and 0 <= prefer_index < len(variants):
            indexed.insert(0, (prefer_index, variants[prefer_index]))

        for index, candidate in indexed:
            candidate_id = f"{bucket}:{index}"
            text = self._text_for(candidate)
            if candidate_id in self.used_ids or text in self.used_texts:
                continue
            if self._would_overuse_words(text):
                continue
            self._remember(candidate_id, text)
            return candidate

        index, candidate = indexed[0]
        self._remember(f"{bucket}:{index}:fallback", self._text_for(candidate))
        return candidate

    def _text_for(self, candidate: Any) -> str:
        if isinstance(candidate, str):
            return candidate
        if isinstance(candidate, dict):
            return " ".join(str(value) for value in candidate.values() if isinstance(value, str))
        return str(candidate)

    def _would_overuse_words(self, text: str) -> bool:
        lowered = text.lower()
        for word in OVERUSED_WORDS:
            if word in lowered and self.word_counts.get(word, 0) >= 2:
                return True
        return False

    def _remember(self, candidate_id: str, text: str) -> None:
        self.used_ids.add(candidate_id)
        self.used_texts.add(text)
        lowered = text.lower()
        for word in OVERUSED_WORDS:
            if word in lowered:
                self.word_counts[word] = self.word_counts.get(word, 0) + 1


def format_template(text: str, values: dict[str, Any]) -> str:
    safe = dict(values)
    for key, value in values.items():
        if isinstance(value, float):
            safe[key] = round(value, 2)
    return re.sub(r"\{([a-zA-Z0-9_]+)\}", lambda match: str(safe.get(match.group(1), match.group(0))), text)

