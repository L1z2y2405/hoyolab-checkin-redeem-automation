"""Persistent local state for processed redemption codes."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeState:
    """Tracks seen/processed redemption codes per game."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, list[str]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = {
                game: [c.upper() for c in codes]
                for game, codes in raw.get("codes", {}).items()
                if isinstance(codes, list)
            }
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load state from %s: %s", self.path, exc)
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"codes": {game: sorted(set(codes)) for game, codes in self._data.items()}}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def get_codes(self, game: str) -> set[str]:
        return set(self._data.get(game, []))

    def add_codes(self, game: str, codes: set[str]) -> None:
        if not codes:
            return
        existing = self.get_codes(game)
        merged = existing | {c.upper() for c in codes}
        self._data[game] = sorted(merged)
        self.save()

    def bootstrap_if_empty(self, game: str, discovered: list[str]) -> bool:
        """Seed cache on first run without redeeming. Returns True if bootstrapped."""
        if self.get_codes(game):
            return False
        normalized = {c.upper() for c in discovered if c}
        if not normalized:
            return False
        self._data[game] = sorted(normalized)
        self.save()
        logger.info(
            "%s: first run — seeded %d known code(s) into local cache (no redemption attempted)",
            game,
            len(normalized),
        )
        return True

    def filter_new(self, game: str, discovered: list[str]) -> list[str]:
        cached = self.get_codes(game)
        seen: set[str] = set()
        new_codes: list[str] = []
        for code in discovered:
            normalized = code.upper().strip()
            if not normalized or normalized in cached or normalized in seen:
                continue
            seen.add(normalized)
            new_codes.append(normalized)
        return new_codes
