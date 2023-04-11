from typing import Tuple, Iterable, Any, Union, Callable
from pathlib import Path

import pygame

from ..model import CarthographersGame
from ..model.general import Terrains
from ..model.map import Map
from .base import View


class Grid(pygame.sprite.Sprite):
    def __init__(
        self,
        cell_widths: Iterable[int],
        cell_heights: Iterable[int],
        background: Path = None,
        grid_line_width: int = 0,
        grid_line_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        self._cell_widths = cell_widths
        self._cell_heights = cell_heights
        self._n_cols = len(cell_widths)
        self._n_rows = len(cell_heights)
        self._x_borders = [sum(cell_widths[:i]) for i in range(self._n_cols + 1)]
        self._y_borders = [sum(cell_heights[:i]) for i in range(self._n_rows + 1)]
        self._grid_line_width = grid_line_width
        self._grid_line_color = grid_line_color

        self.image = pygame.Surface((sum(self._cell_widths), sum(self._cell_heights)))
        self.image.fill((255, 255, 255))
        if background is not None:
            self.image = pygame.image.load(background)
        self._draw_grid()

        self.rect = self.image.get_rect()

    def _draw_grid(self):
        for x_pos in self._x_borders:
            for y_pos in self._y_borders:
                pygame.draw.rect(
                    self.image,
                    self._grid_line_color,
                    (x_pos, y_pos, self._cell_widths, self._cell_heights),
                    self._grid_line_width,
                )

    def hover_grid_coordinate(self) -> Tuple[int, int]:
        x, y = pygame.mouse.get_pos()
        x_rel, y_rel = x - self.rect.x, y - self.rect.y
        x_coord = sum(x_rel < x_border for x_border in self._x_borders)
        y_coord = sum(y_rel < y_border for y_border in self._y_borders)
        if 0 <= x_coord < self._n_cols and 0 <= y_coord < self._n_rows:
            return x_coord, y_coord

        return None

    def arange_sprites(self, data: Iterable[Iterable[pygame.sprite.Sprite]]):
        assert len(data) == self._n_rows
        for i, row in enumerate(data):
            assert len(row) == self._n_cols
            for j, cell in enumerate(row):
                if cell is None:
                    continue
                cell.rect.x = j * self._cell_widths
                cell.rect.y = i * self._cell_heights

    def arange_surface(self, data: Iterable[Iterable[pygame.Surface]]):
        assert len(data) == self._n_rows
        for i, row in enumerate(data):
            assert len(row) == self._n_cols
            for j, cell in enumerate(row):
                if cell is None:
                    continue
                self.image.blit(cell, (j * self._cell_widths, i * self._cell_heights))


class OptionsSprite(pygame.sprite.Sprite):
    pass


class AreaSprite(pygame.sprite.Sprite):
    def __init__(self, coords, terrain) -> None:
        super().__init__()
        self.coords = coords
        self.terrain = terrain

        self.surf = pygame.Surface((1, 1))
        self.rect = self.surf.get_rect()


class NextButtonSprite(pygame.sprite.Sprite):
    pass


class ScoreTableSprite(pygame.sprite.Sprite):
    pass


class PygameView(View):
    def __init__(
        self,
        display_size: Tuple[int, int] = (800, 400),
        frame_rate: int = 30,
        field_size: int = 20,
        map_sheet_pos=(30, 30),
    ):
        super().__init__()

        # self.terrain_colors = {
        #     Terrains.WATER: (0, 0, 255),
        #     # Terrains.LAND: (0, 255, 0),
        # }

        pygame.init()
        self.display = pygame.display.set_mode(display_size)
        self.display.fill((255, 255, 255))

        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        # self.mirrored = False
        # self.rotation = 0
        # self.setable_option_exists = None

        self.map_sheet_pos = map_sheet_pos

        self.field_size = field_size
        self.map_grid = None

        self._game_id = None

    def adjust_to_game(self, game: CarthographersGame):
        self.map_grid = Grid(
            game.map_sheet.size,
            game.map_sheet.size,
            self.field_size,
            self.field_size,
            background=None,
            grid_line_width=2,
        )
        self.map_grid.rect.x = self.map_sheet_pos[0]
        self.map_grid.rect.y = self.map_sheet_pos[1]

        self._game_id = id(game)

    def render(self, game: CarthographersGame):
        if id(game) != self._game_id:
            raise RuntimeError("View is not adjusted to this game")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True

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
