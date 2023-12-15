"""Exploration cards, monster cards amd ruin cards."""

from typing import List, Tuple, FrozenSet
from enum import Enum
from dataclasses import dataclass

from .general import Card, Terrains


@dataclass
class ExplorationOption:
    coin: bool  # whether the option gives a coin
    coords: FrozenSet[Tuple[int, int]]  # coordinates of the fields
    terrain: Terrains  # terrain of the fields


@dataclass
class ExplorationCard(Card):
    name: str  # name of the card
    card_id: int  # id of the card
    time: int  # game progress after playing the card
    options: List[ExplorationOption]  # options of the card


class MonsterCorner(Enum):
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class MonsterRotation(Enum):
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


@dataclass
class MonsterCard(Card):
    name: str  # name of the card
    card_id: int  # id of the card
    corner: MonsterCorner  # inital corner of the monster when playing solo
    rotation: MonsterRotation  # rotation of the monster when playing solo
    coords: FrozenSet[Tuple[int, int]]  # coordinates of the fields


@dataclass
class RuinCard(Card):
    name: str  # name of the card
    card_id: int  # id of the card


EXPLORATION_CARDS = [
    ExplorationCard(
        name="Großer Strom",
        card_id=107,
        time=1,
        options=[
            ExplorationOption(
                coin=True,
                coords=frozenset([(0, 0), (1, 0), (2, 0)]),
                terrain=Terrains.WATER,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 2), (1, 1), (1, 2), (2, 0), (2, 1)]),
                terrain=Terrains.WATER,
            ),
        ],
    ),
    ExplorationCard(
        name="Ackerland",
        card_id=108,
        time=1,
        options=[
            ExplorationOption(
                coin=True, coords=frozenset([(0, 0), (1, 0)]), terrain=Terrains.FARM
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]),
                terrain=Terrains.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Weiler",
        card_id=109,
        time=1,
        options=[
            ExplorationOption(
                coin=True,
                coords=frozenset([(0, 0), (1, 0), (1, 1)]),
                terrain=Terrains.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]),
                terrain=Terrains.VILLAGE,
            ),
        ],
    ),
    ExplorationCard(
        name="Vergessener Wald",
        card_id=110,
        time=1,
        options=[
            ExplorationOption(
                coin=True, coords=frozenset([(0, 0), (1, 1)]), terrain=Terrains.FOREST
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (1, 0), (1, 1), (2, 1)]),
                terrain=Terrains.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Sumpf",
        card_id=115,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)]),
                terrain=Terrains.WATER,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)]),
                terrain=Terrains.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Obsthain",
        card_id=113,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (1, 2)]),
                terrain=Terrains.FARM,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (1, 2)]),
                terrain=Terrains.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Baumwipfeldorf",
        card_id=114,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]),
                terrain=Terrains.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]),
                terrain=Terrains.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Hinterlandbach",
        card_id=111,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]),
                terrain=Terrains.WATER,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]),
                terrain=Terrains.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Gehöft",
        card_id=112,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (1, 0), (1, 1), (2, 0)]),
                terrain=Terrains.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (1, 0), (1, 1), (2, 0)]),
                terrain=Terrains.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Fischerdorf",
        card_id=116,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),
                terrain=Terrains.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),
                terrain=Terrains.WATER,
            ),
        ],
    ),
    ExplorationCard(
        name="Splitterland",
        card_id=117,
        time=0,
        options=[
            ExplorationOption(
                coin=False, coords=frozenset([(0, 0)]), terrain=Terrains.FOREST
            ),
            ExplorationOption(
                coin=False, coords=frozenset([(0, 0)]), terrain=Terrains.FARM
            ),
            ExplorationOption(
                coin=False, coords=frozenset([(0, 0)]), terrain=Terrains.VILLAGE
            ),
            ExplorationOption(
                coin=False, coords=frozenset([(0, 0)]), terrain=Terrains.WATER
            ),
            ExplorationOption(
                coin=False, coords=frozenset([(0, 0)]), terrain=Terrains.MONSTER
            ),
        ],
    ),
]

MONSTER_CARDS = [
    MonsterCard(
        name="Grottenschratüberfall",
        card_id=102,
        corner=MonsterCorner.TOP_RIGHT,
        rotation=MonsterRotation.CLOCKWISE,
        coords=frozenset([(0, 0), (0, 2), (1, 0), (1, 2)]),
    ),
    MonsterCard(
        name="Goblinattacke",
        card_id=101,
        corner=MonsterCorner.BOTTOM_LEFT,
        rotation=MonsterRotation.COUNTER_CLOCKWISE,
        coords=frozenset([(0, 0), (1, 1), (2, 2)]),
    ),
    MonsterCard(
        name="Koboldansturm",
        card_id=103,
        corner=MonsterCorner.BOTTOM_LEFT,
        rotation=MonsterRotation.CLOCKWISE,
        coords=frozenset([(0, 0), (1, 0), (1, 1), (2, 0)]),
    ),
    MonsterCard(
        name="Gnollangriff",
        card_id=104,
        corner=MonsterCorner.TOP_LEFT,
        rotation=MonsterRotation.COUNTER_CLOCKWISE,
        coords=frozenset([(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]),
    ),
]

RUIN_CARDS = [
    RuinCard(name="Verfallenert Außernposeten", card_id=106),
    RuinCard(name="Tempelruinen", card_id=105),
]
