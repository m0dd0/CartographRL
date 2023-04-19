"""Sprites represent elemets of the game which can be drawn on the screen. I.e. they contain an image and a rect.
Sprites can contain a set of attributes describing their logical state. The logical state is always refelcted
in the image and rect of the sprite.
The set of attributes are seperate into changable and fixed options. For the changable attributes
setter functions are implemented which update the image and/or rect of the sprite.
To make this pattern consistent all sprites are derived from the abstract MutabelSprite class which 
enforces the implementation of the _build_image and _build_rect functions.
The distinction on whether an attribute is changable or fixed is done depending on whether the attribute can change during a move (i.e. before the next button is pressed).
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
        initial_position: Tuple[int, int],
        position: Tuple[int, int],
        candidate_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ):
        """Sprite for the potentially movable area.

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): Coordinates of the candidate.
            terrain (Terrains): Terrain of the candidate.
            initial_position (Tuple[int, int]): Initial position of the candidate.
            position (Tuple[int, int]): Current position of the candidate.
            candidate_style (Dict[str, Any]): Style dictionary for the candidate itself.
            field_style (Dict[str, Any]): Style dictionary for the fields in the candidate.
        """
        super().__init__()

        # changable options
        self._shape_coords = shape_coords
        self._position = position

        # fixed options
        self._terrain = terrain
        self._initial_position = initial_position
        self._style = candidate_style
        self._field_style = field_style

        # build
        self.image = None
        self.rect = None
        self._build_image()
        self._build_rect()

    def _build_image(self):
        self.image = AreaSurf(
            self._shape_coords,
            self._terrain,
            self._field_style["frame_width"],
            self._field_style["frame_color"],
        )

    def _build_rect(self):
        self.rect = self.image.get_rect()
        self.rect.topleft = self._position

    @property
    def shape_coords(self):
        return self._shape_coords

    @shape_coords.setter
    def shape_coords(self, value):
        self._shape_coords = value
        self._build_image()

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self._build_rect()


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

        # fixed options
        self._map_values = map_values
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
                    terrain, (x, y) in self._ruin_coords, False, self._map_style
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


# class OptionSprite(MutableSprite):
#     def __init__(
#         self,
#         shape_coords: FrozenSet[Tuple[int, int]],
#         terrain: Terrains,
#         rotation: int,
#         mirror: bool,
#         coin: bool,
#         valid: bool,
#         option_index: Union[int, Terrains],
#         option_col: int,
#         option_style: Dict[str, Any],
#     ) -> None:
#         """Visualization of a single option in the current state of the game.
#         Contains also the state of the option (selected, valid, rotation, mirror, index).

#         Args:
#             shape_coords (FrozenSet[Tuple[int, int]]): Original oordinates of the option shape.
#             terrain (Terrains): Terrain of the option.
#             rotation (int): Rotation of the option.
#             mirror (bool): Whether the option is mirrored.
#             coin (bool): Whether the option contains a coin.
#             valid (bool): Whether the option is valid.
#             option_index (Union[int, Terrains]): Index of the option or terrain if the option is a single field option.
#             option_col (int): At which "place" the option is positioned.
#             style (Dict[str, Any]): Style dictionary.
#         """
#         super().__init__()

#         # changable options
#         self._rotation = rotation
#         self._mirror = mirror

#         # fixed options
#         self._shape_coords = shape_coords
#         self._terrain = terrain
#         self._valid = valid
#         self._coin = coin
#         self._option_index = option_index
#         self._option_col = option_col
#         self._option_style = option_style

#         # build
#         self.image = None
#         self.rect = None
#         self._build()

#     def _build(self):
#         """Builds the option surface depending on the current state of the option."""
#         style = self._option_style["option"]
#         if isinstance(self._option_index, Terrains):
#             style = self._option_style["single_option"]

#         self.image = ImageRectSurf(
#             style["size"],
#             style["color"],
#             style["frame_color"],
#             style["frame_width"],
#             style["frame_rounding"],
#             get_asset_path(style["image"]),
#             style["image_size"],
#             style["image_offset"],
#             style["opacity"],
#         )

