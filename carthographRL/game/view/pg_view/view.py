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
    OptionsBackgroundSprite,
    ScoreTableSprite,
    NextButtonSprite,
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
        self._NEW_MOVE_EVENT = pygame.USEREVENT + 1
        pygame.event.post(pygame.event.Event(self._NEW_MOVE_EVENT))

        # sprites
        self._background_sprite = ScreenSprite(self._style["screen"])
        self._map_sprite: MapSprite = MapSprite(
            self._style["map"], self._style["field"]
        )
        self._options_background_sprite = OptionsBackgroundSprite(
            self._style["options_background"]
        )
        self._option_sprites: List[OptionSprite] = []
        self._candidate_sprites: List[CandidateSprite] = []
        self._score_table_sprite = ScoreTableSprite(self._style["score_table"])
        self._next_button_sprite = NextButtonSprite(self._style["next_button"])
        # self._info_sprite = None

        # view state
        self._option_index = None

    def _all_sprites(self) -> List[pygame.sprite.Sprite]:
        """Returns all sprites of the view.
        The ordering accounts for the drawing order.

        Returns:
            List[pygame.sprite.Sprite]: List of all sprites."""
        sprites = (
            [
                self._background_sprite,
                self._map_sprite,
                self._options_background_sprite,
                self._score_table_sprite,
                self._next_button_sprite,
                # self._info_sprite,
            ]
            + self._option_sprites
            + self._candidate_sprites
        )

        return sprites

    def _build_options(self, game: CarthographersGame):
        # delete option sprites from previous move
        self._option_sprites = []
        self._candidate_sprites = []

        # create regular option sprites
        for i, opt in enumerate(game.exploration_card.options):
            option_sprite = OptionSprite(
                opt.coords,
                opt.terrain,
                opt.coin,
                game.map_sheet.is_setable_anywhere(opt.coords, game.ruin),
                len(game.exploration_card.options) > 2,
                i,
                self._style["option"],
                self._style["field"],
            )
            self._option_sprites.append(option_sprite)

        # create single field option sprites
        setable_option_exists = game.setable_option_exists()
        for i, terrain in enumerate(
            (
                Terrains.FARM,
                Terrains.FOREST,
                Terrains.MONSTER,
                Terrains.VILLAGE,
                Terrains.WATER,
            )
        ):
            option_sprite = OptionSprite(
                frozenset([(0, 0)]),
                terrain,
                False,
                not setable_option_exists,
                True,
                i,
                self._style["single_option"],
                self._style["field"],
            )
            self._option_sprites.append(option_sprite)

        # create candidate sprites
        for os in self._option_sprites:
            self._candidate_sprites.append(
                os.build_candidate_sprite(self._style["candidate"])
            )

    def _candidate_setable(self, game: CarthographersGame) -> bool:
        # as we need game, canditate sprite and map sprite is does not make sense to put this into a sprite method
        assert self._option_index is not None

        candidate_postion = self._candidate_sprites[self._option_index].rect.topleft
        map_position = self._map_sprite.pixel2map_coord(candidate_postion)
        if map_position is None:
            return False

        shape_coords = self._candidate_sprites[self._option_index].coords
        map_coords = game.map_sheet.transform_to_map_coords(
            shape_coords, map_position, 0, False
        )
        return game.map_sheet.is_setable(map_coords, game.ruin)

    def _reset_candidate(self):
        cand = self._candidate_sprites[self._option_index]
        cand.reset_drag()
        self._option_index = None
        self._next_button_sprite.valid = False

    def _on_mouse_down(self, event: pygame.event.Event):
        # press on a valid candidate
        for i, candidate_sprite in enumerate(self._candidate_sprites):
            if candidate_sprite.on_shape(event.pos) and candidate_sprite.valid:
                if i != self._option_index and self._option_index is not None:
                    self._candidate_sprites[self._option_index].reset_drag()

                self._option_index = i
                candidate_sprite.drag(event.pos)

    def _on_mouse_move(self, event: pygame.event.Event, game: CarthographersGame):
        if (
            self._option_index is not None
            and self._candidate_sprites[self._option_index].dragged
        ):
            cand = self._candidate_sprites[self._option_index]
            cand.drag(event.pos)
            cand.setable = self._candidate_setable(game)

    def _on_mouse_up(self, event: pygame.event.Event, game: CarthographersGame):
        if (
            self._option_index is not None
            and self._candidate_sprites[self._option_index].dragged
        ):
            cand = self._candidate_sprites[self._option_index]
            cand.drop()

            if self._candidate_setable(game):
                cand.rect.topleft = self._map_sprite.snap_pixel_coord(cand.rect.topleft)
                self._next_button_sprite.valid = True
            else:
                self._reset_candidate()

        if (
            self._next_button_sprite.valid
            and self._next_button_sprite.rect.collidepoint(event.pos)
        ):
            pygame.event.post(pygame.event.Event(self._NEW_MOVE_EVENT))

    def _on_scroll(self, event: pygame.event.Event):
        for i, option in enumerate(self._option_sprites):
            if option.valid and option.rect.collidepoint(pygame.mouse.get_pos()):
                if i == self._option_index:
                    self._reset_candidate()

                option.rotation = (option.rotation + event.y) % 4
                self._candidate_sprites[i] = option.build_candidate_sprite(
                    self._style["candidate"]
                )

    def _on_key_up(self, event: pygame.event.Event):
        if event.unicode in ("m", "M"):
            for i, option in enumerate(self._option_sprites):
                if option.valid and option.rect.collidepoint(pygame.mouse.get_pos()):
                    if i == self._option_index:
                        self._reset_candidate()

                option.mirror = not option.mirror
                self._candidate_sprites[i] = option.build_candidate_sprite(
                    self._style["candidate"]
                )

    def _on_new_move(self, game: CarthographersGame):
        self._build_options(game)
        self._map_sprite.map_values = game.map_sheet.to_list()
        self._map_sprite.ruin_coords = game.map_sheet.ruin_coords
        self._next_button_sprite.valid = False
        self._score_table_sprite.data = game.season_stats

    def _event_loop(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.MOUSEMOTION:
                self._on_mouse_move(event, game)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(event)
            if event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(event, game)
            if event.type == pygame.MOUSEWHEEL:
                self._on_scroll(event)
            if event.type == pygame.KEYUP:
                self._on_key_up(event)
            if event.type == self._NEW_MOVE_EVENT:
                self._on_new_move(game)

    def render(self, game: CarthographersGame):
        self._event_loop(game)

        for sprite in self._all_sprites():
            self.display.blit(sprite.image, sprite.rect)

        pygame.display.flip()

        if pygame.event.peek(self._NEW_MOVE_EVENT):
            # option, map position, rotation, mirror
            action = (
                game.exploration_card.options[self._option_index],
                self._map_sprite.pixel2map_coord(
                    self._candidate_sprites[self._option_index].rect.topleft
                ),
                self._option_sprites[self._option_index].rotation,
                self._option_sprites[self._option_index].mirror,
            )
            logging.info(f"Action: {action}")
            return action

        return None

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()
