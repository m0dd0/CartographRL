from typing import Tuple, List, FrozenSet, Dict, Any, Union, Set
from pathlib import Path
import logging

import pygame
import yaml
from mergedeep import merge

from ...model import CarthographersGame
from ...model.general import Terrains
from ..base import View
from .sprites import (
    ScreenSprite,
    MapSprite,
    OptionSprite,
    CandidateSprite,
    # ScoreTableSprite,
    # NextButtonSprite,
    # InfoSprite,
)

logging.basicConfig(level=logging.DEBUG)


class PygameView(View):
    def __init__(self, frame_rate: int = 30, style: Dict[str, Any] = None) -> None:
        """Pygame view of the game.

        Args:
            frame_rate (int, optional): Frame rate of the game. Defaults to 30.
            style (Dict[str, Any], optional): Style of the view. Defaults to a dict
                with the values fromm pygame_styles/default.yaml.
        """
        super().__init__()

        # load style
        style = style or {}
        default_style_path = Path(__file__).parent / "styles" / "default.yaml"
        with open(default_style_path, "r") as f:
            default_style = yaml.safe_load(f)
        self._style = merge(default_style, style)

        # pygame basic settings
        pygame.init()
        self.display = pygame.display.set_mode(self._style["screen"]["size"])
        pygame.display.set_caption(self._style["title"])
        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        # sprites
        self._background_sprite = ScreenSprite(self._style["screen"])
        self._map_sprite: MapSprite = None
        self._options_background_sprite = None
        self._option_sprites: List[OptionSprite] = []
        self._candidate_sprites: List[CandidateSprite] = []
        self._score_table_sprite = None
        self._next_button_sprite = None

        # view state
        self._active_candidate = None

    def _all_sprites(self) -> List[pygame.sprite.Sprite]:
        """Returns all sprites of the view. If the sprites hasn't been created yet,
        the values will be None.
        The ordering accounts for the drawing order.

        Returns:
            List[pygame.sprite.Sprite]: List of all sprites."""
        sprites = (
            [
                self._background_sprite,
                self._map_sprite,
                # self._score_table_sprite,
                # self._next_button_sprite,
                # self._info_sprite,
            ]
            + self._option_sprites
            + self._candidate_sprites
        )

        return sprites

    def _rebuild_options(self, game: CarthographersGame):
        # delete option sprites from previous move
        self._option_sprites = []

        # create regular option sprites
        for i, opt in enumerate(game.exploration_card.options):
            option_sprite = OptionSprite(
                opt.coords,
                0,
                False,
                opt.terrain,
                opt.coin,
                game.map_sheet.is_setable_anywhere(opt.coords, game.ruin),
                False,
                i,
                self._style["option"],
                self._style["candidate"],
                self._style["field"],
            )
            self._option_sprites.append(option_sprite)

        # create single field option sprites
        # setable_option_exists = game.setable_option_exists()
        # for i in range(5):  # always 5 single field options
        #     single_option_sprite = OptionSprite(
        #         frozenset([(0, 0)]),
        #         0,
        #         False,

        #         False,
        #         not setable_option_exists,
        #         i,
        #         self._style,
        #     )
        #     self._option_sprites.append(single_option_sprite)

        # also upate the candidate sprites
        self._candidate_sprites = []
        for os in self._option_sprites:
            candidate_sprite = os.initial_candidate_sprite()
            self._candidate_sprites.append(candidate_sprite)

    def _rebuild_map(self, game: CarthographersGame):
        self._map_sprite = MapSprite(
            game.map_sheet.to_list(),
            game.map_sheet.ruin_coords,
            self._style["map"],
            self._style["field"],
        )

    def _on_mouse_down(self, event: pygame.event.Event):
        assert not self._active_candidate.dragged if self._active_candidate else True

        for candidate_sprite in self._candidate_sprites:
            if (  # pressed on a valid candidate
                candidate_sprite.valid
                and candidate_sprite.rect.collidepoint(event.pos)
                and candidate_sprite.on_shape(event.pos)
            ):
                if (  # pressed on a different candidate the one that is already active
                    self._active_candidate != candidate_sprite
                    and self._active_candidate is not None
                ):
                    self._active_candidate.reset_drag()

                self._active_candidate = candidate_sprite
                candidate_sprite.drag(event.pos)

    def _candidate_setable(self, game: CarthographersGame) -> bool:
        assert self._active_candidate is not None

        map_position = self._map_sprite.grid_coord(self._active_candidate.rect.topleft)
        if map_position is None:
            return False

        map_coords = game.map_sheet.transform_to_map_coords(
            self._active_candidate.shape_coords, map_position, 0, False
        )
        return game.map_sheet.is_setable(map_coords, game.ruin)

    def _on_mouse_move(self, event: pygame.event.Event, game: CarthographersGame):
        if self._active_candidate is not None and self._active_candidate.dragged:
            self._active_candidate.drag(event.pos)

            self._active_candidate.setable = self._candidate_setable(game)

    def _on_mouse_up(self, event: pygame.event.Event, game: CarthographersGame):
        if self._active_candidate is not None and self._active_candidate.dragged:
            self._active_candidate.drag(event.pos)
            self._active_candidate.drop()

            if self._candidate_setable(game):
                self._active_candidate.rect.topleft = self._map_sprite.pixel_coord(
                    self._map_sprite.grid_coord(self._active_candidate.rect.topleft)
                )
            else:
                self._active_candidate.reset_drag()
                self._active_candidate = None

    # def _on_next_button_click(self):
    #     self._map_sprite = None
    #     self._option_sprites = []
    #     self._candidate_sprites = []
    #     self._score_table_sprite = None
    #     self._next_button_sprite = None

    def _event_loop(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(event)
            if event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(event, game)
            if event.type == pygame.MOUSEMOTION:
                self._on_mouse_move(event)
            # if event.type == pygame.KEYDOWN:
            #     self._on_key_press(event.key)

    def render(self, game: CarthographersGame):
        if None in self._all_sprites():
            logging.debug("Building sprites again.")
            self._rebuild_map(game)
            self._rebuild_options(game)
            # self._build_score_table_sprite(game)
            # self._build_next_button_sprite(game)

        self._event_loop(game)

        for sprite in self._all_sprites():
            self.display.blit(sprite.image, sprite.rect)

        pygame.display.flip()

        # return action

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()
