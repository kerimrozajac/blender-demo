#!/usr/bin/env python3
"""Project a prepared logo texture onto a canopy mesh in the open Blender scene.

Example:
  Blender --background renders/project/scene.blend \
    --python scripts/add_canopy_decal.py -- \
    --surface Canopy --parent UmbrellaRoot --image assets/logo-print.png \
    --name Umbrella_Logo --center-radius 0.7 --width 0.35 --height 0.22 \
    --radial-offset-degrees 12 --frame 72 --save-as renders/project/scene.blend
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "blender"))

from logo_decal_utils import create_surface_decal  # noqa: E402


def workspace_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", required=True, help="Target canopy mesh object name")
    parser.add_argument("--parent", required=True, help="Object whose motion the decal follows")
    parser.add_argument("--image", required=True, help="Prepared transparent logo PNG")
    parser.add_argument("--camera", help="Camera object name; defaults to the scene camera")
    parser.add_argument("--name", default="Logo_Decal")
    parser.add_argument("--material", default="Logo_Print_Material")
    parser.add_argument("--frame", type=int, help="Frame used to choose the camera-facing panel")
    parser.add_argument("--radial-offset-degrees", type=float, default=0)
    parser.add_argument("--center-radius", type=float, required=True, help="Radius from canopy hub")
    parser.add_argument("--width", type=float, required=True, help="Tangential decal width")
    parser.add_argument("--height", type=float, required=True, help="Radial decal height")
    parser.add_argument("--columns", type=int, default=48)
    parser.add_argument("--rows", type=int, default=44)
    parser.add_argument("--ray-height", type=float, default=110)
    parser.add_argument("--surface-offset", type=float, default=0.08)
    parser.add_argument("--save-as", help="Optional output .blend path")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

    parent = bpy.data.objects.get(args.parent)
    surface = bpy.data.objects.get(args.surface)
    camera = bpy.data.objects.get(args.camera) if args.camera else bpy.context.scene.camera
    if parent is None:
        raise KeyError(f"Parent object not found: {args.parent}")
    if surface is None or surface.type != "MESH":
        raise TypeError(f"Surface must name a mesh object: {args.surface}")
    if camera is None or camera.type != "CAMERA":
        raise TypeError(f"Camera object not found or is not a camera: {args.camera}")
    if bpy.data.objects.get(args.name):
        raise ValueError(f"An object named {args.name!r} already exists")
    image_path = workspace_path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Prepared logo image not found: {image_path}")
    image = bpy.data.images.load(str(image_path), check_existing=True)
    decal = create_surface_decal(
        bpy.context.scene,
        parent,
        surface,
        image,
        name=args.name,
        material_name=args.material,
        camera=camera,
        sample_frame=args.frame,
        radial_offset_degrees=args.radial_offset_degrees,
        center_radius=args.center_radius,
        width=args.width,
        height=args.height,
        columns=args.columns,
        rows=args.rows,
        ray_height=args.ray_height,
        surface_offset=args.surface_offset,
    )
    print(
        f"Created {decal.name} with {len(decal.data.polygons)} faces on {surface.name}; "
        f"parented to {parent.name}"
    )
    if args.save_as:
        output_path = workspace_path(args.save_as)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        print(f"Saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
