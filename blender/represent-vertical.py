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

NAME = "represent-vertical"
WIDTH = 480
HEIGHT = 640
FPS = 24
FRAME_END = 120

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND_PATH = os.path.join(ROOT, f"{NAME}.blend")
OUTPUT_DIR = os.path.join(ROOT, "renders", NAME, "blender-frames")

BACKGROUND_HEX = "1A0838"
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


def make_glossy(name, hex_color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = 0.12
    bsdf.inputs["Metallic"].default_value = 0.35
    for socket in ("Specular IOR Level", "Coat Weight"):
        if socket in bsdf.inputs:
            bsdf.inputs[socket].default_value = 1.0 if socket == "Coat Weight" else 0.8
    return material


def add_tetra(name, material, location, size):
    mesh = bpy.data.meshes.new(name)
    verts = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    mesh.from_pydata(verts, [], [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.scale = (size, size, size)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Bevel", "BEVEL")
    bevel.width = 0.14
    bevel.segments = 6
    bevel.limit_method = "NONE"
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def spin(obj, turns, frames=FRAME_END):
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert("rotation_euler", frame=1)
    obj.rotation_euler = tuple(math.radians(360 * t) for t in turns)
    obj.keyframe_insert("rotation_euler", frame=frames + 1)


def linearize(scene):
    for obj in scene.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        try:
            fcs = list(ad.action.fcurves)
        except AttributeError:
            fcs = [fc for layer in ad.action.layers for strip in layer.strips
                   for bag in strip.channelbags for fc in bag.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def build_scene(scene):
    set_world_color(scene, BACKGROUND_HEX)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    cam = add_front_camera(scene, distance=12.0)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 10.0
    cam.data.sensor_fit = "VERTICAL"
    cam.data.clip_end = 100

    add_area_light("Key", (-4, -6, 5), (60, 0, -30), 600, size=5)
    add_area_light("Rim", (5, -4, -3), (100, 0, 40), 500, size=5)
    add_area_light("Top", (0, -3, 8), (20, 0, 0), 300, size=6)

    cobalt = make_glossy("Cobalt", "1F4BFF")
    magenta = make_glossy("Magenta", "FF1FA8")
    orange = make_glossy("Orange", "FF7A00")
    mats = [cobalt, magenta, orange]
    # (x, y, depth y-axis away from camera, size, material, turns xyz)
    items = [
        (-2.0, 3.6, 3.0, 0.95, 0, (1, 2, -1)),
        (2.0, 3.2, -2.0, 0.65, 1, (-2, 1, 3)),
        (-1.8, 0.6, -4.0, 0.55, 2, (3, -1, 2)),
        (1.9, -0.4, 4.0, 1.05, 0, (-1, -2, 1)),
        (-1.2, -3.0, 0.0, 0.85, 1, (2, 3, -2)),
        (2.0, -3.7, -3.0, 0.6, 2, (-3, 2, 1)),
        (0.2, 4.5, -5.0, 0.4, 2, (4, -2, 1)),
        (-2.3, -1.6, 5.0, 0.45, 1, (-2, 4, 2)),
        (0.4, -1.4, -6.0, 0.35, 0, (1, 3, -4)),
    ]
    for i, (x, z, y, size, m, turns) in enumerate(items):
        obj = add_tetra(f"Tetra{i}", mats[m], (x, y, z), size)
        spin(obj, turns)
    linearize(scene)


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
    setup_render(scene)
    build_scene(scene)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    if not no_render:
        render(scene, frames)


if __name__ == "__main__":
    main()
