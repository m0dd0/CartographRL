"""Sprites represent elemets of the game which can be drawn on the screen. I.e. they contain an image and a rect.
Sprites can contain a set of attributes describing their logical state. 
The logical state is always refelcted in the image and rect of the sprite.
Getter functions are implemented only when the attribute needs to be accessed from outside the sprite.
Sprites only get the style dictionairies with elements they need.
"""

from typing import Tuple, List, FrozenSet, Dict, Any, Union, Set

import pygame

from .surfaces import ImageRectSurf, AreaSurf, FieldSurf
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
    def __init__(
        self,
        map_values: List[List[Terrains]],
        ruin_coords: FrozenSet[Tuple[int, int]],
        map_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ) -> None:
        """Visualization of the map including the backgound of the map.
        Contains also essential properties for the map and some logic for placing candidates.

        Args:
            map_values (List[List[Terrains]]): Map values.
            ruin_coords (FrozenSet[Tuple[int, int]]): Coordinates of the ruins.
            map_style (Dict[str, Any]): Style dictionary for the map.
            field_style (Dict[str, Any]): Style dictionary for the fields in the map.
        """
        super().__init__()

        self._map_values = map_values
        self._ruin_coords = ruin_coords
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

    def pixel2map_coords(self, pixel_pos: Tuple[int, int]) -> Tuple[int, int]:
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
        grid_coord = self.pixel2map_coords(pixel_pos)
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
        single_field: bool,
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
        self._single_field = single_field
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

        if not self._single_field:
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

        self._clickable = False
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
        )

        if self._style["text"] is not None:
            raise NotImplementedError("Text not implemented yet.")
            # text_surf = TextSurf(
            #     self._style["text"],
            #     self._style["text_size"],
            #     self._style["text_color"],
            #     self._style["text_offset"],
            #     self._style["text_font"],
            # )
            # self.image.blit(text_surf, self._style["text_offset"])

        if not self._clickable:
            self.image = pygame.transform.grayscale(self.image)

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._style["position"]

    @property
    def clickable(self):
        return self._clickable

    @clickable.setter
    def clickable(self, clickable):
        self._clickable = clickable
        self._build_image()


# class ScoreTableSprite(pygame.sprite.Sprite):
#     # TODO
#     pass
