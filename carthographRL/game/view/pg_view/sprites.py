"""Sprites represent elemets of the game which can be drawn on the screen. I.e. they contain an image and a rect.
Sprites can contain a set of attributes describing their logical state. 
The logical state is always refelcted in the image and rect of the sprite.
Getter functions are implemented only when the attribute needs to be accessed from outside the sprite.
Sprites only get the style dictionairies with elements they need.
"""

from typing import Tuple, FrozenSet, Dict, Any, List

import pygame

from .surfaces import ImageRectSurf, AreaSurf, FieldSurf, TableSurf, ImageSurf, TextSurf
from ..base import get_asset_path
from ...model.general import Terrains


class ScreenSprite(pygame.sprite.Sprite):
    def __init__(self, screen_style: Dict[str, Any]):
        """Background sprite for the game screen.

        Args:
            screen_style (Dict[str, Any]): Style dictionary for the screen.
        """
        super().__init__()

        self._style = screen_style

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._style["size"],
            self._style["color"],
            self._style["frame_color"],
            self._style["frame_width"],
            self._style["frame_rounding"],
            get_asset_path(self._style["image"]),
            self._style["image_size"],
            self._style["image_offset"],
            self._style["opacity"],
        )
        self.rect = self.image.get_rect()

    def _build_rect(self):
        self.rect.topleft = (0, 0)


class CandidateSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        valid: bool,
        initial_position: Tuple[int, int],
        candidate_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ):
        """Sprite for the potentially movable area.

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): Coordinates of the candidate.
            terrain (Terrains): Terrain of the candidate.
            valid (bool): Whether the candidate is valid.
            initial_position (Tuple[int, int]): Initial position of the candidate.
            candidate_style (Dict[str, Any]): Style dictionary for the candidate itself.
            field_style (Dict[str, Any]): Style dictionary for the fields in the candidate.
        """
        super().__init__()

        self._coords = coords
        self._terrain = terrain
        self._initial_position = initial_position
        self._valid = valid
        self._candidate_style = candidate_style
        self._field_style = field_style
        self._drag_offset = None

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = AreaSurf(
            self._coords,
            self._terrain,
            self._candidate_style["frame_width"],
            self._candidate_style["frame_color"],
            self._field_style,
        )
        if not self._valid:
            self.image = pygame.transform.grayscale(self.image)

        self.image.set_alpha(self._candidate_style["opacity"])

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._initial_position

    def drag(self, position: Tuple[int, int]):
        """Drag the candidate to a new position.

        Args:
            position (Tuple[int, int]): New position of the candidate.
        """
        if self._drag_offset is None:
            self._drag_offset = (
                position[0] - self.rect.topleft[0],
                position[1] - self.rect.topleft[1],
            )
        self.rect.topleft = (
            position[0] - self._drag_offset[0],
            position[1] - self._drag_offset[1],
        )

    def drop(self):
        """Drop the candidate."""
        self._drag_offset = None

    def on_shape(self, position: Tuple[int, int]) -> bool:
        """Check if the candidate contains a given position.

        Args:
            position (Tuple[int, int]): Position to check.

        Returns:
            bool: Whether the candidate contains the position.
        """
        if not self.rect.collidepoint(position):
            return False

        position = (
            (position[0] - self.rect.topleft[0]) // self._field_style["size"],
            (position[1] - self.rect.topleft[1]) // self._field_style["size"],
        )
        return position in self._coords

    def reset_drag(self):
        """Reset the drag offset."""
        self._drag_offset = None
        self.rect.topleft = self._initial_position

    @property
    def valid(self):
        return self._valid

    @property
    def dragged(self):
        return self._drag_offset is not None

    @property
    def coords(self):
        return self._coords


