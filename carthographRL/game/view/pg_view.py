from typing import Tuple, List, FrozenSet, Dict, Any
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

# sprites should contain only the information necessary to draw themselfs, they do not contain any information about their position and no information about the game state
#       -however in some cases they can also contain some logic as this maked live much easier (e.g. the map sprite can contain the logic to get the hover coordinates)

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


def get_assets_path(base_path: Path, name: str):
    """Get the path to an asset. If the name is None return None.

    Args:
        base_path (Path): Base path to the assets folder.
        name (str): Name of the asset.

    Returns:
        Path: Path to the asset.
    """
    if name is None:
        return None
    return base_path / name


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
        image_size: Tuple[int, int] = None,
        image_offset: Tuple[int, int] = (0, 0),
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
            image_size (Tuple[int, int], optional): Size of the image. Defaults to None.
            image_offset (Tuple[int, int], optional): Offset of the image. Defaults to (0, 0).
        """
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        self.blit(
            RectSurf(size, frame_color, frame_width, backgound_color, frame_rounding),
            (0, 0),
        )
        if image is not None:
            self.blit(ImageSurf(image_size, image), image_offset)


class ScreenSurf(ImageRectSurf):
    def __init__(self, style: Dict[str, Any]):
        """Background surface for the game screen.

        Args:
            style (Dict[str, Any]): Style dictionary.
        """
        super().__init__(
            style["screen_size"],
            style["screen_color"],
            style["screen_frame_color"],
            style["screen_frame_width"],
            style["screen_frame_rounding"],
            get_assets_path(style["assets_folder"], style["screen_image"]),
            style["screen_image_size"],
            style["screen_image_offset"],
        )


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
        super().__init__(
            (style["field_size"], style["field_size"]),
            style["field_colors"][terrain],
            style["field_frame_color"],
            style["field_frame_width"],
            style["field_frame_rounding"],
            get_assets_path(style["assets_folder"], style["field_icons"][terrain]),
            style["field_icon_size"],
            style["field_icon_offset"],
        )
        if ruin:
            self.blit(
                ImageSurf(
                    style["field_icon_size"],
                    get_assets_path(
                        style["assets_folder"], style["field_ruin_overlay"]
                    ),
                ),
                style["field_icon_offset"],
            )

        if candidate:
            self.set_alpha(style["field_candidate_opacity"])
        else:
            self.set_alpha(style["field_opacity"])


class MapSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        map_values: List[List[Terrains]],
        ruin_coords: FrozenSet[Tuple[int, int]],
        candidate_coords: FrozenSet[Tuple[int, int]],
        candidate_terrain: Terrains,
        style: Dict[str, Any],
    ) -> None:
        super().__init__()

        # we need to store these values for inferrence of the field coordinates
        self._field_size = style["field_size"]
        self._padding = style["map_padding"]

        extent = len(map_values[0]) * style["field_size"] + style["map_padding"] * 2
        self.image = ImageRectSurf(
            (extent, extent),
            style["map_color"],
            style["map_frame_color"],
            style["map_frame_width"],
            style["map_frame_rounding"],
            get_assets_path(style["assets_folder"], style["map_image"]),
        )

        # here we have some code repetition, but it's not worth it to create a separate area class for this as the cases are always different in some way
        for x, row in enumerate(map_values):
            for y, terrain in enumerate(row):
                field_surf = FieldSurf(terrain, (x, y) in ruin_coords, False, style)
                self.image.blit(
                    field_surf,
                    (
                        x * style["field_size"] + style["map_padding"],
                        y * style["field_size"] + style["map_padding"],
                    ),
                )

        if candidate_coords is not None:
            for x, y in candidate_coords:
                field_surf = FieldSurf(
                    candidate_terrain, (x, y) in ruin_coords, True, style
                )
                self.image.blit(
                    field_surf,
                    (
                        x * style["field_size"] + style["map_padding"],
                        y * style["field_size"] + style["map_padding"],
                    ),
                )

        self.rect = self.image.get_rect()

    def get_mouse_grid_coords(self, mouse_pos: Tuple[int, int]):
        x = (mouse_pos[0] - self.rect.x - self._padding) // self._field_size
        y = (mouse_pos[1] - self.rect.y - self._padding) // self._field_size
        return x, y


class OptionSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        coin: bool,
        valid: bool,
        selected: bool,
        i_option: int,
        single_option: bool,
        style: Dict[str, Any],
    ) -> None:
        super().__init__()

        self.i_option = i_option

        size = style["option_size"]
        if single_option:
            size = (
                style["field_size"] + style["option_shape_offset"][0] * 2,
                style["field_size"] + style["option_shape_offset"][1] * 2,
            )
        if not selected:
            self.image = ImageRectSurf(
                size,
                style["option_color"],
                style["option_frame_color"],
                style["option_frame_width"],
                style["option_frame_rounding"],
                get_assets_path(style["assets_folder"], style["option_image"]),
            )
        else:
            self.image = ImageRectSurf(
                size,
                style["option_color_selected"],
                style["option_frame_color_selected"],
                style["option_frame_width_selected"],
                style["option_frame_rounding_selected"],
                get_assets_path(style["assets_folder"], style["option_image_selected"]),
            )

        if not valid:
            self.image = pygame.transform.grayscale(self.image)

        for x, y in coords:
            field_surf = FieldSurf(terrain, False, False, style)
            self.image.blit(
                field_surf,
                (
                    x * style["field_size"] + style["option_shape_offset"][0],
                    y * style["field_size"] + style["option_shape_offset"][1],
                ),
            )

        if not single_option:
            coin_surf = ImageRectSurf(
                style["option_coin_size"],
                style["option_coin_color"],
                style["option_coin_frame_color"],
                style["option_coin_frame_width"],
                style["option_coin_frame_rounding"],
                get_assets_path(style["assets_folder"], style["option_coin_image"]),
            )
            if not coin:
                coin_surf = pygame.transform.grayscale(coin_surf)

            self.image.blit(coin_surf, style["option_coin_offset"])

        self.rect = self.image.get_rect()


class OptionsBackgroundSurf(ImageRectSurf):
    def __init__(self, name, time, style: Dict[str, Any]) -> None:
        super().__init__(
            style["options_background_size"],
            style["options_background_color"],
            style["options_background_frame_color"],
            style["options_background_frame_width"],
            style["options_background_frame_rounding"],
            get_assets_path(style["assets_folder"], style["options_background_image"]),
        )


class ScoreTableSprite(pygame.sprite.Sprite):
    pass


class NextButtonSprite(pygame.sprite.Sprite):
    def __init__(self, clickable: bool, style) -> None:
        self.image = ImageRectSurf(
            style["next_button_size"],
            style["next_button_color"],
            style["next_button_frame_color"],
            style["next_button_frame_width"],
            style["next_button_frame_rounding"],
            get_assets_path(style["assets_folder"], style["next_button_image"]),
            style["next_button_image_size"],
            style["next_button_image_offset"],
        )

        if not clickable:
            self.image = pygame.transform.grayscale(self.image)


class InfoSprite(pygame.sprite.Sprite):
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
        self.style["assets_folder"] = (
            Path(__file__).parent / self.style["assets_folder"]
        )

        # pygame basic settings
        pygame.init()
        self.display = pygame.display.set_mode(self.style["screen_size"])
        self.display.blit(ScreenSurf(self.style), (0, 0))
        pygame.display.set_caption(self.style["title"])
        self.clock = pygame.time.Clock()
        self.frame_rate = frame_rate

        # sprites
        self._map_sprite = None
        self._option_sprites = []
        self._score_table_sprite = None
        self._next_button_sprite = None
        self._info_sprite = None

        # view state / selected action values
        self._act_i_option = None  # selected option index or terrain if singel option, None if no option selected
        self._act_position = None  # last clicked position on the map which is valid for the selected option
        self._act_rotation = 0
        self._act_mirror = False
        # self._act_single_field = None
        self._map_hover_coord = None  # last hovered position on the map which is valid for the selected option

    def _all_sprites(self) -> List[pygame.sprite.Sprite]:
        """Returns all sprites of the view. If the render methods hasn't been called
        before, the sprites can be None values.

        Returns:
            List[pygame.sprite.Sprite]: List of all sprites."""
        sprites = [
            self._map_sprite,
            # self._score_table_sprite,
            # self._next_button_sprite,
            # self._info_sprite,
        ] + self._option_sprites

        return sprites

    def _state_tuple(self):
        """Returns the current state of the view as a tuple. The state is used to
        check if the view has to be updated and to infer the selected action.
        It contains the following values:
            - i_option: Index of the selected option.
            - position: Position of the selected option.
            - rotation: Rotation of the selected option.
            - mirror: Mirror of the selected option.
        """
        return (
            self._act_i_option,
            self._act_position,
            self._act_rotation,
            self._act_mirror,
            self._map_hover_coord,
        )

    def _rebuild_option_sprites(self, game: CarthographersGame):
        self._option_sprites = []
        for i_opt, opt in enumerate(game.exploration_card.options):
            option_sprite = OptionSprite(
                opt.coords,
                opt.terrain,
                opt.coin,
                game.map_sheet.is_setable_anywhere(opt.coords, game.ruin),
                self._act_i_option == i_opt,
                i_opt,
                self.style,
            )
            option_sprite.rect.topleft = (
                self.style["options_position"][0]
                + i_opt * (option_sprite.rect.width + self.style["options_spacing"]),
                self.style["options_position"][1],
            )
            self._option_sprites.append(option_sprite)

        if game.setable_option_exists():
            return

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
                True,
                self._act_single_field == terrain,
                terrain,
                self.style,
            )
            single_option_sprite.rect.topleft = (
                self.style["options_position"][0]
                + i * (single_option_sprite.rect.width + self.style["options_spacing"]),
                self.style["options_position"][1],
            )
            self._option_sprites.append(single_option_sprite)

    def _option_terrain_coords(self, game):
        coords = None
        terrain = None
        if isinstance(self._act_i_option, Terrains):
            coords = frozenset([(0, 0)])
            terrain = self._act_i_option
        else:
            coords = game.exploration_card.options[self._act_i_option].coords
            terrain = game.exploration_card.options[self._act_i_option].terrain

        return terrain, coords

    def _rebuild_map_sprite(self, game: CarthographersGame):
        position = self._act_position or self._map_hover_coord
        if position is not None:
            terrain, coords = self._option_terrain_coords(game)
            coords = game.map_sheet.transform_to_map_coords(
                coords, self._act_rotation, position, self._act_mirror
            )

        self._map_sprite = MapSprite(
            game.map_sheet.to_list(),
            game.map_sheet.ruin_coords,
            coords,
            terrain,
            self.style,
        )
        self._map_sprite.rect.topleft = self.style["map_position"]

    def _rebuild_sprites(self, game: CarthographersGame):
        self._rebuild_map_sprite(game)
        self._rebuild_option_sprites(game)
        # self._rebuild_score_table_sprite(game)

        for sprite in self._all_sprites():
            self.display.blit(sprite.image, sprite.rect)
        pygame.display.flip()

    def _on_option_click(self, game: CarthographersGame, clicked_sprite: OptionSprite):
        if isinstance(clicked_sprite.i_option, int):
            option = game.exploration_card.options[clicked_sprite.i_option]
            valid = game.map_sheet.is_setable_anywhere(option.coords, game.ruin)
            if valid and self._act_i_option != clicked_sprite.i_option:
                self._act_i_option = clicked_sprite.i_option
                self._act_position = None
                self._act_rotation = 0
                self._act_mirror = False
        else:
            self._act_i_option = clicked_sprite.i_option

    def _get_sprites_under_mouse(self) -> Tuple[int, int]:
        mouse_pos = pygame.mouse.get_pos()

        clicked_sprites = [
            s for s in self._all_sprites() if s.rect.collidepoint(mouse_pos)
        ]
        return clicked_sprites

    def _on_map_click(self, game: CarthographersGame):
        if self._act_i_option is None:
            return

        map_coord = self._map_sprite.get_mouse_grid_coords(pygame.mouse.get_pos())
        if game.map_sheet.is_setable(
            game.exploration_card.options[self._act_i_option].coords,
            self._act_rotation,
            map_coord,
            self._act_mirror,
            game.ruin,
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
        clicked_sprites = self._get_sprites_under_mouse()
        for s in clicked_sprites:
            if s in self._option_sprites:
                self._on_option_click(game, s)

            if s == self._map_sprite:
                self._on_map_click(game)

            if s == self._next_button_sprite:
                self._on_next_button_click()

    def _on_key_press(self, pressed_key: int):
        if pressed_key == pygame.M:
            self._act_mirror = not self._act_mirror

        if pressed_key == pygame.R:
            self._act_rotation = (self._act_rotation + 1) % 4

    def _on_mouse_move(self):
        hovered_sprites = self._get_sprites_under_mouse()
        if self._map_sprite in hovered_sprites:
            self._map_hover_coord = self._map_sprite.get_mouse_grid_coords(
                pygame.mouse.get_pos()
            )
        else:
            self._map_hover_coord = None

    def _event_loop(self, game: CarthographersGame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_click(game)
            if event.type == pygame.KEYDOWN:
                self._on_key_press(event.key)
        self._on_mouse_move()

    def render(self, game: CarthographersGame):
        if None in self._all_sprites():
            logging.debug("Building sprites initially")
            self._rebuild_sprites(game)

        previous_state = self._state_tuple()
        action = self._event_loop(game)
        current_state = self._state_tuple()
        if previous_state != current_state:
            self._rebuild_sprites(game)
            logging.debug(
                f"i_option: {str(current_state[0]):<5}, "
                + f"position: {str(current_state[1]):<5}, "
                + f"rotation: {str(current_state[2]):<5}, "
                + f"mirror: {str(current_state[3]):<5}, "
                + f"single_field: {str(current_state[4]):<5}, "
                + f"hover_posiiton: {str(current_state[5]):<5}"
            )
        self.clock.tick(self.frame_rate)

        return action

    def cleanup(self):
        if not self.closed:
            raise RuntimeError("View is not closed")
        pygame.quit()
