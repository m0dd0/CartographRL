from typing import Tuple, Iterable, Any, Union, Callable
from pathlib import Path

import pygame

from ..model import CarthographersGame
from ..model.general import Terrains
from ..model.map import Map
from .base import View

### DESIGN DECISIONS ###
# there are 3 geneal options:
# use a seperate sprite for everything (every field is a sprite, the grid is a sprite, the background is a sprite, the options are a sprite, the elements in the score table are sprites, ...)
# - most flexible
# - can use pointcollide to check if mouse is in a sprite for all elements
# use a seperate surface for everything (every field is a surface, the grid is a surface, the background is a surface, the options are a surface, the elements in the score table are surfaces, ...)
# - all (point)collision management must be done manually
# use view sprites whose surface consistes of different more elementary surfaces (e.g. a map sprite whose surface consists of a background surface, a grid surface, and a surface for each field)

# it is easier to obtain the map coordinates of the mouse using a grid sprite than iterating over all fields (sprites) and checking if the mouse is in the field (sprite) rect


class Grid(pygame.sprote.Sprite):
    pass


class MapBackgound(pygame.sprite.Sprite):
    pass


class SingleTerrain(pygame.sprite.Sprite):
    pass


class Option(pygame.sprite.Sprite):
    pass


class ScoreTable(pygame.sprite.Sprite):
    pass


class GenericGridSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        cell_widths: Iterable[int],
        cell_heights: Iterable[int],
        grid_line_width: int = 0,
        grid_line_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        super().__init__()

        self._cell_widths = cell_widths
        self._cell_heights = cell_heights
        self._n_cols = len(cell_widths)
        self._n_rows = len(cell_heights)
        self._x_borders = [sum(cell_widths[:i]) for i in range(self._n_cols + 1)]
        self._y_borders = [sum(cell_heights[:i]) for i in range(self._n_rows + 1)]
        self._grid_line_width = grid_line_width
        self._grid_line_color = grid_line_color

        self.image = pygame.Surface((sum(self._cell_widths), sum(self._cell_heights)))
        self.image.fill((255, 255, 255))  # TODO make transparent
        self._draw_grid()

        self.rect = self.image.get_rect()

    def _draw_grid(self):
        for i_col, cell_width in enumerate(self._cell_widths):
            for i_row, cell_height in enumerate(self._cell_heights):
                pygame.draw.rect(
                    self.image,
                    self._grid_line_color,
                    (
                        self._x_borders[i_col],
                        self._y_borders[i_row],
                        cell_width,
                        cell_height,
                    ),
                    self._grid_line_width,
                )

    def mouse_grid_coordinate(self) -> Tuple[int, int]:
        x, y = pygame.mouse.get_pos()
        if not self.rect.collidepoint((x, y)):
            return None

        x_rel, y_rel = x - self.rect.x, y - self.rect.y
        x_coord = sum(x_border < x_rel for x_border in self._x_borders) - 1
        y_coord = sum(y_border < y_rel for y_border in self._y_borders) - 1

        print(x_coord, y_coord)
        return x_coord, y_coord

    def arange_sprites(self, data: Iterable[Iterable[pygame.sprite.Sprite]]):
        assert len(data) == self._n_rows
        for i_row, row in enumerate(data):
            assert len(row) == self._n_cols
            for i_col, cell in enumerate(row):
                if cell is None:
                    continue
                self.arange_sprite(cell, (i_col, i_row))

    def arange_surfaces(self, data: Iterable[Iterable[pygame.Surface]]):
        assert len(data) == self._n_rows
        for i_row, row in enumerate(data):
            assert len(row) == self._n_cols
            for i_col, cell in enumerate(row):
                if cell is None:
                    continue
                self.arange_surface(cell, (i_col, i_row))

    def arange_sprite(self, sprite: pygame.sprite.Sprite, coords: Tuple[int, int]):
        sprite.rect.x = self._x_borders[coords[0]]
        sprite.rect.y = self._y_borders[coords[1]]

    def arange_surface(self, surface: pygame.Surface, coords: Tuple[int, int]):
        self.image.blit(
            surface, (self._x_borders[coords[0]], self._y_borders[coords[1]])
        )


