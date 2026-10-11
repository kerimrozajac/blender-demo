"""Bright yellow cube on a deep burgundy poster. 640x480, 24 fps, 96 frames."""

import math
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

# --- output -----------------------------------------------------------------
WIDTH = 640
HEIGHT = 480
FPS = 24
FRAME_START = 1
FRAME_END = 96

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND_PATH = os.path.join(ROOT, "break-the-pattern.blend")
OUTPUT_DIR = os.path.join(ROOT, "my-animation", "renders", "break-the-pattern-blender")

# --- look -------------------------------------------------------------------
CUBE_SIZE = 1.42
BEVEL_WIDTH = 0.055
CAM_LENS = 36.0
CAM_DIST = 7.15
CUBE_HEX = "FFD000"
BURGUNDY_A = "4A1220"
BURGUNDY_B = "6A2838"

# Location (x, y, z) and euler degrees. Y stays 0 so the cube never
# approaches the fixed camera. Travel stays inside the frame while the
# cube shoots up, snaps sideways, and slams home with an overshoot.
LOCATIONS = {
    1: (0.00, 0.00, -0.58),
    4: (0.00, 0.00, -0.74),
    6: (0.00, 0.00, 0.02),
    12: (0.00, 0.00, 0.28),
    22: (0.00, 0.00, 0.24),
    28: (0.00, 0.00, 0.16),
    30: (0.06, 0.00, 0.12),
    32: (1.36, 0.00, 0.18),
    35: (1.46, 0.00, 0.10),
    42: (0.78, 0.00, 0.04),
    48: (0.16, 0.00, -0.02),
    52: (-0.28, 0.00, -0.13),
    56: (0.055, 0.00, 0.028),
    60: (0.00, 0.00, 0.00),
    96: (0.00, 0.00, 0.00),
}

# Absolute XYZ euler degrees. Values keep climbing so the spin does not
# take the short way home, then settle on a three-quarter view.
ROTATIONS = {
    1: (0.0, 0.0, 0.0),
    6: (70.0, 150.0, 50.0),
    14: (340.0, 520.0, 210.0),
    22: (640.0, 900.0, 390.0),
    30: (900.0, 1160.0, 530.0),
    38: (1040.0, 1320.0, 640.0),
    48: (1090.0, 1435.0, 715.0),
    54: (1110.0, 1392.0, 736.0),
    60: (1098.0, 1408.0, 728.0),
    96: (1098.0, 1408.0, 728.0),
}

CAM_BASE_LOC = (0.0, -CAM_DIST, 0.0)
CAM_BASE_ROT = (90.0, 0.0, 0.0)
# Brief shake as the cube slams through center. Offsets are added to the base.
CAMERA_SHAKE = {
    1: ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    50: ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    52: ((0.11, 0.0, -0.07), (0.85, 0.12, 0.65)),
    54: ((-0.10, 0.04, 0.08), (-0.7, -0.18, -0.55)),
    56: ((0.05, -0.02, -0.035), (0.35, 0.08, 0.22)),
    58: ((-0.02, 0.0, 0.012), (-0.12, 0.0, -0.08)),
    62: ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    96: ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
}


