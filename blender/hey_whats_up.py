"""Build and render the hand-wave Blender half of the hey-whats-up video."""

import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE = os.path.join(ROOT, "hand.blend")
OUTPUT = os.path.join(ROOT, "renders", "hey-whats-up")
BLENDER_FRAMES = os.path.join(OUTPUT, "blender-frames")
BLEND_FILE = os.path.join(OUTPUT, "scene.blend")

WIDTH = 640
HEIGHT = 480
FPS = 24
FRAME_START = 1
FRAME_END = 192
CAMERA_CENTER_Z = 0.2
ORTHO_HEIGHT = 6.2


def parse_args():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    source = SOURCE
    frames = None
    if "--source" in args:
        source = os.path.abspath(args[args.index("--source") + 1])
    if "--frames" in args:
        frames = [int(frame) for frame in args[args.index("--frames") + 1].split(",") if frame]
    return source, frames, "--no-render" in args


def srgb_to_linear(hex_color):
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ) + (1.0,)


def setup_scene(scene):
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.use_file_extension = True
    scene.render.filepath = os.path.join(BLENDER_FRAMES, "frame")


def make_background_material():
    material = bpy.data.materials.new("Studio Gradient")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links

    coordinates = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    gradient = nodes.new("ShaderNodeValToRGB")
    gradient.color_ramp.elements[0].position = 0.0
    gradient.color_ramp.elements[0].color = srgb_to_linear("#A99AD4")
    gradient.color_ramp.elements[1].position = 1.0
    gradient.color_ramp.elements[1].color = srgb_to_linear("#123E46")
    gradient.color_ramp.interpolation = "EASE"

    distance = nodes.new("ShaderNodeVectorMath")
    distance.operation = "DISTANCE"
    distance.inputs[1].default_value = (0.5, 0.53, 0.0)
    glow = nodes.new("ShaderNodeValToRGB")
    glow.color_ramp.elements[0].position = 0.0
    glow.color_ramp.elements[0].color = (0.36, 0.36, 0.36, 1.0)
    glow.color_ramp.elements[1].position = 0.48
    glow.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    glow.color_ramp.interpolation = "EASE"

    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = srgb_to_linear("#679B9A")
    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")

    links.new(coordinates.outputs["UV"], separate.inputs["Vector"])
    links.new(separate.outputs["Y"], gradient.inputs["Fac"])
    links.new(coordinates.outputs["UV"], distance.inputs[0])
    links.new(distance.outputs["Value"], glow.inputs["Fac"])
    links.new(glow.outputs["Color"], mix.inputs[0])
    links.new(gradient.outputs["Color"], mix.inputs[1])
    links.new(mix.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def add_backdrop(scene):
    half_height = ORTHO_HEIGHT / 2
    half_width = half_height * WIDTH / HEIGHT
    z_bottom = CAMERA_CENTER_Z - half_height
    z_top = CAMERA_CENTER_Z + half_height
    mesh = bpy.data.meshes.new("Studio Backdrop Mesh")
    mesh.from_pydata(
        [
            (-3, -half_width, z_bottom),
            (-3, half_width, z_bottom),
            (-3, half_width, z_top),
            (-3, -half_width, z_top),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="BackdropUV")
    for loop in mesh.loops:
        vertex = mesh.vertices[loop.vertex_index].co
        uv_layer.data[loop.index].uv = (
            (vertex.y + half_width) / (2 * half_width),
            (vertex.z - z_bottom) / ORTHO_HEIGHT,
        )
    backdrop = bpy.data.objects.new("Studio Backdrop", mesh)
    scene.collection.objects.link(backdrop)
    backdrop.data.materials.append(make_background_material())
    return backdrop


def add_area_light(scene, name, location, energy, size, color):
    light_data = bpy.data.lights.new(name, "AREA")
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light_data.color = color
    light = bpy.data.objects.new(name, light_data)
    scene.collection.objects.link(light)
    light.location = location
    direction = Vector((0, 0, -0.48)) - light.location
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return light


def add_camera(scene):
    camera_data = bpy.data.cameras.new("Wave Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ORTHO_HEIGHT
    camera_data.sensor_fit = "VERTICAL"
    camera_data.lens = 50
    camera_data.clip_start = 0.1
    camera_data.clip_end = 100
    camera = bpy.data.objects.new("Wave Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (10, 0, CAMERA_CENTER_Z)
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = bpy.data.objects["Hand (source mesh)"].rotation_quaternion.copy()
    scene.camera = camera
    return camera


def animate_pivot(pivot):
    keys = [
        (1, 0, 0),
        (7, -8, -0.08),
        (15, 11, 0.10),
        (23, -11, -0.10),
        (31, 11, 0.10),
        (39, -10, -0.09),
        (47, 11, 0.10),
        (54, 2, 0.02),
        (59, 0, 0),
        (62, -9, -0.07),
        (70, 12, 0.11),
        (78, -12, -0.10),
        (86, 12, 0.11),
        (94, -10, -0.09),
        (102, 10, 0.09),
        (108, 0, 0),
        (113, 0, 0),
        (116, -10, -0.08),
        (124, 12, 0.11),
        (132, -12, -0.11),
        (140, 12, 0.11),
        (148, -10, -0.09),
        (156, 10, 0.09),
        (164, 0, 0),
        (168, 0, 0),
        (171, -9, -0.07),
        (178, 11, 0.10),
        (185, -9, -0.08),
        (192, 0, 0),
    ]
    base_z = pivot.location.z
    for frame, angle, offset_x in keys:
        pivot.location = (0, offset_x, base_z)
        pivot.rotation_euler = (math.radians(angle), 0, 0)
        pivot.keyframe_insert(data_path="location", frame=frame, group="Wave")
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame, group="Wave")

    animation = pivot.animation_data
    if animation and animation.action:
        action = animation.action
        try:
            curves = list(action.fcurves)
        except AttributeError:
            curves = [
                curve
                for layer in action.layers
                for strip in layer.strips
                for channelbag in strip.channelbags
                for curve in channelbag.fcurves
            ]
        for curve in curves:
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.handle_left_type = "AUTO_CLAMPED"
                point.handle_right_type = "AUTO_CLAMPED"


def build_scene(source):
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Blender source asset not found: {source}")
    bpy.ops.wm.open_mainfile(filepath=source)
    scene = bpy.context.scene

    mesh_objects = [obj for obj in scene.objects if obj.type == "MESH"]
    hand = max(mesh_objects, key=lambda obj: len(obj.data.polygons), default=None)
    if hand is None:
        raise RuntimeError("hand.blend contains no mesh object to animate")
    if any(obj.type == "ARMATURE" for obj in scene.objects):
        raise RuntimeError("Expected the inspected unrigged hand; found an armature")
    if not hand.data.materials:
        raise RuntimeError("The hand mesh has no source material to preserve")

    hand.name = "Hand (source mesh)"
    hand.location = (0, 0, -0.48)
    bpy.context.view_layer.update()
    for obj in list(scene.objects):
        if obj != hand:
            bpy.data.objects.remove(obj, do_unlink=True)

    hand_world = hand.matrix_world.copy()
    pivot = bpy.data.objects.new("Wrist Wave Pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = (0, 0, -2.08)
    bpy.context.view_layer.update()
    hand.parent = pivot
    hand.matrix_parent_inverse = pivot.matrix_world.inverted()
    hand.matrix_world = hand_world

    setup_scene(scene)
    add_backdrop(scene)
    add_camera(scene)
    add_area_light(scene, "Soft Key", (-3.2, 2.8, 4.8), 1050, 4.0, (1.0, 0.91, 0.85))
    add_area_light(scene, "Front Fill", (3.0, -1.3, 5.5), 820, 4.5, (0.79, 0.89, 1.0))
    add_area_light(scene, "Top Rim", (0.2, 4.2, 3.0), 980, 3.0, (1.0, 0.83, 0.75))
    scene.world.color = (0.08, 0.15, 0.17)

    animate_pivot(pivot)
    scene.frame_set(FRAME_START)
    os.makedirs(BLENDER_FRAMES, exist_ok=True)
    os.makedirs(OUTPUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
    return scene


def render(scene, frames):
    full_render = frames is None
    frames = frames or list(range(FRAME_START, FRAME_END + 1))
    invalid = [frame for frame in frames if frame < FRAME_START or frame > FRAME_END]
    if invalid:
        raise ValueError(f"Requested frames outside {FRAME_START}-{FRAME_END}: {invalid}")
    if full_render:
        for filename in os.listdir(BLENDER_FRAMES):
            if filename.startswith("preview") and filename.endswith(".png"):
                os.remove(os.path.join(BLENDER_FRAMES, filename))
    for frame in frames:
        scene.frame_set(frame)
        suffix = f"frame{frame:04d}.png" if full_render else f"preview{frame:04d}.png"
        scene.render.filepath = os.path.join(BLENDER_FRAMES, suffix[:-4])
        bpy.ops.render.render(write_still=True)


def main():
    source, frames, no_render = parse_args()
    scene = build_scene(source)
    if not no_render:
        render(scene, frames)
        print(f"Rendered {len(frames) if frames else FRAME_END} Blender frames to {BLENDER_FRAMES}")


if __name__ == "__main__":
    main()
