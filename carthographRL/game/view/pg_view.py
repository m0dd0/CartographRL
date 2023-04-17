from typing import Tuple, List, FrozenSet, Dict, Any, Union
from pathlib import Path
import logging

import pygame
import yaml
from mergedeep import merge

from ..model import CarthographersGame
from ..model.general import Terrains
from .base import View

### DESIGN DECISIONS ###
# there are 3 geneal options to implement the view:
# - use a seperate sprite for everything (every field is a sprite, the grid is a sprite, the background is a sprite, the options are a sprite, the elements in the score table are sprites, ...)
#       - most flexible, can use pointcollide to check if mouse is in a sprite for all elements
#       - we need to keep track of all sprites and delete/update/add them when necessary
# use a seperate surface for everything (every field is a surface, the grid is a surface, the background is a surface, the options are a surface, the elements in the score table are surfaces, ...)
#       - all (point)collision management must be done manually
# use view sprites whose surface consistes of different more elementary surfaces (e.g. a map sprite whose surface consists of a background surface, a grid surface, and a surface for each field)
#       - only areas which might be clicked need to be checked for collision so we need only sprites for these few areas
# --> use sprite for each clickable/hoverable area: map, score table, each option, info field, next button

# use .png assets instead of .svg as it is easier to load them into pygame

# management of style parameters:
# - parameters must be stored in a seperate file as we want to allow for different styles
# - the style arguments are passed to the view as a dictionary to allow for flexible changing of the style (alternative would be to load the style globally)
# - as styled subelements are initialised in styled elements the passed style parameter must contain not only the style parameters for the styled element but also the style parameters for the subelements
# - however subelements might also occur in other styled elements so we can not nest the subelement style into the element style
# - therefore the most practical solution is to pass the whole style dictionary to each element and let the element decide which style parameters it needs
# - the nesting strucuture of the style dictionary is NOT necessarily the same as the nesting structure of the elements
# - as we have many style parameters nesting is preferrred over a flat structure TODO
###

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
        candidate: bool,
        style: Dict[str, Any],
    ) -> None:
        """Surface of a singel field in the map or option card.

        Args:
            terrain (Terrains): Terrain of the field.
            ruin (bool): Whether the field is a ruin.
            candidate (bool): Whether the field is a candidate for a move (opposed to already set field)
            style (Dict[str, Any]): Style dictionary.
        """
        terrain = terrain.name.lower()
        style = style["field"]
        super().__init__(
            (style["size"], style["size"]),
            style["colors"][terrain],
            style["frame_color"],
            style["frame_width"],
            style["frame_rounding"],
            get_asset_path(style["images"][terrain]),
            style["image_size"],
            style["image_offset"],
            style["opacity"],
        )
        if ruin:
            self.blit(
                ImageSurf(
                    style["image_size"],
                    get_asset_path(style["ruin_overlay"]),
                ),
                style["image_offset"],
            )

        if candidate:
            self.set_alpha(style["candidate_opacity"])


