"""Implementation of the Carthographers game logic."""

from typing import Tuple, FrozenSet

import numpy as np

from .general import InvalidMoveError, CardDeck, Terrains
from .scoring import ScoringDeck, SCORING_CARDS
from .map import Map
from .exploration import (
    ExplorationCard,
    ExplorationOption,
    RuinCard,
    MonsterCard,
    MonsterCorner,
    MonsterRotation,
    EXPLORATION_CARDS,
    MONSTER_CARDS,
    RUIN_CARDS,
)


class CarthographersGame:
    def __init__(
        self,
        scoring_deck: ScoringDeck = None,
        exploration_deck: CardDeck = None,
        map_sheet: Map = None,
        season_times: Tuple[int, int, int, int] = (8, 8, 7, 6),
        monster_mode: str = "random",
    ):
        """Initialize a new game.

        Args:
            scoring_deck (ScoringDeck, optional): The scoring deck to use.
                If None is passed, a new deck is created with all available scoring cards.
                Defaults to None.
            exploration_deck (CardDeck, optional): The exploration deck to use.
                If None is passed, a new deck is created with all available exploration, mosnter and ruin cards.
                Defaults to None.
            map_sheet (Map, optional): The map sheet to use.
                If None is passed, a new map sheet is created with the map A.
                Defaults to None.
            season_times (Tuple[int, int, int, int], optional): The number of time per season. Defaults to (8, 8, 7, 6).
            monster_mode (str, optional): The monster mode to use.
                Determines how monsters are placed on the map sheet when playing solo.
                Defaults to "random".
        """
        # game setup
        scoring_deck = scoring_deck or ScoringDeck(SCORING_CARDS)
        self.scoring_cards = scoring_deck.draw()
        self.exploration_deck = exploration_deck or CardDeck(
            EXPLORATION_CARDS + MONSTER_CARDS + RUIN_CARDS
        )
        self.map_sheet = map_sheet or Map.generate_A()
        self.season_times = season_times
        self.monster_mode = monster_mode
        self._rng = np.random.default_rng()  # only used for random monster placement

        # state of the game
        self.season = 0
        self.time = 0
        self.ruin = False  # wehther the next area must be placed on a ruin
        self.exploration_card = None
        self._draw_exploration_card()

        # progress of the game
        self.coins_from_options = 0
        self.season_stats = [
            {
                "coins_from_options": 0,
                "surrounded_mountains": 0,
                "monster_discount": 0,
                "task_A_score": 0,
                "task_B_score": 0,
            }
            for _ in range(len(self.season_times))
        ]

    def _set_monster_random(self, shape_coords: FrozenSet[Tuple[int, int]]):
        """Places the monster randomly on the map sheet.

        Args:
            shape_coords (FrozenSet[Tuple[Int, Int]]): The shape coordinates of the monster.
        """
        setable_options = list(
            self.map_sheet.setable_actions(shape_coords, on_ruin=False)
        )
        rotation, position, mirror = setable_options[
            self._rng.integers(len(setable_options))
        ]
        self.map_sheet.place(
            shape_coords, Terrains.MONSTER, rotation, position, mirror, on_ruin=False
        )

    def _set_monster_solo(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        monster_corner: MonsterCorner,
        monster_rotation: MonsterRotation,
    ):
        """Sets the monster according to the solo rules. I.e. staerting in the outer monster corner
        and cycling until a valid position is found.

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): The shape coordinates of the monster.
            monster_corner (MonsterCorner): The corner to start in.
            monster_rotation (MonsterRotation): The rotation to use for finding a suitable placement.
        """
        raise NotImplementedError()

    def _set_monster_max_borders(self, shape_coords: FrozenSet[Tuple[int, int]]):
        """Places the monster on the map sheet such that it has the most empty fields around it.

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): The shape coordinates of the monster.
        """
        setable_options = list(
            self.map_sheet.setable_actions(shape_coords, on_ruin=False)
        )
        best_opt = max(
            setable_options,
            key=lambda opt: self.map_sheet.transform_to_cluster(
                shape_coords, opt[0], opt[1], opt[2]
            )
            .surrounding_terrains()
            .count(Terrains.EMPTY.value),
        )
        self.map_sheet.place(
            shape_coords,
            Terrains.MONSTER,
            best_opt[0],
            best_opt[1],
            best_opt[2],
            on_ruin=False,
        )

    def _set_monster(self, monster_card: MonsterCard):
        """Places the monster on the map sheet according to the current monster mode.

        Args:
            monster_card (MonsterCard): The monster card to place.
        """
        shape_coords = monster_card.coords
        if not self.map_sheet.is_setable_anywhere(monster_card.coords, on_ruin=False):
            shape_coords = np.array([[0, 0]])

        if self.monster_mode == "random":
            self._set_monster_random(shape_coords)

        elif self.monster_mode == "solo":
            self._set_monster_solo(
                shape_coords, monster_card.corner, monster_card.rotation
            )

        elif self.monster_mode == "max_borders":
            self._set_monster_max_borders(shape_coords)

    def _update_season(self):
        """Updates the season and resets the time if the season has ended.
        Also updates the season stats.
        """
        if self.time < self.season_times[self.season]:
            return

        self.season_stats[self.season]["coins_from_options"] = self.coins_from_options
        self.season_stats[self.season][
            "surrounded_mountains"
        ] = self.map_sheet.surrounded_mountains()
        self.season_stats[self.season][
            "monster_discount"
        ] = self.map_sheet.eval_monsters()
        self.season_stats[self.season]["task_A_score"] = self.scoring_cards[
            self.season
        ].evaluate(self.map_sheet)
        self.season_stats[self.season]["task_B_score"] = self.scoring_cards[
            (self.season + 1) % len(self.season_times)
        ].evaluate(self.map_sheet)

        self.season += 1
        self.time = 0

    def _draw_exploration_card(self):
        """Draws a new exploration card. If the drawn card is a ruin card, the next area must be placed on a ruin.
        If the drawn card is a monster card, the monster is placed on the map sheet.
        Cards are drawn until an exploration card is drawn.
        """
        self.exploration_card = None
        self.ruin = False

        while self.exploration_card is None:
            drawn_card = self.exploration_deck.draw()
            if isinstance(drawn_card, RuinCard):
                self.ruin = True
            elif isinstance(drawn_card, MonsterCard):
                self._set_monster(drawn_card)
            elif isinstance(drawn_card, ExplorationCard):
                self.exploration_card = drawn_card
                # if we can set the exploration card only if the ruin constraint is not active, we deactivate it
                if (
                    self.ruin
                    and not self.setable_option_exists()
                    and self.setable_option_exists(on_ruin=False)
                ):
                    self.ruin = False
                # if there is (still) no setable option, this means we set a single field which never has a ruin constraint
                if not self.setable_option_exists():
                    self.ruin = False
                    # TODO considfer using a single field attribute to avoid recomputing setable options

    def setable_option_exists(self, on_ruin: bool = None) -> bool:
        """Returns whether there is at least one setable option for the current exploration card.

        Returns:
            bool: True if there is at least one setable option, False otherwise.
        """
        return any(
            self.map_sheet.is_setable_anywhere(opt.coords, on_ruin or self.ruin)
            for opt in self.exploration_card.options
        )

    def play(
        self,
        i_option: int,
        position: Tuple[int, int],
        rotation: int,
        mirror: bool,
        single_field: Terrains,
    ):
        """Plays a move. This includes placing the exploration option according to the given parameters,
        evaluating the season if the time is up and drawing a new exploration card.

        Args:
            i_option (int): The index of the exploration option to play.
            position (Tuple[int, int]): The position to place the exploration option.
            rotation (int): The rotation to use for the exploration option.
            mirror (bool): Whether to mirror the exploration option.
            single_field (Terrains, optional): If set, a single field of the given terrain instead of the given exploration option is placed.
                Is only allowed if there is no other option to place. Defaults to None.

        Raises:
            InvalidMoveError: If the move is invalid.
        """
        # validate input
        if self.season >= len(self.season_times):
            raise InvalidMoveError("Game is already over.")

        if len(self.exploration_card.options) < i_option:
            raise InvalidMoveError("Invalid option")

        if single_field is not None and self.setable_option_exists():
            raise InvalidMoveError("There is a possibility to set one of the options.")

        # get exploration option
        exploration_option = self.exploration_card.options[i_option]

        shape_coords = exploration_option.coords
        terrain = exploration_option.terrain
        if single_field:
            shape_coords = frozenset([(0, 0)])
            terrain = single_field

        # place exploration option, implicitly checks if it is setable
        self.map_sheet.place(
            shape_coords,
            terrain,
            rotation,
            position,
            mirror,
            on_ruin=self.ruin,
        )

        # add coin
        if single_field is None and exploration_option.coin:
            self.coins_from_options += 1

        # advance the game and add evaluate season if season has ended
        self.time += self.exploration_card.time
        self._update_season()

        # draw new exploration card
        self._draw_exploration_card()
