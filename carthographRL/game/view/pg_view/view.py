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


def get_asset_path(image_name: str):
    """Get the path to an asset.

    Args:
        image_name (str): Name of the asset.

    Returns:
        Path: Path to the asset.
    """
    if image_name is None:
        return None
    return Path(__file__).parent / "assets" / image_name


class RectSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        frame_color: Tuple[int, int, int],
        frame_width: int,
        infill_color: Tuple[int, int, int],
        rounding: int,
    ):
        """Create a surface with a rectangular frame and an optional infill.
        When using rounded corners the remaining background is transparent.

        Args:
            size (Tuple[int, int]): Size of the surface.
            frame_color (Tuple[int, int, int]): Color of the frame.
            frame_width (int, optional): Width of the frame. If negative no frame is drawn.
            infill_color (Tuple[int, int, int], optional): Color of the infill. If None only a frame is drawn.
            rounding (int, optional): Radius of the rounded corners.
        """
        assert frame_width != 0, "Frame width must not be 0."
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        if infill_color is not None:
            pygame.draw.rect(
                self, infill_color, pygame.Rect(0, 0, size[0], size[1]), 0, rounding
            )
        pygame.draw.rect(
            self,
            frame_color,
            pygame.Rect(0, 0, size[0], size[1]),
            frame_width,
            rounding,
        )


class ImageSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        image: Path,
    ):
        """Create a surface with an image.
        The backgound is transparent to account for (partially) transparent images.

        Args:
            size (Tuple[int, int]): Size of the surface.
            image (Path): Path to the image file.
        """
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        self.image = pygame.transform.scale(
            pygame.image.load(image).convert_alpha(), size
        )
        self.blit(self.image, (0, 0))


class ImageRectSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        backgound_color: Tuple[int, int, int],
        frame_color: Tuple[int, int, int],
        frame_width: int,
        frame_rounding: int,
        image: Path,
        image_size: Tuple[int, int],
        image_offset: Tuple[int, int],
        opacity: int,
    ):
        """Create a surface with a rectangular frame, an optional infill and an image.
        As for nearly all UI elements we draw an image on a rect background this acts as a wrapper for the RectSurf and ImageSurf classes.
        However, in general it should be preferred to use the RectSurf and ImageSurf classes directly as this is more declarative and easier to understand.

        Args:
            size (Tuple[int, int]): Size of the surface.
            backgound_color (Tuple[int, int, int]): Color of the infill.
            frame_color (Tuple[int, int, int]): Color of the frame.
            frame_width (int): Width of the frame.
            frame_rounding (int): Radius of the rounded corners.
            image (Path): Path to the image file.
            image_size (Tuple[int, int], optional): Size of the image. If None, the size of the surface is used.
            image_offset (Tuple[int, int], optional): Offset of the image.
        """
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        self.blit(
            RectSurf(size, frame_color, frame_width, backgound_color, frame_rounding),
            (0, 0),
        )
        image_size = image_size or size
        if image is not None:
            self.blit(ImageSurf(image_size, image), image_offset)

        self.set_alpha(opacity)


class FieldSurf(ImageRectSurf):
    def __init__(
        self,
        terrain: Terrains,
        ruin: bool,
        field_style: Dict[str, Any],
    ) -> None:
        """Surface of a singel field in the map or option card.

        Args:
            terrain (Terrains): Terrain of the field.
            ruin (bool): Whether the field is a ruin.
            candidate (bool): Whether the field is a candidate for a move (opposed to already set field)
            style (Dict[str, Any]): Style dictionary. Must contain the following keys:
                - size (int): Size of the field in pixels.
                - colors (Dict[str, Tuple[int, int, int]]): Colors of the fields.
                - frame_color (Tuple[int, int, int]): Color of the frame.
                - frame_width (int): Width of the frame.
                - frame_rounding (int): Radius of the rounded corners.
                - images (Dict[str, str]): Paths to the images of the fields.
                - image_size (Tuple[int, int]): Size of the image.
                - image_offset (Tuple[int, int]): Offset of the image.
                - opacity (int): Opacity of the field.
                - ruin_overlay (str): Path to the image of the ruin overlay.
        """
        terrain = terrain.name.lower()
        super().__init__(
            (field_style["size"], field_style["size"]),
            field_style["colors"][terrain],
            field_style["frame_color"],
            field_style["frame_width"],
            field_style["frame_rounding"],
            get_asset_path(field_style["images"][terrain]),
            field_style["image_size"],
            field_style["image_offset"],
            field_style["opacity"],
        )
        if ruin:
            self.blit(
                ImageSurf(
                    field_style["image_size"],
                    get_asset_path(field_style["ruin_overlay"]),
                ),
                field_style["image_offset"],
            )


class AreaSurf(pygame.Surface):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        frame_width: int,
        frame_color: Tuple[int, int, int],
        field_style: Dict[str, Any],
    ):
        """Surface of a singel area in the map or option card.

        Args:
            shape_coords (Frozenset[Tuple[int, int]]): List of coordinates of the area.
            terrain (Terrains): Terrain of the area. If None, only the frame is drawn.
            frame_width (int): Width of the frame.
            frame_color (Tuple[int, int, int]): Color of the frame.
            field_style: (Dict[str, Any]): Style dictionary for the fields.
        """
        super().__init__(
            (max(c[0] for c in shape_coords), max(c[1] for c in shape_coords)),
            pygame.SRCALPHA,
        )
        self.fill((0, 0, 0, 0))

        edges = set()
        for x, y in shape_coords:
            top_edge = ((x, y), (x + 1, y))
            bottom_edge = ((x, y + 1), (x + 1, y + 1))
            left_edge = ((x, y), (x, y + 1))
            right_edge = ((x + 1, y), (x + 1, y + 1))

            top = (x - 1, y)
            bottom = (x - 1, y)
            left = (x, y - 1)
            right = (x, y + 1)

            if top not in shape_coords:
                edges.add(top_edge)
            if bottom not in shape_coords:
                edges.add(bottom_edge)
            if left not in shape_coords:
                edges.add(left_edge)
            if right not in shape_coords:
                edges.add(right_edge)

        for edge in edges:
            pygame.draw.line(
                self,
                frame_color,
                (edge[0][0] * field_style["size"], edge[0][1] * field_style["size"]),
                (edge[1][0] * field_style["size"], edge[1][1] * field_style["size"]),
                frame_width,
            )

        if terrain is not None:
            for x, y in shape_coords:
                field_surf = FieldSurf(terrain, False, field_style)
                self.blit(
                    field_surf, (x * field_style["size"], y * field_style["size"])
                )


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