class MapSprite(pygame.sprite.Sprite):
    def __init__(self, map_style: Dict[str, Any], field_style: Dict[str, Any]) -> None:
        """Visualization of the map including the backgound of the map.
        Contains also essential properties for the map and some logic for placing candidates.

        Args:
            map_style (Dict[str, Any]): Style dictionary for the map.
            field_style (Dict[str, Any]): Style dictionary for the fields in the map.
        """
        super().__init__()

        self._map_values = [[]]
        self._ruin_coords = []
        self._map_style = map_style
        self._field_style = field_style

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        """Builds the map surface depending on the current state of the map."""
        extent = (
            len(self._map_values[0]) * self._field_style["size"]
            + self._map_style["padding"] * 2
        )
        self.image = ImageRectSurf(
            (extent, extent),
            self._map_style["color"],
            self._map_style["frame_color"],
            self._map_style["frame_width"],
            self._map_style["frame_rounding"],
            get_asset_path(self._map_style["image"]),
            self._map_style["image_size"],
            self._map_style["image_offset"],
            self._map_style["opacity"],
        )

        for x, row in enumerate(self._map_values):
            for y, terrain in enumerate(row):
                field_surf = FieldSurf(
                    terrain, (x, y) in self._ruin_coords, self._field_style
                )
                self.image.blit(
                    field_surf,
                    (
                        x * self._field_style["size"] + self._map_style["padding"],
                        y * self._field_style["size"] + self._map_style["padding"],
                    ),
                )

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._map_style["position"]

    def pixel2map_coord(self, pixel_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Returns the snapped grid coordinates of the field the mouse is currently over.

        Args:
            mouse_pos (Tuple[int, int]): Mouse position in pixels.

        Returns:
            Tuple[int, int]: Grid coordinates of the field the mouse is currently over.
                None if the mouse is not over the clickable area of the map.
        """
        grid_coord = (
            round((pixel_pos[0] - self.rect.x) / self._field_style["size"]),
            round((pixel_pos[1] - self.rect.y) / self._field_style["size"]),
        )

        if (not 0 <= grid_coord[0] < len(self._map_values[0])) or (
            not 0 <= grid_coord[1] < len(self._map_values[1])
        ):
            return None

        return grid_coord

    def map2pixel_coord(self, grid_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Returns the pixel coordinates of the topleft od the field at the given grid coordinates.

        Args:
            grid_pos (Tuple[int, int]): Grid coordinates of the field.

        Returns:
            Tuple[int, int]: Pixel coordinates of the topleft of the field.
        """

        x = (
            grid_pos[0] * self._field_style["size"]
            + self._map_style["padding"]
            + self.rect.x
        )
        y = (
            grid_pos[1] * self._field_style["size"]
            + self._map_style["padding"]
            + self.rect.y
        )
        return x, y

    def snap_pixel_coord(self, pixel_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Returns the pixel coordinates of the topleft of the field the mouse is currently over.

        Args:
            mouse_pos (Tuple[int, int]): Mouse position in pixels.

        Returns:
            Tuple[int, int]: Pixel coordinates of the topleft of the field the mouse is currently over.
                None if the mouse is not over the clickable area of the map.
        """
        grid_coord = self.pixel2map_coord(pixel_pos)
        if grid_coord is None:
            return None
        return self.map2pixel_coord(grid_coord)

    @property
    def map_values(self):
        return self._map_values

    @map_values.setter
    def map_values(self, value):
        self._map_values = value
        self._build_image()

    @property
    def ruin_coords(self):
        return self._ruin_coords

    @ruin_coords.setter
    def ruin_coords(self, value):
        self._ruin_coords = value
        self._build_image()


class OptionSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        coin: bool,
        valid: bool,
        option_col: int,
        option_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ) -> None:
        """Visualization of a single option in the current state of the game.

        Args:
        """
        super().__init__()

        self._shape_coords = shape_coords
        self._valid = valid
        self._terrain = terrain
        self._coin = coin
        self._option_col = option_col
        self._option_style = option_style
        self._field_style = field_style
        self._rotation = 0
        self._mirror = False

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._option_style["size"],
            self._option_style["color"],
            self._option_style["frame_color"],
            self._option_style["frame_width"],
            self._option_style["frame_rounding"],
            get_asset_path(self._option_style["image"]),
            self._option_style["image_size"],
            self._option_style["image_offset"],
            self._option_style["opacity"],
        )

        self.image.blit(
            AreaSurf(
                self._transform_coords(),
                None,
                self._option_style["candidate_frame_width"],
                self._option_style["candidate_frame_color"],
                self._field_style,
            ),
            self._option_style["shape_offset"],
        )

        if "coin" in self._option_style:
            coin_style = self._option_style["coin"]
            coin_surf = ImageRectSurf(
                coin_style["size"],
                coin_style["color"],
                coin_style["frame_color"],
                coin_style["frame_width"],
                coin_style["frame_rounding"],
                get_asset_path(coin_style["image"]),
                coin_style["image_size"],
                coin_style["image_offset"],
                coin_style["opacity"],
            )

            if not self._coin:
                coin_surf = pygame.transform.grayscale(coin_surf)

            self.image.blit(coin_surf, coin_style["offset"])

        if not self._valid:
            self.image = pygame.transform.grayscale(self.image)

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            self._option_style["position"][0]
            + self._option_col
            * (self._option_style["size"][0] + self._option_style["spacing"]),
            self._option_style["position"][1],
        )

    def _transform_coords(self):
        """Transforms the shape coordinates depending on the current state of the option.
        I.e. rotates and mirrors the shape coordinates to obtain the coorindates to display.
        Tge shape_coord attribute is not changed.
        """
        coords = self._shape_coords

        if self._mirror:
            coords = {(-x, y) for x, y in coords}

        if self._rotation == 0:
            coords = coords
        elif self._rotation == 1:
            coords = {(y, -x) for x, y in coords}
        elif self._rotation == 2:
            coords = {(-x, -y) for x, y in coords}
        elif self._rotation == 3:
            coords = {(-y, x) for x, y in coords}
        else:
            raise ValueError(f"Invalid rotation: {self._rotation}")

        min_x = min(x for x, _ in coords)
        min_y = min(y for _, y in coords)
        coords = {(x - min_x, y - min_y) for x, y in coords}

        return coords

    def build_candidate_sprite(self, candidate_style: Dict[str, Any]):
        """Returns a candidate sprite with the same shape as the option.
        The candidate sprite is not yet placed on the map.
        """
        return CandidateSprite(
            self._transform_coords(),
            self._terrain,
            self._valid,
            (
                self.rect.topleft[0] + self._option_style["shape_offset"][0],
                self.rect.topleft[1] + self._option_style["shape_offset"][1],
            ),
            candidate_style,
            self._field_style,
        )

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._build_image()

    @property
    def mirror(self):
        return self._mirror

    @mirror.setter
    def mirror(self, mirror):
        self._mirror = mirror
        self._build_image()

    @property
    def valid(self):
        return self._valid


class NextButtonSprite(pygame.sprite.Sprite):
    def __init__(self, style: Dict[str, Any]) -> None:
        super().__init__()

        self._valid = False
        self._style = style

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._style["size"],
            self._style["color"],
            self._style["frame_color"],
            self._style["frame_width"],
            self._style["frame_rounding"],
            get_asset_path(self._style["image"]),
            self._style["image_size"],
            self._style["image_offset"],
            self._style["opacity"],
            self._style["text"],
            self._style["text_font"],
            self._style["text_color"],
            self._style["text_size"],
            self._style["text_offset"],
        )

        if not self._valid:
            self.image = pygame.transform.grayscale(self.image)

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._style["position"]

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, valid):
        self._valid = valid
        self._build_image()


class OptionsBackgroundSprite(pygame.sprite.Sprite):
    def __init__(self, style: Dict[str, Any]) -> None:
        super().__init__()

        self._style = style
        self._ruin = False
        self._title = ""
        self._time = 0

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._style["size"],
            self._style["color"],
            self._style["frame_color"],
            self._style["frame_width"],
            self._style["frame_rounding"],
            get_asset_path(self._style["image"]),
            self._style["image_size"],
            self._style["image_offset"],
            self._style["opacity"],
        )

        font = pygame.font.SysFont(self._style["font"], self._style["font_size"])
        title_surf = font.render(
            f"{self._title} ({self._time})", True, self._style["font_color"]
        )
        self.image.blit(title_surf, self._style["title_offset"])

        if self._ruin:
            self.image.blit(
                ImageSurf(
                    self._style["ruin_icon_size"],
                    get_asset_path(self._style["ruin_icon"]),
                ),
                self._style["ruin_icon_offset"],
            )

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._style["position"]

    @property
    def ruin(self):
        return self._ruin

    @ruin.setter
    def ruin(self, ruin):
        self._ruin = ruin
        self._build_image()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title
        self._build_image()

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, time):
        self._time = time
        self._build_image()


class ScoreTableSprite(pygame.sprite.Sprite):
    def __init__(self, style: Dict[str, Any]) -> None:
        super().__init__()

        self._style = style
        self._season_lengths = [0, 0, 0, 0]
        self._data = [{}]
        self._season = 0
        self._time_in_season = 0

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._style["size"],
            self._style["color"],
            self._style["frame_color"],
            self._style["frame_width"],
            self._style["frame_rounding"],
            get_asset_path(self._style["image"]),
            self._style["image_size"],
            self._style["image_offset"],
            self._style["opacity"],
        )

        font = pygame.font.SysFont(self._style["font"], self._style["font_size"])

        table_surfs = [
            [None for _ in range(len(self._style["col_names"]) + 1)]
            for _ in range(len(self._style["row_names"]) + 1)
        ]

        for i, name in enumerate(self._style["col_names"]):
            if i == self._season:
                name = f"{name}({self._time_in_season}/{self._season_lengths[self._season]}) "
            table_surfs[0][i + 1] = font.render(name, True, self._style["font_color"])

        for j, row_name in enumerate(self._style["row_names"]):
            table_surfs[j + 1][0] = font.render(
                row_name, True, self._style["font_color"]
            )

        for i, season_data in enumerate(self._data):
            for j, data in enumerate(season_data.values()):
                table_surfs[j + 1][i + 1] = font.render(
                    self._style["no_value"] if i > self._season else f" {data}",
                    True,
                    self._style["font_color"],
                )

        self.image.blit(
            TableSurf(
                table_surfs,
                self._style["table_frame_width"],
                self._style["table_frame_width"],
                self._style["table_frame_color"],
            ),
            self._style["table_offset"],
        )

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._style["position"]

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self._build_image()

    @property
    def season(self):
        return self._season

    @season.setter
    def season(self, season):
        self._season = season
        self._build_image()

    @property
    def time_in_season(self):
        return self._time_in_season

    @time_in_season.setter
    def time_in_season(self, time_in_season):
        self._time_in_season = time_in_season
        self._build_image()

    @property
    def season_times(self):
        return self._season_lengths

    @season_times.setter
    def season_times(self, season_lengths):
        self._season_lengths = season_lengths
        self._build_image()


class InfoSprite(pygame.sprite.Sprite):
    def __init__(self, style: Dict[str, Any]) -> None:
        super().__init__()

        self._style = style
        self._scoring_cards = []

        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = ImageRectSurf(
            self._style["size"],
            self._style["color"],
            self._style["frame_color"],
            self._style["frame_width"],
            self._style["frame_rounding"],
            get_asset_path(self._style["image"]),
            self._style["image_size"],
            self._style["image_offset"],
            self._style["opacity"],
        )

        font = pygame.font.SysFont(self._style["font"], self._style["font_size"])
        font_bold = pygame.font.SysFont(
            self._style["font"], self._style["font_size"], bold=True
        )

        h = 0
        for card in self._scoring_cards:
            name_surf = font_bold.render(
                f"{card.name}: ", True, self._style["font_color"]
            )
            self.image.blit(
                name_surf,
                (
                    self._style["text_offset"][0],
                    self._style["text_offset"][1] + h,
                ),
            )
            text_surf = TextSurf(
                card.description,
                font,
                self._style["font_color"],
                self._style["size"][0]
                - self._style["text_offset"][0]
                - name_surf.get_width(),
            )
            self.image.blit(
                text_surf,
                (
                    self._style["text_offset"][0] + name_surf.get_width(),
                    self._style["text_offset"][1] + h,
                ),
            )
            h += text_surf.get_height()

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._style["position"]

    @property
    def scoring_cards(self):
        return self._scoring_cards

    @scoring_cards.setter
    def scoring_cards(self, scoring_cards):
        self._scoring_cards = scoring_cards
        self._build_image()