def srgb_to_linear(hex_color):
    hex_color = hex_color.lstrip("#")
    channels = [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def convert(channel):
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    return tuple(convert(channel) for channel in channels) + (1.0,)


def parse_args():
    if "--" not in sys.argv:
        return False, None
    args = sys.argv[sys.argv.index("--") + 1 :]
    no_render = "--no-render" in args
    frames = None
    if "--frames" in args:
        raw = args[args.index("--frames") + 1]
        frames = [int(piece) for piece in raw.split(",") if piece]
    return no_render, frames


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def set_render(scene):
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.use_sequencer = False
    scene.render.film_transparent = False
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_file_extension = True

    engine = None
    for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = candidate
            engine = candidate
            break
        except TypeError:
            continue
    if engine is None:
        raise RuntimeError("Could not assign an Eevee render engine")
    print("ENGINE", engine)

    eevee = scene.eevee
    if hasattr(eevee, "use_raytracing"):
        eevee.use_raytracing = False
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = 48
    if hasattr(eevee, "use_gtao"):
        eevee.use_gtao = True
        if hasattr(eevee, "gtao_distance"):
            eevee.gtao_distance = 0.25
        if hasattr(eevee, "gtao_factor"):
            eevee.gtao_factor = 0.45

    view = scene.view_settings
    # Background mode often leaves this dynamic enum unread until assignment.
    # A failed set lists the real identifiers in the TypeError.
    transforms = []
    try:
        view.view_transform = "__invalid__"
    except TypeError as exc:
        message = str(exc)
        start = message.find("(")
        end = message.rfind(")")
        if start != -1 and end != -1:
            transforms = [part.strip().strip("'\"") for part in message[start + 1 : end].split(",")]
    for name in ("Standard", "Khronos PBR Neutral", "AgX", "Filmic"):
        if name in transforms:
            view.view_transform = name
            break
    print("VIEW_TRANSFORMS", transforms)
    print("VIEW_TRANSFORM", view.view_transform)
    view.exposure = 0.0
    view.gamma = 1.0


def socket(node, *names):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    available = [item.name for item in node.inputs]
    raise KeyError(f"{node.bl_idname} has no {names}; inputs are {available}")


def output_socket(node, *names):
    for name in names:
        if name in node.outputs:
            return node.outputs[name]
    available = [item.name for item in node.outputs]
    raise KeyError(f"{node.bl_idname} has no {names}; outputs are {available}")


def build_world(scene):
    world = bpy.data.worlds.new("BurgundyPoster")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    for node in list(nodes):
        nodes.remove(node)

    output = nodes.new("ShaderNodeOutputWorld")
    background = nodes.new("ShaderNodeBackground")
    mix = nodes.new("ShaderNodeMix")
    noise = nodes.new("ShaderNodeTexNoise")
    mapped = nodes.new("ShaderNodeMapRange")
    coordinates = nodes.new("ShaderNodeTexCoord")

    mix.data_type = "RGBA"
    if hasattr(mix, "blend_type"):
        mix.blend_type = "MIX"
    noise.inputs["Scale"].default_value = 78.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.62
    mapped.inputs["From Min"].default_value = 0.15
    mapped.inputs["From Max"].default_value = 0.85
    mapped.inputs["To Min"].default_value = 0.0
    mapped.inputs["To Max"].default_value = 0.42

    socket(mix, "A", "A_Color").default_value = srgb_to_linear(BURGUNDY_A)
    socket(mix, "B", "B_Color").default_value = srgb_to_linear(BURGUNDY_B)
    background.inputs["Strength"].default_value = 1.0

    links.new(output_socket(coordinates, "Window"), noise.inputs["Vector"])
    links.new(output_socket(noise, "Fac"), mapped.inputs["Value"])
    links.new(output_socket(mapped, "Result"), socket(mix, "Factor", "Factor_Float"))
    links.new(output_socket(mix, "Result"), background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])

    output.location = (480, 0)
    background.location = (260, 0)
    mix.location = (40, 0)
    mapped.location = (-180, -40)
    noise.location = (-400, -40)
    coordinates.location = (-620, -40)


def assign_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return name
    return None


def build_cube():
    bpy.ops.mesh.primitive_cube_add(size=CUBE_SIZE, location=(0.0, 0.0, 0.0))
    cube = bpy.context.active_object
    cube.name = "Cube"
    cube.data.name = "Cube"
    cube.rotation_mode = "XYZ"

    bevel = cube.modifiers.new("RoundEdges", "BEVEL")
    bevel.width = BEVEL_WIDTH
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(40.0)
    if hasattr(bevel, "harden_normals"):
        bevel.harden_normals = True
    if hasattr(bevel, "miter_outer"):
        bevel.miter_outer = "MITER_ARC"

    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(50.0))
    except Exception as exc:
        print("AUTO_SMOOTH_SKIPPED", exc)
        for polygon in cube.data.polygons:
            polygon.use_smooth = True

    material = bpy.data.materials.new("BrightYellow")
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    assign_input(bsdf, ("Base Color",), srgb_to_linear(CUBE_HEX))
    assign_input(bsdf, ("Roughness",), 0.94)
    assign_input(bsdf, ("Metallic",), 0.0)
    assign_input(bsdf, ("Specular IOR Level", "Specular"), 0.12)
    assign_input(bsdf, ("Coat Weight", "Coat"), 0.0)
    assign_input(bsdf, ("Sheen Weight", "Sheen"), 0.0)
    cube.data.materials.append(material)
    return cube


