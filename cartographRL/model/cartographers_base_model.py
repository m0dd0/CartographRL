from abc import ABC, abstractmethod
from typing import List
from enum import Enum

from pydantic import BaseModel, validator, conlist, PositiveInt


class FieldTypes(Enum):
    EMPTY = " "
    MOUNTAIN = "M"
    RUIN = "R"


class Terrains(Enum):
    WATER = "W"
    FOREST = "F"
    MOUNTAIN = "M"
    FIELD = "L"


class ScoringTypes(Enum):
    VILLAGE = "V"
    WATER_AND_FARMS = "W"
    FOREST = "F"
    GEOMETRY = "G"


class Map(BaseModel):
    name: str
    fields: List[List[FieldTypes]]

    @validator("fields")
    def field_must_be_square(cls, fields):
        if all(len(row) == len(fields) for row in fields):
            raise ValueError("Map must be quadratic")
        return fields


class ExplorationOption(BaseModel):
    coin: bool
    shape: List[List[bool]]
    terrain: Terrains

    @validator("shape")
    def shape_must_be_square(cls, shape):
        if all(len(row) == len(shape) for row in shape):
            raise ValueError("Shape must be quadratic")
        return shape


class ExplorationCard(BaseModel):
    name: str
    card_id: int
    time: PositiveInt
    options: conlist(ExplorationOption, min_items=1, max_items=5)


class ScoringCard(BaseModel):
    name: str
    card_id: int
    task_type: ScoringTypes
    solo_points: PositiveInt
    description: str
    evaluation_function: str

    @validator("evaluation_function")
    def evaluation_function_must_be_defined(cls, evaluation_function):
        # check that a function with this name exists in the scoring_functions module
        pass


class CarthographersBaseModel(ABC):
    def __init__(
        self,
        map: Map,
        scoring_cards: List[ScoringCard],
        exploration_cards: List[ExplorationCard],
        season_times: List[int],
    ):
        assert len(scoring_cards) == len(
            season_times
        ), "Scoring cards and season times must have the same length"

        self._map = map
        self._scoring_cards = scoring_cards
        self._all_exploration_cards = exploration_cards
        self._season_times = season_times

    @property
    def map(self) -> Map:
        return self._map

    @property
    def scoring_cards(self) -> List[ScoringCard]:
        return self._scoring_cards

    @property
    def all_exploration_cards(self) -> List[ExplorationCard]:
        return self._all_exploration_cards

    @property
    def season_times(self) -> List[int]:
        return self._season_times

    @property
    @abstractmethod
    def current_season(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_time(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_exploration_options(self) -> List[ExplorationOption]:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_game_over(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_score(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_playable(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def play(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ):
        raise NotImplementedError
