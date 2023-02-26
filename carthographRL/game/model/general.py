from dataclasses import dataclass
from abc import ABC
from enum import Enum
from typing import List

import numpy as np


class Terrains(Enum):
    VILLAGE = 1
    WATER = 2
    FOREST = 3
    FARM = 4
    MONSTER = 5
    EMPTY = 6
    MOUNTAIN = 7
    WASTE = 8


@dataclass
class Card(ABC):
    name: str
    card_id: int

    def is_hero(self):
        if self.card_id % 100 == 1:
            return False
        elif self.card_id % 100 == 2:
            return True
        else:
            raise ValueError("Card ID is invalid.")


class CardDeck:
    def __init__(self, cards: List[Card], rng: np.random.Generator = None):
        if rng is None:
            rng = np.random.default_rng()
        self.rng = rng

        self.cards = cards
        self.rng.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop(0)


class InvalidMoveError(Exception):
    pass


class MonsterMode(Enum):
    RANDOM = 0
    SOLO = 1
    MAX_BORDERS = 2
