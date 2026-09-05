#!/usr/bin/env python3
"""Stabilize the writing animation in row 7 of the v2 pet spritesheet.

The first running frame is the canonical pose. Each later frame reuses that
pose pixel-for-pixel, then restores only the original writing-arm region and
the existing blink. A short ink trail is revealed across the loop.
"""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL_WIDTH = 192
CELL_HEIGHT = 208
COLUMNS = 8
ROWS = 11
RUNNING_ROW = 7
RUNNING_FRAMES = 6

# This polygon deliberately stops below the face. It contains the quill,
# writing sleeve, hand, and nib, while the head, torso, desk, and chair remain
# the canonical first-frame pixels.
WRITING_ARM_POLYGON = [
    (51, 78),
    (65, 75),
    (76, 80),
    (83, 95),
    (91, 103),
    (88, 111),
    (86, 124),
    (80, 129),
    (65, 125),
    (61, 116),
    (62, 104),
    (53, 99),
]

# The fifth frame is the original blink. These polygons stay strictly inside
# the lenses so the glasses remain the exact base-frame pixels.
BLINK_EYE_POLYGONS = [
    [(72, 62), (75, 60), (87, 60), (91, 63), (91, 69), (87, 73), (77, 73), (72, 69)],
    [(100, 62), (104, 60), (116, 60), (120, 63), (120, 69), (116, 73), (105, 73), (100, 69)],
]

# One-pixel handwritten wave, revealed from screen-right to screen-left so it
# follows the quill's motion. Every point is clipped to the paper; nothing is
# drawn at or behind the feather's upper end.
INK_PATH = [
    (99, 121),
    (98, 120),
    (97, 120),
    (96, 121),
    (95, 122),
    (94, 122),
    (93, 121),
    (92, 120),
    (91, 120),
    (90, 121),
    (89, 122),
    (88, 122),
    (87, 121),
    (86, 120),
    (85, 120),
    (84, 121),
]
# The feather moves screen-right to screen-left in frames 0 -> 1 -> 2.
# Start the stroke on frame 0 so the ink appears with the motion, not after it.
INK_STEPS = (4, 10, 16, 16, 16, 16)
INK_COLOR = (73, 42, 27, 255)
PAPER_INK_RECT = (82, 118, 101, 124)
PAPER_SURFACE_POLYGON = [
    (72, 111),
    (111, 112),
    (108, 125),
    (101, 131),
    (63, 129),
    (65, 119),
]
PAPER_COLOR = (244, 207, 166)
QUILL_EFFECT_RECT = (79, 101, 86, 109)
FEATHER_TOP_RECT = (45, 70, 70, 86)
SIDE_HAIR_RECT = (71, 61, 75, 70)


def extract_frame(sheet: Image.Image, column: int) -> Image.Image:
    left = column * CELL_WIDTH
    top = RUNNING_ROW * CELL_HEIGHT
    return sheet.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))


def build_running_frames(sheet: Image.Image) -> list[Image.Image]:
    donors = [extract_frame(sheet, column) for column in range(RUNNING_FRAMES)]
    base = donors[0]

    arm_mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(arm_mask).polygon(WRITING_ARM_POLYGON, fill=255)

    frames: list[Image.Image] = []
    for index, donor in enumerate(donors):
        # Remove ink produced by an earlier run before rebuilding the frame.
        # This keeps regeneration idempotent when the reveal direction changes.
        donor = donor.copy()
        donor_pixels = donor.load()
        base_pixels = base.load()
        left, top, right, bottom = PAPER_INK_RECT
        for y in range(top, bottom):
            for x in range(left, right):
                if donor_pixels[x, y] == INK_COLOR:
                    donor_pixels[x, y] = base_pixels[x, y]

        frame = base.copy()
        frame.paste(donor, (0, 0), arm_mask)
        # Replace the whole moving feather tip. The narrower arm polygon used
        # to leave the base frame's tip behind, creating a false "~~" trail.
        frame.paste(donor.crop(FEATHER_TOP_RECT), FEATHER_TOP_RECT)

        if index == 4:
            blink_mask = Image.new("L", base.size, 0)
            blink_draw = ImageDraw.Draw(blink_mask)
            for polygon in BLINK_EYE_POLYGONS:
                blink_draw.polygon(polygon, fill=255)
            frame.paste(donor, (0, 0), blink_mask)

        remove_side_hair(frame)
        remove_quill_effect(frame)
        flatten_paper(frame)

        ink_point_count = INK_STEPS[index]
        if ink_point_count > 1:
            ImageDraw.Draw(frame).line(
                INK_PATH[:ink_point_count], fill=INK_COLOR, width=1
            )

        frames.append(frame)

    return frames


def remove_side_hair(frame: Image.Image) -> None:
    """Remove the loose strand on Ivan's right (screen-left) temple."""
    pixels = frame.load()
    left, top, right, bottom = SIDE_HAIR_RECT
    for y in range(top, bottom):
        for x in range(left, right):
            pixels[x, y] = (0, 0, 0, 0)


