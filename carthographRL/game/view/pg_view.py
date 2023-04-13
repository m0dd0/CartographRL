from typing import Tuple, List, FrozenSet
from pathlib import Path

import pygame

from ..model import CarthographersGame
from ..model.general import Terrains
from .base import View

### DESIGN DECISIONS ###
# there are 3 geneal options:
# use a seperate sprite for everything (every field is a sprite, the grid is a sprite, the background is a sprite, the options are a sprite, the elements in the score table are sprites, ...)
# - most flexible
# - can use pointcollide to check if mouse is in a sprite for all elements
# - we need to keep track of all sprites and delete/update/add them when necessary
# use a seperate surface for everything (every field is a surface, the grid is a surface, the background is a surface, the options are a surface, the elements in the score table are surfaces, ...)
# - all (point)collision management must be done manually
# use view sprites whose surface consistes of different more elementary surfaces (e.g. a map sprite whose surface consists of a background surface, a grid surface, and a surface for each field)
# - only areas which might be clicked need to be checked for collision so we need only sprites for these few areas
# --> use sprite for non overlapping areas: map, score table, each option, info field, next button

# the visuliazetion option can be passed as arguments to the constructor of the view or used as a global variable or a class variable
# --> use class variabels for sprites and surfaces as the variables often also depend on the way how we create the basic surface

# sprites contain only the information necessary to draw themselfs, they do not contain any information about their position and no information about the game state

# surfaces are the most elementary pygame objects, sprites are built from multiple surfaces
# --> create a subclass for all used surfaces, to change the appearance of the game only the surface classes need to be changed
# these surface subclasses encapsulate the backgound, size and fill of the surface which are otherwise a lot of arguments to the constructor of the surface

# use .png assets instead of .svg as it is easier to load them into pygame
###


class FieldSurf(pygame.surf.Surface):
    RUIN_OVERLAY = Path(__file__).parent / "assets" / "ruin_128.png"
    ICONS = {
        Terrains.VILLAGE: (Path(__file__).parent / "assets" / "house_128.png",),
        Terrains.WATER: (Path(__file__).parent / "assets" / "water_128.png",),
        Terrains.FOREST: (Path(__file__).parent / "assets" / "tree_128.png",),
        Terrains.FARM: (Path(__file__).parent / "assets" / "field_128.png",),
        Terrains.MONSTER: (Path(__file__).parent / "assets" / "monster_128.png",),
        Terrains.EMPTY: (Path(__file__).parent / "assets" / "empty.png",),
        Terrains.MOUNTAIN: (Path(__file__).parent / "assets" / ".png",),
        Terrains.WASTE: (Path(__file__).parent / "assets" / ".png",),
    }
    BACKGROUND_COLOR = {
        Terrains.VILLAGE: (204, 24, 24),
        Terrains.WATER: (47, 32, 179),
        Terrains.FOREST: (10, 120, 10),
        Terrains.FARM: (245, 172, 2),
        Terrains.MONSTER: (122, 16, 143),
        Terrains.EMPTY: (219, 175, 132),
        Terrains.MOUNTAIN: (104, 108, 110),
        Terrains.WASTE: (92, 92, 54),
    }
    SIZE = 10

    def __init__(self, terrain: Terrains, ruin: bool = False) -> None:
        super().__init__((self.SIZE, self.SIZE))
        self.fill(self.BACKGROUND_COLOR[terrain])


class MapSprite(pygame.sprite.Sprite):
    # BORDER_WIDTH = 10
    # BACKGROUND = Path(__file__).parent / "assets" / "background.png"
    def __init__(
        self,
        map_values: List[List[Terrains]],
        ruin_coords: FrozenSet[Tuple[int, int]],
        candidate_coords: FrozenSet[Tuple[int, int]],
        candidate_terrain: Terrains,
    ) -> None:
        super().__init__()

        extent = len(map_values[0]) * FieldSurf.SIZE
        self.image = pygame.Surface((extent, extent))
        self.rect = self.image.get_rect()

        for x, row in enumerate(map_values):
            for y, terrain in enumerate(row):
                field_surf = FieldSurf(terrain, (x, y) in ruin_coords)
                self.image.blit(field_surf, (x * FieldSurf.SIZE, y * FieldSurf.SIZE))

        # for x, y in candidate_coords:
        #     field_surf = FieldSurf(candidate_terrain)
        #     field_surf.fill((0, 255, 0))
        #     self.image.blit(field_surf, (x * 10, y * 10))


class OptionSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        coin: bool,
        valid: bool,
        selected: bool,
        i_option: int,
        single: bool,
    ) -> None:
        super().__init__()

        # self.image = pygame.Surface((60,30))
        # self.image.fill((255,255,255))
        # self.rect = self.image.get_rect()

        # for x,y in coords:
        #     field_surf =
        #     self.image.blit(field_surf, (x * OPTION_FIELD_SIZE, y * OPTION_FIELD_SIZE))


class ScoreTableSprite(pygame.sprite.Sprite):
    pass


class NextButtonSprite(pygame.sprite.Sprite):
    pass


class InfoSprite(pygame.sprite.Sprite):
    pass


class PygameView(View):
    FRAME_RATE = 30

    def __init__(self):
        super().__init__()

        # pygame basic settings
        pygame.init()
        self.display = pygame.display.set_mode((800, 400))
        self.clock = pygame.time.Clock()

        # sprites
        self._map_sprite = None
        self._option_sprites = []
        self._score_table_sprite = None
        self._next_button_sprite = None
        self._info_sprite = None

        # view state / selected action values
        self._act_i_option = None
        self._act_position = None
        self._act_rotation = 0
        self._act_mirror = False
        self._act_single_field = None

    def _all_sprites(self) -> List[pygame.sprite.Sprite]:
        return [
            self.map_sprite,
            self._score_table_sprite,
            self._next_button_sprite,
            self._info_sprite,
        ] + self._option_sprites

    def _get_sprite_under_mouse(self) -> Tuple[int, int]:
        mouse_pos = pygame.mouse.get_pos()
        clicked_sprites = [
            s for s in self._all_sprites() if s.rect.collidepoint(mouse_pos)
        ]
        assert len(clicked_sprites) <= 1
        return clicked_sprites[0] if clicked_sprites else None

    def _rebuild_option_sprites(self, game: CarthographersGame):
        self._option_sprites = []
        for i_opt, opt in enumerate(game.exploration_card.options):
            self._option_sprites.append(
                OptionSprite(
                    opt.coords,
                    opt.terrain,
                    opt.coin,
                    game.map_sheet.is_setable_anywhere(opt.coords),
                    self._act_i_option == i_opt,
                )
            )

        if game.setable_option_exists():
            return

        for terrain in Terrains:
            if terrain == Terrains.EMPTY:
                continue
            self._option_sprites.append(
                OptionSprite(
                    (0, 0),
                    terrain.value,
                    0,
                    not game.setable_option_exists(),
                    self._act_single_field == terrain,
                )
            )

    def _rebuild_map_sprite(self, game: CarthographersGame):
        coords = None
        terrain = None
        if self._act_position is not None:
            if self._act_single_field is not None:
                coords = frozenset([(0, 0)])
                terrain = self._act_single_field
            else:
                coords = game.exploration_card.options[self._act_i_option].coords
                terrain = game.exploration_card.options[self._act_i_option].terrain

            coords = game.map_sheet.transform_to_map_coords(
                coords, self._act_rotation, self._act_position, self._act_mirror
            )

        self.map_sprite = MapSprite(game.map_sheet.to_list(), coords, terrain)

    def _on_option_click(self, game: CarthographersGame, clicked_sprite: OptionSprite):
        i_option = self._option_sprites.index(clicked_sprite)
        # TODO account for singel field options
        option = game.exploration_card.options[i_option]
        valid_option = game.map_sheet.is_setable_anywhere(option.coords)
        if self._act_i_option != i_option and valid_option:
            self._act_position = None
            self._act_rotation = 0
            self._act_mirror = False
            self._act_i_option = i_option

    def _on_map_click(self, game: CarthographersGame):
        if self._act_i_option is None:
            return

        map_coord = self._map_sprite.get_mouse_grid_coordinate()
        if game.map_sheet.is_setable(
            game.exploration_card.options[self._act_i_option].coords,
            map_coord,
            self._act_mirror,
            self._act_rotation,
        ):
            self._act_position = map_coord

    def _on_next_button_click(self):
        if self._act_i_option is None or self._act_position is None:
            return None

        action = (
            self._act_i_option,
            self._act_position,
            self._act_rotation,
            self._act_mirror,
            self._act_single_field,
        )
        self._act_i_option = None
        self._act_position = None
        self._act_rotation = 0
        self._act_mirror = False

        return action

    def _on_mouse_click(self, game: CarthographersGame):
        action = None
        clicked_sprite = self._get_sprite_under_mouse()
        # update the selected option if option is clicked and valid, if the clicked option is different to the previous one reset the selecte map position
        if clicked_sprite in self._option_sprites:
            self._on_option_click(game, clicked_sprite)

        # update the selected map position if map is clicked, an option is selected and the position is valid
        if clicked_sprite == self._map_sprite:
            self._on_map_click(game)

        # directly return the current action if the next button is clicked and an option is selected and a position is selected, reset the selected actions
        if clicked_sprite == self._next_button_sprite:
            action = self._on_next_button_click()

        return action

    def _on_key_press(self, pressed_key: int):
        if pressed_key == pygame.M:
            self._act_mirror = not self._act_mirror

        if pressed_key == pygame.R:
            self._act_rotation = (self._act_rotation + 1) % 4

    def _rebuild_sprites(self, game: CarthographersGame):
        # self._rebuild_option_sprites(game)
        self._rebuild_map_sprite(game)
        # self._rebuild_score_table_sprite(game)

    def _event_loop(self, game: CarthographersGame):
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.MOUSEBUTTONUP:
                action = self._on_mouse_click(game)
            if event.type == pygame.KEYDOWN:
                self._on_key_press(event.key)

        return action

    def render(self, game: CarthographersGame):
        action = self._event_loop(game)
        self._rebuild_sprites(game)

        for sprite in self._all_sprites():
            self.display.blit(sprite.image, sprite.rect)

        pygame.display.flip()
        self.clock.tick(self.FRAME_RATE)

        return action

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()