class ScreenSprite(pygame.sprite.Sprite):
    def __init__(self, style: Dict[str, Any]):
        """Background sprite for the game screen.

        Args:
            style (Dict[str, Any]): Style dictionary.
        """
        style = style["screen"]
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
        self.rect = self.image.get_rect()

        self.rect.topleft = (0, 0)


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
        self._candidate_map_coords = frozenset()
        self._candidate_terrain = None
        self._fixed_candidate = False
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

        for x, y in self._candidate_map_coords:
            # TODO different display for fixed candidates
            field_surf = FieldSurf(
                self.candidate_terrain, (x, y) in self._ruin_coords, True, self._style
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

    def candidate_position(self) -> Tuple[int, int]:
        """Returns the origin position of the candidate field in pixels.

        Returns:
            Tuple[int, int]: Origin position of the candidate field in pixels.
                None if there are no candidate fields.
        """
        if len(self.candidate_map_coords) == 0:
            return None

        x = min([x for x, _ in self.candidate_map_coords])
        y = min([y for _, y in self.candidate_map_coords])

        return x, y

    @property
    def map_values(self):
        return self._map_values

    @map_values.setter
    def map_values(self, map_values):
        self._map_values = map_values
        self._build()

    @property
    def candidate_map_coords(self):
        return self._candidate_map_coords

    @candidate_map_coords.setter
    def candidate_map_coords(self, candidate_map_coords):
        self._candidate_map_coords = candidate_map_coords
        if self._candidate_terrain is not None:
            self._build()

    @property
    def candidate_terrain(self):
        return self._candidate_terrain

    @candidate_terrain.setter
    def candidate_terrain(self, candidate_terrain):
        self._candidate_terrain = candidate_terrain
        if self._candidate_map_coords is not None:
            self._build()

    @property
    def fixed_candidate(self):
        return self._fixed_candidate

    @fixed_candidate.setter
    def fixed_candidate(self, fixed_candidate):
        self._fixed_candidate = fixed_candidate
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
        self._selected = False
        self._option_col = option_col
        self._style = style

        self.image = None
        self.rect = None
        self._build()

    def _build(self):
        """Builds the option surface depending on the current state of the option."""
        option_style = self._style["option"]
        if isinstance(self._i_option, Terrains):
            option_style = self._style["single_option"]

        style = option_style["normal"]
        if self._selected:
            style = option_style["selected"]

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
        for x, y in coords:
            field_surf = FieldSurf(self._terrain, False, False, self._style)
            self.image.blit(
                field_surf,
                (
                    x * self._style["field"]["size"] + option_style["shape_offset"][0],
                    y * self._style["field"]["size"] + option_style["shape_offset"][1],
                ),
            )

        if not isinstance(self._i_option, Terrains):
            coin_style = option_style["coin"]
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
            option_style["position"][0]
            + self._option_col * (style["size"][0] + option_style["spacing"]),
            option_style["position"][1],
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
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected):
        self._selected = selected
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

    def _selected_option_sprite(self) -> OptionSprite:
        for os in self._option_sprites:
            if os.selected:
                return os

        return None

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

    def _build_map_sprite(self, game: CarthographersGame):
        self._map_sprite = MapSprite(
            game.map_sheet.to_list(),
            game.map_sheet.ruin_coords,
            self.style,
        )

    def _on_option_click(self, option_sprite: OptionSprite):
        if option_sprite.valid and not option_sprite.selected:
            current_selected_option_sprite = self._selected_option_sprite()
            if current_selected_option_sprite is not None:
                current_selected_option_sprite.selected = False
            option_sprite.selected = True

    def _on_map_click(self, game: CarthographersGame):
        if self._map_sprite.candidate_map_coords is None:
            return
        self._map_sprite.fixed_candidate = not self._map_sprite.fixed_candidate

    def _on_map_mouse_move(self, game: CarthographersGame):
        map_coord = self._map_sprite.get_mouse_grid_coords(pygame.mouse.get_pos())
        selected_option_sprite = self._selected_option_sprite()
        if map_coord is None or selected_option_sprite is None:
            return

        if game.map_sheet.is_setable(
            selected_option_sprite.shape_coords,
            selected_option_sprite.rotation,
            map_coord,
            selected_option_sprite.mirror,
            game.ruin,
        ):
            self._map_sprite.candidate_map_coords = (
                game.map_sheet.transform_to_map_coords(
                    selected_option_sprite.shape_coords,
                    selected_option_sprite.rotation,
                    map_coord,
                    selected_option_sprite.mirror,
                )
            )
            self._map_sprite.candidate_terrain = selected_option_sprite.terrain

    def _on_mouse_move(self, game):
        hovered_sprites = self._sprites_under_mouse()
        if self._map_sprite in hovered_sprites:
            self._on_map_mouse_move(game)

    def _on_next_button_click(self):
        pass

    def _on_mouse_click(self, game: CarthographersGame):
        clicked_sprites = self._sprites_under_mouse()
        for s in clicked_sprites:
            if s in self._option_sprites:
                self._on_option_click(s)

            if s == self._map_sprite:
                self._on_map_click(game)

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
                self._on_mouse_click(game)
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
