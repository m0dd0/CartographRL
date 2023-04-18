from typing import Tuple, List, FrozenSet, Dict, Any, Union, Set
from pathlib import Path
import logging

import pygame
import yaml
from mergedeep import merge

from ...model import CarthographersGame
from ...model.general import Terrains
from ..base import View

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
        default_style_path = Path(__file__).parent / "pygame_styles" / "default.yaml"
        with open(default_style_path, "r") as f:
            default_style = yaml.safe_load(f)
        self.style = merge(default_style, style)

        # pygame basic settings
        pygame.init()
        self.display = pygame.display.set_mode(self.style["screen"]["size"])
        pygame.display.set_caption(self.style["title"])
        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        # sprites
        self._background_sprite = ScreenSprite(self.style)
        self._map_sprite = None
        self._options_background_sprite = None
        self._option_sprites = []
        self_candidate_sprites = []
        self._score_table_sprite = None
        self._next_button_sprite = None

    def _state_tuple(self):
        selected_option_sprite = self._selected_option_sprite()
        return (
            selected_option_sprite.i_option
            if selected_option_sprite is not None
            else None,
            self._map_sprite.candidate_position(),
            self._map_sprite.fixed_candidate,
            selected_option_sprite.rotation
            if selected_option_sprite is not None
            else None,
            selected_option_sprite.mirror
            if selected_option_sprite is not None
            else None,
        )

    def _all_sprites(self) -> List[pygame.sprite.Sprite]:
        """Returns all sprites of the view. If the sprites hasn't been created yet,
        the values will be None.
        The ordering accounts for the drawing order.

        Returns:
            List[pygame.sprite.Sprite]: List of all sprites."""
        sprites = [
            self._background_sprite,
            self._map_sprite,
            # self._score_table_sprite,
            # self._next_button_sprite,
            # self._info_sprite,
        ] + self._option_sprites

        return sprites

    def _sprites_under_mouse(self) -> Tuple[int, int]:
        mouse_pos = pygame.mouse.get_pos()

        under_mouse_sprites = [
            s for s in self._all_sprites() if s.rect.collidepoint(mouse_pos)
        ]
        return under_mouse_sprites

    def _build_option_sprites(self, game: CarthographersGame):
        # delete option sprites from previous move
        self._option_sprites = []

        # create regular option sprites
        for i_opt, opt in enumerate(game.exploration_card.options):
            option_sprite = OptionSprite(
                opt.coords,
                opt.terrain,
                opt.coin,
                game.map_sheet.is_setable_anywhere(opt.coords, game.ruin),
                i_opt,
                i_opt,
                self.style,
            )
            self._option_sprites.append(option_sprite)

        # create single field option sprites
        setable_option_exists = game.setable_option_exists()
        for i, terrain in enumerate(
            [
                Terrains.VILLAGE,
                Terrains.WATER,
                Terrains.FOREST,
                Terrains.FARM,
                Terrains.MONSTER,
            ]
        ):
            single_option_sprite = OptionSprite(
                frozenset([(0, 0)]),
                terrain,
                False,
                not setable_option_exists,
                terrain,
                i,
                self.style,
            )
            self._option_sprites.append(single_option_sprite)

    def _build_candidate_sprites(self):
        self._candidate_sprites = []
        for os in self._option_sprites:
            candidate_sprite = CandidateSprite(
                os.transformed_coords,
                os.terrain,
            )
            self._candidate_sprites.append(candidate_sprite)

    def _build_map_sprite(self, game: CarthographersGame):
        self._map_sprite = MapSprite(
            game.map_sheet.to_list(),
            game.map_sheet.ruin_coords,
            self.style,
        )

    def _on_mouse_move(self, game):
        if self.selected_candidate_sprite() is not None:
            selected_candidate_sprite.move_to(self._map_sprite.candidate_position())

    def _on_next_button_click(self):
        pass

    def _on_mouse_click(self):
        clicked_sprites = self._sprites_under_mouse()
        for s in clicked_sprites:
            if s in self._option_sprites:
                self._on_option_click(s)

            if s == self._map_sprite:
                self._on_map_click()

            if s == self._next_button_sprite:
                self._on_next_button_click()

    def _on_key_press(self, pressed_key: int):
        # if pressed_key == pygame.M:
        #     self._act_mirror = not self._act_mirror

        # if pressed_key == pygame.R:
        #     self._act_rotation = (self._act_rotation + 1) % 4
        pass

    def _event_loop(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_click()
            if event.type == pygame.KEYDOWN:
                self._on_key_press(event.key)
        self._on_mouse_move(game)

    def render(self, game: CarthographersGame):
        if None in self._all_sprites():
            logging.debug("Building sprites initially")
            self._build_option_sprites(game)
            self._build_map_sprite(game)

        old_state = self._state_tuple()
        self._event_loop(game)
        new_state = self._state_tuple()
        if old_state != new_state:
            logging.debug(
                f"i_option: {str(new_state[0]):<5}, "
                + f"position: {str(new_state[1]):<5}, "
                + f"fixed: {str(new_state[2]):<5}, "
                + f"rotation: {str(new_state[3]):<5}, "
                + f"mirror: {str(new_state[4]):<5}, "
            )

        for sprite in self._all_sprites():
            self.display.blit(sprite.image, sprite.rect)
        pygame.display.flip()

        self.clock.tick(self.frame_rate)

        # return action

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()
