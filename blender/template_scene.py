"""Starter for a new Blender scene. Copy to blender/<name>.py, set NAME, fill in build_scene().

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
    --python blender/<name>.py                     # full render
  ... --python blender/<name>.py -- --frames 1,48,96  # preview stills only
  ... --python blender/<name>.py -- --no-render       # build + save .blend only
"""

import math
import os
import sys

import bpy

NAME = "template"
WIDTH = 640
HEIGHT = 480
FPS = 24
FRAME_END = 96

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.join(ROOT, "renders", NAME)
BLEND_PATH = os.path.join(PROJECT_DIR, "scene.blend")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "blender-frames")

BACKGROUND_HEX = "4A1220"
SUBJECT_HEX = "FFD000"


def srgb_to_linear(hex_color):
    hex_color = hex_color.lstrip("#")
    channels = [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels) + (1.0,)


def parse_args():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    frames = None
    if "--frames" in args:
        frames = [int(f) for f in args[args.index("--frames") + 1].split(",") if f]
    return "--no-render" in args, frames


def enum_choices(owner, prop):
    """Background Blender often reports dynamic enums as ['NONE']; a failed assignment lists the real ones."""
    try:
        setattr(owner, prop, "__invalid__")
    except TypeError as exc:
        message = str(exc)
        inner = message[message.find("(") + 1 : message.rfind(")")]
        return [part.strip().strip("'\"") for part in inner.split(",")]
    return []


def setup_render(scene):
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

    transforms = enum_choices(scene.view_settings, "view_transform")
    if "Standard" in transforms:
        scene.view_settings.view_transform = "Standard"


def set_world_color(scene, hex_color):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    background.inputs["Color"].default_value = srgb_to_linear(hex_color)
    background.inputs["Strength"].default_value = 1.0


def make_material(name, hex_color, roughness=0.9):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def add_area_light(name, location, rotation_deg, energy, size=3.0):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = tuple(math.radians(a) for a in rotation_deg)
    return light


def add_front_camera(scene, distance=7.0, lens=36.0):
    data = bpy.data.cameras.new("Camera")
    data.lens = lens
    camera = bpy.data.objects.new("Camera", data)
    scene.collection.objects.link(camera)
    camera.location = (0.0, -distance, 0.0)
    camera.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.camera = camera
    return camera


def key(obj, frame, location=None, rotation_deg=None, scale=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if rotation_deg is not None:
        obj.rotation_euler = tuple(math.radians(a) for a in rotation_deg)
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


def build_scene(scene):
    set_world_color(scene, BACKGROUND_HEX)
    add_front_camera(scene)
    add_area_light("Key", (-2.6, -4.2, 3.3), (58, -8, -28), 150)
    add_area_light("Fill", (3.4, -3.2, 0.6), (78, 6, 32), 100, size=4.5)

    bpy.ops.mesh.primitive_cube_add(size=1.4)
    subject = bpy.context.active_object
    subject.data.materials.append(make_material("Subject", SUBJECT_HEX))
    key(subject, 1, location=(0, 0, -0.6), rotation_deg=(0, 0, 0))
    key(subject, FRAME_END, location=(0, 0, 0), rotation_deg=(30, 45, 0))


def render(scene, frames):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if frames:
        for frame in frames:
            scene.frame_set(frame)
            scene.render.filepath = os.path.join(OUTPUT_DIR, f"preview{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    for old in os.listdir(OUTPUT_DIR):
        if old.startswith("preview"):
            os.remove(os.path.join(OUTPUT_DIR, old))
    scene.render.filepath = os.path.join(OUTPUT_DIR, "frame####")
    bpy.ops.render.render(animation=True)


def main():
    no_render, frames = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    os.makedirs(PROJECT_DIR, exist_ok=True)
    setup_render(scene)
    build_scene(scene)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    if not no_render:
        render(scene, frames)


if __name__ == "__main__":
    main()
