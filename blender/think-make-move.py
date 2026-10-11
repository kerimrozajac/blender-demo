"""Glossy purple sphere on pale mint paper. Orthographic, left side of frame."""

import math
import os
import sys

import bpy

NAME = "think-make-move"
WIDTH = 640
HEIGHT = 480
FPS = 24
FRAME_END = 144

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND_PATH = os.path.join(ROOT, f"{NAME}.blend")
OUTPUT_DIR = os.path.join(ROOT, "my-animation", "renders", f"{NAME}-blender")

MINT_A = "E7FBF3"
MINT_B = "C6EEDD"
PURPLE = "6D28D9"


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


def set_world_paper(scene):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    background = next(n for n in nodes if n.type == "BACKGROUND")
    background.inputs["Strength"].default_value = 1.0

    coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 80.0
    noise.inputs["Detail"].default_value = 2.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = srgb_to_linear(MINT_A)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = srgb_to_linear(MINT_B)
    links.new(coord.outputs["Window"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], background.inputs["Color"])


def make_glossy(name, hex_color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = 0.06
    for socket_name, value in (("Coat Weight", 0.45), ("Coat Roughness", 0.08), ("Specular IOR Level", 0.6)):
        socket = bsdf.inputs.get(socket_name)
        if socket is not None:
            socket.default_value = value
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


def add_point_light(name, location, energy):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    return light


def add_ortho_camera(scene, distance=12.0, ortho_scale=8.0):
    data = bpy.data.cameras.new("Camera")
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.sensor_fit = "VERTICAL"
    camera = bpy.data.objects.new("Camera", data)
    scene.collection.objects.link(camera)
    camera.location = (0.0, -distance, 0.0)
    camera.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.camera = camera
    return camera


def key(obj, frame, location=None, scale=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


def clamp_keys(obj):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    fcurves = getattr(action, "fcurves", None)
    if fcurves is None:
        try:
            slot = action.slots[0]
            fcurves = action.layers[0].strips[0].channelbag(slot).fcurves
        except (AttributeError, IndexError):
            return
    for curve in fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"


def build_scene(scene):
    set_world_paper(scene)
    add_ortho_camera(scene)
    add_area_light("Key", (-2.4, -6.5, 3.6), (62, 0, -24), 700, size=3.2)
    add_area_light("Fill", (2.2, -7.0, -1.4), (100, 8, 20), 180, size=5.0)
    add_point_light("Glint", (-2.0, -3.4, 2.6), 120)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, segments=48, ring_count=24)
    sphere = bpy.context.active_object
    for poly in sphere.data.polygons:
        poly.use_smooth = True
    sphere.data.materials.append(make_glossy("Sphere", PURPLE))

    # Stay inside the left half, travel bottom-left toward upper-left, squash, then exit.
    key(sphere, 1, location=(-3.4, 0.0, -2.6), scale=(1.0, 1.0, 1.0))
    key(sphere, 48, location=(-4.05, 0.0, 0.42), scale=(1.0, 1.0, 1.0))
    key(sphere, 52, location=(-4.08, 0.0, 0.28), scale=(1.14, 1.14, 0.74))
    key(sphere, 57, location=(-4.08, 0.0, 0.28), scale=(0.94, 0.94, 1.14))
    key(sphere, 66, location=(-4.45, 0.0, 1.35), scale=(1.0, 1.0, 1.0))
    key(sphere, 100, location=(-6.2, 0.0, 7.4), scale=(1.0, 1.0, 1.0))
    key(sphere, FRAME_END, location=(-7.4, 0.0, 11.0), scale=(1.0, 1.0, 1.0))
    clamp_keys(sphere)


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
