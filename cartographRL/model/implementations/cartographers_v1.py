"""This implementation is kepp as simple as possible to allow for easy testing of the environment.
It does not include any performance optimizations."""

from typing import List
import random

from cartographRL.model.cartographers_base_model import (
    CartographersBaseModel,
    Map,
    ScoringCard,
    ExplorationCard,
    ExplorationOption,
    RuinCard,
    AmbushCard,
    Terrains,
)


class Cartographers(CartographersBaseModel):
    def __init__(
        self,
        map: Map,
        scoring_cards: List[ScoringCard],
        exploration_cards: List[ExplorationCard],
        ruin_cards: List[RuinCard],
        ambush_cards: List[AmbushCard],
        season_times: List[int],
    ):
        super().__init__(
            map,
            scoring_cards,
            exploration_cards,
            ambush_cards,
            ruin_cards,
            season_times,
        )

        self._current_season = 0
        self._current_time = 0
        self._exploration_cards = random.sample(
            exploration_cards, len(exploration_cards)
        )
        self._current_exploration_options = self._exploration_cards.pop().options
        self._is_game_over = False

    @property
    def current_season(self) -> int:
        return self._current_season

    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def current_exploration_options(self) -> List[ExplorationOption]:
        return self._current_exploration_options

    @property
    def is_game_over(self) -> bool:
        return self._is_game_over

    def calculate_score(self) -> int:
        score = 0
        for scoring_card in self._scoring_cards:
            score += scoring_card.evaluation_function(self._map)
        return score

    def _transform_shape(
        self,
        shape: List[List[bool]],
        rotation: int,
        flip: bool,
    ) -> List[List[bool]]:
        rotation = rotation % 4
        new_shape = [[False for _ in range(len(shape))] for _ in range(len(shape[0]))]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if not cell:
                    continue

                if rotation == 1:
                    x, y = y, -x + len(shape) - 1
                elif rotation == 2:
                    x, y = -x + len(shape) - 1, -y + len(shape[0]) - 1
                elif rotation == 3:
                    x, y = -y + len(shape[0]) - 1, x
                if flip:
                    x = -x + len(shape) - 1
                new_shape[x][y] = True

        return new_shape

    def _shape_is_setable_at(self, shape: List[List[bool]], x, y) -> bool:
        for shape_y, row in enumerate(shape):
            for shape_x, cell in enumerate(row):
                if not cell:
                    continue

                if (
                    x + shape_x >= len(self._map)
                    or y + shape_y >= len(self._map[0])
                    or self._map[x + shape_x][y + shape_y] != Terrains.EMPTY
                ):
                    return False
        return True

    def _shape_is_setable_on_map(self, shape: List[List[bool]]) -> bool:
        for x in range(len(self._map)):
            for y in range(len(self._map[0])):
                if self._shape_is_setable_at(shape, x, y):
                    return True
        return False

    def _option_is_playable_on_map(self, exploration_option: ExplorationOption) -> bool:
        for rotation in range(4):
            for flip in [False, True]:
                transformed_shape = self._transform_shape(
                    exploration_option.shape, rotation, flip
                )
                if self._shape_is_setable_on_map(transformed_shape):
                    return True
        return False

    def _action_is_playable(
        self, exploration_option: ExplorationOption, x, y, rotation, flip
    ) -> bool:
        transformed_shape = self._transform_shape(
            exploration_option.shape, rotation, flip
        )
        return self._shape_is_setable_at(transformed_shape, x, y)

    def _option_is_rift_lands(self, exploration_option: ExplorationOption) -> bool:
        return (
            len(exploration_option.shape) == 1
            and len(exploration_option.shape[0]) == 1
            and exploration_option.coin == False
        )

    def play(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ):
        assert not self._is_game_over
        assert (exploration_option in self._current_exploration_options) or (
            not self._option_is_playable_on_map(exploration_option)
            and self._option_is_rift_lands(exploration_option)
        )
        assert self._action_is_playable(exploration_option, x, y, rotation, flip)

        transformed_shape = self._transform_shape(
            exploration_option.shape, rotation, flip
        )
        for shape_y, row in enumerate(transformed_shape):
            for shape_x, cell in enumerate(row):
                if not cell:
                    continue

                self._map[x + shape_x][y + shape_y] = exploration_option.terrain

        self._current_time += exploration_option.time
        if self._current_time >= self._season_times[self._current_season]:
            self._current_time = 0
            self._current_season += 1
        self._current_exploration_options = self._exploration_cards.pop().options
        self._is_game_over = self._current_season >= len(self._season_times)
