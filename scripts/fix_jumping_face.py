#!/usr/bin/env python3
"""Rebuild the five jumping cells from the approved 10-o'clock-view strip."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont


CELL_WIDTH = 192
CELL_HEIGHT = 208
SHEET_SIZE = (1536, 2288)
JUMPING_ROW = 4
JUMPING_FRAMES = 5

# These common crop dimensions keep the feet registered while retaining the
# progressively bowed upper body from the generated five-panel source.
SOURCE_TOP = 100
SOURCE_BOTTOM = 725
SOURCE_CROP_WIDTH = 300
NORMALIZED_WIDTH = 95
NORMALIZED_HEIGHT = 198
NORMALIZED_TOP = 5
IDLE_SKIN_BASE = (243, 223, 215)


def largest_component(mask: list[bytearray], width: int, height: int) -> set[int]:
    """Return the largest 8-connected component in a binary mask."""
    visited = bytearray(width * height)
    largest: set[int] = set()

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or not mask[y][x]:
                continue

            component: set[int] = set()
            queue = deque([(x, y)])
            visited[index] = 1
            while queue:
                current_x, current_y = queue.popleft()
                current_index = current_y * width + current_x
                component.add(current_index)
                for offset_y in (-1, 0, 1):
                    for offset_x in (-1, 0, 1):
                        if offset_x == 0 and offset_y == 0:
                            continue
                        next_x = current_x + offset_x
                        next_y = current_y + offset_y
                        if not (0 <= next_x < width and 0 <= next_y < height):
                            continue
                        next_index = next_y * width + next_x
                        if visited[next_index] or not mask[next_y][next_x]:
                            continue
                        visited[next_index] = 1
                        queue.append((next_x, next_y))

            if len(component) > len(largest):
                largest = component

    return largest


def fill_component_holes(component: set[int], width: int, height: int) -> set[int]:
    """Keep pale enclosed details such as shirt and eye whites."""
    outside = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def add_if_outside(x: int, y: int) -> None:
        index = y * width + x
        if index in component or outside[index]:
            return
        outside[index] = 1
        queue.append((x, y))

    for x in range(width):
        add_if_outside(x, 0)
        add_if_outside(x, height - 1)
    for y in range(height):
        add_if_outside(0, y)
        add_if_outside(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= next_x < width and 0 <= next_y < height:
                add_if_outside(next_x, next_y)

    filled = set(component)
    for index, is_outside in enumerate(outside):
        if not is_outside:
            filled.add(index)
    return filled


def extract_character(panel: Image.Image) -> Image.Image:
    """Remove the baked neutral checkerboard and retain the character cutout."""
    rgb = panel.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    foreground = [bytearray(width) for _ in range(height)]

    for y in range(height):
        row = foreground[y]
        for x in range(width):
            red, green, blue = pixels[x, y]
            is_checker = min(red, green, blue) >= 235 and max(red, green, blue) - min(
                red, green, blue
            ) <= 12
            row[x] = 0 if is_checker else 1

    component = largest_component(foreground, width, height)
    component = fill_component_holes(component, width, height)
    result = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    result_pixels = result.load()
    for index in component:
        x = index % width
        y = index // width
        result_pixels[x, y] = (*pixels[x, y], 255)
    return result


def crop_with_padding(
    image: Image.Image, left: int, top: int, right: int, bottom: int
) -> Image.Image:
    output = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    source_box = (
        max(left, 0),
        max(top, 0),
        min(right, image.width),
        min(bottom, image.height),
    )
    if source_box[0] < source_box[2] and source_box[1] < source_box[3]:
        output.paste(
            image.crop(source_box),
            (source_box[0] - left, source_box[1] - top),
        )
    return output


def clear_transparent_rgb(image: Image.Image) -> None:
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0 and (red or green or blue):
                pixels[x, y] = (0, 0, 0, 0)


def match_idle_skin(frame: Image.Image) -> None:
    """Shift only warm skin pixels onto the idle sprite's skin palette."""
    pixels = frame.load()
    bright_skin: list[tuple[int, int, int]] = []

    def is_skin(red: int, green: int, blue: int) -> bool:
        if red < 95 or green < 70 or blue < 60:
            return False
        if not (6 <= red - green <= 85 and 0 <= green - blue <= 55):
            return False
        return blue / green >= 0.7

    for y in range(frame.height):
        for x in range(frame.width):
            red, green, blue, alpha = pixels[x, y]
            if (
                alpha
                and red >= 235
                and green >= 180
                and blue >= 160
                and is_skin(red, green, blue)
            ):
                bright_skin.append((red, green, blue))

    if not bright_skin:
        raise ValueError("Could not locate generated skin palette")

    source_base = tuple(
        round(median(color[channel] for color in bright_skin))
        for channel in range(3)
    )
    shift = tuple(target - source for target, source in zip(IDLE_SKIN_BASE, source_base))

    for y in range(frame.height):
        for x in range(frame.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha and is_skin(red, green, blue):
                pixels[x, y] = (
                    max(0, min(255, red + shift[0])),
                    max(0, min(255, green + shift[1])),
                    max(0, min(255, blue + shift[2])),
                    alpha,
                )


def normalize_frame(panel: Image.Image) -> Image.Image:
    character = extract_character(panel)
    alpha = character.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("No character found in generated panel")

    bottom_band_top = max(bbox[1], bbox[3] - 110)
    band_bbox = alpha.crop((0, bottom_band_top, character.width, bbox[3])).getbbox()
    if band_bbox is None:
        raise ValueError("Could not locate feet in generated panel")
    feet_center = (band_bbox[0] + band_bbox[2]) // 2

    crop_left = feet_center - SOURCE_CROP_WIDTH // 2
    cropped = crop_with_padding(
        character,
        crop_left,
        SOURCE_TOP,
        crop_left + SOURCE_CROP_WIDTH,
        SOURCE_BOTTOM,
    )
    normalized = cropped.resize(
        (NORMALIZED_WIDTH, NORMALIZED_HEIGHT),
        Image.Resampling.LANCZOS,
    )
    frame = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    frame.paste(
        normalized,
        ((CELL_WIDTH - NORMALIZED_WIDTH) // 2, NORMALIZED_TOP),
        normalized,
    )
    match_idle_skin(frame)
    clear_transparent_rgb(frame)
    return frame


def build_frames(generated_strip: Path) -> list[Image.Image]:
    strip = Image.open(generated_strip).convert("RGB")
    panel_edges = [
        round(index * strip.width / JUMPING_FRAMES)
        for index in range(JUMPING_FRAMES + 1)
    ]
    return [
        normalize_frame(
            strip.crop((panel_edges[index], 0, panel_edges[index + 1], strip.height))
        )
        for index in range(JUMPING_FRAMES)
    ]


def update_contact_sheet(path: Path, frames: list[Image.Image]) -> None:
    contact = Image.open(path).convert("RGB")
    header_height = 22
    cell_width = CELL_WIDTH // 2
    cell_height = CELL_HEIGHT // 2
    row_top = JUMPING_ROW * (header_height + cell_height) + header_height
    font = ImageFont.load_default()

    for column, frame in enumerate(frames):
        cell = Image.new("RGB", (cell_width, cell_height), "white")
        draw = ImageDraw.Draw(cell)
        for y in range(0, cell_height, 16):
            for x in range(0, cell_width, 16):
                if (x // 16 + y // 16) % 2:
                    draw.rectangle(
                        (x, y, min(x + 15, cell_width - 1), min(y + 15, cell_height - 1)),
                        fill=(232, 232, 232),
                    )
        sprite = frame.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        cell.paste(sprite.convert("RGB"), (0, 0), sprite.getchannel("A"))
        draw = ImageDraw.Draw(cell)
        draw.rectangle(
            (0, 0, cell_width - 1, cell_height - 1), outline=(24, 160, 88)
        )
        draw.text((3, 2), str(column), fill=(0, 0, 0), font=font)
        contact.paste(cell, (column * cell_width, row_top))
    contact.save(path, "PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("spritesheet.webp"))
    parser.add_argument(
        "--generated-strip",
        type=Path,
        default=Path("assets/generated/jumping-10oclock-strip.png"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()

    sheet = Image.open(args.source).convert("RGBA")
    if sheet.size != SHEET_SIZE:
        raise ValueError(f"Unexpected spritesheet size: {sheet.size}")
    frames = build_frames(args.generated_strip)
    for column, frame in enumerate(frames):
        sheet.paste(frame, (column * CELL_WIDTH, JUMPING_ROW * CELL_HEIGHT))
    clear_transparent_rgb(sheet)
    sheet.save(args.output, "WEBP", lossless=True, method=6, exact=True)

    if args.preview:
        frames[0].save(
            args.preview,
            "GIF",
            save_all=True,
            append_images=frames[1:],
            duration=190,
            loop=0,
            disposal=2,
        )
    if args.contact_sheet:
        update_contact_sheet(args.contact_sheet, frames)


if __name__ == "__main__":
    main()
