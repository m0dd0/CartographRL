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

    def is_hero(self) -> bool:
        """Whether the card is from the hero deck ("Karthographin").

        Returns:
            bool: True if the card is from the hero deck, False otherwise.

        Raises:
            ValueError: If the card ID is invalid.
        """
        if self.card_id % 100 == 1:
            return False
        elif self.card_id % 100 == 2:
            return True
        else:
            raise ValueError("Card ID is invalid.")


class CardDeck:
    def __init__(self, cards: List[Card], rng: np.random.Generator = None):
        """Initialize a generic card deck abstraction.

        Args:
            cards (List[Card]): The cards in the deck.
            rng (np.random.Generator, optional): The random number generator.
                Defaults to None.
        """
        if rng is None:
            rng = np.random.default_rng()
        self.rng = rng

        self.cards = cards
        self.rng.shuffle(self.cards)

    def draw(self) -> Card:
        """Draw a card from the deck and remove it from the deck.

        Returns:
            Card: The drawn card.

        Raises:
            IndexError: If the deck is empty.
        """
        return self.cards.pop(0)


class InvalidMoveError(Exception):
    pass
