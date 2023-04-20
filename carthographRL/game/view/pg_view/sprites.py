"""Sprites represent elemets of the game which can be drawn on the screen. I.e. they contain an image and a rect.
Sprites can contain a set of attributes describing their logical state. The logical state is always refelcted
in the image and rect of the sprite.
The set of attributes are seperate into changable and fixed options. For the changable attributes
setter functions are implemented which update the image and/or rect of the sprite.
To make this pattern consistent all sprites are derived from the abstract MutabelSprite class which 
enforces the implementation of the _build_image and _build_rect functions.
The distinction on whether an attribute is changable or fixed is done depending on whether the attribute can change during its livetime.
Getter functions are implemented only when the attribute needs to be accessed from outside the sprite.
Sprites only get the style dictionairies with elements they need.
"""

from typing import Tuple, List, FrozenSet, Dict, Any, Union, Set
from abc import ABC, abstractmethod

import pygame

from .surfaces import ImageRectSurf, AreaSurf, FieldSurf
from ..base import get_asset_path
from ...model.general import Terrains


class MutableSprite(pygame.sprite.Sprite, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _build_image(self):
        pass

    @abstractmethod
    def _build_rect(self):
        pass


class ScreenSprite(MutableSprite):
    def __init__(self, screen_style: Dict[str, Any]):
        """Background sprite for the game screen.

        Args:
            screen_style (Dict[str, Any]): Style dictionary for the screen.
        """
        super().__init__()

        # changable options

        # fixed options
        self._style = screen_style

        # build
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


class CandidateSprite(MutableSprite):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
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

        # changable options
        self._shape_coords = shape_coords

        # fixed options
        self._terrain = terrain
        self._initial_position = initial_position
        self._valid = valid
        self._candidate_style = candidate_style
        self._field_style = field_style

        # build
        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

        # internals
        self._drag_offset = None

    def _build_image(self):
        self.image = AreaSurf(
            self._shape_coords,
            self._terrain,
            self._candidate_style["frame_width"],
            self._candidate_style["frame_color"],
            self._field_style,
        )
        if not self._valid:
            self.image = pygame.transform.grayscale(self.image)

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
        # TODO use only fields as collision detection
        return self.rect.collidepoint(position)

    def reset_drag(self):
        """Reset the drag offset."""
        self._drag_offset = None
        self.rect.topleft = self._initial_position

    @property
    def shape_coords(self):
        return self._shape_coords

    @shape_coords.setter
    def shape_coords(self, value):
        self._shape_coords = value
        self._build_image()

    @property
    def valid(self):
        return self._valid

    @property
    def dragged(self):
        return self._drag_offset is not None


class MapSprite(MutableSprite):
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

        # changable options
        self._map_values = map_values

        # fixed options
        self._ruin_coords = ruin_coords
        self._map_style = map_style
        self._field_style = field_style

        # build
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

    def get_mouse_grid_coords(self, mouse_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Returns the grid coordinates of the field the mouse is currently over.

        Args:
            mouse_pos (Tuple[int, int]): Mouse position in pixels.

        Returns:
            Tuple[int, int]: Grid coordinates of the field the mouse is currently over.
                None if the mouse is not over the clickable area of the map.
        """

        if not self.rect.collidepoint(mouse_pos):
            return None
        x = (
            mouse_pos[0] - self.rect.x - self._map_style["padding"]
        ) // self._field_style["size"]
        y = (
            mouse_pos[1] - self.rect.y - self._map_style["padding"]
        ) // self._field_style["size"]
        return x, y

    @property
    def map_values(self):
        return self._map_values

    @map_values.setter
    def map_values(self, value):
        self._map_values = value
        self._build_image()


class OptionSprite(MutableSprite):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        rotation: int,
        mirror: bool,
        terrain: Terrains,
        coin: bool,
        valid: bool,
        single_field: bool,
        option_col: int,
        option_style: Dict[str, Any],
        candidate_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ) -> None:
        """Visualization of a single option in the current state of the game.
        Contains also the state of the option (selected, valid, rotation, mirror, index).

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): Original oordinates of the option shape.
            rotation (int): Rotation of the option.
            mirror (bool): Whether the option is mirrored.
            coin (bool): Whether the option contains a coin.
            valid (bool): Whether the option is valid.
            single_field (bool): Whether the option is a single field.
            option_col (int): At which "place" the option is positioned.
        """
        super().__init__()

        # changable options
        self._rotation = rotation
        self._mirror = mirror

        # fixed options
        self._shape_coords = shape_coords
        self._valid = valid
        self._terrain = terrain
        self._coin = coin
        self._option_col = option_col
        self._single_field = single_field
        self._option_style = option_style
        self._candidate_style = candidate_style
        self._field_style = field_style

        # build
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
                self.transformed_coords(),
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

    def transformed_coords(self):
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

    def initial_candidate_sprite(self):
        """Returns a candidate sprite with the same shape as the option.
        The candidate sprite is not yet placed on the map.
        """
        return CandidateSprite(
            self.transformed_coords(),
            self._terrain,
            self._valid,
            (
                self.rect.topleft[0] + self._option_style["shape_offset"][0],
                self.rect.topleft[1] + self._option_style["shape_offset"][1],
            ),
            self._candidate_style,
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


# class ScoreTableSprite(pygame.sprite.Sprite):
#     # TODO
#     pass


# class NextButtonSprite(pygame.sprite.Sprite):
#     # def __init__(self, clickable: bool, style) -> None:
#     #     self.image = ImageRectSurf(
#     #         style["next_button_size"],
#     #         style["next_button_color"],
#     #         style["next_button_frame_color"],
#     #         style["next_button_frame_width"],
#     #         style["next_button_frame_rounding"],
#     #         get_asset_path(style["assets_folder"], style["next_button_image"]),
#     #         style["next_button_image_size"],
#     #         style["next_button_image_offset"],
#     #     )

#     #     if not clickable:
#     #         self.image = pygame.transform.grayscale(self.image)
#     # TODO
#     pass
