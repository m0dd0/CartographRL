from dataclasses import dataclass
from abc import ABC
from enum import Enum


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


class InvalidMoveError(Exception):
    pass
