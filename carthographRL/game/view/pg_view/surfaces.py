"""Contains subclasses of pygame.Surface that are used to draw the UI elements.
These subclasses always act as a alternate constructor for the pygame.Surface class
and do not provide any additional functionality or attributes.
Surfaces have no position. To draw them onto the screen thy should be encapsulated into a Sprite.
As some surfaces are used in different sprite classes they are defined here so that they can be reused.
On the other hand sprites should contain as less drawing logic as possible."""

from typing import Tuple, FrozenSet, Dict, Any, Union, List
from pathlib import Path

import pygame

from ..base import get_asset_path
from ...model.general import Terrains


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
        text: str = None,
        font: str = None,
        text_color: Tuple[int, int, int] = None,
        text_size: int = None,
        text_offset: Tuple[int, int] = None,
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

        if text is not None:
            font = pygame.font.SysFont(font, text_size)
            text_surf = font.render(text, True, text_color)
            self.blit(text_surf, text_offset)

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
            (
                (max(c[0] for c in shape_coords) + 1) * field_style["size"],
                (max(c[1] for c in shape_coords) + 1) * field_style["size"],
            ),
            pygame.SRCALPHA,
        )
        self.fill((0, 0, 0, 0))

        if terrain is not None:
            for x, y in shape_coords:
                field_surf = FieldSurf(terrain, False, field_style)
                self.blit(
                    field_surf, (x * field_style["size"], y * field_style["size"])
                )

        # we define the edges as rectangles as this avoids problems on the edges of the surface
        # TODO handle concave shapes (idea: use lines again but use larger surface to avoid problems on the edges)
        s = field_style["size"]
        d = frame_width
        edges = []
        for x, y in shape_coords:
            if (x - 1, y) not in shape_coords:  # left edge
                left_edge = (x * s, y * s, d, s)
                edges.append(left_edge)
            if (x + 1, y) not in shape_coords:  # right edge
                right_edge = ((x + 1) * s - d, y * s, d, s)
                edges.append(right_edge)
            if (x, y - 1) not in shape_coords:  # top edge
                top_edge = (x * s, y * s, s, d)
                edges.append(top_edge)
            if (x, y + 1) not in shape_coords:  # bottom edge
                bottom_edge = (x * s, (y + 1) * s - d, s, d)
                edges.append(bottom_edge)

        for edge in edges:
            pygame.draw.rect(self, frame_color, edge)


class TableSurf(pygame.Surface):
    def __init__(
        self,
        data: List[List[pygame.Surface]],
        vertical_line_widths: Union[int, List[int]],
        horizontal_line_widths: Union[int, List[int]],
        line_color: Tuple[int, int, int],
        row_heights: Union[int, List[int]] = None,
        col_widths: Union[int, List[int]] = None,
    ):
        if isinstance(vertical_line_widths, int):
            vertical_line_widths = [vertical_line_widths] * (len(data[0]) + 1)
        if isinstance(horizontal_line_widths, int):
            horizontal_line_widths = [horizontal_line_widths] * (len(data) + 1)

        if isinstance(row_heights, int):
            row_heights = [row_heights] * len(data)
        elif row_heights is None:
            row_heights = [
                max(s.get_height() for s in row if s is not None) for row in data
            ]

        if isinstance(col_widths, int):
            col_widths = [col_widths] * len(data[0])
        elif col_widths is None:
            col_widths = [
                max(s.get_width() for s in col if s is not None) for col in zip(*data)
            ]

        super().__init__(
            (
                sum(col_widths) + sum(vertical_line_widths),
                sum(row_heights) + sum(horizontal_line_widths),
            ),
            pygame.SRCALPHA,
        )
        self.fill((0, 0, 0, 0))

        for i, row in enumerate(data):
            for j, surf in enumerate(row):
                if surf is not None:
                    self.blit(
                        surf,
                        (
                            sum(col_widths[:j]) + sum(vertical_line_widths[: j + 1]),
                            sum(row_heights[:i]) + sum(horizontal_line_widths[: i + 1]),
                        ),
                    )

        for i in range(len(vertical_line_widths)):
            x = sum(col_widths[:i]) + sum(vertical_line_widths[:i])
            pygame.draw.rect(
                self,
                line_color,
                (x, 0, vertical_line_widths[i], self.get_height()),
            )

        for j in range(len(horizontal_line_widths)):
            y = sum(row_heights[:j]) + sum(horizontal_line_widths[:j])
            pygame.draw.rect(
                self,
                line_color,
                (0, y, self.get_width(), horizontal_line_widths[j]),
            )