def remove_quill_effect(frame: Image.Image) -> None:
    """Remove the stray cyan stroke beside the quill's upper-right corner."""
    pixels = frame.load()
    left, top, right, bottom = QUILL_EFFECT_RECT
    for y in range(top, bottom):
        for x in range(left, right):
            red, green, blue, alpha = pixels[x, y]
            is_cyan_effect = alpha > 40 and max(green, blue) > 35 and (
                green - red >= 18 or blue - red >= 18
            )
            if is_cyan_effect:
                pixels[x, y] = (4, 3, 2, alpha)


def flatten_paper(frame: Image.Image) -> None:
    """Replace the mottled paper texture with one warm parchment tone."""
    mask = Image.new("1", frame.size, 0)
    ImageDraw.Draw(mask).polygon(PAPER_SURFACE_POLYGON, fill=1)
    mask_pixels = mask.load()
    pixels = frame.load()

    for y in range(frame.height):
        for x in range(frame.width):
            if not mask_pixels[x, y]:
                continue

            red, green, blue, alpha = pixels[x, y]
            if alpha < 128:
                continue

            # Preserve the dark pen/outline and pale, near-neutral hand pixels.
            is_dark_foreground = max(red, green, blue) < 150
            is_pale_hand = min(red, green, blue) > 155 and max(
                red, green, blue
            ) - min(red, green, blue) < 18
            if is_dark_foreground or is_pale_hand:
                continue

            pixels[x, y] = (*PAPER_COLOR, alpha)


def clear_transparent_rgb(image: Image.Image) -> None:
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y][3] == 0:
                pixels[x, y] = (0, 0, 0, 0)


def save_lossless_webp(image: Image.Image, path: Path) -> None:
    original_mode = stat.S_IMODE(path.stat().st_mode)
    with tempfile.NamedTemporaryFile(
        suffix=".webp", dir=path.parent, delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        image.save(temp_path, "WEBP", lossless=True, method=6, exact=True)
        os.replace(temp_path, path)
        os.chmod(path, original_mode)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def checker_cell() -> Image.Image:
    cell = Image.new("RGB", (CELL_WIDTH // 2, CELL_HEIGHT // 2), "white")
    draw = ImageDraw.Draw(cell)
    square = 16
    for y in range(0, cell.height, square):
        for x in range(0, cell.width, square):
            if (x // square + y // square) % 2:
                draw.rectangle(
                    (x, y, x + square - 1, y + square - 1), fill=(232, 232, 232)
                )
    return cell


def update_contact_sheet(path: Path, frames: list[Image.Image]) -> None:
    if not path.exists():
        return

    contact = Image.open(path).convert("RGB")
    if contact.size != (768, 1386):
        raise ValueError(f"Unexpected contact sheet size: {contact.size}")

    header_height = 22
    cell_width = CELL_WIDTH // 2
    cell_height = CELL_HEIGHT // 2
    row_top = RUNNING_ROW * (header_height + cell_height) + header_height
    font = ImageFont.load_default()

    for column, frame in enumerate(frames):
        cell = checker_cell()
        sprite = frame.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        cell.paste(sprite.convert("RGB"), (0, 0), sprite.getchannel("A"))

        draw = ImageDraw.Draw(cell)
        draw.rectangle(
            (0, 0, cell_width - 1, cell_height - 1), outline=(24, 160, 88), width=1
        )
        draw.text((3, 2), str(column), fill=(0, 0, 0), font=font)
        contact.paste(cell, (column * cell_width, row_top))

    contact.save(path, "PNG", optimize=True)


def save_running_preview(path: Path, frames: list[Image.Image]) -> None:
    frames[0].save(
        path,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        disposal=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root containing spritesheet.webp",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="optional clean source spritesheet; output still goes to --root",
    )
    args = parser.parse_args()

    spritesheet_path = args.root / "spritesheet.webp"
    contact_sheet_path = args.root / "contact-sheet.png"
    running_preview_path = args.root / "preview-running.gif"
    source_path = args.source or spritesheet_path
    sheet = Image.open(source_path).convert("RGBA")
    expected_size = (CELL_WIDTH * COLUMNS, CELL_HEIGHT * ROWS)
    if sheet.size != expected_size:
        raise ValueError(f"Unexpected spritesheet size: {sheet.size}; expected {expected_size}")

    frames = build_running_frames(sheet)
    for column, frame in enumerate(frames):
        sheet.paste(
            frame,
            (column * CELL_WIDTH, RUNNING_ROW * CELL_HEIGHT),
        )

    clear_transparent_rgb(sheet)
    save_lossless_webp(sheet, spritesheet_path)
    update_contact_sheet(contact_sheet_path, frames)
    save_running_preview(running_preview_path, frames)


if __name__ == "__main__":
    main()
