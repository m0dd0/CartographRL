from typing import Tuple, Iterable, Any, Union, Callable
from pathlib import Path

import pygame

from ..model import CarthographersGame
from ..model.general import Terrains
from ..model.map import Map
from .base import View


class FieldSprite(pygame.sprite.Sprite):
    pass


class GridSprite(pygame.sprite.Sprite):
    pass


class PygameView(View):
    def __init__(
        self,
        map_size: int,
        display_size: Tuple[int, int] = (800, 400),
        frame_rate: int = 30,
    ):
        super().__init__()

        self.display_size = display_size

        pygame.init()

        self.display = pygame.display.set_mode(display_size)
        self.display.fill((255, 255, 255))

        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        self.field_sprites = pygame.sprite.Group()

    def _get_map_pos(self):
        pass

    def _create_field_surface(self, terrain_type: Terrains):
        pass

    def _draw_field(self, x, y, terrain_type: Terrains):
        surf = self._create_field_surface(game.map_sheet[x, y])
        self.display.blit(
            surf, self.map_pos + (x * self.field_size, y * self.field_size)
        )

    def render(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True

        for x in range(game.map_sheet.size):
            for y in range(game.map_sheet.size):
                self._draw_field(x, y, game.map_sheet[x, y])

        mouse_pos = self._get_map_pos()

        # surf = self._create_field_surface(game.map_sheet[x, y])
        # self.display.blit(self.map_grid.image, self.map_grid.rect)

        # self.display.blit(self.layout_sprite.image, self.layout_sprite.rect)
        # c = self.map_grid.mouse_grid_coordinate()
        # print(c)

        self.display.blit(self.score_table.image, self.score_table.rect)
        self.display.blit(self.map_grid.image, self.map_grid.rect)

        pygame.display.flip()
        self.clock.tick(self.frame_rate)

        # action = None
        # if self.next_button_pressed():
        #     action = ...
        #     self.mirrored = False
        #     self.rotation = 0
        #     # self.setable_option_exists = None

        # return action

    # def get_action(self) -> Tuple[int, Tuple[int, int], int, bool, Terrains]:
    #     action = self.action
    #     self.action = None
    #     return action

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()