# class GenericGridSprite(pygame.sprite.Sprite):
#     def __init__(
#         self,
#         cell_widths: Iterable[int],
#         cell_heights: Iterable[int],
#         grid_line_width: int = 0,
#         grid_line_color: Tuple[int, int, int] = (0, 0, 0),
#     ) -> None:
#         super().__init__()

#         self._cell_widths = cell_widths
#         self._cell_heights = cell_heights
#         self._n_cols = len(cell_widths)
#         self._n_rows = len(cell_heights)
#         self._x_borders = [sum(cell_widths[:i]) for i in range(self._n_cols + 1)]
#         self._y_borders = [sum(cell_heights[:i]) for i in range(self._n_rows + 1)]
#         self._grid_line_width = grid_line_width
#         self._grid_line_color = grid_line_color

#         self.image = pygame.Surface((sum(self._cell_widths), sum(self._cell_heights)))
#         self.image.fill((255, 255, 255))  # TODO make transparent
#         self._draw_grid()

#         self.rect = self.image.get_rect()

#     def _draw_grid(self):
#         for i_col, cell_width in enumerate(self._cell_widths):
#             for i_row, cell_height in enumerate(self._cell_heights):
#                 pygame.draw.rect(
#                     self.image,
#                     self._grid_line_color,
#                     (
#                         self._x_borders[i_col],
#                         self._y_borders[i_row],
#                         cell_width,
#                         cell_height,
#                     ),
#                     self._grid_line_width,
#                 )

#     def mouse_grid_coordinate(self) -> Tuple[int, int]:
#         x, y = pygame.mouse.get_pos()
#         if not self.rect.collidepoint((x, y)):
#             return None

#         x_rel, y_rel = x - self.rect.x, y - self.rect.y
#         x_coord = sum(x_border < x_rel for x_border in self._x_borders) - 1
#         y_coord = sum(y_border < y_rel for y_border in self._y_borders) - 1

#         print(x_coord, y_coord)
#         return x_coord, y_coord

#         # def arange_sprites(self, data: Iterable[Iterable[pygame.sprite.Sprite]]):
#         #     assert len(data) == self._n_rows
#         #     for i_row, row in enumerate(data):
#         #         assert len(row) == self._n_cols
#         #         for i_col, cell in enumerate(row):
#         #             if cell is None:
#         #                 continue
#         #             self.arange_sprite(cell, (i_col, i_row))

#         # def arange_surfaces(self, data: Iterable[Iterable[pygame.Surface]]):
#         #     assert len(data) == self._n_rows
#         #     for i_row, row in enumerate(data):
#         #         assert len(row) == self._n_cols
#         #         for i_col, cell in enumerate(row):
#         #             if cell is None:
#         #                 continue
#         #             self.arange_surface(cell, (i_col, i_row))

