#!/usr/bin/env python3
"""Validate, alpha-composite, encode, and verify one project's image sequences.

Usage:
  python3 scripts/finalize_video.py <name> [--fps 24] [--frames 192]
      [--output renders/<name>/<name>.mp4]
      [--blender-frames PATH] [--overlay-frames PATH]
      [--overlay-behind-subject]

The default inputs are renders/<name>/blender-frames and
renders/<name>/motion-canvas. Older my-animation/renders/<name>-blender and
<name>-overlay projects are detected as a compatibility fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from render_utils import validate_sequence


ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="kebab-case project name")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--frames", type=int, help="expected frame count (inferred if omitted)")
    parser.add_argument("--output", type=Path, help="MP4 output path")
    parser.add_argument("--blender-frames", type=Path, help="override Blender sequence directory")
    parser.add_argument("--overlay-frames", type=Path, help="override overlay sequence directory")
    parser.add_argument(
        "--overlay-behind-subject",
        action="store_true",
        help="composite an opaque Motion Canvas background below transparent Blender frames",
    )
    parser.add_argument("--ffmpeg", help="use this ffmpeg executable")
    parser.add_argument("--ffprobe", help="use this ffprobe executable")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium")
    return parser.parse_args()


def workspace_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def choose_directory(explicit: Path | None, candidates: list[Path], description: str) -> Path:
    if explicit is not None:
        return workspace_path(explicit)
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*.png")):
            return candidate
    expected = ", ".join(str(path.relative_to(ROOT)) for path in candidates)
    raise FileNotFoundError(f"no {description} PNG sequence found; checked: {expected}")


def find_executable(explicit: str | None, command: str, package: str) -> str:
    if explicit:
        resolved = shutil.which(explicit) or (explicit if Path(explicit).is_file() else None)
        if resolved:
            return str(resolved)
        raise FileNotFoundError(f"{command} executable not found: {explicit}")
    resolved = shutil.which(command)
    if resolved:
        return resolved
    bundled = sorted((ROOT / "my-animation" / "node_modules" / package).glob(f"*/{command}"))
    if bundled:
        return str(bundled[0])
    raise FileNotFoundError(
        f"{command} is unavailable; install it or pass --{command} /path/to/{command}"
    )


def verify_video(ffprobe: str, output: Path, frames: int, fps: int, size: tuple[int, int]) -> dict:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,avg_frame_rate,nb_read_frames,pix_fmt:"
            "format=duration",
            "-of",
            "json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(result.stdout)
    streams = metadata.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(video_streams) != 1 or audio_streams:
        raise ValueError(
            f"expected exactly one video stream and no audio; got "
            f"{len(video_streams)} video and {len(audio_streams)} audio streams"
        )

    video = video_streams[0]
    expected_rate = Fraction(fps, 1)
    checks = {
        "codec": (video.get("codec_name"), "h264"),
        "size": ((video.get("width"), video.get("height")), size),
        "frame rate": (Fraction(video.get("avg_frame_rate", "0/1")), expected_rate),
        "frame count": (int(video.get("nb_read_frames", 0)), frames),
        "pixel format": (video.get("pix_fmt"), "yuv420p"),
    }
    failures = [f"{label}: got {actual}, expected {expected}" for label, (actual, expected) in checks.items() if actual != expected]
    duration = float(metadata.get("format", {}).get("duration", 0))
    expected_duration = frames / fps
    if abs(duration - expected_duration) > 1e-5:
        failures.append(f"duration: got {duration:g}s, expected {expected_duration:g}s")
    if failures:
        raise ValueError("encoded video verification failed: " + "; ".join(failures))
    return {
        "file": str(output),
        "codec": video["codec_name"],
        "width": video["width"],
        "height": video["height"],
        "fps": str(expected_rate),
        "frames": int(video["nb_read_frames"]),
        "duration_seconds": duration,
        "pixel_format": video["pix_fmt"],
        "audio_streams": 0,
        "bytes": output.stat().st_size,
    }


def main() -> int:
    args = parse_args()
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name) is None:
        raise ValueError("name must be a lowercase kebab-case project slug")
    if args.fps < 1:
        raise ValueError("--fps must be a positive integer")
    if args.frames is not None and args.frames < 1:
        raise ValueError("--frames must be a positive integer")
    if not 0 <= args.crf <= 51:
        raise ValueError("--crf must be between 0 and 51")

    project = ROOT / "renders" / args.name
    blender_dir = choose_directory(
        args.blender_frames,
        [
            project / "blender-frames",
            ROOT / "my-animation" / "renders" / f"{args.name}-blender",
        ],
        "Blender",
    )
    overlay_dir = choose_directory(
        args.overlay_frames,
        [
            project / "motion-canvas",
            ROOT / "my-animation" / "renders" / f"{args.name}-overlay",
            ROOT / "my-animation" / "renders" / args.name,
        ],
        "Motion Canvas",
    )

    blender_frames, width, height = validate_sequence(
        blender_dir,
        label="Blender",
        pattern=r"frame(\d{4})\.png",
        start=1,
        frames=args.frames,
    )
    overlay_frames, overlay_width, overlay_height = validate_sequence(
        overlay_dir,
        label="Motion Canvas",
        pattern=r"(\d{6})\.png",
        start=0,
        frames=args.frames or blender_frames,
        require_rgba=True,
    )
    if blender_frames != overlay_frames:
        raise ValueError(
            f"sequence lengths differ: Blender {blender_frames}, Motion Canvas {overlay_frames}"
        )
    if (width, height) != (overlay_width, overlay_height):
        raise ValueError(
            f"sequence sizes differ: Blender {width}x{height}, "
            f"Motion Canvas {overlay_width}x{overlay_height}"
        )

    output = workspace_path(args.output) if args.output else project / f"{args.name}.mp4"
    if output.suffix.lower() != ".mp4":
        raise ValueError(f"output must use the .mp4 extension: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.partial-{os.getpid()}.mp4")
    ffmpeg = find_executable(args.ffmpeg, "ffmpeg", "@ffmpeg-installer")
    ffprobe = find_executable(args.ffprobe, "ffprobe", "@ffprobe-installer")

    temporary.unlink(missing_ok=True)
    try:
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-y",
                "-v",
                "error",
                "-framerate",
                str(args.fps),
                "-start_number",
                "1",
                "-i",
                str(blender_dir / "frame%04d.png"),
                "-framerate",
                str(args.fps),
                "-start_number",
                "0",
                "-i",
                str(overlay_dir / "%06d.png"),
                "-filter_complex",
                (
                    "[1:v][0:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]"
                    if args.overlay_behind_subject
                    else "[0:v][1:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]"
                ),
                "-map",
                "[v]",
                "-frames:v",
                str(blender_frames),
                "-c:v",
                "libx264",
                "-preset",
                args.preset,
                "-crf",
                str(args.crf),
                "-r",
                str(args.fps),
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                "-f",
                "mp4",
                str(temporary),
            ],
            check=True,
        )
        report = verify_video(ffprobe, temporary, blender_frames, args.fps, (width, height))
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    report["file"] = str(output)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
