"""Shared validation helpers for the Blender/Motion Canvas render pipeline."""

from __future__ import annotations

import re
import struct
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_info(path: Path) -> tuple[int, int, int]:
    """Return PNG width, height, and IHDR color type."""
    with path.open("rb") as image:
        header = image.read(26)
    if len(header) < 26 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError(f"not a valid PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    color_type = header[25]
    if width < 1 or height < 1:
        raise ValueError(f"invalid PNG dimensions in {path}: {width}x{height}")
    return width, height, color_type


def validate_sequence(
    directory: Path,
    *,
    label: str,
    pattern: str,
    start: int,
    frames: int | None = None,
    require_rgba: bool = False,
) -> tuple[int, int, int]:
    """Validate a contiguous PNG sequence and return frame count and dimensions."""
    if not directory.is_dir():
        raise FileNotFoundError(f"{label} frame directory does not exist: {directory}")

    files = sorted(directory.glob("*.png"))
    expression = re.compile(pattern)
    indexed: dict[int, Path] = {}
    unexpected: list[str] = []
    for path in files:
        match = expression.fullmatch(path.name)
        if match is None:
            unexpected.append(path.name)
            continue
        index = int(match.group(1))
        if index in indexed:
            raise ValueError(f"duplicate {label} frame index {index} in {directory}")
        indexed[index] = path

    if unexpected:
        shown = ", ".join(unexpected[:5])
        suffix = " ..." if len(unexpected) > 5 else ""
        raise ValueError(f"unexpected PNGs in {label} frame directory: {shown}{suffix}")

    if frames is None:
        frames = len(indexed)
    if frames < 1:
        raise ValueError(f"no {label} frames found in {directory}")

    expected = set(range(start, start + frames))
    actual = set(indexed)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing indices {missing[:5]}")
        if extra:
            details.append(f"unexpected indices {extra[:5]}")
        raise ValueError(
            f"{label} frame sequence mismatch ({len(actual)} found, {frames} expected): "
            + "; ".join(details)
        )

    dimensions: tuple[int, int] | None = None
    for index in range(start, start + frames):
        path = indexed[index]
        width, height, color_type = png_info(path)
        if dimensions is None:
            dimensions = width, height
        elif dimensions != (width, height):
            raise ValueError(
                f"{label} frame size mismatch at {path.name}: "
                f"{width}x{height}, expected {dimensions[0]}x{dimensions[1]}"
            )
        if require_rgba and color_type != 6:
            raise ValueError(
                f"{label} frame must be RGBA PNG (IHDR color type 6): "
                f"{path.name} has color type {color_type}"
            )

    assert dimensions is not None
    return frames, dimensions[0], dimensions[1]