class MapView(GenericGrid):
    def __init__(
        self,
        pos: Tuple[int, int],
        field_size: int,
        map_size: int,
        background: Path,
        line_width: int,
        line_color: Tuple[int, int, int],
    ) -> None:
        super().__init__(
            [field_size] * map_size,
            [field_size] * map_size,
            background,
            line_width,
            line_color,
        )

        self.rect.x, self.rect.y = pos


class ScoreTable(GenericGrid):
    def __init__(
        self,
        pos: Tuple[int, int],
        font_name: str,
        font_size: int,
        font_color: Tuple[int, int, int],
        line_width: int,
        line_color: Tuple[int, int, int],
        first_row: Tuple[str],
        first_col: Tuple[str],
        background: Path,
    ) -> None:
        font = pygame.font.SysFont(font_name, font_size)
        first_col_surfs = [font.render(s, False, font_color) for s in first_col]
        first_row_surfs = [font.render(s, False, font_color) for s in first_row]
        col_widths = [max(s.get_rect().width for s in first_col_surfs)] + [
            s.get_rect().width for s in first_row_surfs[1:]
        ]
        row_heights = [font_size + 2] * len(first_col)

        super().__init__(
            col_widths,
            row_heights,
            background,
            line_width,
            line_color,
        )

        self.rect.x, self.rect.y = pos

        for x, c in enumerate(first_row_surfs):
            self.arange_surface(c, (x, 0))
        for y, c in enumerate(first_col_surfs):
            self.arange_surface(c, (0, y))


class AreaSurf(pygame.surface.Surface):
    def __init__(self, terrain_type: Terrains, field_size, coordinates):
        super().__init__(
            (
                field_size * max(c[0] for c in coordinates),
                field_size * max(c[1] for c in coordinates),
            )
        )

        # resize terrain_surf
        terrain_surf = pygame.transform.scale(terrain_surf, (field_size, field_size))
        for c in coordinates:
            self.blit(terrain_surf, (c[0] * field_size, c[1] * field_size))


# class FieldSurf(pygame.surface.Surface):
#     def __init__(self, terrain_type: Terrains, field_size: int):
#         super().__init__((field_size, field_size))
#         self.fill(terrain_type.color)
# class NextButtonSprite(pygame.sprite.Sprite):
#     pass


class PygameView(View):
    def __init__(
        self,
        map_size: int,
        display_size: Tuple[int, int] = (800, 400),
        frame_rate: int = 30,
        map_field_size: int = 20,
        map_sheet_pos: Tuple[int, int] = (30, 30),
        map_background: Path = None,
        map_line_width: int = 1,
        map_line_color: Tuple[int, int, int] = (0, 0, 0),
        score_table_pos: Tuple[int, int] = (30, 300),
        score_table_font_name: str = "Arial",
        score_table_font_size: int = 10,
        score_table_font_color: Tuple[int, int, int] = (0, 0, 0),
        score_table_line_width: int = 1,
        score_table_line_color: Tuple[int, int, int] = (0, 0, 0),
        score_table_background: Path = None,
        score_table_first_row: Tuple[str] = (
            "  Seasons  ",
            "  Spring  ",
            "  Summer  ",
            "  Autumn  ",
            "  Winter  ",
            "  Total  ",
        ),
        score_table_first_col: Tuple[str] = (
            "  Seasons  ",
            "  Task 1  ",
            "  Task 2  ",
            "  Coins  ",
            "  Mountains  ",
            "  Monsters  ",
            "  Total  ",
        ),
    ):
        super().__init__()

        # settings for the view
        self.display_size = display_size

        # pygame basic settings
        pygame.init()

        self.display = pygame.display.set_mode(display_size)
        self.display.fill((255, 255, 255))

        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        # sprites
        self.score_table = ScoreTable(
            score_table_pos,
            score_table_font_name,
            score_table_font_size,
            score_table_font_color,
            score_table_line_width,
            score_table_line_color,
            score_table_first_row,
            score_table_first_col,
            score_table_background,
        )
        self.map_grid = MapView(
            map_sheet_pos,
            map_field_size,
            map_size,
            map_background,
            map_line_width,
            map_line_color,
        )

    def render(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True

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
