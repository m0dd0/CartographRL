from typing import Tuple, List, FrozenSet, Dict, Any, Union, Set
from pathlib import Path

import pygame

from ..base import get_asset_path
from ...model.general import Terrains

class ScreenSprite(pygame.sprite.Sprite):
    def __init__(self, screen_style: Dict[str, Any]):
        """Background sprite for the game screen.

        Args:
            screen_style (Dict[str, Any]): Style dictionary. Must contain the following keys:
                - size (Tuple[int, int]): Size of the screen in pixels.
                - color (Tuple[int, int, int]): Color of the screen.
                - frame_color (Tuple[int, int, int]): Color of the frame.
                - frame_width (int): Width of the frame.
                - frame_rounding (int): Radius of the rounded corners.
                - image (str): Path to the image of the screen.
                - image_size (Tuple[int, int]): Size of the image.
                - image_offset (Tuple[int, int]): Offset of the image.
                - opacity (int): Opacity of the screen.
        """
        self.image = ImageRectSurf(
            screen_style["size"],
            screen_style["color"],
            screen_style["frame_color"],
            screen_style["frame_width"],
            screen_style["frame_rounding"],
            get_asset_path(screen_style["image"]),
            screen_style["image_size"],
            screen_style["image_offset"],
            screen_style["opacity"],
        )
        self.rect = self.image.get_rect()

        self.rect.topleft = (0, 0)


class CandidateSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        shape_coords,
        terrain,
        candidate_style: Dict[str, Any],
        field_style: Dict[str, Any],
    ):
        """Sprite for the potentially movable area.

        Args:
        """
        super().__init__()

        self._style = candidate_style
        self.image = AreaSurf(
            shape_coords, terrain, style["frame_width"], style["frame_color"]
        )


class MapSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        map_values: List[List[Terrains]],
        ruin_coords: FrozenSet[Tuple[int, int]],
        style: Dict[str, Any],
    ) -> None:
        """Visualization of the map including the backgound of the map.
        Created the initial state of the map with no candidate fields.
        Contains also essential properties for the map and some logic for placing candidates.

        Args:
            map_values (List[List[Terrains]]): Map values.
            ruin_coords (FrozenSet[Tuple[int, int]]): Coordinates of the ruins.
            style (Dict[str, Any]): Style dictionary.
        """
        super().__init__()

        self._style = style
        self._map_values = map_values
        self._ruin_coords = ruin_coords
        self._style = style

        self.image = None
        self.rect = None
        self._build()

    def _build(self):
        """Builds the map surface depending on the current state of the map."""
        style = self._style["map"]
        extent = (
            len(self._map_values[0]) * self._style["field"]["size"]
            + style["padding"] * 2
        )
        self.image = ImageRectSurf(
            (extent, extent),
            style["color"],
            style["frame_color"],
            style["frame_width"],
            style["frame_rounding"],
            get_asset_path(style["image"]),
            style["image_size"],
            style["image_offset"],
            style["opacity"],
        )

        for x, row in enumerate(self._map_values):
            for y, terrain in enumerate(row):
                field_surf = FieldSurf(
                    terrain, (x, y) in self._ruin_coords, False, self._style
                )
                self.image.blit(
                    field_surf,
                    (
                        x * self._style["field"]["size"] + style["padding"],
                        y * self._style["field"]["size"] + style["padding"],
                    ),
                )

        self.rect = self.image.get_rect()
        self.rect.topleft = style["position"]

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
        x = (mouse_pos[0] - self.rect.x - self._style["map"]["padding"]) // self._style[
            "field"
        ]["size"]
        y = (mouse_pos[1] - self.rect.y - self._style["map"]["padding"]) // self._style[
            "field"
        ]["size"]
        return x, y

    @property
    def map_values(self) -> List[List[Terrains]]:
        """List[List[Terrains]]: Map values."""
        return self._map_values

    @map_values.setter
    def map_values(self, map_values: List[List[Terrains]]) -> None:
        self._map_values = map_values
        self._build()

    @property
    def ruin_coords(self) -> FrozenSet[Tuple[int, int]]:
        """FrozenSet[Tuple[int, int]]: Coordinates of the ruins."""
        return self._ruin_coords

    @ruin_coords.setter
    def ruin_coords(self, ruin_coords: FrozenSet[Tuple[int, int]]) -> None:
        self._ruin_coords = ruin_coords
        self._build()


class OptionSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        coin: bool,
        valid: bool,
        option_index: Union[int, Terrains],
        option_col: int,
        style: Dict[str, Any],
    ) -> None:
        """Visualization of a single option in the current state of the game.
        Contains also the state of the option (selected, valid, rotation, mirror, index).

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): Original oordinates of the option shape.
            terrain (Terrains): Terrain of the option.
            coin (bool): Whether the option contains a coin.
            valid (bool): Whether the option is valid.
            i_option (Union[int, Terrains]): Index of the option or terrain if the option is a single field option.
            option_col (int): At which "place" the option is positioned.
            style (Dict[str, Any]): Style dictionary.
        """
        super().__init__()

        self._shape_coords = shape_coords
        self._terrain = terrain
        self._coin = coin
        self._valid = valid
        self._i_option = option_index
        self._rotation = 0
        self._mirror = False
        self._option_col = option_col
        self._style = style

        self.image = None
        self.rect = None
        self._build()

    def _build(self):
        """Builds the option surface depending on the current state of the option."""
        style = self._style["option"]
        if isinstance(self._i_option, Terrains):
            style = self._style["single_option"]

        self.image = ImageRectSurf(
            style["size"],
            style["color"],
            style["frame_color"],
            style["frame_width"],
            style["frame_rounding"],
            get_asset_path(style["image"]),
            style["image_size"],
            style["image_offset"],
            style["opacity"],
        )

        coords = self._transform_shape_coords(
            self.shape_coords, self._mirror, self._rotation
        )
        self.image.blit(
            AreaFrameSurf(
                coords,
                self._terrain,
                style["candidate_frame_width"],
                style["candidate_frame_color"],
                self._style["field"]["size"],
            ),
            style["shape_offset"],
        )

        if not isinstance(self._i_option, Terrains):
            coin_style = style["coin"]
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

        self.rect = self.image.get_rect()
        self.rect.topleft = (
            style["position"][0]
            + self._option_col * (style["size"][0] + style["spacing"]),
            style["position"][1],
        )

    def _transform_shape_coords(
        self, shape_coords: FrozenSet[Tuple[int, int]], mirror: bool, rotation: int
    ) -> FrozenSet[Tuple[int, int]]:
        """Transforms the shape coordinates depending on the current state of the option.
        I.e. rotates and mirrors the shape coordinates to obtain the coorindates to display.
        Tge shape_coord attribute is not changed.

        Args:
            shape_coords (FrozenSet[Tuple[int, int]]): Original coordinates of the option shape.
            mirror (bool): Whether the option is mirrored.
            rotation (int): Rotation of the option.

        Returns:
            FrozenSet[Tuple[int, int]]: Transformed coordinates of the option shape.
        """
        if mirror:
            shape_coords = {(-x, y) for x, y in shape_coords}

        if rotation == 0:
            shape_coords = shape_coords
        elif rotation == 1:
            shape_coords = {(y, -x) for x, y in shape_coords}
        elif rotation == 2:
            shape_coords = {(-x, -y) for x, y in shape_coords}
        elif rotation == 3:
            shape_coords = {(-y, x) for x, y in shape_coords}
        else:
            raise ValueError(f"Invalid rotation: {rotation}")

        min_x = min(x for x, _ in shape_coords)
        min_y = min(y for _, y in shape_coords)
        shape_coords = {(x - min_x, y - min_y) for x, y in shape_coords}

        return shape_coords

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._build()

    @property
    def mirror(self):
        return self._mirror

    @mirror.setter
    def mirror(self, mirror):
        self._mirror = mirror
        self._build()

    @property
    def valid(self):
        return self._valid

    @property
    def shape_coords(self):
        return self._shape_coords

    @property
    def i_option(self):
        return self._i_option

    @property
    def terrain(self):
        return self._terrain

    @property
    def shape_position(self):
        return (
            self.rect.topleft[0] + self._style["option"]["shape_offset"][0],
            self.rect.topleft[1] + self._style["option"]["shape_offset"][1],
        )


class OptionsBackgrounSprite(pygame.sprite.Sprite):
    def __init__(self, name: str, time: int, style: Dict[str, Any]) -> None:
        style = style["options_background"]
        self.image = ImageRectSurf(
            style["size"],
            style["color"],
            style["frame_color"],
            style["frame_width"],
            style["frame_rounding"],
            get_asset_path(style["image"]),
            style["image_size"],
            style["image_offset"],
            style["opacity"],
        )

        # TODO time and name

        self.rect = self.image.get_rect()
        self.rect.topleft = style["position"]


class ScoreTableSprite(pygame.sprite.Sprite):
    # TODO
    pass


class NextButtonSprite(pygame.sprite.Sprite):
    # def __init__(self, clickable: bool, style) -> None:
    #     self.image = ImageRectSurf(
    #         style["next_button_size"],
    #         style["next_button_color"],
    #         style["next_button_frame_color"],
    #         style["next_button_frame_width"],
    #         style["next_button_frame_rounding"],
    #         get_asset_path(style["assets_folder"], style["next_button_image"]),
    #         style["next_button_image_size"],
    #         style["next_button_image_offset"],
    #     )

    #     if not clickable:
    #         self.image = pygame.transform.grayscale(self.image)
    # TODO
    pass

