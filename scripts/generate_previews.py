#!/usr/bin/env python3
"""Generate README animation previews from the v2 spritesheet."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


CELL_WIDTH = 192
CELL_HEIGHT = 208


@dataclass(frozen=True)
class Preview:
    filename: str
    cells: tuple[tuple[int, int], ...]
    duration_ms: int


PREVIEWS = (
    Preview("preview-idle.gif", tuple((0, column) for column in range(7)), 280),
    Preview("preview-running-right.gif", tuple((1, column) for column in range(8)), 140),
    Preview("preview-running-left.gif", tuple((2, column) for column in range(8)), 140),
    Preview("preview-waving.gif", tuple((3, column) for column in range(4)), 220),
    Preview("preview-jumping.gif", tuple((4, column) for column in range(5)), 160),
    Preview("preview-failed.gif", tuple((5, column) for column in range(8)), 180),
    Preview("preview-waiting.gif", tuple((6, column) for column in range(6)), 240),
    Preview("preview-running.gif", tuple((7, column) for column in range(6)), 180),
    Preview("preview-review.gif", tuple((8, column) for column in range(6)), 220),
    Preview(
        "preview-look.gif",
        tuple((9, column) for column in range(8))
        + tuple((10, column) for column in range(8)),
        140,
    ),
)


def extract(sheet: Image.Image, row: int, column: int) -> Image.Image:
    left = column * CELL_WIDTH
    top = row * CELL_HEIGHT
    return sheet.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    sheet_path = args.root / "spritesheet.webp"
    sheet = Image.open(sheet_path).convert("RGBA")
    if sheet.size != (1536, 2288):
        raise ValueError(f"Unexpected spritesheet size: {sheet.size}")

    for preview in PREVIEWS:
        frames = [extract(sheet, row, column) for row, column in preview.cells]
        frames[0].save(
            args.root / preview.filename,
            "GIF",
            save_all=True,
            append_images=frames[1:],
            duration=preview.duration_ms,
            loop=0,
            disposal=2,
        )


if __name__ == "__main__":
    main()