#         coords = self._transform_shape_coords(
#             self.shape_coords, self._mirror, self._rotation
#         )
#         self.image.blit(
#             AreaFrameSurf(
#                 coords,
#                 self._terrain,
#                 style["candidate_frame_width"],
#                 style["candidate_frame_color"],
#                 self._option_style["field"]["size"],
#             ),
#             style["shape_offset"],
#         )

#         if not isinstance(self._option_index, Terrains):
#             coin_style = style["coin"]
#             coin_surf = ImageRectSurf(
#                 coin_style["size"],
#                 coin_style["color"],
#                 coin_style["frame_color"],
#                 coin_style["frame_width"],
#                 coin_style["frame_rounding"],
#                 get_asset_path(coin_style["image"]),
#                 coin_style["image_size"],
#                 coin_style["image_offset"],
#                 coin_style["opacity"],
#             )

#             if not self._coin:
#                 coin_surf = pygame.transform.grayscale(coin_surf)

#             self.image.blit(coin_surf, coin_style["offset"])

#         if not self._valid:
#             self.image = pygame.transform.grayscale(self.image)

#         self.rect = self.image.get_rect()
#         self.rect.topleft = (
#             style["position"][0]
#             + self._option_col * (style["size"][0] + style["spacing"]),
#             style["position"][1],
#         )

#     def _build_rect(self):
#         return super()._build_rect()

#     def _transform_shape_coords(
#         self, shape_coords: FrozenSet[Tuple[int, int]], mirror: bool, rotation: int
#     ) -> FrozenSet[Tuple[int, int]]:
#         """Transforms the shape coordinates depending on the current state of the option.
#         I.e. rotates and mirrors the shape coordinates to obtain the coorindates to display.
#         Tge shape_coord attribute is not changed.

#         Args:
#             shape_coords (FrozenSet[Tuple[int, int]]): Original coordinates of the option shape.
#             mirror (bool): Whether the option is mirrored.
#             rotation (int): Rotation of the option.

#         Returns:
#             FrozenSet[Tuple[int, int]]: Transformed coordinates of the option shape.
#         """
#         if mirror:
#             shape_coords = {(-x, y) for x, y in shape_coords}

#         if rotation == 0:
#             shape_coords = shape_coords
#         elif rotation == 1:
#             shape_coords = {(y, -x) for x, y in shape_coords}
#         elif rotation == 2:
#             shape_coords = {(-x, -y) for x, y in shape_coords}
#         elif rotation == 3:
#             shape_coords = {(-y, x) for x, y in shape_coords}
#         else:
#             raise ValueError(f"Invalid rotation: {rotation}")

#         min_x = min(x for x, _ in shape_coords)
#         min_y = min(y for _, y in shape_coords)
#         shape_coords = {(x - min_x, y - min_y) for x, y in shape_coords}

#         return shape_coords

#     @property
#     def rotation(self):
#         return self._rotation

#     @rotation.setter
#     def rotation(self, rotation):
#         self._rotation = rotation
#         self._build()

#     @property
#     def mirror(self):
#         return self._mirror

#     @mirror.setter
#     def mirror(self, mirror):
#         self._mirror = mirror
#         self._build()

#     @property
#     def valid(self):
#         return self._valid

#     @property
#     def shape_coords(self):
#         return self._shape_coords

#     @property
#     def i_option(self):
#         return self._option_index

#     @property
#     def terrain(self):
#         return self._terrain

#     @property
#     def shape_position(self):
#         return (
#             self.rect.topleft[0] + self._option_style["option"]["shape_offset"][0],
#             self.rect.topleft[1] + self._option_style["option"]["shape_offset"][1],
#         )


# class OptionsBackgrounSprite(pygame.sprite.Sprite):
#     def __init__(self, name: str, time: int, style: Dict[str, Any]) -> None:
#         style = style["options_background"]
#         self.image = ImageRectSurf(
#             style["size"],
#             style["color"],
#             style["frame_color"],
#             style["frame_width"],
#             style["frame_rounding"],
#             get_asset_path(style["image"]),
#             style["image_size"],
#             style["image_offset"],
#             style["opacity"],
#         )

#         # TODO time and name

#         self.rect = self.image.get_rect()
#         self.rect.topleft = style["position"]


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