#         # def arange_sprite(self, sprite: pygame.sprite.Sprite, coords: Tuple[int, int]):
#         #     sprite.rect.x = self._x_borders[coords[0]]
#         #     sprite.rect.y = self._y_borders[coords[1]]

#         # def arange_surface(self, surface: pygame.Surface, coords: Tuple[int, int]):
#         self.image.blit(
#             surface, (self._x_borders[coords[0]], self._y_borders[coords[1]])
#         )


# class MapView(GenericGrid):
#     def __init__(
#         self,
#         pos: Tuple[int, int],
#         field_size: int,
#         map_size: int,
#         background: Path,
#         line_width: int,
#         line_color: Tuple[int, int, int],
#     ) -> None:
#         super().__init__(
#             [field_size] * map_size,
#             [field_size] * map_size,
#             background,
#             line_width,
#             line_color,
#         )

#         self.rect.x, self.rect.y = pos


# class ScoreTable(GenericGrid):
#     def __init__(
#         self,
#         pos: Tuple[int, int],
#         font_name: str,
#         font_size: int,
#         font_color: Tuple[int, int, int],
#         line_width: int,
#         line_color: Tuple[int, int, int],
#         first_row: Tuple[str],
#         first_col: Tuple[str],
#         background: Path,
#     ) -> None:
#         font = pygame.font.SysFont(font_name, font_size)
#         first_col_surfs = [font.render(s, False, font_color) for s in first_col]
#         first_row_surfs = [font.render(s, False, font_color) for s in first_row]
#         col_widths = [max(s.get_rect().width for s in first_col_surfs)] + [
#             s.get_rect().width for s in first_row_surfs[1:]
#         ]
#         row_heights = [font_size + 2] * len(first_col)

#         super().__init__(
#             col_widths,
#             row_heights,
#             background,
#             line_width,
#             line_color,
#         )

#         self.rect.x, self.rect.y = pos

#         for x, c in enumerate(first_row_surfs):
#             self.arange_surface(c, (x, 0))
#         for y, c in enumerate(first_col_surfs):
#             self.arange_surface(c, (0, y))


# class AreaSurf(pygame.surface.Surface):
# def __init__(self, terrain_type: Terrains, field_size, coordinates):
#     super().__init__(
#         (
#             field_size * max(c[0] for c in coordinates),
#             field_size * max(c[1] for c in coordinates),
#         )
#     )

#     # resize terrain_surf
#     terrain_surf = pygame.transform.scale(terrain_surf, (field_size, field_size))
#     for c in coordinates:
#         self.blit(terrain_surf, (c[0] * field_size, c[1] * field_size))

# FRAME_RATE = 30
# DISPLAY_SIZE = (800, 400)
# BACKGOUND = (255, 255, 255)
# MAP_POS = (20, 20)
# # map dosent need a size as its computed from the field sizes
# # map doesnt need a background as its completely covered by the fields
# FIELD_SIZE = 10
# OPTIONS_POS = (20, 300)
# OPTION_SIZE = (60, 30)
# OPTIONS_SPACING = 10
# OPTION_VALID_BACKGROUND = (0, 255, 0)
# OPTION_INVALID_BACKGROUND = (255, 0, 0)
# OPTION_FIELD_OFFSET = (5, 5)
# OPTION_FIELD_SIZE = 10
# OPTION_COIN_OFFSET = (5, 5)
# TERRAIN_FILLS = {
#     Terrains.EMPTY: (255, 255, 255),
#     Terrains.FOREST: (0, 255, 0),
#     Terrains.MOUNTAIN: (0, 0, 0),
#     Terrains.WATER: (0, 0, 255),
#     Terrains.WASTE: (255, 255, 0),
# }

# OPTION_BACKGROUND_FILL = (255, 255, 255)
# OPTION_SIZE = (50, 50)
# OPTION_FIELD_SIZE = 10
# VALID_OPTION_FILL = (0, 255, 0)
# INVALID_OPTION_FILL = (255, 0, 0)

# def create_surface(fill_value: Union[str, Path, Iterable], size):
#     if fill_value is None:
#         surf = pygame.Surface(size)
#     elif isinstance(fill_value, (tuple, list)):
#         surf = pygame.Surface(size)
#         surf.fill(fill_value)
#     elif isinstance(fill_value, (str, Path)):
#         surf = pygame.transform.scale(pygame.image.load(fill_value).convert(), size)
#     else:
#         raise ValueError(f"Invalid fill value: {fill_value}")

#     return surf
