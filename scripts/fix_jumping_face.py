#!/usr/bin/env python3
"""Repair the jumping face and sharpen its forward glare.

Only the eyebrow pixels in row 4 are touched. The head silhouette,
hair, glasses, cheek blood, body, arms, hands, and legs stay byte-for-byte
identical at the decoded RGBA level.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL_WIDTH = 192
CELL_HEIGHT = 208
JUMPING_ROW = 4
JUMPING_FRAMES = 5

# Coordinates are local to a 192x208 frame. These small rectangles contain
# only the original brows and the skin immediately around them.
LEFT_BROW_CLEAR = (78, 47, 92, 51)
RIGHT_BROW_CLEAR = (100, 49, 110, 52)

SKIN = (243, 223, 215, 255)
BROW_EDGE = (111, 96, 92, 255)
BROW_DARK = (35, 27, 26, 255)


def frame_at(sheet: Image.Image, column: int) -> Image.Image:
    left = column * CELL_WIDTH
    top = JUMPING_ROW * CELL_HEIGHT
    return sheet.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))


def repair_expression(frame: Image.Image) -> Image.Image:
    fixed = frame.copy()
    draw = ImageDraw.Draw(fixed)

    # Remove the nearly horizontal brows, then redraw them descending toward
    # the bridge of the nose. The screen-right brow is shorter because the
    # existing fringe naturally covers its outer end.
    draw.rectangle(LEFT_BROW_CLEAR, fill=SKIN)
    draw.rectangle(RIGHT_BROW_CLEAR, fill=SKIN)
    draw.line(((78, 47), (84, 48), (91, 51)), fill=BROW_EDGE, width=2)
    draw.line(((79, 47), (85, 49), (91, 51)), fill=BROW_DARK, width=1)
    draw.line(((100, 51), (105, 49), (109, 48)), fill=BROW_EDGE, width=2)
    draw.line(((100, 51), (105, 49), (109, 48)), fill=BROW_DARK, width=1)

    return fixed


def build_sheet(source: Path) -> tuple[Image.Image, list[Image.Image]]:
    sheet = Image.open(source).convert("RGBA")
    if sheet.size != (1536, 2288):
        raise ValueError(f"Unexpected spritesheet size: {sheet.size}")

    frames = [repair_expression(frame_at(sheet, column)) for column in range(JUMPING_FRAMES)]
    for column, frame in enumerate(frames):
        sheet.paste(frame, (column * CELL_WIDTH, JUMPING_ROW * CELL_HEIGHT))
    return sheet, frames


def checker_cell() -> Image.Image:
    cell = Image.new("RGB", (CELL_WIDTH // 2, CELL_HEIGHT // 2), "white")
    draw = ImageDraw.Draw(cell)
    square = 16
    for y in range(0, cell.height, square):
        for x in range(0, cell.width, square):
            if (x // square + y // square) % 2:
                draw.rectangle(
                    (x, y, x + square - 1, y + square - 1),
                    fill=(232, 232, 232),
                )
    return cell


def update_contact_sheet(path: Path, frames: list[Image.Image]) -> None:
    contact = Image.open(path).convert("RGB")
    if contact.size != (768, 1386):
        raise ValueError(f"Unexpected contact sheet size: {contact.size}")

    header_height = 22
    cell_width = CELL_WIDTH // 2
    cell_height = CELL_HEIGHT // 2
    row_top = JUMPING_ROW * (header_height + cell_height) + header_height
    font = ImageFont.load_default()

    for column, frame in enumerate(frames):
        cell = checker_cell()
        sprite = frame.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        cell.paste(sprite.convert("RGB"), (0, 0), sprite.getchannel("A"))
        draw = ImageDraw.Draw(cell)
        draw.rectangle(
            (0, 0, cell_width - 1, cell_height - 1),
            outline=(24, 160, 88),
            width=1,
        )
        draw.text((3, 2), str(column), fill=(0, 0, 0), font=font)
        contact.paste(cell, (column * cell_width, row_top))

    contact.save(path, "PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("spritesheet.webp"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()

    sheet, frames = build_sheet(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, "WEBP", lossless=True, method=6, exact=True)

    if args.preview:
        frames[0].save(
            args.preview,
            "GIF",
            save_all=True,
            append_images=frames[1:],
            duration=160,
            loop=0,
            disposal=2,
        )

    if args.contact_sheet:
        update_contact_sheet(args.contact_sheet, frames)


if __name__ == "__main__":
    main()