def build_lights():
    key_data = bpy.data.lights.new("Key", "AREA")
    key_data.energy = 150.0
    key_data.shape = "RECTANGLE"
    key_data.size = 3.4
    key_data.size_y = 2.4
    key_data.color = srgb_to_linear("FFF6E8")[:3]
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (-2.6, -4.2, 3.3)
    key.rotation_euler = (math.radians(58.0), math.radians(-8.0), math.radians(-28.0))

    fill_data = bpy.data.lights.new("Fill", "AREA")
    fill_data.energy = 100.0
    fill_data.shape = "RECTANGLE"
    fill_data.size = 4.5
    fill_data.size_y = 3.0
    fill_data.color = srgb_to_linear("F3E4FF")[:3]
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (3.4, -3.2, 0.6)
    fill.rotation_euler = (math.radians(78.0), math.radians(6.0), math.radians(32.0))

    rim_data = bpy.data.lights.new("Rim", "AREA")
    rim_data.energy = 45.0
    rim_data.size = 2.2
    rim_data.color = srgb_to_linear("FFE7A8")[:3]
    rim = bpy.data.objects.new("Rim", rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim.location = (0.4, 3.6, 2.1)
    rim.rotation_euler = (math.radians(118.0), 0.0, math.radians(170.0))


def build_camera(scene):
    camera_data = bpy.data.cameras.new("Front")
    camera_data.lens = CAM_LENS
    camera_data.sensor_width = 36.0
    camera_data.clip_start = 0.1
    camera_data.clip_end = 100.0
    camera = bpy.data.objects.new("Front", camera_data)
    scene.collection.objects.link(camera)
    camera.rotation_mode = "XYZ"
    camera.location = CAM_BASE_LOC
    camera.rotation_euler = tuple(math.radians(axis) for axis in CAM_BASE_ROT)
    scene.camera = camera
    return camera


def iter_fcurves(obj):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    if getattr(action, "fcurves", None):
        yield from action.fcurves
        return
    slot = getattr(obj.animation_data, "action_slot", None)
    layers = getattr(action, "layers", None)
    if not layers:
        return
    for layer in layers:
        for strip in layer.strips:
            channelbag = None
            if hasattr(strip, "channelbag") and slot is not None:
                try:
                    channelbag = strip.channelbag(slot)
                except Exception:
                    channelbag = None
            if channelbag is None:
                continue
            yield from channelbag.fcurves


def clamp_handles(obj):
    count = 0
    for curve in iter_fcurves(obj):
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"
            count += 1
        if curve.data_path == "location" and curve.array_index == 0:
            for point in curve.keyframe_points:
                if point.co[0] in (30.0, 32.0):
                    point.interpolation = "LINEAR"
    print(f"KEYS {obj.name} {count}")


def key_transform(obj, frame, location=None, rotation_degrees=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)
    if rotation_degrees is not None:
        obj.rotation_euler = tuple(math.radians(axis) for axis in rotation_degrees)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def animate(cube, camera):
    for frame, location in LOCATIONS.items():
        key_transform(cube, frame, location=location)
    for frame, rotation in ROTATIONS.items():
        key_transform(cube, frame, rotation_degrees=rotation)
    for frame, (location_offset, rotation_offset) in CAMERA_SHAKE.items():
        location = tuple(base + offset for base, offset in zip(CAM_BASE_LOC, location_offset))
        rotation = tuple(base + offset for base, offset in zip(CAM_BASE_ROT, rotation_offset))
        key_transform(camera, frame, location=location, rotation_degrees=rotation)
    clamp_handles(cube)
    clamp_handles(camera)


def projected_bounds(scene, camera, cube, frame):
    scene.frame_set(frame)
    matrix = cube.matrix_world
    xs = []
    ys = []
    for corner in cube.bound_box:
        point = world_to_camera_view(scene, camera, matrix @ Vector(corner))
        xs.append(point.x)
        ys.append(point.y)
    center = world_to_camera_view(scene, camera, matrix @ Vector((0.0, 0.0, 0.0)))
    print(
        "BOUNDS",
        frame,
        f"x {min(xs):.3f} {max(xs):.3f}",
        f"y {min(ys):.3f} {max(ys):.3f}",
        f"mc {((center.x - 0.5) * WIDTH):.1f} {((center.y - 0.5) * HEIGHT):.1f}",
    )


def render(scene, frames):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if frames:
        for frame in frames:
            scene.frame_set(frame)
            scene.render.filepath = os.path.join(OUTPUT_DIR, f"preview{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("WROTE", scene.render.filepath)
        return
    scene.render.filepath = os.path.join(OUTPUT_DIR, "frame####")
    bpy.ops.render.render(animation=True)
    print("WROTE_ANIMATION", OUTPUT_DIR)


def main():
    no_render, frames = parse_args()
    clear_scene()
    scene = bpy.context.scene
    set_render(scene)
    build_world(scene)
    cube = build_cube()
    build_lights()
    camera = build_camera(scene)
    animate(cube, camera)

    meshes = [obj.name for obj in scene.objects if obj.type == "MESH"]
    print("MESHES", meshes)
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("SAVED", BLEND_PATH)

    sample_frames = frames or [1, 12, 32, 48, 52, 60, 96]
    for frame in sample_frames:
        projected_bounds(scene, camera, cube, frame)

    if no_render:
        return
    render(scene, frames)


if __name__ == "__main__":
    main()
